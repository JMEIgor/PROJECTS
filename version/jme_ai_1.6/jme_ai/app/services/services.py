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

#MySQL Connection 
mysql_connection = mysql.connector.connect(
    host=Config.DB_LETTEL_HOST,
    user=Config.DB_LETTEL_USER,
    password=Config.DB_LETTEL_PASSWORD,
    database=Config.DB_LETTEL_NAME
)

# JME DB - Functions
#Function to validade if table exists no DB JME
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

#Function to ensure that primordial tables exists on DB JME
def ensure_table_exists():
    for table_name, create_query in create_table_queries.items():
        if not table_exists(table_name):
            create_table(create_query)

# Function to create primordial tables on DB JME
def create_table(query):
    try: 
        postgres_cursor = postgres_connection.cursor()
        postgres_cursor.execute(query)
        postgres_connection.commit()
        postgres_cursor.close()
        app.logger.info(f"Tabela criada com sucesso ou ja existente.")
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
                vct.`start` AS start_time,
                vct.`end` AS end_time,
                vct.`text`,
                vqcf.duration,
                vqcf.agente 
            FROM v_cdr_transcriptions vct 
            INNER JOIN v_queue_calls_full vqcf ON vct.uniqueid = vqcf.callid 
            WHERE vct.uniqueid IN (
                SELECT callid FROM v_queue_calls_full vqcf2 
                WHERE timestamp BETWEEN '2024-06-04' AND '2024-06-10'
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
                    start_time = int(row['start_time']) if row['start_time'] else 0
                    end_time = int(row['end_time']) if row['end_time'] else 0
                    text = row['text']
                    duration = int(row['duration'])
                    agente = row.get('agente', 'N/A')

                    postgres_cursor.execute("""
                    INSERT INTO tb_import_call (callid, caller_id, transfer, status, date, queue, holdtime, start_time, end_time, text, duration, agente)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (callid, caller_id, transfer, status, date, queue, holdtime, start_time, end_time, text, duration, agente))
                    app.logger.info(f"Registro Inserido: {callid}, {caller_id}, {transfer}, {status}, {date}, {queue}, {holdtime}, {start_time}, {end_time}, {text}, {duration}, {agente}")
                except Exception as error:
                    app.logger.error(f"Erro ao inserir registro {callid}, {caller_id}, {transfer}, {status}, {date}, {queue}, {holdtime}, {start_time}, {end_time}, {text}, {duration}, {agente}: {error}")
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
        
