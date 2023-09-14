# Version 1.23.1 release

import configparser
import json
import logging
import mysql.connector as mysql
import pytz
import requests
import time
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path

from tools import config_data, db, work_data

TG_USER_ID = int(Path(__file__).stem.split("_")[1])  # Path(__file__).stem = ../path/program_0.py > program_0 > 0
TG_BOT_API_TOKEN = config_data.get_bot(configparser.ConfigParser())["bot_token"]
BASE_URL = "https://shyftplan.com"
COMPANY_ID = 50272
DB_DATA = config_data.get_db(configparser.ConfigParser())
DB_CONNECT = mysql.connect(user="root",
                           host=DB_DATA["ip"],
                           port=DB_DATA["port"],
                           password=DB_DATA["password"])
requests.post(f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_USER_ID}&text="
              f"💫 <b>The auto-shifting has been started/restarted!</b>"
              f"&parse_mode=HTML")

logging_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logging_handler = RotatingFileHandler(f'script_{TG_USER_ID}.log', maxBytes=10 * 1024 * 1024, backupCount=1)
logging_handler.setLevel(logging.DEBUG)
logging_handler.setFormatter(logging_formatter)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging_handler)

logging.info('Начало выполнения скрипта')

def api_data_checker(sp_user_data: dict,
                     sp_user_locations: list,
                     shift_loc_pos_id: int,
                     shift_time_range: tuple) -> list:
    for location in sp_user_locations:
        if (shift_loc_pos_id in location["ids"]["car"] and sp_user_data["car_status"]) or \
           (shift_loc_pos_id in location["ids"]["scooter"] and sp_user_data["scooter_status"]) or \
           (shift_loc_pos_id in location["ids"]["ebike"] and sp_user_data["ebike_status"]) or \
           (shift_loc_pos_id in location["ids"]["bike"] and sp_user_data["bike_status"]):
            if shift_time_range in location["dates"]:
                return [True, location]
    return [False, None]


def can_be_shifted(shift_id: int,
                   shift_from_news: bool,
                   shift_loc_pos_id: int,
                   shift_time_range: tuple,
                   trusted_shift: bool) -> bool:
    def highers_without_this_shift(my_subscription: str):
        higher_subscriptions = {
            "friend": ["admin"],
            "premium": ["admin", "friend"],
            "standard": ["admin", "friend", "premium"],
            "trial": ["admin", "friend", "premium", "standard"]
        }

        if DB_CONNECT.database != "users_db":
            DB_CONNECT.connect(database="users_db")
        with DB_CONNECT.cursor(dictionary=True) as cursor:
            if trusted_shift:
                cursor.execute("SELECT * FROM users_auth WHERE sp_uid IS NOT NULL AND trusted=1")
                suitable_users_data = cursor.fetchall()
            else:
                cursor.execute("SELECT * FROM users_auth WHERE sp_uid IS NOT NULL")
                suitable_users_data = cursor.fetchall()
        if suitable_users_data:
            suitable_users_sp_uids = [suitable_user_data["sp_uid"] for suitable_user_data in suitable_users_data]

            if DB_CONNECT.database != "sp_users_db":
                DB_CONNECT.connect(database="sp_users_db")
            with DB_CONNECT.cursor(dictionary=True) as cursor:
                if shift_from_news:
                    shared_query = "AND sp_users_configs.prog_shift_offers=1 "
                else:
                    shared_query = "AND sp_users_configs.prog_open_shifts=1 "
                cursor.execute("SELECT sp_users_configs.*, sp_users_subscriptions.subscription "
                               "FROM sp_users_configs "
                               "JOIN sp_users_subscriptions "
                               "ON sp_users_configs.sp_uid = sp_users_subscriptions.sp_uid "
                               f"WHERE sp_users_configs.sp_uid IN ({','.join(['%s'] * len(suitable_users_sp_uids))}) "
                               "AND sp_users_configs.prog_status=1 "
                               f"{shared_query}"
                               "AND sp_users_configs.shifts != '[]' "
                               "AND sp_users_subscriptions.subscription "
                               f"IN ({','.join(['%s'] * len(higher_subscriptions[my_subscription]))}) "
                               "AND sp_users_subscriptions.expire > NOW()",
                               tuple(suitable_users_sp_uids) + tuple(higher_subscriptions[my_subscription]))
                suitable_sp_users_data = cursor.fetchall()
            if suitable_sp_users_data:
                suitable_sp_users_with_shifts_data = []
                for suitable_sp_user_data in suitable_sp_users_data:
                    suitable_sp_user_locations = work_data.easy_converter(shifts=suitable_sp_user_data["shifts"])
                    adc_response = api_data_checker(sp_user_data=suitable_sp_user_data,
                                                    sp_user_locations=suitable_sp_user_locations,
                                                    shift_loc_pos_id=shift_loc_pos_id,
                                                    shift_time_range=shift_time_range)
                    if adc_response[0]:
                        shift_starts_at = shift_time_range[0]
                        # Соседние смены всех не проверяем - потому что это не рационально
                        if suitable_sp_user_data["prog_cutoff_time"] == 30:
                            if datetime.now() + timedelta(minutes=30) > shift_starts_at:
                                continue
                        else:
                            if datetime.now() + timedelta(hours=suitable_sp_user_data["prog_cutoff_time"]) > shift_starts_at:
                                continue
                        suitable_sp_users_with_shifts_data.append(suitable_sp_user_data)
                if suitable_sp_users_with_shifts_data:
                    if shift_from_news:
                        return False
                    else:
                        response = requests.get(f"{BASE_URL}/api/v1/shifts/{shift_id}",
                                                params={"user_email": USER_DATA["sp_email"],
                                                        "authentication_token": USER_DATA["sp_token"]})
                        json_response = response.json()
                        if len(suitable_sp_users_with_shifts_data) >= json_response["workers"]:
                            return False
                        else:
                            return True
                else:
                    return True
            else:
                return True
        else:
            return True
    trusted_loc_pos_ids = [170251, 170258, 170254  # Warsaw
                           ]  # Gdansk
    response = requests.get(f"{BASE_URL}/api/v1/shifts",
                            params={"user_email": USER_DATA["sp_email"],
                                    "authentication_token": USER_DATA["sp_token"],
                                    "page": 1,
                                    "per_page": 1,
                                    "starts_at": POLAND_TIMEZONE.localize(datetime.now()).isoformat(),
                                    "ends_at": POLAND_TIMEZONE.localize(datetime.now() + timedelta(days=2)).isoformat(),
                                    "locations_position_ids[]": trusted_loc_pos_ids})
    json_response = response.json()
    if json_response["total"]:
        is_trusted = True
    else:
        is_trusted = False
    if USER_DATA["trusted"] != is_trusted:
        db.users_auth_update_user(conn=DB_CONNECT, user_id=TG_USER_ID, trusted=is_trusted)

    if SP_USER_DATA["subscription"] == "admin":
        return True
    else:
        if highers_without_this_shift(my_subscription=SP_USER_DATA["subscription"]):
            return True
        else:
            return False


def join_or_accept_shift(shift_id: int,
                         shift_loc_pos_id: int,
                         shift_time_range: tuple,
                         user_location: dict,
                         request_type: str) -> None:
    shift_starts_at = POLAND_TIMEZONE.localize(shift_time_range[0])
    response = requests.get(f"{BASE_URL}/api/v1/evaluations",
                            params={"user_email": USER_DATA["sp_email"],
                                    "authentication_token": USER_DATA["sp_token"],
                                    "page": 1,
                                    "per_page": 1,
                                    "starts_at": (shift_starts_at - timedelta(hours=4)).isoformat(),
                                    "ends_at": shift_starts_at.isoformat(),
                                    "state": "no_evaluation",
                                    "employment_id": USER_DATA["sp_eid"]})
    json_response = response.json()
    if len(json_response["items"]) > 0:  # Если уже что-то забронированно между часами
        evaluation_ends_at_iso = datetime.fromisoformat(json_response["items"][0]["evaluation_ends_at"])
        parent_shift = (shift_starts_at == evaluation_ends_at_iso)
    else:
        parent_shift = False

    if not parent_shift:
        if SP_USER_DATA["prog_cutoff_time"] == 30:
            if datetime.now() + timedelta(minutes=30) > shift_starts_at.replace(tzinfo=None):
                return
        else:
            if datetime.now() + timedelta(hours=SP_USER_DATA["prog_cutoff_time"]) > shift_starts_at.replace(tzinfo=None):
                return

    response = requests.get(f"{BASE_URL}/api/v1/locations_positions/{shift_loc_pos_id}",
                            params={"user_email": USER_DATA["sp_email"],
                                    "authentication_token": USER_DATA["sp_token"]})
    json_response = response.json()
    if "Zaufany" in json_response["position_name"]:
        trusted_shift = True
    else:
        trusted_shift = False

    if request_type == "join":
        if can_be_shifted(shift_id=shift_id, shift_from_news=False,
                          shift_time_range=shift_time_range, shift_loc_pos_id=shift_loc_pos_id,
                          trusted_shift=trusted_shift):
            response = requests.post(f"{BASE_URL}/api/v1/requests/join", params={
                "user_email": USER_DATA["sp_email"],
                "authentication_token": USER_DATA["sp_token"],
                "company_id": COMPANY_ID,
                "shift_id": shift_id
            })
            if response.status_code == 400:  # Conflict
                date_start_str = shift_time_range[0].strftime("%d.%m.%Y")
                date_end_str = shift_time_range[1].strftime("%d.%m.%Y")
                time_start_str = shift_time_range[0].strftime("%H:%M")
                time_end_str = shift_time_range[1].strftime("%H:%M")
                day_string = f"{user_location['name']}/{date_start_str}/{time_start_str}-{time_end_str}"
                work_data.remove_days(conn=DB_CONNECT, sp_uid=USER_DATA["sp_uid"], days=day_string)
                requests.post(f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_USER_ID}&text="
                              f"📕 <b>Shift was removed from your list:</b>\n"
                              f"<b>DS:</b> {user_location['fullname']}\n"
                              f"<b>Start:</b> {date_start_str} at {time_start_str}\n"
                              f"<b>End:</b> {date_end_str} at {time_end_str}\n"
                              f"<b>Info:</b> You already have a shift at the same time"
                              f"&parse_mode=HTML")
    elif request_type == "replace":
        if can_be_shifted(shift_id=shift_id, shift_from_news=True,
                          shift_time_range=shift_time_range, shift_loc_pos_id=shift_loc_pos_id,
                          trusted_shift=trusted_shift):
            response = requests.post(f"{BASE_URL}/api/v1/requests/replace/accept",
                                     params={"user_email": USER_DATA["sp_email"],
                                             "authentication_token": USER_DATA["sp_token"],
                                             "company_id": COMPANY_ID,
                                             "id": shift_id,
                                             "ignore_conflicts": "false"})
            if response.status_code == 400:  # Conflict
                date_start_str = shift_time_range[0].strftime("%d.%m.%Y")
                date_end_str = shift_time_range[1].strftime("%d.%m.%Y")
                time_start_str = shift_time_range[0].strftime("%H:%M")
                time_end_str = shift_time_range[1].strftime("%H:%M")
                day_string = f"{user_location['name']}/{date_start_str}/{time_start_str}-{time_end_str}"
                work_data.remove_days(conn=DB_CONNECT, sp_uid=USER_DATA["sp_uid"], days=day_string)
                requests.post(f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_USER_ID}&text="
                              f"📕 <b>Shift was removed from your list:</b>\n"
                              f"<b>DS:</b> {user_location['fullname']}\n"
                              f"<b>Start:</b> {date_start_str} at {time_start_str}\n"
                              f"<b>End:</b> {date_end_str} at {time_end_str}\n"
                              f"<b>Info:</b> You already have a shift at the same time"
                              f"&parse_mode=HTML")


def newsfeeds_checker() -> bool:
    logging.debug('Вход в функцию newsfeeds_checker() - успешно')
    locations = work_data.converter(conn=DB_CONNECT, sp_uid=USER_DATA["sp_uid"])
    response = requests.get(f"{BASE_URL}/api/v1/newsfeeds",
                            params={"user_email": USER_DATA["sp_email"],
                                    "authentication_token": USER_DATA["sp_token"],
                                    "company_id": COMPANY_ID,
                                    "page": 1,
                                    "per_page": 1})
    if response.status_code == 401:  # login data is outdated
        db.users_auth_update_user(conn=DB_CONNECT, user_id=TG_USER_ID,
                                  sp_email=None, sp_token=None)
        db.sp_users_configs_update_user(conn=DB_CONNECT, sp_uid=USER_DATA["sp_uid"],
                                        prog_status=False)
        requests.post(f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_USER_ID}&text="
                      f"⛔ Auto-shifting was stopped because your data is outdated, "
                      f"use command /auth to authorize again.")
        return False
    else:
        json_response = response.json()
        json_items = json_response["items"][0]
        is_old = db.is_old_id(conn=DB_CONNECT, sp_uid=USER_DATA["sp_uid"], item_id=json_items["id"])
        if not is_old:
            if json_items["key"] == "request.swap_request" and "objekt" in json_items and \
               SP_USER_DATA["prog_shift_offers"]:
                shift_loc_pos_id: int = json_items["metadata"]["locations_position_ids"][0]
                shift_id: int = json_items["objekt"]["shift"]["id"]
                shift_starts_at_iso: str = json_items["objekt"]["shift"]["starts_at"]  # tz +02:00
                shift_ends_at_iso: str = json_items["objekt"]["shift"]["ends_at"]  # tz +02:00
                shift_starts_at = datetime.fromisoformat(shift_starts_at_iso).replace(tzinfo=None)
                shift_ends_at = datetime.fromisoformat(shift_ends_at_iso).replace(tzinfo=None)
                adc_response = api_data_checker(sp_user_data=SP_USER_DATA,
                                                sp_user_locations=locations,
                                                shift_loc_pos_id=shift_loc_pos_id,
                                                shift_time_range=(shift_starts_at, shift_ends_at))
                adc_response_code = adc_response[0]
                adc_response_loc = adc_response[1]
                if adc_response_code:
                    join_or_accept_shift(shift_id=json_items["objekt_id"],
                                         shift_loc_pos_id=shift_loc_pos_id,
                                         shift_time_range=(shift_starts_at, shift_ends_at),
                                         user_location=adc_response_loc,
                                         request_type="replace")
            elif json_items["key"] == "request.refused":
                requests.post(f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id=1630691291&text="
                              f"❌ Unsuccessfully shifted (Refused): {response.text}")
            elif json_items["key"] == "message" and SP_USER_DATA["prog_news"]:
                requests.post(f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_USER_ID}&text="
                              f"💬 Shyftplan Message:\n{json_items['message']}")
            db.add_old_id(conn=DB_CONNECT, sp_uid=USER_DATA["sp_uid"], item_id=json_items["id"])
        return True


def open_shifts_checker() -> bool:
    logging.debug('Вход в функцию open_shifts_checker() - успешно')
    locations = work_data.converter(conn=DB_CONNECT, sp_uid=USER_DATA["sp_uid"])
    shifts_url_params = {
        "user_email": USER_DATA["sp_email"],
        "authentication_token": USER_DATA["sp_token"],
        "company_id": COMPANY_ID,
        "page": 1,
        "per_page": 300,
        "only_open": "true",
        "order_dir": "asc",
        "starts_at": POLAND_TIMEZONE.localize(datetime.now()).isoformat(),
        "locations_position_ids[]": []
    }
    for location in locations:
        if len(location["dates"]) > 0:
            if SP_USER_DATA["bike_status"]:
                shifts_url_params["locations_position_ids[]"].append(location["ids"]["bike"])
            if SP_USER_DATA["ebike_status"]:
                shifts_url_params["locations_position_ids[]"].append(location["ids"]["ebike"])
            if SP_USER_DATA["scooter_status"]:
                shifts_url_params["locations_position_ids[]"].append(location["ids"]["scooter"])
            if SP_USER_DATA["car_status"]:
                shifts_url_params["locations_position_ids[]"].append(location["ids"]["car"])
    if shifts_url_params["locations_position_ids[]"]:
        response = requests.get(f"{BASE_URL}/api/v1/shifts", params=shifts_url_params)
        if response.status_code == 401:  # login data is outdated
            db.users_auth_update_user(conn=DB_CONNECT, user_id=TG_USER_ID,
                                      sp_email=None, sp_token=None)
            db.sp_users_configs_update_user(conn=DB_CONNECT, sp_uid=USER_DATA["sp_uid"],
                                            prog_status=False)
            requests.post(f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_USER_ID}&text="
                          f"⛔ Auto-shifting was stopped because your data is outdated, "
                          f"use command /auth to authorize again.")
            return False
        else:
            json_response = response.json()
            json_items = json_response["items"]
            for item in json_items:
                shift_loc_pos_id = item["locations_position_id"]
                shift_starts_at = datetime.fromisoformat(item["starts_at"]).replace(tzinfo=None)
                shift_ends_at = datetime.fromisoformat(item["ends_at"]).replace(tzinfo=None)
                adc_response = api_data_checker(sp_user_data=SP_USER_DATA,
                                                sp_user_locations=locations,
                                                shift_loc_pos_id=shift_loc_pos_id,
                                                shift_time_range=(shift_starts_at, shift_ends_at))
                adc_response_code = adc_response[0]
                adc_response_loc = adc_response[1]
                if adc_response_code:
                    is_old = db.is_old_id(conn=DB_CONNECT, sp_uid=USER_DATA["sp_uid"], item_id=item["id"])
                    if not is_old:
                        join_or_accept_shift(shift_id=item["id"],
                                             shift_loc_pos_id=shift_loc_pos_id,
                                             shift_time_range=(shift_starts_at, shift_ends_at),
                                             user_location=adc_response_loc,
                                             request_type="join")
                        db.add_old_id(conn=DB_CONNECT, sp_uid=USER_DATA["sp_uid"], item_id=item["id"])
    return True


def notificator() -> None:
    logging.debug('Вход в функцию notificator() - успешно')
    wait_locations = work_data.converter(conn=DB_CONNECT, sp_uid=USER_DATA["sp_uid"])
    wait_location_date_ranges = [location_date for location in wait_locations for location_date in location["dates"]]
    if wait_location_date_ranges:
        min_start_date_iso = POLAND_TIMEZONE.localize(min(wait_location_date_ranges,
                                                          key=lambda location_date: location_date[0])[0]).isoformat()
        max_end_date_iso = POLAND_TIMEZONE.localize(max(wait_location_date_ranges,
                                                        key=lambda location_date: location_date[1])[1]).isoformat()
        response = requests.get(f"{BASE_URL}/api/v1/shifts", params={
            "user_email": USER_DATA["sp_email"],
            "authentication_token": USER_DATA["sp_token"],
            "company_id": COMPANY_ID,
            "page": 1,
            "per_page": 150,
            "starts_at": min_start_date_iso,
            "ends_at": max_end_date_iso,
            "employment_id": USER_DATA["sp_eid"],
            "order_dir": "desc"
        })
        json_response = response.json()
        booked_shifts = json_response["items"]

        # delete locations that was booked
        for location in wait_locations:
            for shift in booked_shifts:
                if any(shift["locations_position_id"] in ids_set for ids_set in location["ids"].values()):
                    shift_starts_at = datetime.fromisoformat(shift["starts_at"]).replace(tzinfo=None)
                    shift_ends_at = datetime.fromisoformat(shift["ends_at"]).replace(tzinfo=None)
                    shift_time_range = (shift_starts_at, shift_ends_at)
                    if shift_time_range in location["dates"]:
                        date_start_str = shift_starts_at.strftime("%d.%m.%Y")
                        date_end_str = shift_ends_at.strftime("%d.%m.%Y")
                        time_start_str = shift_starts_at.strftime("%H:%M")
                        time_end_str = shift_ends_at.strftime("%H:%M")
                        day_string = f"{location['name']}/{date_start_str}/{time_start_str}-{time_end_str}"
                        work_data.remove_days(conn=DB_CONNECT, sp_uid=USER_DATA["sp_uid"], days=day_string)
                        addition_hours = (shift_ends_at - shift_starts_at).seconds / 60 / 60
                        addition_earn = addition_hours * 25
                        db.users_statistics_update_user_add(conn=DB_CONNECT, user_id=TG_USER_ID,
                                                            shifted_shifts_add=1, shifted_hours_add=addition_hours,
                                                            earned_add=addition_earn)
                        requests.post(
                            f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_USER_ID}&text="
                            f"✅ <b>New shift booked!</b>\n"
                            f"<b>DS:</b> {location['fullname']}\n"
                            f"<b>Start:</b> {date_start_str} <b>at</b> {time_start_str}\n"
                            f"<b>End:</b> {date_end_str} <b>at</b> {time_end_str}"
                            f"&parse_mode=HTML")


# MAIN SCRIPT #
while True:
    try:
        logging.info('Новая итерация цикла')
        POLAND_TIMEZONE = pytz.timezone("Europe/Warsaw")
        USER_DATA = db.users_get_user(conn=DB_CONNECT, user_id=TG_USER_ID)
        SP_USER_DATA = db.sp_users_get_user(conn=DB_CONNECT, sp_uid=USER_DATA["sp_uid"])
        SP_USER_SHIFTS_EXTRACTED = json.loads(SP_USER_DATA["shifts"])

        logging.debug('Чтение базы данных - успешно')

        if not SP_USER_DATA["subscription"]:
            time.sleep(5)
            continue

        if datetime.now() >= SP_USER_DATA["expire"]:
            time.sleep(5)
            continue

        if SP_USER_DATA["prog_news"] == 0 and not SP_USER_SHIFTS_EXTRACTED:
            time.sleep(5)
            continue

        if not SP_USER_DATA["prog_status"] or \
                not (SP_USER_DATA["prog_open_shifts"] or
                     SP_USER_DATA["prog_shift_offers"] or
                     SP_USER_DATA["prog_news"]) or \
                not (SP_USER_DATA["bike_status"] or
                     SP_USER_DATA["ebike_status"] or
                     SP_USER_DATA["scooter_status"] or
                     SP_USER_DATA["car_status"]):
            time.sleep(5)
            continue

        logging.debug('Условия для продолжения работы скрипта - успешно')
        time.sleep(SP_USER_DATA["prog_sleep"])

        try:
            if SP_USER_DATA["prog_open_shifts"]:
                if not open_shifts_checker():
                    continue
            if SP_USER_DATA["prog_shift_offers"] or SP_USER_DATA["prog_news"]:
                if not newsfeeds_checker():
                    continue
            notificator()
        except (requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
                json.decoder.JSONDecodeError) as e:
            print(f"[ERROR] {type(e).__name__}")
            logging.error('Возникла ошибка во втором блоке исключений, повторение скрипта через 5 секунд')
            time.sleep(5)
            continue
    except mysql.errors.OperationalError as e:
        print(f"[ERROR] {type(e).__name__}")
        logging.error('Возникла ошибка в первом блоке исключений, повторение скрипта через 5 секунд')
        time.sleep(5)
        continue
