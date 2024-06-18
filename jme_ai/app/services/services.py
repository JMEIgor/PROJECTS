# app/services/services.py

import requests
import json
import psycopg2
import mysql.connector  # Importando o mysql.connector
from datetime import datetime
from flask import current_app as app
from config import Config

# Configurações de conexão com o banco de dados
postgres_connection = psycopg2.connect(
    host=Config.DB_JME_HOST,
    user=Config.DB_JME_USER,
    password=Config.DB_JME_PASSWORD,
    dbname=Config.DB_JME_NAME
)

mysql_connection = mysql.connector.connect(
    host=Config.DB_LETTEL_HOST,
    user=Config.DB_LETTEL_USER,
    password=Config.DB_LETTEL_PASSWORD,
    database=Config.DB_LETTEL_NAME
)

# Função para chamar a API do ChatGPT
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

# Função que grava a resposta no banco de dados
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

# Função que envia a consulta na DB da JME e ao chatGPT  
def process_and_send_data():
    try:
        postgres_cursor = postgres_connection.cursor()
        query = "SELECT text FROM tb_ligacoes WHERE uniqueid = '1717758142.10313'"
        postgres_cursor.execute(query)
        rows = postgres_cursor.fetchall()
        columns = [desc[0] for desc in postgres_cursor.description]

        # Formatar os dados como string para enviar ao ChatGPT 
        data_string = "\n".join([str(dict(zip(columns, row))) for row in rows])

        prompt = f"Você é um assistente de trabalho que vai receber ligações transcritas e deve identificar como foi o atendimento, classificá-lo com (Atendente, Cliente, Mercado, Problema, Resolução do Problema, Foi solicitada avaliação do atendimento no fim da ligação)\n{data_string}"
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

# Função de importação dos dados da Lettel e inserção na base da JME 
def import_data():
    try:
        mysql_cursor = mysql_connection.cursor(dictionary=True)
        try:
            mysql_cursor.execute("SELECT * FROM v_cdr_transcriptions WHERE uniqueid in (select callid from v_queue_calls_full where timestamp between '2024-06-01' and '2024-06-11')")
            rows = mysql_cursor.fetchall()
            app.logger.info(f"Importando {len(rows)} registros do MySQL")

            postgres_cursor = postgres_connection.cursor()
            for row in rows:
                # Log do registro 
                app.logger.debug(f"Registro do MySQL: {row}")

                id = row['id']
                uniqueid = row['uniqueid']
                speaker = row['speaker'] if row['speaker'] is not None else 'N/A'
                start = row['start']
                end_time = row['end']
                text = row['text']

                try:
                    postgres_cursor.execute("""
                    INSERT INTO tb_ligacoes (id, uniqueid, speaker, start, end_time, text)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """, (id, uniqueid, speaker, start, end_time, text)
                    )
                    app.logger.info(f"Registro Inserido: {row['id'], row['uniqueid'], row['speaker'], row['start'], row['end'], row['text']}")
                except Exception as error:
                    app.logger.error(f"Erro ao inserir registro {row['id'], row['uniqueid'], row['speaker'], row['start'], row['end'], row['text']}: {error}")

            postgres_connection.commit()
            app.logger.info("Dados importados com sucesso!")
        except Exception as error:
            app.logger.error(f"Erro ao interagir com MySQL: {error}")
        finally:
            mysql_cursor.close()
    except Exception as error:
        app.logger.error(f"Erro ao importar dados: {error}")
