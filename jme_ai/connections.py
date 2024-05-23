from flask import Flask
from flask_mysqldb import MySQL
from dotenv import load_dotenv
import os

# Carregar variáveis do arquivo .env
load_dotenv()

app = Flask(__name__)

# Configuração da primeira base de dados MySQL
app.config['DB1_HOST'] = os.getenv('DB1_HOST')
app.config['DB1_USER'] = os.getenv('DB1_USER')
app.config['DB1_PASSWORD'] = os.getenv('DB1_PASSWORD')
app.config['DB1_DB'] = os.getenv('DB1_NAME')

# Configuração da segunda base de dados MySQL
app.config['DB2_HOST'] = os.getenv('DB2_HOST')
app.config['DB2_USER'] = os.getenv('DB2_USER')
app.config['DB2_PASSWORD'] = os.getenv('DB2_PASSWORD')
app.config['DB2_DB'] = os.getenv('DB2_NAME')

# Inicializando as conexões com os bancos de dados MySQL
mysql_db1 = MySQL()
mysql_db1.init_app(app)

mysql_db2 = MySQL()
mysql_db2.init_app(app)

@app.route('/')
def index():
    return "Conexões com duas bases de dados MySQL configuradas!"

@app.route('/data_db1')
def get_data_from_db1():
    cur = mysql_db1.connection.cursor()
    cur.execute('SELECT * FROM your_table_db1')
    data = cur.fetchall()
    cur.close()
    return str(data)

@app.route('/data_db2')
def get_data_from_db2():
    cur = mysql_db2.connection.cursor()
    cur.execute('SELECT * FROM your_table_db2')
    data = cur.fetchall()
    cur.close()
    return str(data)

if __name__ == '__main__':
    app.run(debug=True)
