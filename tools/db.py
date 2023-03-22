# Version 2.4.1 release

from mysql.connector import MySQLConnection


# KEYS_DB
def keys_activate_key(conn: MySQLConnection, key: str):
    if conn.database != "keys_db":
        conn.connect(database="keys_db")
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT * FROM activation_keys WHERE activation_key=%s", (key,))
        key_data = cursor.fetchone()
        cursor.execute("DELETE FROM activation_keys WHERE activation_key=%s", (key,))
        conn.commit()
    return key_data if key_data else False


def keys_add_key(conn: MySQLConnection, key: str, key_type: str, key_days: int):
    if conn.database != "keys_db":
        conn.connect(database="keys_db")
    with conn.cursor() as cursor:
        cursor.execute("INSERT IGNORE INTO activation_keys (activation_key, key_type, key_days) VALUES (%s, %s, %s)",
                       (key, key_type, key_days))
        conn.commit()


def keys_remove_key(conn: MySQLConnection, key: str):
    if conn.database != "keys_db":
        conn.connect(database="keys_db")
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM activation_keys WHERE activation_key = %s", (key,))
        conn.commit()


# NEWSFEEDS_DB
def newsfeeds_is_old_id(conn: MySQLConnection, sp_uid: int, newsfeed_id: int) -> bool:
    if conn.database != "newsfeeds_db":
        conn.connect(database="newsfeeds_db")
    with conn.cursor() as cursor:
        cursor.execute("SELECT EXISTS (SELECT 1 FROM old_ids WHERE user_id=%s AND newsfeed_id=%s)",
                       (sp_uid, newsfeed_id))
        id_exists = cursor.fetchone()[0]
    return id_exists


def newsfeeds_add_old_id(conn: MySQLConnection, sp_uid: int, newsfeed_id: int):
    if conn.database != "newsfeeds_db":
        conn.connect(database="newsfeeds_db")
    with conn.cursor() as cursor:
        cursor.execute("INSERT IGNORE INTO old_ids (user_id, newsfeed_id) VALUES (%s, %s)", (sp_uid, newsfeed_id))
        conn.commit()


# SP_USERS_DB
def sp_users_add_user(conn: MySQLConnection, sp_uid: int) -> None:
    if conn.database != "sp_users_db":
        conn.connect(database="sp_users_db")
    with conn.cursor() as cursor:
        tables = ["sp_users_configs", "sp_users_subscriptions"]
        for table in tables:
            cursor.execute(f"INSERT IGNORE INTO {table} (sp_uid) VALUES (%s)", (sp_uid,))
        conn.commit()


def sp_users_get_user(conn: MySQLConnection, sp_uid: int) -> dict:
    if conn.database != "sp_users_db":
        conn.connect(database="sp_users_db")
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT * FROM sp_users_configs, sp_users_subscriptions "
                       "WHERE sp_users_configs.sp_uid=%s AND sp_users_subscriptions.sp_uid=%s", (sp_uid, sp_uid))
        sp_user_data = cursor.fetchone()
    return sp_user_data


def sp_users_get_subs_count(conn: MySQLConnection) -> dict:
    if conn.database != "sp_users_db":
        conn.connect(database="sp_users_db")
    with conn.cursor() as cursor:
        cursor.execute("SELECT subscription, COUNT(*) FROM sp_users_subscriptions GROUP BY subscription")
        subscription_counts = cursor.fetchall()
    subscription_counts_dict = {subscription: count for subscription, count in subscription_counts}
    return {"trial": subscription_counts_dict.get("trial", 0),
            "standard": subscription_counts_dict.get("standard", 0),
            "premium": subscription_counts_dict.get("premium", 0)}


def sp_users_configs_update_user(conn: MySQLConnection, sp_uid: int, **kwargs) -> None:
    if conn.database != "sp_users_db":
        conn.connect(database="sp_users_db")
    with conn.cursor() as cursor:
        for arg in kwargs.items():
            arg_name = arg[0]
            arg_data = arg[1]
            cursor.execute(f"UPDATE sp_users_configs SET {arg_name}=%s WHERE sp_uid=%s", (arg_data, sp_uid))
        conn.commit()


def sp_users_subscriptions_update_user(conn: MySQLConnection, sp_uid: int, **kwargs) -> None:
    if conn.database != "sp_users_db":
        conn.connect(database="sp_users_db")
    with conn.cursor() as cursor:
        for arg in kwargs.items():
            arg_name = arg[0]
            arg_data = arg[1]
            cursor.execute(f"UPDATE sp_users_subscriptions SET {arg_name}=%s WHERE sp_uid=%s", (arg_data, sp_uid))
        conn.commit()


# USERS_DB
def users_add_user(conn: MySQLConnection, user_id: int) -> None:
    if conn.database != "users_db":
        conn.connect(database="users_db")
    with conn.cursor() as cursor:
        tables = ["users_auth", "users_statistics"]
        for table in tables:
            cursor.execute(f"INSERT IGNORE INTO {table} (user_id) VALUES (%s)", (user_id,))
        conn.commit()


def users_get_user(conn: MySQLConnection, user_id: int) -> dict:
    if conn.database != "users_db":
        conn.connect(database="users_db")
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT * FROM users_auth JOIN users_statistics "
                       "ON users_auth.user_id = users_statistics.user_id "
                       "WHERE users_auth.user_id=%s", (user_id,))
        user_data = cursor.fetchone()
    return user_data


def users_get_users_ids(conn: MySQLConnection) -> list:
    if conn.database != "users_db":
        conn.connect(database="users_db")
    with conn.cursor() as cursor:
        cursor.execute("SELECT user_id FROM users_auth")
        user_ids = cursor.fetchall()
    return [user_id[0] for user_id in user_ids]


def users_auth_update_user(conn: MySQLConnection, user_id: int, **kwargs) -> None:
    if conn.database != "users_db":
        conn.connect(database="users_db")
    with conn.cursor() as cursor:
        for arg in kwargs.items():
            arg_name = arg[0]
            arg_data = arg[1]
            cursor.execute(f"UPDATE users_auth SET {arg_name}=%s WHERE user_id=%s", (arg_data, user_id))
        conn.commit()


def users_statistics_update_user_add(conn: MySQLConnection, user_id: int,
                                     shifted_shifts_add: int, shifted_hours_add: float, earned_add: float) -> None:
    if conn.database != "users_db":
        conn.connect(database="users_db")
    with conn.cursor() as cursor:
        cursor.execute(f"UPDATE users_statistics "
                       f"SET shifted_shifts=shifted_shifts+%s, shifted_hours=shifted_hours+%s, earned=earned+%s "
                       f"WHERE user_id=%s", (shifted_shifts_add, shifted_hours_add, earned_add, user_id))
        conn.commit()
