from flask import Flask
from flask_mysqldb import MySQL
from dotenv import load_dotenv
import os

# Carregar variáveis do arquivo .env
load_dotenv()

app = Flask(__name__)

# Conexão da base de dados da JME 
app.config['JME_DB_HOST'] = os.getenv('DB_HOST')
app.config['JME_DB_USER'] = os.getenv('DB_USER')
app.config['JME_DB_PASSWORD'] = os.getenv('DB_PASSWORD')
app.config['JME_DB_NAME'] = os.getenv('DB_NAME')

# Conexão da base de dados Lettel(Transcrições) 
app.config['LETTEL_DB_HOST'] = os.getenv('DB_LETTEL_HOST')
app.config['LETTEL_DB_USER'] = os.getenv('DB_LETTEL_USER')
app.config['LETTEL_DB_PASSWORD'] = os.getenv('DB_LETTEL_PASSWORD')
app.config['LETTEL_DB_NAME'] = os.getenv('DB_LETTEL_NAME')

# Inicializando as conexões com os bancos de dados
mysql_db1 = MySQL()
mysql_db1.init_app(app)

mysql_db2 = MySQL()
mysql_db2.init_app(app)

@app.route('/')
def index():
    return "Conexões com MySQL configuradas!"

if __name__ == '__main__':
    app.run(debug=True)
