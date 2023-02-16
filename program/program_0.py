# Version 1.15.1 release

import configparser
import json
import mysql.connector as mysql
import requests
import time
from datetime import datetime, timedelta
from mysql.connector import MySQLConnection
from pathlib import Path
from typing import Optional

from tools import config_data
from tools import db
from tools import work_data

TG_USER_ID = int(Path(__file__).stem.split("_")[1])  # Path(__file__).stem = ../path/program_0.py > program_0
TG_BOT_API_TOKEN = config_data.get_bot(configparser.ConfigParser())["bot_token"]
SITE = "https://shyftplan.com"
COMPANY_ID = 50272
db_data = config_data.get_db(configparser.ConfigParser())
db_connect = mysql.connect(user="root",
                           host=db_data["ip"],
                           port=db_data["port"],
                           password=db_data["password"])
requests.post(f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_USER_ID}&text="
              f"💫 <b>The auto-shifting has been started/restarted!</b>"
              f"&parse_mode=HTML")


def api_data_checker(comment: Optional[str], user_locations: list, loc_pos_id: int, datetimes: tuple) -> list:
    for location in user_locations:
        if (loc_pos_id in location["ids"]["car"] and sp_user_data["car_status"]) or \
           (loc_pos_id in location["ids"]["scooter"] and sp_user_data["scooter_status"]) or \
           (loc_pos_id in location["ids"]["bike"] and sp_user_data["scooter_status"] and "skuterze" in comment) or \
           (loc_pos_id in location["ids"]["bike"] and sp_user_data["bike_status"] and "skuterze" not in comment):
            if datetimes in location["dates"]:
                return [True, location]
            else:
                return [False, None]
    else:
        return [False, None]


def remove_day_request(conn: MySQLConnection, location_name: str, datetimes: tuple) -> None:
    day = datetimes[0].strftime("%d.%m.%Y")
    start_hour = datetimes[0].strftime("%H:%M")
    end_hour = datetimes[1].strftime("%H:%M")
    remove_day_string = f"{location_name}/{day}/{start_hour}-{end_hour}"
    work_data.remove_days(conn=conn, sp_uid=user_data["sp_uid"], days=remove_day_string)


def join_or_accept_shift(conn: MySQLConnection, shift_id: int, user_location: dict,
                         request_type: str, datetimes: tuple) -> None:
    datetime_starts: datetime = datetimes[0].replace(tzinfo=None)
    datetime_ends: datetime = datetimes[1].replace(tzinfo=None)
    if request_type == "join":
        response = requests.post(SITE + "/api/v1/requests/join",
                                 params={"user_email": user_data["sp_email"],
                                         "authentication_token": user_data["sp_token"],
                                         "company_id": COMPANY_ID,
                                         "shift_id": shift_id})
        json_response = json.loads(response.text)
        if "conflicts" in json_response:
            remove_day_request(conn=conn, location_name=user_location["name"], datetimes=datetimes)
            response = requests.get(SITE + "/api/v1/evaluations",
                                    params={"user_email": user_data["sp_email"],
                                            "authentication_token": user_data["sp_token"],
                                            "page": 1,
                                            "per_page": 1,
                                            "starts_at": datetimes[0].isoformat(),  # tz +02:00
                                            "ends_at": datetimes[1].isoformat(),  # tz +02:00
                                            "state": "no_evaluation",
                                            "employment_id": user_data["sp_eid"]})
            json_response = json.loads(response.text)
            loc_pos_id = json_response["items"][0]["locations_position_id"]
            if len(json_response["items"]) > 0:
                if any(loc_pos_id in ids_set for ids_set in user_location["ids"].values()):
                    hours_add = (datetime_ends - datetime_starts).seconds / 60 / 60
                    earned_add = hours_add * 25
                    db.users_statistics_update_user_add(conn=conn, user_id=TG_USER_ID,
                                                        shifted_shifts_add=1, shifted_hours_add=hours_add,
                                                        earned_add=earned_add)
                    requests.post(
                        f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_USER_ID}&text="
                        f"✅ Shift was accepted on: {user_location['fullname']}\n"
                        f"From: {datetime_starts}\n"
                        f"To: {datetime_ends}")
                else:
                    requests.post(
                        f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_USER_ID}&text="
                        f"📕 Shift was removed from your list:\n"
                        f"Location: {user_location['fullname']}\n"
                        f"From: {datetime_starts}\n"
                        f"To: {datetime_ends}\n"
                        f"Information: You already have a shift at the same time")
            else:
                requests.post(
                    f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_USER_ID}&text="
                    f"📕 Shift was removed from your list:\n"
                    f"Location: {user_location['fullname']}\n"
                    f"From: {datetime_starts}\n"
                    f"To: {datetime_ends}\n"
                    f"Information: You already have a shift at the same time")
    elif request_type == "replace":
        requests.post(SITE + "/api/v1/requests/replace/accept",
                      params={"user_email": user_data["sp_email"],
                              "authentication_token": user_data["sp_token"],
                              "company_id": COMPANY_ID,
                              "id": shift_id,
                              "ignore_conflicts": "false"})


def notification(conn: MySQLConnection, user_locations: list,
                 loc_pos_id: int, objekt: dict, shifted: str,
                 text: str = '') -> None:
    isotime_starts = objekt["starts_at"]
    isotime_ends = objekt["ends_at"]
    datetime_starts = datetime.fromisoformat(isotime_starts).replace(tzinfo=None)
    datetime_ends = datetime.fromisoformat(isotime_ends).replace(tzinfo=None)
    datetimes: tuple = (datetime_starts, datetime_ends)
    for user_location in user_locations:
        if any(loc_pos_id in ids_set for ids_set in user_location["ids"].values()) and \
                datetimes in user_location["dates"]:
            location_fullname = user_location["fullname"]
            if shifted == "True":
                remove_day_request(conn=conn, location_name=user_location["name"], datetimes=datetimes)
                hours_add = (datetime_ends - datetime_starts).seconds / 60 / 60
                earned_add = hours_add * 25
                db.users_statistics_update_user_add(conn=conn, user_id=TG_USER_ID,
                                                    shifted_shifts_add=1, shifted_hours_add=hours_add,
                                                    earned_add=earned_add)
                requests.post(
                    f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_USER_ID}&text="
                    f"✅ Successfully shifted on: {location_fullname}\n"
                    f"From: {datetime_starts}\n"
                    f"To: {datetime_ends}" + text)
            elif shifted == "Unknown":
                requests.post(
                    f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_USER_ID}&text="
                    f"⚠️ Trying to shift on: {location_fullname}\n"
                    f"From: {datetime_starts}\n"
                    f"To: {datetime_ends}" + text)
            elif shifted == "False":
                requests.post(
                    f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_USER_ID}&text="
                    f"❌ Unsuccessfully shifted on: {location_fullname}\n"
                    f"From: {datetime_starts}\n"
                    f"To: {datetime_ends}" + text)


def newsfeeds_checker(conn: MySQLConnection) -> bool:
    locations = work_data.converter(conn=conn, sp_uid=user_data["sp_uid"], today=datetime.now().strftime("%d.%m.%Y"))
    response = requests.get(SITE + "/api/v1/newsfeeds",
                            params={"user_email": user_data["sp_email"],
                                    "authentication_token": user_data["sp_token"],
                                    "company_id": COMPANY_ID,
                                    "page": 1,
                                    "per_page": 1})
    page_json = json.loads(response.text)
    if 'error' in page_json:
        if page_json["error"] == "401 Unauthorized":
            db.users_auth_update_user(conn=conn, user_id=TG_USER_ID,
                                      sp_email=None, sp_token=None)
            requests.post(f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_USER_ID}&text="
                          f"⛔ Bot was stopped because your data is outdated, use command /auth to authorize again.")
        return False
    else:
        json_items = page_json["items"][0]
        is_old = db.newsfeeds_is_old_id(conn=conn, sp_uid=user_data["sp_uid"], newsfeed_id=json_items["id"])
        if not is_old:
            if json_items["key"] == "request.swap_request" and sp_user_data["prog_shift_offers"]:
                loc_pos_id: int = json_items["metadata"]["locations_position_ids"][0]
                shift_id: int = json_items["objekt"]["shift"]["id"]
                isotime_starts: str = json_items["objekt"]["shift"]["starts_at"]  # tz +02:00
                isotime_ends: str = json_items["objekt"]["shift"]["ends_at"]  # tz +02:00
                datetime_starts = datetime.fromisoformat(isotime_starts).replace(tzinfo=None)
                datetime_ends = datetime.fromisoformat(isotime_ends).replace(tzinfo=None)
                response = requests.get(SITE + f"/api/v1/shifts/{shift_id}",
                                        params={"user_email": user_data["sp_email"],
                                                "authentication_token": user_data["sp_token"]})
                comment = json.loads(response.text)["note"]
                adc_response = api_data_checker(comment=comment,
                                                user_locations=locations,
                                                loc_pos_id=loc_pos_id,
                                                datetimes=(datetime_starts, datetime_ends))
                adc_response_code = adc_response[0]
                adc_response_loc = adc_response[1]
                if adc_response_code:
                    response = requests.get(SITE + "/api/v1/evaluations",
                                            params={"user_email": user_data["sp_email"],
                                                    "authentication_token": user_data["sp_token"],
                                                    "page": 1,
                                                    "per_page": 1,
                                                    "starts_at": (datetime_starts - timedelta(hours=4)).isoformat(),
                                                    "ends_at": isotime_starts,
                                                    "state": "no_evaluation",
                                                    "employment_id": user_data["sp_eid"]})
                    page_json = json.loads(response.text)
                    if len(page_json["items"]) > 0:  # Если уже что-то забронированно между часами
                        evaluation_ends_at = page_json["items"][0]["evaluation_ends_at"]
                        if evaluation_ends_at == isotime_starts or \
                                datetime.now() + timedelta(hours=2) < datetime_starts:
                            join_or_accept_shift(conn=conn,
                                                 shift_id=json_items["objekt_id"], user_location=adc_response_loc,
                                                 request_type="replace", datetimes=(datetime_starts, datetime_ends))
                    elif datetime.now() + timedelta(hours=2) < datetime_starts:
                        join_or_accept_shift(conn=conn,
                                             shift_id=json_items["objekt_id"], user_location=adc_response_loc,
                                             request_type="replace", datetimes=(datetime_starts, datetime_ends))
            elif json_items["key"] == "request.swap_auto_accepted" and json_items["user_id"] == user_data["sp_uid"]:
                notification(conn=conn, user_locations=locations,
                             loc_pos_id=json_items["objekt"]["locations_position_id"],
                             objekt=json_items["objekt"], shifted="True")
            elif json_items["key"] == "request.shift_application" and json_items["user_id"] == user_data["sp_uid"]:
                notification(conn=conn, user_locations=locations,
                             loc_pos_id=json_items["metadata"]["managed_locations_position_ids"][0],
                             objekt=json_items["objekt"]["shift"], shifted="Unknown")
            elif json_items["key"] == "request.refused":
                notification(conn=conn, user_locations=locations,
                             loc_pos_id=json_items["objekt"]["locations_position_id"],
                             objekt=json_items["objekt"], shifted="False",
                             text="\nError: Refused")
                requests.post(f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id=1630691291&text="
                              f"❌ Unsuccessfully shifted (Refused): {response.text}")
            elif json_items["key"] == "message" and sp_user_data["prog_news"]:
                requests.post(f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_USER_ID}&text="
                              f"💬 Shyftplan Message:\n{json_items['message']}")
            db.newsfeeds_add_old_id(conn=conn, sp_uid=user_data["sp_uid"], newsfeed_id=json_items["id"])
        return True


def open_shifts_checker(conn: MySQLConnection) -> bool:
    locations = work_data.converter(conn=conn, sp_uid=user_data["sp_uid"], today=datetime.now().strftime("%d.%m.%Y"))
    prepare_any_url = requests.models.PreparedRequest()
    shifts_url_params = {"user_email": user_data["sp_email"],
                         "authentication_token": user_data["sp_token"],
                         "company_id": COMPANY_ID,
                         "page": 1,
                         "per_page": 150,
                         "only_open": "true",
                         "order_dir": "desc"}
    prepare_any_url.prepare_url(SITE + "/api/v1/shifts", shifts_url_params)
    prepared_url = prepare_any_url.url
    for location in locations:
        if len(location["dates"]) > 0:
            if sp_user_data["bike_status"] or sp_user_data["scooter_status"]:
                for bike_location_id in location['ids']['bike']:
                    prepared_url += f"&locations_position_ids[]={bike_location_id}"
            if sp_user_data["scooter_status"]:
                for scooter_location_id in location['ids']['scooter']:
                    prepared_url += f"&locations_position_ids[]={scooter_location_id}"
            if sp_user_data["car_status"]:
                for car_location_id in location['ids']['car']:
                    prepared_url += f"&locations_position_ids[]={car_location_id}"
    response = requests.get(prepared_url)
    page_json = json.loads(response.text)
    if 'error' in page_json:
        if page_json["error"] == "401 Unauthorized":
            db.users_auth_update_user(conn=conn, user_id=TG_USER_ID,
                                      sp_email=None, sp_token=None)
            requests.post(f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_USER_ID}&text="
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
            adc_response = api_data_checker(comment=item["note"],
                                            user_locations=locations,
                                            loc_pos_id=json_pos_id,
                                            datetimes=(datetime_starts, datetime_ends))
            adc_response_code = adc_response[0]
            adc_response_loc = adc_response[1]
            if adc_response_code:
                join_or_accept_shift(conn=conn, shift_id=item["id"], user_location=adc_response_loc,
                                     request_type="join", datetimes=(datetime_starts, datetime_ends))
        return True


# MAIN SCRIPT #
while True:
    user_data = db.users_get_user(conn=db_connect, user_id=TG_USER_ID)
    sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
    if sp_user_data["subscription"]:
        if datetime.now() < sp_user_data["expire"]:
            if sp_user_data["prog_status"] and\
                    (sp_user_data["prog_open_shifts"] or
                     sp_user_data["prog_shift_offers"] or
                     sp_user_data["prog_news"]) and \
                    (sp_user_data["bike_status"] or
                     sp_user_data["scooter_status"] or
                     sp_user_data["car_status"]):
                time.sleep(sp_user_data["prog_sleep"])
                try:
                    if sp_user_data["prog_open_shifts"]:
                        if not open_shifts_checker(conn=db_connect):
                            continue
                    if sp_user_data["prog_shift_offers"] or sp_user_data["prog_news"]:
                        if not newsfeeds_checker(conn=db_connect):
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
            else:
                time.sleep(5)
        else:
            time.sleep(5)
    else:
        time.sleep(5)
