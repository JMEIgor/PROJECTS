from flask import Flask, request, render_template, jsonify
import requests
import os
from dotenv import load_dotenv
import mysql.connector
import psycopg2
import logging

load_dotenv()

app = Flask(__name__)

# Configuracao do logging
logging.basicConfig(
    level=logging.DEBUG), 
format='%(asctime)s %(levelname)s %(message)s',
handlers=[
        logging.FileHandler("log.log"),
        logging.StreamHandler()
]

# ENV 
# Busca chave e URL de conexão com a API do ChatGPT
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("A chave API da OpenAI não está definida!")

API_URL = 'https://api.openai.com/v1/chat/completions'

# Conexão PostgreSQL - DB JME 
postgres_connection = psycopg2.connect(
    host = os.getenv("DB_JME_HOST"),
    user = os.getenv("DB_JME_USER"),
    password = os.getenv("DB_JME_PASSWORD"),
    dbname = os.getenv("DB_JME_NAME")
)

# Conexão MySQL - DB LETTEL 
mysql_connection = mysql.connector.connect(
    host = os.getenv("DB_LETTEL_HOST"),
    user = os.getenv("DB_LETTEL_USER"),
    password = os.getenv("DB_LETTEL_PASSWORD"),
    database = os.getenv("DB_LETTEL_NAME")
)

# GPT Functions
# Função para chamar a API do ChatGPT
def call_chatgpt_api(prompt):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}'
    }
    data = {
        'model': 'gpt-4',
        'messages': [
            {'role': 'system', 'content': 'Você é um assistente de trabalho e está encarregado de analisar transcrição de ligações e identificar o assunto principal da ligação e detalhar o que foi resolvido'},
            {'role': 'user', 'content': prompt}
        ]
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        response_json = response.json()
        return response_json
    except requests.exceptions.RequestException as error:
        print(f"Erro ao chamar a API do ChatGPT: {error}")
        return None

#Funcao para selecionar e enviar dados para o ChatGPT 
def select_and_send_data():
    try:
        postgres_cursor = postgres_connection.cursor()
        query = "SELECT * FROM tb_ligacoes WHERE UNIQUEID = '1717761778.10421'"
        postgres_cursor.execute(query)
        rows = postgres_cursor.fetchall()
        columns = [desc[0] for desc in postgres_cursor.description]

        #Formatar os dados como string para enviar ao ChatGPT 
        data_string = "\n".join([str(dict(zip(columns, row))) for row in rows])

        prompt = f"Por favor, analise os dados da ligação abaixo e retorne um resumo do atendimento:\n{data_string}"
        response = call_chatgpt_api(prompt)
        return response
    except Exception as error:
        app.logger.error(f"Error ao selecionar dados: {error}")
        return None

# DB Functions 
# Função para importar os dados do MySQL(v_queue_calls_full) e inserir no PostgreSQL
#  def import_data(): 
#     try:
#         mysql_cursor = mysql_connection.cursor(dictionary=True)
#         try:
#             mysql_cursor.execute("SELECT * FROM v_queue_calls_full WHERE timestamp between '2024-06-01' and '2024-06-11'")
#             rows = mysql_cursor.fetchall()
#             app.logger.info(f"Importando {len(rows)} registros do MySQL")
#
#             postgres_cursor  = postgres_connection.cursor()
#             for row in rows:
#                 #Log do registro 
#                 app.logger.debug(f"Registro do MySQL: {row}")
#
#                 callid = row['callid']
#                 caller_id = row['caller_id']
#                 transfer = row['transfer'] if row['transfer'] is not None else 'N/A'
#                 status = row['status']
#                 timestamp = row['timestamp']
#                 queue = row['queue']
#                 position = row['position'] if row['position'] is not None else 0
#                 original_position = row['position'] if row['position'] is not None else 0
#                 holdtime = row['holdtime'] if row['holdtime'] is not None else 0 
#                 key_pressed = row['key_pressed'] if row['key_pressed'] is not None else 0
#                 duration = row['duration'] if row['duration'] is not None else 0 
#                 agente = row['agente'] if row['agente'] is not None else 'Unknown'
#
#                 try:
#                     postgres_cursor.execute("""
#                     INSERT INTO tb_ligacoes (callid, caller_id, transfer, status, timestamp, queue, position, original_position, holdtime, key_pressed, duration, agente)
#                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#                     """, (callid, caller_id, transfer, status, timestamp, queue, position, original_position, holdtime, key_pressed, duration, agente)
#                     )
#                     app.logger.info(f"Registro Inserido: {row['callid'], row['caller_id'], row['transfer'], row['status'], row['timestamp'], row['queue'], row['holdtime'], row['duration'], row['agente']}")
#                 except Exception as error:
#                     app.logger.error(f"Erro ao inserir registro {row['callid'], row['caller_id'], row['transfer'], row['status'], row['timestamp'], row['queue'], row['holdtime'], row['duration'], row['agente']}: {error}")
#
#                 postgres_connection.commit()
#                 app.logger.info("Dados importados com sucesso!")
#         except Exception as error:
#                 app.logger.error(f"Erro ao integir com MySQL: {error}")
#         finally:
#                 mysql_cursor.close()
#     except Exception as error:
#         app.logger.error(f"Erro ao imporar dados: {error}")

def import_data():
    try:
        mysql_cursor = mysql_connection.cursor(dictionary=True)
        try:
            mysql_cursor.execute("SELECT * FROM v_cdr_transcriptions WHERE uniqueid in (select callid from v_queue_calls_full where timestamp between '2024-06-01' and '2024-06-11')")
            rows = mysql_cursor.fetchall()
            app.logger.info(f"Importando {len(rows)} registros do MySQL")

            postgres_cursor  = postgres_connection.cursor()
            for row in rows:
                #Log do registro 
                app.logger.debug(f"Registro do MySQL: {row}")

                id = row['id']
                uniqueid = row['uniqueid']
                speaker = row['speaker'] if row['speaker'] is not None else 'N/A'
                start = row['start']
                end_time = row['end']
                text = row['text']

                try:
                    postgres_cursor.execute("""
                    INSERT INTO tb_ligacoes (id, uniqueid, speaker,start,end_time,text)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """, (id, uniqueid, speaker,start,end_time,text)
                    )
                    app.logger.info(f"Registro Inserido: {row['id'], row['uniqueid'], row['speaker'], row['start'], row['end'], row['text']}")
                except Exception as error:
                    app.logger.error(f"Erro ao inserir registro {row['id'], row['uniqueid'], row['speaker'], row['start'], row['end'], row['text']}: {error}")

                postgres_connection.commit()
                app.logger.info("Dados importados com sucesso!")
        except Exception as error:
                app.logger.error(f"Erro ao integir com MySQL: {error}")
        finally:
                mysql_cursor.close()
    except Exception as error:
        app.logger.error(f"Erro ao imporar dados: {error}")

# Connections Routes
# Definição de rota principal
@app.route('/', methods=['GET', 'POST'])
def index():
    response = None
    if request.method == 'POST':
        user_prompt = request.form['prompt']
        api_response = call_chatgpt_api(user_prompt)
        if api_response:
            response = api_response['choices'][0]['message']['content']
        else:
            response = "Ocorreu um erro ao processar sua solicitação. Por favor, tente novamente mais tarde."
    return render_template('index.html', response=response)

#Definicao de rota de importação de dados 
@app.route('/import_data', methods=['GET','POST'])
def import_data_route():
    import_data()
    return "Dados importados com sucesso!"

#Definica de rota de envio de dados ao GPT 
@app.route('/send_data_gpt', methods=['GET','POST'])
def send_data_gpt():
    api_response = select_and_send_data()
    if api_response:
        try:
            response = api_response['choices'][0]['message']['content']
        except (KeyError, IndexError) as e:
            app.logger.error(f"Erro ao processar a resposta da API: {e}")
            response = "Ocorreu um erro ao processar sua solicitacao. Por favor, tente novamente mais tarde"
    else:
        response = "Ocorreu um erro ao processar sua solicitacao. Por favor, tente novamente mais tarde"
    return jsonify({'response': response});

# Executa a aplicação
if __name__ == '__main__':
    app.run(debug=True)
