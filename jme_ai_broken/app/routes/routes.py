import csv
from flask import make_response
from flask import current_app as app
from flask import render_template, request, jsonify, redirect, url_for
from . import main_routes
from ..services.services import import_data, transform_and_insert_data
from ..services.gpt_functions import process_and_send_data, call_chatgpt_api

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
@main_routes.route('/import_data', methods=['GET', 'POST'])
def import_data_route():
    import_data()
    return "Dados importados com sucesso!"

# Route to transform and insert data
@main_routes.route('/transform_and_insert_data', methods=['GET', 'POST'])
def transform_and_insert_data_route():
    transform_and_insert_data()
    return "Dados transformados e inseridos com sucesso!"

#Definica de rota de envio de dados ao GPT 
@main_routes.route('/send_data_gpt', methods=['GET', 'POST'])
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
    return jsonify({'response': response})

# Route to export data from PostgreSQL
@main_routes.route('/export_data', methods=['GET'])
def export_data():
    try:
        postgres_connection = get_postgres_connection()
        postgres_cursor = postgres_connection.cursor()
        postgres_cursor.execute("SELECT * FROM tb_info_call")
        rows = postgres_cursor.fetchall()
        columns = [desc[0] for desc in postgres_cursor.description]

        # Create a CSV response
        def generate():
            data = csv.writer(open("tb_info_call.csv", "w"))
            data.writerow(columns)
            data.writerows(rows)
            with open("tb_info_call.csv", "r") as file:
                for row in file:
                    yield row
        response = make_response(generate())
        response.headers["Content-Disposition"] = "attachment; filename=tb_info_call.csv"
        response.headers["Content-Type"] = "text/csv"
        return response
    except Exception as error:
        app.logger.error(f"Erro ao exportar dados: {error}")
        return "Erro ao exportar dados", 500
