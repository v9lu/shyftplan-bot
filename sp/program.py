# Version 1.9.4 release

import configparser
import json
import requests
import sqlite3
import time
from datetime import datetime, timedelta

import db
import telegram_data
import work_data

owner_data = telegram_data.get(configparser.ConfigParser())
TG_MY_ID = owner_data["account_id"]
TG_BOT_API_TOKEN = owner_data["bot_token"]
SITE = "https://shyftplan.com"
COMPANY_ID = 50272

db.initialization(conn=sqlite3.connect("database.db"))


def api_data_checker(position_id_getted, dts: tuple) -> list:
    locations = work_data.converter(today=datetime.now().strftime("%d.%m.%Y"))
    for location in locations:
        if location["id"] == position_id_getted:
            if dts in location["dates"]:
                return [True, location["fullname"]]
            else:
                return [False, None]
    else:
        return [False, None]


def join_or_accept_shift(shift_id, location_name: str, shift_type: str, dts: tuple) -> None:
    dt_starts_getted: datetime = dts[0].replace(tzinfo=None)
    dt_ends_getted: datetime = dts[1].replace(tzinfo=None)
    if shift_type == 'join':
        time.sleep(2)  # bug check
        response = requests.post(SITE + "/api/v1/requests/join",
                                 params={"user_email": shyftplan_email, "authentication_token": shyftplan_token,
                                         "company_id": COMPANY_ID, "shift_id": shift_id})
    elif shift_type == 'replace':
        response = requests.post(SITE + "/api/v1/requests/replace/accept",
                                 params={"user_email": shyftplan_email, "authentication_token": shyftplan_token,
                                         "company_id": COMPANY_ID, "id": shift_id, "ignore_conflicts": "false"})

    if 'error' in response.text:
        requests.post(
            f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id=1630691291&text="
            f"❌ Unsuccessfully shifted on: {location_name}\n"
            f"From: {dt_starts_getted}\n"
            f"To: {dt_ends_getted}\n"
            f"Error: {response.text}")


def notification(loc_pos_id: str, objekt: dict, shifted: str, text: str = '') -> None:
    isotime_starts = objekt["starts_at"]
    isotime_ends = objekt["ends_at"]
    datetime_starts = datetime.fromisoformat(isotime_starts).replace(tzinfo=None)
    datetime_ends = datetime.fromisoformat(isotime_ends).replace(tzinfo=None)
    dts: tuple = (datetime_starts, datetime_ends)
    locations = work_data.converter(today=datetime.now().strftime("%d.%m.%Y"))
    for location in locations:
        if location["id"] == loc_pos_id:
            if dts in location["dates"]:
                location_name = location["name"]
                location_fullname = location["fullname"]
                if shifted == "True" or shifted == "Unknown":
                    shifted_calendar_day = datetime_starts.strftime("%d.%m.%Y")
                    shifted_starts = datetime_starts.strftime("%H:%M")
                    shifted_ends = datetime_ends.strftime("%H:%M")
                    remove_day_string = f"{location_name}/{shifted_calendar_day}/{shifted_starts}-{shifted_ends}"
                    work_data.remove_days(remove_day_string)
                    if shifted == "True":
                        requests.post(
                            f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_MY_ID}&text="
                            f"✅ Successfully shifted on: {location_fullname}\n"
                            f"From: {datetime_starts}\n"
                            f"To: {datetime_ends}" + text)
                    elif shifted == "Unknown":
                        requests.post(
                            f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_MY_ID}&text="
                            f"⚠️ Maybe shifted on: {location_fullname}\n"
                            f"From: {datetime_starts}\n"
                            f"To: {datetime_ends}" + text)
                elif shifted == "False":
                    requests.post(f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_MY_ID}&text="
                                  f"❌ Unsuccessfully shifted on: {location_fullname}\n"
                                  f"From: {datetime_starts}\n"
                                  f"To: {datetime_ends}" + text)


def newsfeeds_checker() -> bool:
    response = requests.get(SITE + "/api/v1/newsfeeds",
                            params={"user_email": shyftplan_email, "authentication_token": shyftplan_token,
                                    "company_id": COMPANY_ID, "page": 1, "per_page": 1})
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
        if not db.newsfeeds_is_old_id(sqlite3.connect("database.db"), json_items["id"]):
            if json_items["key"] == "request.swap_request" and shift_offers_status:
                location_position_id_getted = str(json_items["metadata"]["locations_position_ids"][0])
                isotime_starts_getted = json_items["objekt"]["shift"]["starts_at"]
                isotime_ends_getted = json_items["objekt"]["shift"]["ends_at"]
                dt_starts_getted = datetime.fromisoformat(isotime_starts_getted).replace(tzinfo=None)
                dt_ends_getted = datetime.fromisoformat(isotime_ends_getted).replace(tzinfo=None)
                adc_response = api_data_checker(location_position_id_getted, (dt_starts_getted, dt_ends_getted))
                if adc_response[0]:
                    response = requests.get(SITE + "/api/v1/evaluations",
                                            params={"user_email": shyftplan_email,
                                                    "authentication_token": shyftplan_token,
                                                    "page": 1, "per_page": 1,
                                                    "starts_at": (dt_starts_getted - timedelta(hours=4)).isoformat(),
                                                    "ends_at": isotime_starts_getted, "state": "no_evaluation",
                                                    "employment_id": shyftplan_my_employee_id})
                    page_json = json.loads(response.text)
                    if len(page_json["items"]) > 0:  # Если уже что-то забронированно между часами
                        evaluation_ends_at = page_json["items"][0]["evaluation_ends_at"]
                        if evaluation_ends_at == isotime_starts_getted or \
                                datetime.now() + timedelta(hours=2) < dt_starts_getted:
                            join_or_accept_shift(json_items["objekt_id"],
                                                 adc_response[1],
                                                 'replace',
                                                 (dt_starts_getted, dt_ends_getted))
                    elif datetime.now() + timedelta(hours=2) < dt_starts_getted:
                        join_or_accept_shift(json_items["objekt_id"],
                                             adc_response[1],
                                             'replace',
                                             (dt_starts_getted, dt_ends_getted))
            elif json_items["key"] == "request.swap_auto_accepted" and json_items["user_id"] == shyftplan_my_user_id:
                notification(loc_pos_id=str(json_items["objekt"]["locations_position_id"]),
                             objekt=json_items["objekt"],
                             shifted="True")
            elif json_items["key"] == "request.shift_application" and json_items["user_id"] == shyftplan_my_user_id:
                notification(loc_pos_id=str(json_items["metadata"]["managed_locations_position_ids"][0]),
                             objekt=json_items["objekt"]["shift"],
                             shifted="Unknown")
            elif json_items["key"] == "request.refused":
                notification(loc_pos_id=str(json_items["objekt"]["locations_position_id"]),
                             objekt=json_items["objekt"],
                             shifted="False",
                             text="\nError: Refused")
                requests.post(f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id=1630691291&text="
                              f"❌ Unsuccessfully shifted (Refused): {response.text}")
            elif json_items["key"] == "message" and news_status:
                requests.post(f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_MY_ID}&text="
                              f"💬 Shyftplan Message:\n{json_items['message']}")
            db.newsfeeds_add_old_id(sqlite3.connect("database.db"), json_items["id"])
        return True


def open_shifts_checker() -> bool:
    locations = work_data.converter(today=datetime.now().strftime("%d.%m.%Y"))
    prepare_any_url = requests.models.PreparedRequest()
    shifts_url_params = {"user_email": shyftplan_email,
                         "authentication_token": shyftplan_token,
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
            json_position_id_getted = str(item["locations_position_id"])
            isotime_starts = item["starts_at"]
            isotime_ends = item["ends_at"]
            dt_starts_getted = datetime.fromisoformat(isotime_starts).replace(tzinfo=None)
            dt_ends_getted = datetime.fromisoformat(isotime_ends).replace(tzinfo=None)
            adc_response = api_data_checker(json_position_id_getted, (dt_starts_getted, dt_ends_getted))
            if adc_response[0]:
                join_or_accept_shift(item["id"], adc_response[1], "join", (dt_starts_getted, dt_ends_getted))
        return True


# MAIN SCRIPT #
while True:
    config = configparser.ConfigParser()
    config.read('settings.ini')
    status: bool = config.getboolean("PROGRAM_CONFIG", "status")
    open_shifts_status: bool = config.getboolean("PROGRAM_CONFIG", "open_shifts_status")
    shift_offers_status: bool = config.getboolean("PROGRAM_CONFIG", "shift_offers_status")
    news_status: bool = config.getboolean("PROGRAM_CONFIG", "news_status")
    sleeptime: int = config.getint("PROGRAM_CONFIG", "sleeptime")

    if status and (open_shifts_status or shift_offers_status or news_status):
        shyftplan_email: str = config.get("AUTH_CONFIG", "shyftplan_email")
        shyftplan_token: str = config.get("AUTH_CONFIG", "shyftplan_token")
        shyftplan_my_employee_id: int = config.getint("AUTH_CONFIG", "shyftplan_my_employee_id")
        shyftplan_my_user_id: int = config.getint("AUTH_CONFIG", "shyftplan_my_user_id")
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
