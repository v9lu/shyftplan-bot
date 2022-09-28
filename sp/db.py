# Version 1.1.0 release

def initialization(conn):
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS neewsfeeds_old_ids (id INT PRIMARY KEY)''')
    conn.commit()
    cursor.close()


def newsfeeds_is_old_id(conn, newsfeed_id):
    cursor = conn.cursor()
    response = cursor.execute(f"SELECT EXISTS (SELECT 1 FROM neewsfeeds_old_ids WHERE id=?)", (newsfeed_id,))
    id_exists = response.fetchone()[0]
    cursor.close()
    return bool(id_exists)


def newsfeeds_add_old_id(conn, newsfeed_id):
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO neewsfeeds_old_ids (id) VALUES (?)", (newsfeed_id,))
    conn.commit()
    cursor.close()
