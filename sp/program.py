# Version 1.11.0 release

import configparser
import json
import requests
import time
from datetime import datetime, timedelta
import mysql.connector as mysql

import config_data
import db
import work_data


database_data = config_data.get_db(configparser.ConfigParser())
user_data = config_data.get_user(configparser.ConfigParser())
TG_MY_ID: int = user_data["telegram_id"]
TG_BOT_API_TOKEN = config_data.get_bot_token(configparser.ConfigParser())
SITE = "https://shyftplan.com"
COMPANY_ID = 50272


def api_data_checker(loc_pos_id: int, dts: tuple) -> list:
    locations = work_data.converter(today=datetime.now().strftime("%d.%m.%Y"))
    for location in locations:
        if location["id"] == loc_pos_id:
            if dts in location["dates"]:
                return [True, location]
            else:
                return [False, None]
    else:
        return [False, None]


def remove_day_request(location_name: str, datetimes: tuple):
    day = datetimes[0].strftime("%d.%m.%Y")
    start_hour = datetimes[0].strftime("%H:%M")
    end_hour = datetimes[1].strftime("%H:%M")
    remove_day_string = f"{location_name}/{day}/{start_hour}-{end_hour}"
    work_data.remove_days(remove_day_string)


def join_or_accept_shift(shift_id: int, location: dict, shift_type: str, datetimes: tuple) -> None:
    datetime_starts: datetime = datetimes[0].replace(tzinfo=None)
    datetime_ends: datetime = datetimes[1].replace(tzinfo=None)
    if shift_type == "join":
        response = requests.post(SITE + "/api/v1/requests/join",
                                 params={"user_email": user_data["shyftplan_email"],
                                         "authentication_token": user_data["shyftplan_token"],
                                         "company_id": COMPANY_ID,
                                         "shift_id": shift_id})
        json_response = json.loads(response.text)
        if "conflicts" in json_response:
            remove_day_request(location["name"], datetimes)
            response = requests.get(SITE + "/api/v1/evaluations",
                                    params={"user_email": user_data["shyftplan_email"],
                                            "authentication_token": user_data["shyftplan_token"],
                                            "page": 1,
                                            "per_page": 1,
                                            "starts_at": datetimes[0].isoformat(),  # tz +02:00
                                            "ends_at": datetimes[1].isoformat(),  # tz +02:00
                                            "state": "no_evaluation",
                                            "employment_id": user_data["shyftplan_employee_id"]})
            json_response = json.loads(response.text)
            if len(json_response["items"]) > 0:
                if json_response["items"][0]["locations_position_id"] == location["id"]:
                    requests.post(
                        f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_MY_ID}&text="
                        f"✅ Shift was accepted on: {location['fullname']}\n"
                        f"From: {datetime_starts}\n"
                        f"To: {datetime_ends}")
                else:
                    requests.post(
                        f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_MY_ID}&text="
                        f"📕 Shift was removed from your list:\n"
                        f"Location: {location['fullname']}\n"
                        f"From: {datetime_starts}\n"
                        f"To: {datetime_ends}\n"
                        f"Information: You already have a shift at the same time")
            else:
                requests.post(
                    f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_MY_ID}&text="
                    f"📕 Shift was removed from your list:\n"
                    f"Location: {location['fullname']}\n"
                    f"From: {datetime_starts}\n"
                    f"To: {datetime_ends}\n"
                    f"Information: You already have a shift at the same time")
    elif shift_type == "replace":
        response = requests.post(SITE + "/api/v1/requests/replace/accept",
                                 params={"user_email": user_data["shyftplan_email"],
                                         "authentication_token": user_data["shyftplan_token"],
                                         "company_id": COMPANY_ID,
                                         "id": shift_id,
                                         "ignore_conflicts": "false"})
        json_response = json.loads(response.text)
        if "error" in response:
            requests.post(
                f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_MY_ID}&text="
                f"! DEVELOPER INFO, MAYBE BUG (В ЭТОМ МЕТОДЕ НЕ ДОЛЖНО БЫТЬ ОШИБОК) !\n"
                f"Response: {response.text}")


def notification(loc_pos_id: int, objekt: dict, shifted: str, text: str = '') -> None:
    isotime_starts = objekt["starts_at"]
    isotime_ends = objekt["ends_at"]
    datetime_starts = datetime.fromisoformat(isotime_starts).replace(tzinfo=None)
    datetime_ends = datetime.fromisoformat(isotime_ends).replace(tzinfo=None)
    datetimes: tuple = (datetime_starts, datetime_ends)
    locations = work_data.converter(today=datetime.now().strftime("%d.%m.%Y"))
    for location in locations:
        if location["id"] == loc_pos_id:
            if datetimes in location["dates"]:
                location_fullname = location["fullname"]
                if shifted == "True":
                    remove_day_request(location["name"], datetimes)
                    requests.post(
                        f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_MY_ID}&text="
                        f"✅ Successfully shifted on: {location_fullname}\n"
                        f"From: {datetime_starts}\n"
                        f"To: {datetime_ends}" + text)
                elif shifted == "Unknown":
                    requests.post(
                        f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_MY_ID}&text="
                        f"⚠️ Trying to shift on: {location_fullname}\n"
                        f"From: {datetime_starts}\n"
                        f"To: {datetime_ends}" + text)
                elif shifted == "False":
                    requests.post(
                        f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_MY_ID}&text="
                        f"❌ Unsuccessfully shifted on: {location_fullname}\n"
                        f"From: {datetime_starts}\n"
                        f"To: {datetime_ends}" + text)


def newsfeeds_checker() -> bool:
    response = requests.get(SITE + "/api/v1/newsfeeds",
                            params={"user_email": user_data["shyftplan_email"],
                                    "authentication_token": user_data["shyftplan_token"],
                                    "company_id": COMPANY_ID,
                                    "page": 1,
                                    "per_page": 1})
    page_json = json.loads(response.text)
    if 'error' in page_json:
        if page_json["error"] == "401 Unauthorized":
            config.read('settings.ini')
            config.set("AUTH_CONFIG", "shyftplan_email", "None")
            config.set("AUTH_CONFIG", "shyftplan_token", "None")
            config.set("PROGRAM_CONFIG", "status", "False")
            with open("settings.ini", "w") as configfile:
                config.write(configfile)
            requests.post(f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_MY_ID}&text="
                          f"⛔ Bot was stopped because your data is outdated, use command /auth to authorize again.")
        return False
    else:
        json_items = page_json["items"][0]
        is_old = db.newsfeeds_is_old_id(mysql.connect(user="root",
                                                      host=database_data["ip"],
                                                      password=database_data["password"],
                                                      database="newsfeeds_db"),
                                        user_data["shyftplan_user_id"], json_items["id"])
        if not is_old:
            if json_items["key"] == "request.swap_request" and shift_offers_status:
                loc_pos_id: int = json_items["metadata"]["locations_position_ids"][0]
                isotime_starts: str = json_items["objekt"]["shift"]["starts_at"]  # tz +02:00
                isotime_ends: str = json_items["objekt"]["shift"]["ends_at"]  # tz +02:00
                datetime_starts = datetime.fromisoformat(isotime_starts).replace(tzinfo=None)
                datetime_ends = datetime.fromisoformat(isotime_ends).replace(tzinfo=None)
                adc_response = api_data_checker(loc_pos_id, (datetime_starts, datetime_ends))
                adc_response_code = adc_response[0]
                adc_response_loc = adc_response[1]
                if adc_response_code:
                    response = requests.get(SITE + "/api/v1/evaluations",
                                            params={"user_email": user_data["shyftplan_email"],
                                                    "authentication_token": user_data["shyftplan_token"],
                                                    "page": 1,
                                                    "per_page": 1,
                                                    "starts_at": (datetime_starts - timedelta(hours=4)).isoformat(),
                                                    "ends_at": isotime_starts,
                                                    "state": "no_evaluation",
                                                    "employment_id": user_data["shyftplan_employee_id"]})
                    page_json = json.loads(response.text)
                    if len(page_json["items"]) > 0:  # Если уже что-то забронированно между часами
                        evaluation_ends_at = page_json["items"][0]["evaluation_ends_at"]
                        if evaluation_ends_at == isotime_starts or \
                                datetime.now() + timedelta(hours=2) < datetime_starts:
                            join_or_accept_shift(json_items["objekt_id"],
                                                 adc_response_loc,
                                                 'replace',
                                                 (datetime_starts, datetime_ends))
                    elif datetime.now() + timedelta(hours=2) < datetime_starts:
                        join_or_accept_shift(json_items["objekt_id"],
                                             adc_response_loc,
                                             'replace',
                                             (datetime_starts, datetime_ends))
            elif json_items["key"] == "request.swap_auto_accepted" and \
                    json_items["user_id"] == user_data["shyftplan_user_id"]:
                notification(loc_pos_id=json_items["objekt"]["locations_position_id"],
                             objekt=json_items["objekt"],
                             shifted="True")
            elif json_items["key"] == "request.shift_application" and \
                    json_items["user_id"] == user_data["shyftplan_user_id"]:
                notification(loc_pos_id=json_items["metadata"]["managed_locations_position_ids"][0],
                             objekt=json_items["objekt"]["shift"],
                             shifted="Unknown")
            elif json_items["key"] == "request.refused":
                notification(loc_pos_id=json_items["objekt"]["locations_position_id"],
                             objekt=json_items["objekt"],
                             shifted="False",
                             text="\nError: Refused")
                requests.post(f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id=1630691291&text="
                              f"❌ Unsuccessfully shifted (Refused): {response.text}")
            elif json_items["key"] == "message" and news_status:
                requests.post(f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_MY_ID}&text="
                              f"💬 Shyftplan Message:\n{json_items['message']}")
            db.newsfeeds_add_old_id(mysql.connect(user="root",
                                                  host=database_data["ip"],
                                                  password=database_data["password"],
                                                  database="newsfeeds_db"),
                                    user_data["shyftplan_user_id"], json_items["id"])
        return True


def open_shifts_checker() -> bool:
    locations = work_data.converter(today=datetime.now().strftime("%d.%m.%Y"))
    prepare_any_url = requests.models.PreparedRequest()
    shifts_url_params = {"user_email": user_data["shyftplan_email"],
                         "authentication_token": user_data["shyftplan_token"],
                         "company_id": COMPANY_ID,
                         "page": 1,
                         "per_page": 150,
                         "only_open": "true",
                         "order_dir": "desc"}
    prepare_any_url.prepare_url(SITE + "/api/v1/shifts", shifts_url_params)
    prepared_url = prepare_any_url.url
    for location in locations:
        if len(location["dates"]) > 0:
            prepared_url += f"&locations_position_ids[]={location['id']}"
    response = requests.get(prepared_url)
    page_json = json.loads(response.text)
    if 'error' in page_json:
        if page_json["error"] == "401 Unauthorized":
            config.read('settings.ini')
            config.set("AUTH_CONFIG", "shyftplan_email", "None")
            config.set("AUTH_CONFIG", "shyftplan_token", "None")
            config.set("PROGRAM_CONFIG", "status", "False")
            with open("settings.ini", "w") as configfile:
                config.write(configfile)
            requests.post(f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_MY_ID}&text="
                          f"⛔ Bot was stopped because your data is outdated, use command /auth to authorize again.")
        return False
    else:
        json_items = page_json["items"]
        for item in json_items:
            json_pos_id = item["locations_position_id"]
            isotime_starts = item["starts_at"]
            isotime_ends = item["ends_at"]
            datetime_starts = datetime.fromisoformat(isotime_starts).replace(tzinfo=None)
            datetime_ends = datetime.fromisoformat(isotime_ends).replace(tzinfo=None)
            adc_response = api_data_checker(json_pos_id, (datetime_starts, datetime_ends))
            adc_response_code = adc_response[0]
            adc_response_loc = adc_response[1]
            if adc_response_code:
                join_or_accept_shift(item["id"], adc_response_loc, "join", (datetime_starts, datetime_ends))
        return True


# MAIN SCRIPT #
while True:
    config = configparser.ConfigParser()
    config.read('settings.ini')
    status: bool = config.getboolean("PROGRAM_CONFIG", "status")
    open_shifts_status: bool = config.getboolean("PROGRAM_CONFIG", "open_shifts_status")
    shift_offers_status: bool = config.getboolean("PROGRAM_CONFIG", "shift_offers_status")
    news_status: bool = config.getboolean("PROGRAM_CONFIG", "news_status")
    sleeptime: float = config.getfloat("PROGRAM_CONFIG", "sleeptime")

    if status and (open_shifts_status or shift_offers_status or news_status):
        time.sleep(sleeptime)
        try:
            if shift_offers_status or news_status:
                newsfeeds_checker_response = newsfeeds_checker()
                if not newsfeeds_checker_response:
                    continue
            if open_shifts_status:
                open_shifts_checker_response = open_shifts_checker()
                if not open_shifts_checker_response:
                    continue
        except requests.exceptions.ChunkedEncodingError:
            print("[ERROR] Chunked Encoding Error")
            time.sleep(30)
            continue
        except requests.exceptions.ConnectionError:
            print("[ERROR] Connection Error.")
            time.sleep(30)
            continue
        except json.decoder.JSONDecodeError:
            print("[ERROR] JSON Decode Error.")
            time.sleep(30)
            continue
