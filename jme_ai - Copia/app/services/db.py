import psycopg2
from config import Config
from flask import current_app as app

def get_postgres_connection():
    try:
        connection = psycopg2.connect(
            host=Config.DB_JME_HOST,
            user=Config.DB_JME_USER,
            password=Config.DB_JME_PASSWORD,
            dbname=Config.DB_JME_NAME
        )
        return connection
    except Exception as error:
        print(f"Erro ao conectar ao PostgreSQL: {error}")
        return None
