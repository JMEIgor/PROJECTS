# The models folder is responsible to content all the db-models from application # 

# Connection PostgreSQL - DB JME 
postgres_connection = psycopg2.connect(
    host = os.getenv("DB_JME_HOST"),
    user = os.getenv("DB_JME_USER"),
    password = os.getenv("DB_JME_PASSWORD"),
    dbname = os.getenv("DB_JME_NAME")
)

# Connection MySQL - DB LETTEL 
mysql_connection = mysql.connector.connect(
    host = os.getenv("DB_LETTEL_HOST"),
    user = os.getenv("DB_LETTEL_USER"),
    password = os.getenv("DB_LETTEL_PASSWORD"),
    database = os.getenv("DB_LETTEL_NAME")
)

#DB Functions 
#Import data from DB Lettel to DB JME 
def import_data():
    try:
        mysql_cursor = mysql_connection.cursor(dictionary=True)
        try:
            mysql_cursor.execute("SELECT * FROM v_cdr_transcriptions WHERE uniqueid in (select callid from v_queue_calls_full where timestamp between '2024-06-01' and '2024-06-11')")
            rows = mysql_cursor.fetchall()
            app.logger.info(f"Importando {len(rows)} registros do MySQL")

            postgres_cursor  = postgres_connection.cursor()
            for row in rows:
                #Log do registro 
                app.logger.debug(f"Registro do MySQL: {row}")

                id = row['id']
                uniqueid = row['uniqueid']
                speaker = row['speaker'] if row['speaker'] is not None else 'N/A'
                start = row['start']
                end_time = row['end']
                text = row['text']

                try:
                    postgres_cursor.execute("""
                    INSERT INTO tb_ligacoes (id, uniqueid, speaker,start,end_time,text)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """, (id, uniqueid, speaker,start,end_time,text)
                    )
                    app.logger.info(f"Registro Inserido: {row['id'], row['uniqueid'], row['speaker'], row['start'], row['end'], row['text']}")
                except Exception as error:
                    app.logger.error(f"Erro ao inserir registro {row['id'], row['uniqueid'], row['speaker'], row['start'], row['end'], row['text']}: {error}")

                postgres_connection.commit()
                app.logger.info("Dados importados com sucesso!")
        except Exception as error:
                app.logger.error(f"Erro ao integir com MySQL: {error}")
        finally:
                mysql_cursor.close()
    except Exception as error:
        app.logger.error(f"Erro ao imporar dados: {error}")