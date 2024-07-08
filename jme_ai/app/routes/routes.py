from flask import current_app as app
from flask import render_template, request, jsonify
from . import main_routes
from flask import Blueprint
from ..services.gpt_functions import process_and_send_data, call_chatgpt_api
from ..services.services import import_data, process_data

#main_page route 
@main_routes.route('/')
def index():
    return render_template('index.html')

#outines page route
@main_routes.route('/routines')
def routine_page():
    return render_template('routines.html')

#exportation page route
@main_routes.route('/exportation')
def exportation_page():
    return render_template('exportation.html')

#ChatWGPT page route 
@main_routes.route('/chatwithgpt')
def chatwithgpt_page():
    return render_template('chatwithgpt.html')

#Route to import data from Lettel DB to JME DB 
@main_routes.route('/import_data', methods=['GET', 'POST'])
def import_data_route():
    import_data()
    return "Dados importados com sucesso!"

#Route to process data from JME DB
@main_routes.route('/process_data')
def process_data_route():
    process_data()
    return "Dados processados com sucesso"

#Route to transform 
@main_routes.route('/transform_and_insert_data', methods=['GET', 'POST'])
def transform_and_insert_data_route():
    transform_and_insert_data()
    return "Dados transformados e inseridos com sucesso!"

@main_routes.route('/send_data_gpt', methods=['GET', 'POST'])
def send_data_gpt_route():
    api_response = process_and_send_data()
    if api_response:
        try:
            response = api_response['choices'][0]['message']['content']
            app.logger.info(f"Resposta da API: {response}")
        except (KeyError, IndexError) as e:
            app.logger.error(f"Erro ao processar a resposta da API: {e}")
            response = "Ocorreu um erro ao processar sua solicitação. Por favor, tente novamente mais tarde."
    else:
        response = "Ocorreu um erro ao processar sua solicitação. Por favor, tente novamente mais tarde."
    return jsonify({'response': response})

@main_routes.route('/export_data', methods=['GET'])
def export_data():
    try:
        postgres_connection = get_postgres_connection()
        postgres_cursor = postgres_connection.cursor()
        postgres_cursor.execute("SELECT * FROM tb_info_call")
        rows = postgres_cursor.fetchall()
        columns = [desc[0] for desc in postgres_cursor.description]

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
