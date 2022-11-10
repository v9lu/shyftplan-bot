# Version 1.12.0 release

import configparser
import json
import mysql.connector as mysql
import requests
import time
from datetime import datetime, timedelta
from mysql.connector.connection_cext import CMySQLConnection

import config_data
import db
import work_data

TG_USER_ID = 0
TG_BOT_API_TOKEN = config_data.get_bot(configparser.ConfigParser())["bot_token"]
SITE = "https://shyftplan.com"
COMPANY_ID = 50272


def api_data_checker(user_locations: list, loc_pos_id: int, datetimes: tuple) -> list:
    for location in user_locations:
        if location["id"] == loc_pos_id:
            if datetimes in location["dates"]:
                return [True, location]
            else:
                return [False, None]
    else:
        return [False, None]


def remove_day_request(conn: CMySQLConnection, location_name: str, datetimes: tuple):
    day = datetimes[0].strftime("%d.%m.%Y")
    start_hour = datetimes[0].strftime("%H:%M")
    end_hour = datetimes[1].strftime("%H:%M")
    remove_day_string = f"{location_name}/{day}/{start_hour}-{end_hour}"
    work_data.remove_days(conn=conn, user_id=TG_USER_ID, days=remove_day_string)


def join_or_accept_shift(conn: CMySQLConnection, shift_id: int, shift_location: dict,
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
            remove_day_request(conn=conn, location_name=shift_location["name"], datetimes=datetimes)
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
            if len(json_response["items"]) > 0:
                if json_response["items"][0]["locations_position_id"] == shift_location["id"]:
                    requests.post(
                        f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_USER_ID}&text="
                        f"✅ Shift was accepted on: {shift_location['fullname']}\n"
                        f"From: {datetime_starts}\n"
                        f"To: {datetime_ends}")
                else:
                    requests.post(
                        f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_USER_ID}&text="
                        f"📕 Shift was removed from your list:\n"
                        f"Location: {shift_location['fullname']}\n"
                        f"From: {datetime_starts}\n"
                        f"To: {datetime_ends}\n"
                        f"Information: You already have a shift at the same time")
            else:
                requests.post(
                    f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_USER_ID}&text="
                    f"📕 Shift was removed from your list:\n"
                    f"Location: {shift_location['fullname']}\n"
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


def notification(conn: CMySQLConnection, user_locations: list,
                 loc_pos_id: int, objekt: dict, shifted: str,
                 text: str = '') -> None:
    isotime_starts = objekt["starts_at"]
    isotime_ends = objekt["ends_at"]
    datetime_starts = datetime.fromisoformat(isotime_starts).replace(tzinfo=None)
    datetime_ends = datetime.fromisoformat(isotime_ends).replace(tzinfo=None)
    datetimes: tuple = (datetime_starts, datetime_ends)
    for location in user_locations:
        if location["id"] == loc_pos_id and datetimes in location["dates"]:
            location_fullname = location["fullname"]
            if shifted == "True":
                remove_day_request(conn=conn, location_name=location["name"], datetimes=datetimes)
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


def newsfeeds_checker(conn: CMySQLConnection) -> bool:
    locations = work_data.converter(conn=conn, user_id=TG_USER_ID, today=datetime.now().strftime("%d.%m.%Y"))
    response = requests.get(SITE + "/api/v1/newsfeeds",
                            params={"user_email": user_data["sp_email"],
                                    "authentication_token": user_data["sp_token"],
                                    "company_id": COMPANY_ID,
                                    "page": 1,
                                    "per_page": 1})
    page_json = json.loads(response.text)
    if 'error' in page_json:
        if page_json["error"] == "401 Unauthorized":
            db.users_configs_update_user(conn=conn, user_id=TG_USER_ID,
                                         sp_email=None, sp_token=None)
            requests.post(f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_USER_ID}&text="
                          f"⛔ Bot was stopped because your data is outdated, use command /auth to authorize again.")
        return False
    else:
        json_items = page_json["items"][0]
        conn.connect(database="newsfeeds_db")
        is_old = db.newsfeeds_is_old_id(conn=conn, sp_uid=user_data["sp_uid"], newsfeed_id=json_items["id"])
        if not is_old:
            conn.connect(database="users_db")
            if json_items["key"] == "request.swap_request" and user_data["prog_shift_offers"]:
                loc_pos_id: int = json_items["metadata"]["locations_position_ids"][0]
                isotime_starts: str = json_items["objekt"]["shift"]["starts_at"]  # tz +02:00
                isotime_ends: str = json_items["objekt"]["shift"]["ends_at"]  # tz +02:00
                datetime_starts = datetime.fromisoformat(isotime_starts).replace(tzinfo=None)
                datetime_ends = datetime.fromisoformat(isotime_ends).replace(tzinfo=None)
                adc_response = api_data_checker(user_locations=locations,
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
                                                 shift_id=json_items["objekt_id"], shift_location=adc_response_loc,
                                                 request_type="replace", datetimes=(datetime_starts, datetime_ends))
                    elif datetime.now() + timedelta(hours=2) < datetime_starts:
                        join_or_accept_shift(conn=conn,
                                             shift_id=json_items["objekt_id"], shift_location=adc_response_loc,
                                             request_type="replace", datetimes=(datetime_starts, datetime_ends))
            elif json_items["key"] == "request.swap_auto_accepted" and \
                    json_items["user_id"] == user_data["shyftplan_user_id"]:
                notification(conn=conn, user_locations=locations,
                             loc_pos_id=json_items["objekt"]["locations_position_id"],
                             objekt=json_items["objekt"], shifted="True")
            elif json_items["key"] == "request.shift_application" and \
                    json_items["user_id"] == user_data["shyftplan_user_id"]:
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
            elif json_items["key"] == "message" and user_data["prog_news"]:
                requests.post(f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage?chat_id={TG_USER_ID}&text="
                              f"💬 Shyftplan Message:\n{json_items['message']}")
            conn.connect(database="newsfeeds_db")
            db.newsfeeds_add_old_id(conn=conn, sp_uid=user_data["sp_uid"], newsfeed_id=json_items["id"])
        return True


def open_shifts_checker(conn: CMySQLConnection) -> bool:
    locations = work_data.converter(conn=conn, user_id=TG_USER_ID, today=datetime.now().strftime("%d.%m.%Y"))
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
            prepared_url += f"&locations_position_ids[]={location['id']}"
    response = requests.get(prepared_url)
    page_json = json.loads(response.text)
    if 'error' in page_json:
        if page_json["error"] == "401 Unauthorized":
            db.users_configs_update_user(conn=conn, user_id=TG_USER_ID,
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
            adc_response = api_data_checker(user_locations=locations,
                                            loc_pos_id=json_pos_id,
                                            datetimes=(datetime_starts, datetime_ends))
            adc_response_code = adc_response[0]
            adc_response_loc = adc_response[1]
            if adc_response_code:
                join_or_accept_shift(conn=conn, shift_id=item["id"], shift_location=adc_response_loc,
                                     request_type="join", datetimes=(datetime_starts, datetime_ends))
        return True


# MAIN SCRIPT #
while True:
    db_data = config_data.get_db(configparser.ConfigParser())
    users_db_connect = mysql.connect(user="root",
                                     host=db_data["ip"],
                                     port=db_data["port"],
                                     password=db_data["password"],
                                     database="users_db")
    user_data = db.users_get_user(conn=users_db_connect, user_id=TG_USER_ID)
    if user_data["prog_status"] and (user_data["prog_open_shifts"] or user_data["prog_shift_offers"] or
                                     user_data["prog_news"]):
        time.sleep(user_data["prog_sleep"])
        try:
            if user_data["prog_open_shifts"]:
                if not open_shifts_checker(conn=users_db_connect):
                    continue
            if user_data["prog_shift_offers"] or user_data["prog_news"]:
                if not newsfeeds_checker(conn=users_db_connect):
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
        finally:
            users_db_connect.close()
    else:
        users_db_connect.close()
