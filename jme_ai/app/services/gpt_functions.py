from flask import current_app as app
import requests
import json
from datetime import datetime
from .db import get_postgres_connection
from config import Config
from .services import create_table, create_table_queries, ensure_table_exists


# GPT Functions 
# Main page input to ChatGPT and return response on main page screen 
def call_chatgpt_api(prompt):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {Config.OPENAI_API_KEY}'
    }
    data = {
        'model': 'gpt-4',
        'messages': [
            {'role': 'system', 'content': 'A JME é uma empresa de prestação de serviços. Atuamos como Representação de Software da Sysmo Sistemas. A Sysmo Sistemas desenvolve software especializado para supermercados. Nossa maior demanda é no Suporte Técnico nos produtos Sysmo, que incluem ERP, PDV, aplicativos móveis CRM e Pricing. Buscamos otimizar a avaliação das ligações de suporte técnico para garantir um atendimento de alta qualidade e eficiente. Para isso, as ligações são transcritas para extrair informações relevantes.'},
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

# JME to GPT Functions  
# Process JME DB data and send to ChatGPT for analysis 
def process_and_send_data():
    try:
        ensure_table_exists()


        postgres_connection = get_postgres_connection()
        postgres_cursor = postgres_connection.cursor()
        query = "SELECT callid, text FROM tb_info_call WHERE date BETWEEN '2024-06-07' AND '2024-06-09'"
        postgres_cursor.execute(query)
        rows = postgres_cursor.fetchall()
        columns = [desc[0] for desc in postgres_cursor.description]

        for row in rows:
            # Formatar os dados como string para enviar ao ChatGPT 
            data_string = str(dict(zip(columns, row)))

            prompt = f"""
            Perguntas a serem respondidas:
            1 - Descrição do Problema,
            2 - Descrição da Solução, 
            3 - Tipo de problema: (Cadastro, Configuração, Processo ou Erro de Sistema), 
            4 - Tempo gasto em cada etapa, Identificação do problema e Resolução, 
            5 - Alguma sugestão ou feedback do cliente, 
            6 - O problema foi resolvido na ligação?
            
            {data_string}
            """
            response = call_chatgpt_api(prompt)

            if response and 'choices' in response and len(response['choices']) > 0:
                response_text = response['choices'][0]['message']['content']
                callid = row[0]
                save_response_to_db(callid, response_text)
            else:
                app.logger.error(f"Resposta inválida da API do ChatGPT para o registro {row[0]}")

        return "Processamento concluído com sucesso!"
    except Exception as error:
        app.logger.error(f"Erro ao selecionar dados: {error}")
        return None

# Record the GPT return (return from process_and_send_data) on JME DB 
def save_response_to_db(callid, response_text):
    try:
        postgres_connection = get_postgres_connection()
        postgres_cursor = postgres_connection.cursor()
        insert_query = """
        INSERT INTO tb_gpt_output (callid, tx_response)
        VALUES (%s, %s)
        """
        postgres_cursor.execute(insert_query, (callid, response_text))
        postgres_connection.commit()
        postgres_cursor.close()
        app.logger.info("Resposta salva no banco de dados com sucesso.")
    except Exception as error:
        app.logger.error(f"Erro ao salvar a resposta no banco de dados: {error}")
