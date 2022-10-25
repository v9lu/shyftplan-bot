# Version 2.1.0 release

from mysql.connector.connection_cext import CMySQLConnection


def newsfeeds_is_old_id(conn: CMySQLConnection, user_id: int, newsfeed_id: int):
    cursor = conn.cursor()
    cursor.execute("SELECT EXISTS (SELECT 1 FROM old_ids WHERE user_id=%s AND newsfeed_id=%s)", (user_id, newsfeed_id))
    id_exists = cursor.fetchone()[0]
    cursor.close()
    return bool(id_exists)


def newsfeeds_add_old_id(conn: CMySQLConnection, user_id: int, newsfeed_id: int):
    cursor = conn.cursor()
    cursor.execute("INSERT IGNORE INTO old_ids (user_id, newsfeed_id) VALUES (%s, %s)", (user_id, newsfeed_id))
    conn.commit()
    cursor.close()
