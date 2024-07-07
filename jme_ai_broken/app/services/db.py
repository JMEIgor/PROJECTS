# app/services/db.py

import psycopg2
from config import Config

def get_postgres_connection():
    return psycopg2.connect(
        host=Config.DB_JME_HOST,
        user=Config.DB_JME_USER,
        password=Config.DB_JME_PASSWORD,
        dbname=Config.DB_JME_NAME
    )