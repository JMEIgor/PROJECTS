# app/services/services.py

import requests
import json
import psycopg2
import mysql.connector  # Importando o mysql.connector
from datetime import datetime
from flask import current_app as app
from config import Config
from .queries import create_table_queries
from .db import get_postgres_connection

# DB Connections 
# PostgreSQL Connection 
def get_postgres_connection():
    return psycopg2.connect(
        host=Config.DB_JME_HOST,    
        user=Config.DB_JME_USER,
        password=Config.DB_JME_PASSWORD,
        dbname=Config.DB_JME_NAME
    )

# MySQL Connection 
def get_mysql_connection(): 
    return mysql.connector.connect(
        host=Config.DB_LETTEL_HOST,
        user=Config.DB_LETTEL_USER,
        password=Config.DB_LETTEL_PASSWORD,
        database=Config.DB_LETTEL_NAME
    )

# Virtu - Functions
# Function to validate if table exists in DB JME
def table_exists(table_name, postgres_connection):
    try:
        with postgres_connection.cursor() as postgres_cursor:
            postgres_cursor.execute(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{table_name}');")
            exists = postgres_cursor.fetchone()[0]
        return exists
    except Exception as error:
        app.logger.error(f'Erro ao verificar existencia da tabela {table_name}: {error}')
        return False

# Function to ensure that primordial tables exist in DB JME
def ensure_table_exists(postgres_connection):
    for table_name, create_query in create_table_queries.items():
        if not table_exists(table_name, postgres_connection):
            create_table(create_query, postgres_connection)

# Function to create primordial tables in DB JME
def create_table(query, postgres_connection):
    try: 
        with postgres_connection.cursor() as postgres_cursor:
            postgres_cursor.execute(query)
        postgres_connection.commit()
        app.logger.info(f"Tabela criada com sucesso ou já existente.")
    except Exception as error: 
        app.logger.error(f"Erro ao criar tabela: {error}")
        postgres_connection.rollback()

# Function to import data from Lettel DB to JME DB
def import_data(date_entry, date_final):
    mysql_connection = None
    postgres_connection = None
    try:
        app.logger.info(f"Iniciando importacao de dados de {date_entry} ate {date_final}")

        postgres_connection = get_postgres_connection()
        ensure_table_exists(postgres_connection)

        mysql_connection = get_mysql_connection()

        date_entry = datetime.strptime(date_entry, '%Y-%m-%d')
        date_final = datetime.strptime(date_final, '%Y-%m-%d')

        app.logger.info(f"Consultando dados no MySQL entre {date_entry} ate {date_final}")
        
        mysql_cursor = mysql_connection.cursor(dictionary=True)
        query = """
        SELECT vct.uniqueid AS callid, 
            vqcf.caller_id,
            vqcf.transfer,
            vqcf.status,
            vqcf.timestamp AS date,
            vqcf.queue,
            vqcf.holdtime,
            vqcf.duration,
            vqcf.agente,
            vct.speaker,
            vct.start AS start_time,
            vct.end AS end_time,
            vct.text                
        FROM v_cdr_transcriptions vct 
        INNER JOIN v_queue_calls_full vqcf ON vct.uniqueid = vqcf.callid 
        WHERE vqcf.timestamp BETWEEN %s AND %s
        """
        mysql_cursor.execute(query, (date_entry, date_final))
        rows = mysql_cursor.fetchall()
        app.logger.info(f"Importando {len(rows)} registros do MySQL")

        postgres_cursor = postgres_connection.cursor()
        for row in rows:
            app.logger.debug(f"Registro do MySQL: {row}")
            try:
                callid = row['callid']
                caller_id = row['caller_id']
                transfer = row.get('transfer', 'N/A')
                status = row['status']
                date = row['date']
                queue = row['queue']
                holdtime = int(row['holdtime']) if row['holdtime'] else 0
                duration = int(row['duration'])
                agente = row.get('agente', 'N/A')
                speaker = row['speaker']
                start_time = int(row['start_time']) if row['start_time'] else 0
                end_time = int(row['end_time']) if row['end_time'] else 0
                text = row['text']
                
                postgres_cursor.execute("""
                INSERT INTO tb_import_call (callid, caller_id, transfer, status, date, queue, holdtime, duration, agente, speaker, start_time, end_time, text)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (callid, caller_id, transfer, status, date, queue, holdtime, duration, agente, speaker, start_time, end_time, text))
                app.logger.info(f"Registro Inserido: {callid}, {caller_id}, {transfer}, {status}, {date}, {queue}, {holdtime}, {duration}, {agente}, {speaker}, {start_time}, {end_time}, {text}")
            except Exception as error:
                app.logger.error(f"Erro ao inserir registro {callid}, {caller_id}, {transfer}, {status}, {date}, {queue}, {holdtime}, {duration}, {agente}, {speaker}, {start_time}, {end_time}, {text}: {error}")
                # Continua sem reverter a transação

        postgres_connection.commit()
        postgres_cursor.close()
        mysql_cursor.close()
        app.logger.info("Dados importados com sucesso!")
    except Exception as e:
        app.logger.error(f"Erro ao importar dados: {str(e)}")
    finally:
        if mysql_connection:
            mysql_connection.close()
        if postgres_connection:
            postgres_connection.close()

# Function to process data from tb_import_call - Reorganize rows to unique call for row
def process_data(date_entry, date_final):
    postgres_connection = None
    try:
        postgres_connection = get_postgres_connection()
        ensure_table_exists(postgres_connection)

        with postgres_connection.cursor() as postgres_cursor:
            # Selecionar os dados da tabela tb_import_call e agrupar por callid
            select_query = """
            SELECT callid, caller_id, transfer, status, date, queue, holdtime,
                MIN(start_time) as start_time, 
                MAX(end_time) as end_time, 
                STRING_AGG(
                    '(' || 
                    CASE 
                        WHEN speaker = 'A' or speaker = '1' THEN 'Atendente:' 
                        WHEN speaker = 'B' or speaker = '2' THEN 'Cliente:' 
                        ELSE speaker 
                    END || ', Start: ' || COALESCE(start_time::text, '') || ', End: ' || COALESCE(end_time::text, '') || ') ' || 
                    COALESCE(text, '') || E'\n', 
                    '' ORDER BY start_time
                ) as text, 
                duration, agente
            FROM tb_import_call
            WHERE date BETWEEN %s AND %s
            GROUP BY callid, caller_id, transfer, status, date, queue, holdtime, duration, agente
            ORDER BY date, callid, start_time ASC; 
            """
            postgres_cursor.execute(select_query, (date_entry, date_final))
            rows = postgres_cursor.fetchall()
            app.logger.info(f"Importando {len(rows)} registros da tabela tb_import_call")

            # Inserir os dados na tabela tb_info_call
            for row in rows:
                callid, caller_id, transfer, status, date, queue, holdtime, start_time, end_time, text, duration, agente = row
                try:
                    insert_query = """
                    INSERT INTO tb_info_call (callid, caller_id, transfer, status, date, queue, holdtime, start_time, end_time, text, duration, agente)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING
                    """
                    postgres_cursor.execute(insert_query, (callid, caller_id, transfer, status, date, queue, holdtime, start_time, end_time, text, duration, agente))
                    app.logger.info(f"Registro Inserido: {callid}, {caller_id}, {transfer}, {status}, {date}, {queue}, {holdtime}, {start_time}, {end_time}, {text}, {duration}, {agente}")
                except Exception as error:
                    app.logger.error(f"Erro ao inserir registro {callid}: {error}")
                    postgres_connection.rollback()  # Reverter a transação para este registro
                    raise  # Interromper o processo e reverter a transação completa

            postgres_connection.commit()
            app.logger.info("Dados importados para tb_info_call com sucesso!")
    except Exception as error:
        app.logger.error(f"Erro ao importar dados para tb_info_call: {error}")
        if postgres_connection:
            postgres_connection.rollback()
    finally:
        if postgres_connection:
            postgres_connection.close()
