import os
import pandas as pd
from flask import current_app as app
from flask import render_template, request, jsonify, make_response, send_file, Flask
from . import main_routes
from flask import Blueprint
from ..services.gpt_functions import process_and_send_data, call_chatgpt_api
from ..services.services import import_data, process_data
from ..services.db import get_postgres_connection

#main_page route 
@main_routes.route('/' , methods=['GET', 'POST'])
def index():
    return render_template('index.html')

#outines page route
@main_routes.route('/routines')
def routines_page():
    return render_template('routines_2.html')

#exportation page route
@main_routes.route('/exportation')
def exportation_page():
    return render_template('exportation.html')

#ChatWGPT page route 
@main_routes.route('/chatwithgpt')
def chatwithgpt_page():
    return render_template('chatwithgpt.html')

#Route to import data from Lettel DB to JME DB 
@main_routes.route('/import_data', methods=['POST'])
def import_data_route():
    try:
        data = request.get_json()
        app.logger.info(f"Data received: {data}")
        
        date_entry = data.get('date_entry')
        date_final = data.get('date_final')

        app.logger.info(f"Received date_entry: {date_entry}, date_final: {date_final}")

        if not date_entry or not date_final:
            return jsonify({"error": "As datas de entrada e final devem ser fornecidas"}), 400

        import_data(date_entry, date_final)
        result = {"message": "Concluded Successfully"}
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Erro ao importar dados: {str(e)}")
        return jsonify({"error": str(e)}), 500

#Route to process data from JME DB
@main_routes.route('/process_data', methods=['POST'])
def process_data_route():
    try:
        data = request.get_json()
        app.logger.info(f"Data received: {data}")
        date_entry = data.get('date_entry')
        date_final = data.get('date_final')

        app.logger.info(f"Received date_entry: {date_entry}, date_final: {date_final}")

        if not date_entry or not date_final:
            return jsonify({"error": "As datas de entrada e final devem ser fornecidas"}), 400

        process_data(date_entry, date_final)
        result = {"message": "Concluded Successfully"}
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Erro ao processar dados: {str(e)}")
        return jsonify({"error": str(e)}), 500

#Route to transform 
@main_routes.route('/transform_and_insert_data', methods=['GET', 'POST'])
def transform_and_insert_data_route():
    transform_and_insert_data()
    return "Dados transformados e inseridos com sucesso!"

#Route to send data to ChatGPT and import return response on JME BD
@main_routes.route('/send_data_gpt', methods=['POST'])
def send_data_gpt_route():
    data = request.get_json()
    date_entry = data.get('date_entry')
    date_final = data.get('date_final')
    
    app.logger.info(f"Received date_entry: {date_entry}, date_final: {date_final}")

    try:
        api_response = process_and_send_data(date_entry, date_final)
        return jsonify({'response': api_response})
    except Exception as e:
        app.logger.error(f"Erro ao enviar dados para o ChatGPT: {e}")
        return jsonify({'error': str(e)}), 500

#Route to export data from JME DB
@main_routes.route('/export_data', methods=['GET', 'POST'])
def export_data_route():
    try:
        postgres_connection = get_postgres_connection()
        postgres_cursor = postgres_connection.cursor()
        postgres_cursor.execute("SELECT * FROM tb_gpt_output")
        rows = postgres_cursor.fetchall()
        columns = [desc[0] for desc in postgres_cursor.description]

        df = pd.DataFrame(rows, columns=columns)
        filename = "tb_gpt_output.xlsx"
        filepath = os.path.join(os.getcwd(), filename)
        df.to_excel(filepath, index=False)

        return send_file(filepath, as_attachment=True)
    except Exception as error:
        app.logger.error(f"Erro ao exportar dados: {error}")
        return jsonify({"error": "Erro ao exportar dados"}), 500
    finally:
        if postgres_cursor:
            postgres_cursor.close()
        if postgres_connection:
            postgres_connection.close()

