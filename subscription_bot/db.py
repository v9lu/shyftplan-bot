# Version 1.2.0

from mysql.connector.connection_cext import CMySQLConnection


def add_key(conn: CMySQLConnection, key: str, key_type: str, key_days: int):
    cursor = conn.cursor()
    cursor.execute("INSERT IGNORE INTO activation_keys (activation_key, key_type, key_days) VALUES (%s, %s, %s)",
                   (key, key_type, key_days))
    conn.commit()
    cursor.close()


def remove_key(conn: CMySQLConnection, key: str):
    cursor = conn.cursor()
    cursor.execute("DELETE IGNORE FROM activation_keys WHERE activation_key = %s", (key,))
    conn.commit()
    cursor.close()
