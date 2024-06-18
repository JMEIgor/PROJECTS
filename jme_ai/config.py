import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or 'you-will-never-guess'
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    API_URL = os.getenv('API_URL_CHATGPT')
    DB_JME_HOST = os.getenv('DB_JME_HOST')
    DB_JME_USER = os.getenv('DB_JME_USER')
    DB_JME_PASSWORD = os.getenv('DB_JME_PASSWORD')
    DB_JME_NAME = os.getenv('DB_JME_NAME')
    DB_LETTEL_HOST = os.getenv('DB_LETTEL_HOST')
    DB_LETTEL_USER = os.getenv('DB_LETTEL_USER')
    DB_LETTEL_PASSWORD = os.getenv('DB_LETTEL_PASSWORD')
    DB_LETTEL_NAME = os.getenv('DB_LETTEL_NAME')