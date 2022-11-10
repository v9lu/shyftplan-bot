# Version 2.2.2 release

from mysql.connector.connection_cext import CMySQLConnection


def keys_activate_key(conn: CMySQLConnection, key: str):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM activation_keys WHERE activation_key = %s", (key,))
    key_data = cursor.fetchone()
    if key_data:
        cursor.execute("DELETE FROM activation_keys WHERE activation_key = %s", (key,))
        cursor.close()
        return key_data
    else:
        cursor.close()
        return False


def keys_add_key(conn: CMySQLConnection, key: str, key_type: str, key_days: int):
    cursor = conn.cursor()
    cursor.execute("INSERT IGNORE INTO activation_keys (activation_key, key_type, key_days) VALUES (%s, %s, %s)",
                   (key, key_type, key_days))
    conn.commit()
    cursor.close()


def keys_remove_key(conn: CMySQLConnection, key: str):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM activation_keys WHERE activation_key = %s", (key,))
    conn.commit()
    cursor.close()


def newsfeeds_is_old_id(conn: CMySQLConnection, sp_uid: int, newsfeed_id: int) -> bool:
    cursor = conn.cursor()
    cursor.execute("SELECT EXISTS (SELECT 1 FROM old_ids WHERE user_id=%s AND newsfeed_id=%s)", (sp_uid, newsfeed_id))
    id_exists = cursor.fetchone()[0]
    cursor.close()
    return bool(id_exists)


def newsfeeds_add_old_id(conn: CMySQLConnection, sp_uid: int, newsfeed_id: int):
    cursor = conn.cursor()
    cursor.execute("INSERT IGNORE INTO old_ids (user_id, newsfeed_id) VALUES (%s, %s)", (sp_uid, newsfeed_id))
    conn.commit()
    cursor.close()


def sp_users_add_user(conn: CMySQLConnection, sp_uid: int) -> None:
    cursor = conn.cursor()
    cursor.execute("INSERT IGNORE INTO sp_users_subscriptions (sp_uid) VALUES (%s)", (sp_uid,))
    conn.commit()
    cursor.close()


def sp_users_sub_info(conn: CMySQLConnection, sp_uid: int) -> dict:
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM sp_users_subscriptions WHERE sp_uid=%s", (sp_uid,))
    user_data = cursor.fetchone()
    cursor.close()
    return user_data


def sp_users_update_user(conn: CMySQLConnection, sp_uid: int, **kwargs) -> None:
    cursor = conn.cursor()
    for arg in kwargs.items():
        arg_name = arg[0]
        arg_data = arg[1]
        cursor.execute(f"UPDATE users_configs SET {arg_name}=%s WHERE sp_uid=%s", (arg_data, sp_uid))
    conn.commit()
    cursor.close()


def users_add_user(conn: CMySQLConnection, user_id: int) -> None:
    cursor = conn.cursor()
    cursor.execute("INSERT IGNORE INTO users_configs (user_id) VALUES (%s)", (user_id,))
    cursor.execute("INSERT IGNORE INTO users_statistics (user_id) VALUES (%s)", (user_id,))
    conn.commit()
    cursor.close()


def users_get_user(conn: CMySQLConnection, user_id: int) -> dict:
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users_configs, users_statistics WHERE users_configs.user_id=%s", (user_id,))
    user_data = cursor.fetchone()
    cursor.close()
    return user_data


def users_configs_update_user(conn: CMySQLConnection, user_id: int, **kwargs) -> None:
    cursor = conn.cursor()
    for arg in kwargs.items():
        arg_name = arg[0]
        arg_data = arg[1]
        cursor.execute(f"UPDATE users_configs SET {arg_name}=%s WHERE user_id=%s", (arg_data, user_id))
    conn.commit()
    cursor.close()


def users_statistics_update_user_add(conn: CMySQLConnection, user_id: int,
                                     shifted_shifts_add: int, shifted_hours_add: float, earned_add: float) -> None:
    cursor = conn.cursor()
    cursor.execute(f"UPDATE users_statistics "
                   f"SET shifted_shifts=shifted_shifts+%s, shifted_hours=shifted_hours+%s, earned=earned+%s "
                   f"WHERE user_id=%s", (shifted_shifts_add, shifted_hours_add, earned_add, user_id))
    conn.commit()
    cursor.close()
