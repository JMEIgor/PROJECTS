@app.route('/data1')
def get_data_from_db1():
    cur = mysql_db1.connection.cursor()
    cur.execute('SELECT * FROM your_table1')
    data = cur.fetchall()
    cur.close()
    return str(data)

@app.route('/data2')
def get_data_from_db2():
    cur = mysql_db2.connection.cursor()
    cur.execute('SELECT * FROM your_table2')
    data = cur.fetchall()
    cur.close()
    return str(data)
