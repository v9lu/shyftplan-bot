# Version 1.0.0


from mysql.connector import errorcode


def initialization(conn):
    cursor = conn.cursor()
    cursor.execute('''CREATE DATABASE IF NOT EXISTS server_database''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS neewsfeeds_old_ids (id INT PRIMARY KEY)''')
    conn.commit()
    cursor.close()
