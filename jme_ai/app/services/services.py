# app/services/services.py

import requests
import json
import psycopg2
import mysql.connector  # Importando o mysql.connector
from datetime import datetime
from flask import current_app as app
from config import Config
from .queries import create_table_queries

# DB Connections 
# PostgreSQL Connection 
postgres_connection = psycopg2.connect(
    host=Config.DB_JME_HOST,
    user=Config.DB_JME_USER,
    password=Config.DB_JME_PASSWORD,
    dbname=Config.DB_JME_NAME
)

# MySQL Connection 
mysql_connection = mysql.connector.connect(
    host=Config.DB_LETTEL_HOST,
    user=Config.DB_LETTEL_USER,
    password=Config.DB_LETTEL_PASSWORD,
    database=Config.DB_LETTEL_NAME
)

# JME DB - Functions
# Function to validate if table exists in DB JME
def table_exists(table_name):
    try:
        postgres_cursor = postgres_connection.cursor()
        postgres_cursor.execute(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{table_name}');")
        exists = postgres_cursor.fetchone()[0]
        postgres_cursor.close()
        return exists
    except Exception as error:
        app.logger.error(f'Erro ao verificar existencia da tabela {table_name}: {error}')
        return False

# Function to ensure that primordial tables exist in DB JME
def ensure_table_exists():
    for table_name, create_query in create_table_queries.items():
        if not table_exists(table_name):
            create_table(create_query)

# Function to create primordial tables in DB JME
def create_table(query):
    try: 
        postgres_cursor = postgres_connection.cursor()
        postgres_cursor.execute(query)
        postgres_connection.commit()
        postgres_cursor.close()
        app.logger.info(f"Tabela criada com sucesso ou já existente.")
    except Exception as error: 
        app.logger.error(f"Erro ao criar tabela: {error}")

# Function to import data from Lettel DB to JME DB
def import_data():
    try:
        ensure_table_exists()

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
                vqcf.duration,
                vqcf.agente,
                vct.speaker,
                vct.`start` AS start_time,
                vct.`end` AS end_time,
                vct.`text`                
            FROM v_cdr_transcriptions vct 
            INNER JOIN v_queue_calls_full vqcf ON vct.uniqueid = vqcf.callid 
            WHERE vct.uniqueid IN (
                SELECT callid FROM v_queue_calls_full vqcf2 
                WHERE timestamp BETWEEN '2024-06-01' AND '2024-07-18'
            );
            """
            mysql_cursor.execute(query)
            rows = mysql_cursor.fetchall()
            app.logger.info(f"Importando {len(rows)} registros do MySQL")

            postgres_cursor = postgres_connection.cursor()
            for row in rows:
                # Log do registro 
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
            app.logger.info("Dados importados com sucesso!")
        except mysql.connector.Error as mysql_error:
            app.logger.error(f"Erro ao interagir com MySQL: {mysql_error}")
        finally:
            mysql_cursor.close()
    except Exception as error:
        app.logger.error(f"Erro ao importar dados: {error}")

# Function to process data from tb_import_call - Reorganize rows to unique call for row
def process_data():
    try:
        ensure_table_exists()

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
            GROUP BY callid, caller_id, transfer, status, date, queue, holdtime, duration, agente
            ORDER BY date, callid, start_time ASC; 
            """
            postgres_cursor.execute(select_query)
            rows = postgres_cursor.fetchall()
            app.logger.info(f"Importando {len(rows)} registros da tabela tb_import_call")

            # Inserir os dados na tabela tb_info_call
            for row in rows:
                callid, caller_id, transfer, status, date, queue, holdtime, start_time, end_time, text, duration, agente = row
                try:
                    insert_query = """
                    INSERT INTO tb_info_call (callid, caller_id, transfer, status, date, queue, holdtime, start_time, end_time, text, duration, agente)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
        postgres_connection.rollback()
