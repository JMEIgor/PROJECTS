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
