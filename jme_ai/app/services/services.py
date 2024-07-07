# app/services/services.py

import requests
import json
import psycopg2
import mysql.connector  # Importando o mysql.connector
from datetime import datetime
from flask import current_app as app
from config import Config

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
# Function to validade if primordial tables exists, if not, create them 
def create_tables():
    try: 
        postgres_cursor = postgres_connection.cursor()

        create_table_queries = [
            """
            CREATE TABLE IF NOT EXISTS tb_analyst (
                id_analyst SERIAL PRIMARY KEY,
                lettel_agent VARCHAR(20) NOT NULL,
                name VARCHAR(40) NOT NULL,
                team VARCHAR(25) NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS tb_gpt_output (
                id SERIAL PRIMARY KEY,
                uid_call VARCHAR(32) NOT NULL,
                dt_call DATE NOT NULL,
                id_speaker VARCHAR(8) NOT NULL,
                id_caller VARCHAR(30) NOT NULL,
                tx_response TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS tb_info_call (
                id SERIAL PRIMARY KEY,
                callid VARCHAR(32) NOT NULL,
                caller_id VARCHAR(30) NOT NULL,
                transfer VARCHAR(30),
                status VARCHAR(30) NOT NULL,
                date DATE NOT NULL,
                queue VARCHAR(25) NOT NULL,
                position INT,
                original_position INT,
                holdtime INT,
                start_time INT NOT NULL,
                end_time INT NOT NULL,
                text VARCHAR(50000),
                duration INT NOT NULL,
                agente VARCHAR(30)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS tb_import_call (
                id SERIAL PRIMARY KEY,
                callid VARCHAR(32) NOT NULL,
                caller_id VARCHAR(30) NOT NULL,
                transfer VARCHAR(30),
                status VARCHAR(30) NOT NULL,
                date DATE NOT NULL,
                queue VARCHAR(25) NOT NULL,
                holdtime INT,
                start_time INT NOT NULL,
                end_time INT NOT NULL,
                text VARCHAR(1000),
                duration INT NOT NULL,
                agente VARCHAR(30)
            );
            """
        ]

        for query in create_table_queries:
            postgres_cursor.execute(query)

        postgres_cursor.execute(create_table_query)
        postgres_connection.commit()
        postgres_cursor.close()
        app.logger.info("Tabela criada ou já existente.")
    except Exception as error:
        app.logger.error(f"Erro ao criar tabelas: {error}")

# Function to import data from Lettel DB to JME DB
# Função de importação dos dados da Lettel e inserção na base da JME
def import_data():
    try:
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
                WHERE timestamp BETWEEN '2024-07-01' AND '2024-01-01'
            );
            """
            mysql_cursor.execute(query)
            rows = mysql_cursor.fetchall()
            app.logger.info(f"Importando {len(rows)} registros do MySQL")

            postgres_cursor = postgres_connection.cursor()
            for row in rows:
                # Log do registro 
                app.logger.debug(f"Registro do MySQL: {row}")

                callid = row['callid']
                caller_id = row['caller_id']
                transfer = row['transfer']
                status = row['status']
                date = row['date']
                queue = row['queue']
                holdtime = int(row['holdtime']) if row['holdtime'] else None
                start_time = int(row['start_time']) if row['start_time'] else None
                end_time = int(row['end_time']) if row['end_time'] else None
                text = row['text']
                duration = int(row['duration'])
                agente = row['agente']

                try:
                    postgres_cursor.execute("""
                    INSERT INTO tb_import_call (callid, caller_id, transfer, status, date, queue, holdtime, start_time, end_time, text, duration, agente)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (callid, caller_id, transfer, status, date, queue, holdtime, start_time, end_time, text, duration, agente))
                    app.logger.info(f"Registro Inserido: {row['callid'], row['caller_id'], row['transfer'], row['status'], row['date'], row['queue'], row['holdtime'], row['start_time'], row['end_time'], row['text'], row['duration'], row['agente']}")
                except Exception as error:
                    app.logger.error(f"Erro ao inserir registro {row['callid'], row['caller_id'], row['transfer'], row['status'], row['date'], row['queue'], row['holdtime'], row['start_time'], row['end_time'], row['text'], row['duration'], row['agente']}: {error}")

            postgres_connection.commit()
            app.logger.info("Dados importados com sucesso!")
        except Exception as error:
            app.logger.error(f"Erro ao interagir com MySQL: {error}")
        finally:
            mysql_cursor.close()
    except Exception as error:
        app.logger.error(f"Erro ao importar dados: {error}")


#GPT  Functions 
# main page input to chatgpt and return response on main page screen 
def call_chatgpt_api(prompt):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {Config.OPENAI_API_KEY}'
    }
    data = {
        'model': 'gpt-4',
        'messages': [
            {'role': 'system', 'content': 'Você é um assistente de trabalho e está encarregado de analisar transcrição de ligações e identificar o assunto principal da ligação e detalhar o que foi resolvido'},
            {'role': 'user', 'content': prompt}
        ]
    }
    try:
        response = requests.post(Config.API_URL, headers=headers, json=data)
        response.raise_for_status()
        response_json = response.json()
        app.logger.debug(f"Resposta da API do ChatGPT (JSON): {response_json}")
        return response_json
    except requests.exceptions.RequestException as error:
        app.logger.error(f"Erro ao chamar a API do ChatGPT: {error}")
        return None
    except json.JSONDecodeError as json_error:
        app.logger.error(f"Erro ao decodificar JSON: {json_error}")
        return {"error": "Invalid JSON response from ChatGPT"}


#JME to GPT - Functions  
# Process JME DB data and send to chatgpt analysis 
def process_and_send_data():
    try:
        postgres_cursor = postgres_connection.cursor()
        query = "SELECT text FROM tb_ligacoes WHERE uniqueid = ''"
        postgres_cursor.execute(query)
        rows = postgres_cursor.fetchall()
        columns = [desc[0] for desc in postgres_cursor.description]

        # Formatar os dados como string para enviar ao ChatGPT 
        data_string = "\n".join([str(dict(zip(columns, row))) for row in rows])

        prompt = f"A JME é uma empresa de prestação de serviços. Atuamos como Representação de Software da Sysmo Sistemas. A Sysmo Sistemas desenvolve software especializado para supermercados. Nossa maior demanda é no Suporte Técnico nos produtos Sysmo, que incluem ERP, PDV, aplicativos móveis CRM e Pricing. Buscamos otimizar a avaliação das ligações de suporte técnico para garantir um atendimento de alta qualidade e eficiente. Para isso, as ligações são transcritas para extrair informações relevantes. Perguntas a serem respondidas: 1 - Descrição do Problema, 2 - Descrição da Solução, 3 - Tipo de problema:(Cadastro, Configuração, Processo ou Erro de Sistema), 4 - Tempo gasto em cada etapa, Identificação do problema e Resolução, 5 - Alguma sugestão ou feedback do cliente, 6 - O problema foi resolvido na ligação?\n{data_string}"
        response = call_chatgpt_api(prompt)

        if response and 'choices' in response and len(response['choices']) > 0: 
            response_text = response['choices'][0]['message']['content']
            dt_call = datetime.now()
            id_speaker = 'some_speaker_id'  # Ajuste conforme necessário
            id_caller = 'some_caller_id'  # Ajuste conforme necessário
            save_response_to_db('1717758142.10313', dt_call, id_speaker, id_caller, response_text)
            return response
        else:
            return None
    except Exception as error:
        app.logger.error(f"Erro ao selecionar dados: {error}")
        return None

# Record the GPT return(return from process_and_send_data) on JME DB 
def save_response_to_db(uid_call, dt_call, id_speaker, id_caller, response_text):
    try:
        postgres_cursor = postgres_connection.cursor()
        insert_query = """
        INSERT INTO tb_gpt_output (uid_call, dt_call, id_speaker, id_caller, tx_response)
        VALUES (%s, %s, %s, %s, %s)
        """
        postgres_cursor.execute(insert_query, (uid_call, dt_call, id_speaker, id_caller, response_text))
        postgres_connection.commit()
        postgres_cursor.close()
        app.logger.info("Resposta salva no banco de dados com sucesso.")
    except Exception as error:
        app.logger.error(f"Erro ao salvar a resposta no banco de dados: {error}")
