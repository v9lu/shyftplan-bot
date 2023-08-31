# Version 1.0.1 release

import configparser
import mysql.connector as mysql
import requests
from datetime import datetime, timedelta
from mysql.connector import MySQLConnection
from tools import config_data, db


def get_subscribers(conn: MySQLConnection) -> dict:
    if conn.database != "sp_users_db":
        conn.connect(database="sp_users_db")
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT * FROM sp_users_subscriptions WHERE "
                       "subscription != 'admin' AND "
                       "expire IS NOT NULL AND "
                       "is_notified IS NOT NULL")
        return cursor.fetchall()


def get_user_ids_by_sp_uid(conn: MySQLConnection, sp_uid: int) -> list:
    if conn.database != "users_db":
        conn.connect(database="users_db")
    with conn.cursor() as cursor:
        cursor.execute("SELECT user_id FROM users_auth WHERE "
                       "sp_uid=%s", (sp_uid,))
        user_ids = [row[0] for row in cursor.fetchall()]
    return user_ids


def notify(conn: MySQLConnection, sp_uid: int, text: str):
    users_ids = get_user_ids_by_sp_uid(conn, sp_uid)
    for user_id in users_ids:
        requests.post(f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={user_id}&text="
                      f"<b>{text}</b>"
                      f"&parse_mode=HTML")


TG_BOT_API_TOKEN = config_data.get_bot(configparser.ConfigParser())["bot_token"]
db_data = config_data.get_db(configparser.ConfigParser())
db_connect = mysql.connect(user="root",
                           host=db_data["ip"],
                           port=db_data["port"],
                           password=db_data["password"])
matching_users = get_subscribers(db_connect)
for user in matching_users:
    if datetime.now() > user["expire"] + timedelta(days=3):
        if user["is_notified"] and (user["subscription"] == "standard" or user["subscription"] == "premium"):
            notify(conn=db_connect, sp_uid=user["sp_uid"],
                   text="🚮 You didn't renew your subscription, your slot was opened for other users!")
            db.sp_users_subscriptions_update_user(conn=db_connect, sp_uid=user["sp_uid"],
                                                  subscription=None, expire=None)
    if datetime.now() > user["expire"]:
        if not user["is_notified"] and (user["subscription"] == "trial" or user["subscription"] == "friend"):
            notify(conn=db_connect, sp_uid=user["sp_uid"],
                   text="📛 Your subscription has been expired. Auto-shifting was stopped!")
            db.sp_users_subscriptions_update_user(conn=db_connect, sp_uid=user["sp_uid"],
                                                  subscription=None, expire=None, is_notified=True)
            db.sp_users_configs_update_user(conn=db_connect, sp_uid=user["sp_uid"],
                                            prog_status=0)
        elif not user["is_notified"] and (user["subscription"] == "standard" or user["subscription"] == "premium"):
            notify(conn=db_connect, sp_uid=user["sp_uid"],
                   text="📛 Your subscription has expired, settings have been reset. Auto-shifting was stopped!\n"
                        "⚠️ If the subscription won't be renewed within 3 days, "
                        "your slot will be released for other users!!!")
            db.sp_users_subscriptions_update_user(conn=db_connect, sp_uid=user["sp_uid"],
                                                  is_notified=True)
            db.sp_users_configs_update_user(conn=db_connect, sp_uid=user["sp_uid"], prog_status=0)
db_connect.close()
