import time
import requests
import json
import backoff
from flask import current_app as app
from .db import get_postgres_connection
from config import Config
from .services import ensure_table_exists

# Função para chamar a API do ChatGPT com retentativas e backoff exponencial
@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_time=300)
def call_chatgpt_api(prompt):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {Config.OPENAI_API_KEY}'
    }
    data = {
        'model': 'gpt-4',
        'messages': [
            {'role': 'system', 'content': 'A JME é uma empresa de prestação de serviços. Atuamos como Representação de Software da Sysmo Sistemas. A Sysmo Sistemas desenvolve software especializado para supermercados. Nossa maior demanda é no Suporte Técnico nos produtos Sysmo, que incluem ERP, PDV, aplicativos móveis CRM e Pricing. Buscamos otimizar a avaliação das ligações de suporte técnico para garantir um atendimento de alta qualidade e eficiente. Para isso, as ligações são transcritas para obtenção de informaões.'},
            {'role': 'user', 'content': prompt}
        ]
    }

    response = requests.post(Config.API_URL, headers=headers, json=data)
    
    if response.status_code == 429:
        rate_limit_reset = response.headers.get('X-RateLimit-Reset')
        if rate_limit_reset:
            wait_time = int(rate_limit_reset) - time.time()
            app.logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds until reset.")
            time.sleep(wait_time)
        else:
            app.logger.warning("Rate limit exceeded. Retrying after default wait time.")
            time.sleep(60)  # Espera padrão se o cabeçalho não estiver presente
        raise requests.exceptions.RequestException("Rate limit exceeded")
    
    response.raise_for_status()
    
    response_json = response.json()
    app.logger.debug(f"Resposta da API do ChatGPT (JSON): {response_json}")

    return response_json

# Função principal para processar e enviar dados para a API do ChatGPT
def process_and_send_data():
    try:
        ensure_table_exists()

        postgres_connection = get_postgres_connection()
        postgres_cursor = postgres_connection.cursor()
        query = "SELECT callid, text FROM tb_info_call WHERE where date = '2024-06-07'"
        postgres_cursor.execute(query)
        rows = postgres_cursor.fetchall()
        columns = [desc[0] for desc in postgres_cursor.description]

        for row in rows:
            data_string = str(dict(zip(columns, row)))

            prompt = f"""
            {data_string}

            Com base nessa ligação transcrita enviada, responda as perguntas. 
             1 - Descrição do Problema.
             2 - Descrição da Solução.
             3 - Tipo de problema: (Cadastro) ou (Configuração) ou (Processo) ou (Erro de Sistema)
             4 - Tempo gasto em cada etapa, Identificação do problema e Resolução.
             5 - Alguma sugestão ou feedback do cliente.
             6 - O problema foi resolvido:(SIM ou NÃO)
            """
            response = call_chatgpt_api(prompt)

            # Verifica se a resposta é válida e salva no banco de dados
            if response and 'choices' in response and len(response['choices']) > 0:
                response_text = response['choices'][0]['message']['content']
                callid = row[0]
                save_response_to_db(callid, response_text)
            else:
                app.logger.error(f"Resposta inválida da API do ChatGPT para o registro {row[0]}: {response}")

            # Adiciona um intervalo maior entre as chamadas para evitar atingir o limite de taxa
            time.sleep(2)  # Ajuste conforme necessário
    except Exception as error:
        app.logger.error(f"Erro ao selecionar dados: {error}")

# Função para salvar a resposta da API no banco de dados
def save_response_to_db(callid, response_text):
    try:
        postgres_connection = get_postgres_connection()
        postgres_cursor = postgres_connection.cursor()
        insert_query = """
        INSERT INTO tb_gpt_output (callid, response_text)
        VALUES (%s, %s)
        """
        postgres_cursor.execute(insert_query, (callid, response_text))
        postgres_connection.commit()
        postgres_cursor.close()
        app.logger.info("Resposta salva no banco de dados com sucesso.")
    except Exception as error:
        app.logger.error(f"Erro ao salvar a resposta no banco de dados: {error}")