# The routes folder is responsible to content all the routes from flask #
#    Flask Routes 
# Route to connection to main page (templates/index.html)

from flask import current_app as app
from flask import render_template, request, jsonify
from . import main_routes
from ..services.services import process_and_send_data, import_data, call_chatgpt_api, create_tables

@main_routes.route('/', methods=['GET', 'POST'])
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

# Route to import data from Lettel DB 
@main_routes.route('/import_data', methods=['GET','POST'])
def import_data_route():
     import_data()
     return "Dados importados com sucesso!"

#Definica de rota de envio de dados ao GPT 
@main_routes.route('/send_data_gpt', methods=['GET','POST'])
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