# Version 2.0.0 release
import mysql.connector


def initialization():
    # Create server_db if not exists
    conn = mysql.connector.connect(user="root", password="174537",
                                   host="188.166.104.222")
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS newsfeeds_db")

    # Create tables if not exists
    conn = mysql.connector.connect(user="root", password="174537",
                                   host="188.166.104.222", database="newsfeeds_db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS old_ids "
                   "(user_id INT, newsfeed_id INT)")

    # Save changes
    conn.commit()
    cursor.close()


def newsfeeds_is_old_id(user_id: int, newsfeed_id: int):
    conn = mysql.connector.connect(user="root", password="174537",
                                   host="188.166.104.222", database="newsfeeds_db")
    cursor = conn.cursor()
    cursor.execute("SELECT EXISTS (SELECT 1 FROM old_ids WHERE user_id=%s AND newsfeed_id=%s)", (user_id, newsfeed_id))
    id_exists = cursor.fetchone()[0]
    cursor.close()
    return bool(id_exists)


def newsfeeds_add_old_id(user_id: int, newsfeed_id: int):
    conn = mysql.connector.connect(user="root", password="174537",
                                   host="188.166.104.222", database="newsfeeds_db")
    cursor = conn.cursor()
    cursor.execute("INSERT IGNORE INTO old_ids (user_id, newsfeed_id) VALUES (%s, %s)", (user_id, newsfeed_id))
    conn.commit()
    cursor.close()
