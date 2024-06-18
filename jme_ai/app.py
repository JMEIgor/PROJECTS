from flask import Flask, request, render_template, jsonify
import requests
import os
import json
from dotenv import load_dotenv
import mysql.connector
import psycopg2
import logging
from datetime import datetime

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

#ENV CONFIG
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
        'model': 'gpt-4o',
        'messages': [
            {'role': 'system', 'content': 'Você é um assistente de trabalho e está encarregado de analisar transcrição de ligações e identificar o assunto principal da ligação e detalhar o que foi resolvido'},
            {'role': 'user', 'content': prompt}
        ]
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        response_json = response.json()
        app.logger.debug(f"Resposta da API do ChatGPT (JSON):{response_json}") # Decodifica o JSON
        return response_json
    except requests.exceptions.RequestException as error:
        print(f"Erro ao chamar a API do ChatGPT: {error}")
        return None
    except json.JSONDecodeError as json_error:
        app.logger.error(f"Erro ao decodificar JSON: {json_error}")
        return {"error":"Invalid JSON response from ChatGPT"}

# Funcao que envia a consulta na DB da JME e ao chatGPT  
def process_and_send_data():
    try:
        postgres_cursor = postgres_connection.cursor()
        query = "SELECT text FROM tb_ligacoes WHERE UNIQUEID = '1718020109.11382'"
        postgres_cursor.execute(query)
        rows = postgres_cursor.fetchall()
        columns = [desc[0] for desc in postgres_cursor.description]

        #Formatar os dados como string para enviar ao ChatGPT 
        data_string = "\n".join([str(dict(zip(columns, row))) for row in rows])

        prompt = f"Você é um assistente de trabalho que vai receber ligações transcritas e deve identificar como foi o atendimento, classificá-lo com (Atendente, Cliente, Mercado, Problema, Resolução do Problema, Foi solicitada avaliação do atendimento no fim da ligação)\n{data_string}"
        response = call_chatgpt_api(prompt)

        if response and 'choices' in response and len(response['choices']) > 0: 
            response_text = response['choices'][0]['message']['content']
            dt_call = datetime.now()
            id_speaker= '116'
            id_caller = '9999999'
            save_response_to_db('1718020109.11382','2024-06-10','123','9999999', response_text)
            return response
        else:
            return None
    except Exception as error:
        app.logger.error(f"Error ao selecionar dados: {error}")
        return None

# Funcao que salva o retorno  do ChatGPT no BD 
def save_response_to_db(uid_call,dt_call,id_speaker,id_caller,response_text):
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


# DB Functions 
# Funcao de importacao dos dados da Lettel e insercao na base da JME 
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

#    Flask Routes 
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
# @app.route('/import_data', methods=['GET','POST'])
# def import_data_route():
#     import_data()
#     return "Dados importados com sucesso!"

#Definica de rota de envio de dados ao GPT 
@app.route('/send_data_gpt', methods=['GET','POST'])
def send_data_gpt_route():
    api_response = process_and_send_data()
    if api_response:
        try:
            response = api_response['choices'][0]['message']['content']
            app.logger.info(f"Resposta da API: {response}")
        except (KeyError, IndexError) as e:
            app.logger.error(f"Erro ao processar a resposta da API: {e}")
            response = "Ocorreu um erro ao processar sua solicitacao. Por favor, tente novamente mais tarde"
    else:
        response = "Ocorreu um erro ao processar sua solicitacao. Por favor, tente novamente mais tarde"
    return jsonify({'response': response});

# Executa a aplicação
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) # Permite conexao para todos os IPs na rede, na porta 5000

# 13-06 00:55 - Criada a function import_data para importar as informações da lettel.v_cdr_transcriptions para jme.tb_ligacoes
# 13-06 01:15 - Criada a function send_data_gpt para enviar informações do BD da JME para o ChatGPT como prompt para validação da ligação 
# 13-06 09:40 - Ajustada function process_and_send_data para consultar corretamente os dados na API

