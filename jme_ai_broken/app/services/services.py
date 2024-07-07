import requests
import json
import psycopg2
import mysql.connector
from datetime import datetime
from flask import current_app as app
from config import Config
from .db import get_postgres_connection

# Configuração da conexão com o banco de dados MySQL
mysql_connection = mysql.connector.connect(
    host=Config.DB_LETTEL_HOST,
    user=Config.DB_LETTEL_USER,
    password=Config.DB_LETTEL_PASSWORD,
    database=Config.DB_LETTEL_NAME
)

# Função de importação dos dados da Lettel e inserção na base da JME
def import_data():
    try:
        # Verificar se a tabela existe e criar se não existir
        if not table_exists('tb_import_call'):
            create_tables()

        mysql_cursor = mysql_connection.cursor(dictionary=True)
        try:
            query = """
            SELECT vct.uniqueid AS callid, 
                vqcf.caller_id,
                vqcf.transfer,
                vqcf.status,
                vqcf.`timestamp` AS date,
                vqcf.queue,
                vqcf.holdtime,
                vct.`start` AS start_time,
                vct.`end` AS end_time,
                vct.`text`,
                vqcf.duration,
                vqcf.agente 
            FROM v_cdr_transcriptions vct 
            INNER JOIN v_queue_calls_full vqcf ON vct.uniqueid = vqcf.callid 
            WHERE vct.uniqueid IN (
                SELECT callid FROM v_queue_calls_full vqcf2 
                WHERE timestamp BETWEEN '2024-01-01' AND '2024-06-01'
            );
            """
            mysql_cursor.execute(query)
            rows = mysql_cursor.fetchall()
            app.logger.info(f"Importando {len(rows)} registros do MySQL")

            postgres_connection = get_postgres_connection()
            postgres_cursor = postgres_connection.cursor()
            for row in rows:
                # Log do registro
                app.logger.debug(f"Registro do MySQL: {row}")

                callid = row['callid']
                caller_id = row['caller_id']
                transfer = row.get('transfer', 'N/A')
                status = row['status']
                date = row['date']
                queue = row['queue']
                holdtime = int(row['holdtime']) if row['holdtime'] else 0
                start_time = int(row['start_time']) if row['start_time'] else 0
                end_time = int(row['end_time']) if row['end_time'] else 0
                text = row['text']
                duration = int(row['duration'])
                agente = row.get('agente', 'N/A')

                try:
                    postgres_cursor.execute("""
                        INSERT INTO tb_import_call (callid, caller_id, transfer, status, date, queue, holdtime, start_time, end_time, text, duration, agente)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (callid, caller_id, transfer, status, date, queue, holdtime, start_time, end_time, text, duration, agente))
                    app.logger.info(f"Registro Inserido: {callid}, {caller_id}, {transfer}, {status}, {date}, {queue}, {holdtime}, {start_time}, {end_time}, {text}, {duration}, {agente}")
                except Exception as error:
                    app.logger.error(f"Erro ao inserir registro {callid}, {caller_id}, {transfer}, {status}, {date}, {queue}, {holdtime}, {start_time}, {end_time}, {text}, {duration}, {agente}: {error}")
                    postgres_connection.rollback()  # Reverter a transação para este registro

            postgres_connection.commit()
            postgres_cursor.close()
            app.logger.info("Dados importados com sucesso!")
        except mysql.connector.Error as mysql_error:
            app.logger.error(f"Erro ao interagir com MySQL: {mysql_error}")
        finally:
            mysql_cursor.close()
    except Exception as error:
        app.logger.error(f"Erro ao importar dados: {error}")

def table_exists(table_name):
    postgres_connection = get_postgres_connection()
    postgres_cursor = postgres_connection.cursor()
    postgres_cursor.execute(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{table_name}');")
    exists = postgres_cursor.fetchone()[0]
    postgres_cursor.close()
    return exists

def create_tables():
    postgres_connection = get_postgres_connection()
    postgres_cursor = postgres_connection.cursor()
    
    # Criação da tabela tb_import_call
    postgres_cursor.execute("""
    CREATE TABLE IF NOT EXISTS tb_import_call (
        id SERIAL PRIMARY KEY,
        callid VARCHAR(32) NOT NULL,
        caller_id VARCHAR(30) NOT NULL,
        transfer VARCHAR(30),
        status VARCHAR(30) NOT NULL,
        date DATE NOT NULL,
        queue VARCHAR(25) NOT NULL,
        holdtime INTEGER,
        start_time INTEGER NOT NULL,
        end_time INTEGER NOT NULL,
        text VARCHAR(1000),
        duration INT4 NOT NULL,
        agente VARCHAR(30)
    );
    """)
    
    # Criação da tabela tb_call_info
    postgres_cursor.execute("""
    CREATE TABLE IF NOT EXISTS tb_info_call (
        id SERIAL PRIMARY KEY,
        callid VARCHAR(32) NOT NULL,
        caller_id VARCHAR(30) NOT NULL,
        transfer VARCHAR(30),
        status VARCHAR(30) NOT NULL,
        date DATE NOT NULL,
        queue VARCHAR(25) NOT NULL,
        position INTEGER,
        original_position INTEGER,
        holdtime INTEGER,
        start_time INTEGER NOT NULL,
        end_time INTEGER NOT NULL,
        text VARCHAR(50000),
        duration INT4 NOT NULL,
        agente VARCHAR(30)
    );
    """)

    # Criação da tabela tb_analyst
    postgres_cursor.execute("""
    CREATE TABLE IF NOT EXISTS tb_analyst (
        id_analyst SERIAL PRIMARY KEY, 
        lettel_agent VARCHAR(20) NOT NULL, 
        name VARCHAR(40) NOT NULL,
        team VARCHAR(25) NOT NULL
    );
    """)

    postgres_connection.commit()
    postgres_cursor.close()
    app.logger.info("Tabelas criadas com sucesso!")

# Função para transformar e inserir dados da tabela tb_import_call para tb_call_info
def transform_and_insert_data():
    try:
        if not table_exists('tb_info_call'):
            create_tables()

        postgres_connection = get_postgres_connection()
        postgres_cursor = postgres_connection.cursor()

        select_query = """
        WITH ranked_calls AS (
            SELECT callid, caller_id, transfer, status, date, queue,
                   position, original_position, holdtime, start_time, end_time, text, duration, agente,
                   ROW_NUMBER() OVER (PARTITION BY callid ORDER BY end_time DESC) as rn
            FROM tb_import_call
        )
        SELECT callid, caller_id, transfer, status, date, queue, 
               MIN(position) as position, MIN(original_position) as original_position, 
               holdtime, MIN(start_time) as start_time, 
               MAX(CASE WHEN rn = 1 THEN end_time ELSE NULL END) as end_time, 
               STRING_AGG(text, ' ' ORDER BY start_time ASC) as text, 
               SUM(duration) as duration, agente
        FROM ranked_calls
        GROUP BY callid, caller_id, transfer, status, date, queue, agente
        """
        postgres_cursor.execute(select_query)
        rows = postgres_cursor.fetchall()
        columns = [desc[0] for desc in postgres_cursor.description]

        for row in rows:
            callid = row[columns.index('callid')]
            caller_id = row[columns.index('caller_id')]
            transfer = row[columns.index('transfer')] or 'N/A'
            status = row[columns.index('status')]
            date = row[columns.index('date')]
            queue = row[columns.index('queue')]
            position = row[columns.index('position')]
            original_position = row[columns.index('original_position')]
            holdtime = row[columns.index('holdtime')]
            start_time = row[columns.index('start_time')]
            end_time = row[columns.index('end_time')]
            text = row[columns.index('text')] or 'N/A'
            duration = row[columns.index('duration')]
            agente = row[columns.index('agente')] or 'N/A'

            # Ensure integer columns get NULL if value is None or not applicable
            position = int(position) if position else None
            original_position = int(original_position) if original_position else None
            holdtime = int(holdtime) if holdtime else None
            start_time = int(start_time) if start_time else None
            end_time = int(end_time) if end_time else None
            duration = int(duration) if duration else 0

            try:
                insert_query = """
                INSERT INTO tb_info_call (callid, caller_id, transfer, status, date, queue, position, original_position, holdtime, start_time, end_time, text, duration, agente)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                postgres_cursor.execute(insert_query, (callid, caller_id, transfer, status, date, queue, position, original_position, holdtime, start_time, end_time, text, duration, agente))
                app.logger.info(f"Dados transformados e inseridos para callid: {callid}")
            except Exception as error:
                app.logger.error(f"Erro ao inserir dados transformados para callid: {callid}: {error}")
                postgres_connection.rollback()

        postgres_connection.commit()
        postgres_cursor.close()
        app.logger.info("Dados transformados e inseridos com sucesso!")
    except Exception as error:
        app.logger.error(f"Erro ao transformar e inserir dados: {error}")
