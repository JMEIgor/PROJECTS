import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

class Config:
    # Carrega a chave da API do OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # URL da API do OpenAI
    API_URL = os.getenv('API_URL')
    
    # Configurações do banco de dados PostgreSQL
    DB_JME_HOST = os.getenv('DB_JME_HOST')
    DB_JME_USER = os.getenv('DB_JME_USER')
    DB_JME_PASSWORD = os.getenv('DB_JME_PASSWORD')
    DB_JME_NAME = os.getenv('DB_JME_NAME')
    
    # Configurações do banco de dados MySQL
    DB_LETTEL_HOST = os.getenv('DB_LETTEL_HOST')
    DB_LETTEL_USER = os.getenv('DB_LETTEL_USER')
    DB_LETTEL_PASSWORD = os.getenv('DB_LETTEL_PASSWORD')
    DB_LETTEL_NAME = os.getenv('DB_LETTEL_NAME')
