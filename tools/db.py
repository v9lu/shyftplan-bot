# Version 2.3.2 release

from mysql.connector import MySQLConnection


# KEYS_DB
def keys_activate_key(conn: MySQLConnection, key: str):
    if conn.database != "keys_db":
        conn.connect(database="keys_db")
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM activation_keys WHERE activation_key=%s", (key,))
    key_data = cursor.fetchone()
    if key_data:
        cursor.execute("DELETE FROM activation_keys WHERE activation_key=%s", (key,))
        conn.commit()
        cursor.close()
        return key_data
    else:
        cursor.close()
        return False


def keys_add_key(conn: MySQLConnection, key: str, key_type: str, key_days: int):
    if conn.database != "keys_db":
        conn.connect(database="keys_db")
    cursor = conn.cursor()
    cursor.execute("INSERT IGNORE INTO activation_keys (activation_key, key_type, key_days) VALUES (%s, %s, %s)",
                   (key, key_type, key_days))
    conn.commit()
    cursor.close()


def keys_remove_key(conn: MySQLConnection, key: str):
    if conn.database != "keys_db":
        conn.connect(database="keys_db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM activation_keys WHERE activation_key = %s", (key,))
    conn.commit()
    cursor.close()


# NEWSFEEDS_DB
def newsfeeds_is_old_id(conn: MySQLConnection, sp_uid: int, newsfeed_id: int) -> bool:
    if conn.database != "newsfeeds_db":
        conn.connect(database="newsfeeds_db")
    cursor = conn.cursor()
    cursor.execute("SELECT EXISTS (SELECT 1 FROM old_ids WHERE user_id=%s AND newsfeed_id=%s)", (sp_uid, newsfeed_id))
    id_exists = cursor.fetchone()[0]
    cursor.close()
    return bool(id_exists)


def newsfeeds_add_old_id(conn: MySQLConnection, sp_uid: int, newsfeed_id: int):
    if conn.database != "newsfeeds_db":
        conn.connect(database="newsfeeds_db")
    cursor = conn.cursor()
    cursor.execute("INSERT IGNORE INTO old_ids (user_id, newsfeed_id) VALUES (%s, %s)", (sp_uid, newsfeed_id))
    conn.commit()
    cursor.close()


# SP_USERS_DB
def sp_users_add_user(conn: MySQLConnection, sp_uid: int) -> None:
    if conn.database != "sp_users_db":
        conn.connect(database="sp_users_db")
    cursor = conn.cursor()
    cursor.execute("INSERT IGNORE INTO sp_users_configs (sp_uid) VALUES (%s)", (sp_uid,))
    cursor.execute("INSERT IGNORE INTO sp_users_subscriptions (sp_uid) VALUES (%s)", (sp_uid,))
    conn.commit()
    cursor.close()


def sp_users_get_user(conn: MySQLConnection, sp_uid: int) -> dict:
    if conn.database != "sp_users_db":
        conn.connect(database="sp_users_db")
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM sp_users_configs, sp_users_subscriptions "
                   "WHERE sp_users_configs.sp_uid=%s AND sp_users_subscriptions.sp_uid=%s", (sp_uid, sp_uid))
    user_data = cursor.fetchone()
    cursor.close()
    return user_data


def sp_users_configs_update_user(conn: MySQLConnection, sp_uid: int, **kwargs) -> None:
    if conn.database != "sp_users_db":
        conn.connect(database="sp_users_db")
    cursor = conn.cursor()
    for arg in kwargs.items():
        arg_name = arg[0]
        arg_data = arg[1]
        cursor.execute(f"UPDATE sp_users_configs SET {arg_name}=%s WHERE sp_uid=%s", (arg_data, sp_uid))
    conn.commit()
    cursor.close()


def sp_users_subscriptions_update_user(conn: MySQLConnection, sp_uid: int, **kwargs) -> None:
    if conn.database != "sp_users_db":
        conn.connect(database="sp_users_db")
    cursor = conn.cursor()
    for arg in kwargs.items():
        arg_name = arg[0]
        arg_data = arg[1]
        cursor.execute(f"UPDATE sp_users_subscriptions SET {arg_name}=%s WHERE sp_uid=%s", (arg_data, sp_uid))
    conn.commit()
    cursor.close()


# USERS_DB
def users_add_user(conn: MySQLConnection, user_id: int) -> None:
    if conn.database != "users_db":
        conn.connect(database="users_db")
    cursor = conn.cursor()
    cursor.execute("INSERT IGNORE INTO users_auth (user_id) VALUES (%s)", (user_id,))
    cursor.execute("INSERT IGNORE INTO users_statistics (user_id) VALUES (%s)", (user_id,))
    conn.commit()
    cursor.close()


def users_get_user(conn: MySQLConnection, user_id: int) -> dict:
    if conn.database != "users_db":
        conn.connect(database="users_db")
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users_auth, users_statistics "
                   "WHERE users_auth.user_id=%s AND users_statistics.user_id=%s", (user_id, user_id))
    user_data = cursor.fetchone()
    cursor.close()
    return user_data


def users_auth_update_user(conn: MySQLConnection, user_id: int, **kwargs) -> None:
    if conn.database != "users_db":
        conn.connect(database="users_db")
    cursor = conn.cursor()
    for arg in kwargs.items():
        arg_name = arg[0]
        arg_data = arg[1]
        cursor.execute(f"UPDATE users_auth SET {arg_name}=%s WHERE user_id=%s", (arg_data, user_id))
    conn.commit()
    cursor.close()


def users_statistics_update_user_add(conn: MySQLConnection, user_id: int,
                                     shifted_shifts_add: int, shifted_hours_add: float, earned_add: float) -> None:
    if conn.database != "users_db":
        conn.connect(database="users_db")
    cursor = conn.cursor()
    cursor.execute(f"UPDATE users_statistics "
                   f"SET shifted_shifts=shifted_shifts+%s, shifted_hours=shifted_hours+%s, earned=earned+%s "
                   f"WHERE user_id=%s", (shifted_shifts_add, shifted_hours_add, earned_add, user_id))
    conn.commit()
    cursor.close()
