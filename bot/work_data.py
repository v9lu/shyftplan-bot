# Version 1.3.0 release

import copy
import json
from datetime import datetime, timedelta
from mysql.connector.connection_cext import CMySQLConnection
from typing import Optional
from unidecode import unidecode

import db

locations_sample = [{"name": "szarych", "fullname": "Szarych Szeregów 11", "id": 163056, "dates": []},
                    {"name": "hawajska", "fullname": "Hawajska 11", "id": 165605, "dates": []},
                    {"name": "lirowa", "fullname": "Lirowa 26", "id": 165606, "dates": []},
                    {"name": "tarnowiecka", "fullname": "Tarnowiecka 13", "id": 165607, "dates": []},
                    {"name": "kamienna", "fullname": "Kamienna 1", "id": 165608, "dates": []},
                    {"name": "miedzynarodowa", "fullname": "Międzynarodowa 42", "id": 166576, "dates": []},
                    {"name": "sikorskiego", "fullname": "Sikorskiego 3A", "id": 166585, "dates": []},
                    {"name": "solidarnosci", "fullname": "Solidarności 155", "id": 166586, "dates": []},
                    {"name": "herbu", "fullname": "Herbu Janina 5", "id": 166587, "dates": []},
                    {"name": "czluchowska", "fullname": "Człuchowska 35", "id": 168928, "dates": []},
                    {"name": "rydygiera", "fullname": "Rydygiera 13", "id": 169661, "dates": []},
                    {"name": "europlex", "fullname": "Europlex (Puławska 17)", "id": 170617, "dates": []},
                    {"name": "grochowskiego", "fullname": "Grochowskiego 5", "id": 170856, "dates": []},
                    {"name": "dolna", "fullname": "Dolna 41", "id": 171705, "dates": []},
                    {"name": "sielecka", "fullname": "Sielecka 35", "id": 174110, "dates": []},
                    {"name": "lekka", "fullname": "Lekka 3", "id": 174113, "dates": []},
                    {"name": "elektryczna", "fullname": "Elektryczna 2", "id": 174114, "dates": []},
                    {"name": "konstruktorska", "fullname": "Konstruktorska 13A", "id": 174153, "dates": []},
                    {"name": "grenadierow", "fullname": "Grenadierów 11", "id": 177820, "dates": []}]


def take_date(element):
    element = element.split("/")
    element = datetime.strptime(element[1], "%d.%m.%Y")
    return element


def converter(conn: CMySQLConnection, sp_uid: int, today: str) -> list:
    # conn > sp_users_db
    locations = copy.deepcopy(locations_sample)

    # READ SHIFTS
    sp_user_data = db.sp_users_get_user(conn=conn, sp_uid=sp_uid)
    if sp_user_data["shifts"]:
        work_data_extracted = json.loads(sp_user_data["shifts"])
    else:
        work_data_extracted = []
    work_data = []

    # REMOVE OUTDATED DAYS
    for work_day in work_data_extracted:
        if today in work_day:
            work_data_extracted = work_data_extracted[work_data_extracted.index(work_day):]
            break

    # OTHER ACTIONS
    for work_day in work_data_extracted:
        list_from_work_day = work_day.split("/")
        template = '/'.join(list_from_work_day[:2])   # '/'.join(["szarych", "09.09.2020"]) >>> "szarych/09.09.2020"
        if template not in work_data and not work_day.isspace() and len(list_from_work_day) > 2:
            work_data.append(template)
    for work_day in work_data_extracted:
        list_from_work_day = work_day.split("/")
        template = '/'.join(list_from_work_day[:2])  # '/'.join(["szarych", "09.09.2020"]) >>> "szarych/09.09.2020"
        for index in range(len(work_data)):
            if template in work_data[index]:
                work_day = work_day.split()[0]

                # work_data[work_data.index(work_data[index])] >>> work_data[0]
                # '/'.join(work_day.split('/')[2:]) >>> '/'.join(WORK_DAY_HOURS_ONLY) >>> '/'.join(["07:00-11:00", ...])
                # >>> work_data[0] += '/' + "07:00-11:00/11:00-15:00"
                work_data[work_data.index(work_data[index])] += '/' + '/'.join(work_day.split('/')[2:])

    # WRITE RESULT
    work_data.sort(key=take_date)
    db.sp_users_configs_update_user(conn=conn, sp_uid=sp_uid, shifts=json.dumps(work_data))

    # WORK WITH LOCATIONS LIST
    for index in range(len(locations)):
        for work_day in work_data:
            work_day = work_day.split("/")  # "name/date/15-19" > ["name", "date", "15-19"]
            work_day_location_name = work_day[0]
            if work_day_location_name == locations[index]["name"]:
                work_day_calendar_day = work_day[1]
                work_day_hours = work_day[2:]
                for hours_couple in work_day_hours:  # ["name", "date", "15-19"] > ["15-19"]
                    starts_ends_time = hours_couple.split("-")  # 15-19 > [15, 19]
                    starts_time = starts_ends_time[0]
                    ends_time = starts_ends_time[1]

                    dt_starts = datetime.strptime(work_day_calendar_day + starts_time, '%d.%m.%Y%H:%M')
                    dt_ends = datetime.strptime(work_day_calendar_day + ends_time, '%d.%m.%Y%H:%M')
                    if ends_time == "00:00" or ends_time == "00:30":
                        dt_ends += timedelta(days=1)

                    locations[index]["dates"].append((dt_starts, dt_ends))

    return locations


def user_converter(conn: CMySQLConnection, sp_uid: int, work_data_extracted_string: str) -> list:
    locations = copy.deepcopy(locations_sample)
    work_data_extracted = work_data_extracted_string.split()
    for index in range(len(locations)):
        for work_day in work_data_extracted:
            work_day = work_day.split("/")  # "name/date/15-19" > ["name", "date", "15-19"]
            work_day_location_name = work_day[0]
            if work_day_location_name == locations[index]["name"]:
                work_day_calendar_day = work_day[1]
                work_day_hours = work_day[2:]
                for hours_couple in work_day_hours:  # ["name", "date", "15-19"] > ["15-19"]
                    starts_ends_time = hours_couple.split("-")  # 15-19 > [15, 19]
                    starts_time = starts_ends_time[0]
                    ends_time = starts_ends_time[1]

                    dt_starts = datetime.strptime(work_day_calendar_day + starts_time, '%d.%m.%Y%H:%M')
                    dt_ends = datetime.strptime(work_day_calendar_day + ends_time, '%d.%m.%Y%H:%M')
                    if ends_time == "00:00" or ends_time == "00:30":
                        dt_ends += timedelta(days=1)

                    locations[index]["dates"].append((dt_starts, dt_ends))

    return locations


def add_days(conn: CMySQLConnection, sp_uid: int, days: str) -> None:
    # conn > sp_users_db
    days = unidecode(days)
    days = days.lower().split("\n")

    sp_user_data = db.sp_users_get_user(conn=conn, sp_uid=sp_uid)
    work_data_extracted_string = sp_user_data["shifts"]
    if work_data_extracted_string:
        work_data_extracted = json.loads(work_data_extracted_string)
    else:
        work_data_extracted_string = ''
        work_data_extracted = []
    work_data = []

    for day in days:
        list_from_day = day.split("/")
        location_calendar_day = '/'.join(list_from_day[:2])

        if day not in work_data_extracted and location_calendar_day not in work_data_extracted_string:
            work_data_extracted.append(day)
        elif location_calendar_day in work_data_extracted_string:
            for work_day in work_data_extracted:
                work_day_index = work_data_extracted.index(work_day)
                if location_calendar_day in work_day:
                    work_day_hours = work_day.split("/")[2:]
                    day_hours = day.split("/")[2:]
                    for hours_couple in day_hours:
                        if hours_couple not in work_day_hours:
                            work_data_extracted[work_day_index] += f"/{hours_couple}"
                    break

    work_data_extracted.sort(key=take_date)
    for work_day in work_data_extracted:
        work_data.append(work_day.strip())

    db.sp_users_configs_update_user(conn=conn, sp_uid=sp_uid, shifts=json.dumps(work_data))


def remove_days(conn: CMySQLConnection, sp_uid: int, days: str) -> None:
    # conn > sp_users_db
    days = unidecode(days)
    days = days.lower().split("\n")

    sp_user_data = db.sp_users_get_user(conn=conn, sp_uid=sp_uid)
    work_data_extracted_string = sp_user_data["shifts"]
    if work_data_extracted_string:
        work_data_extracted = json.loads(work_data_extracted_string)
    else:
        work_data_extracted_string = ''
        work_data_extracted = []
    work_data = []

    for day in days:
        list_from_day = day.split("/")
        location_calendar_day = '/'.join(list_from_day[:2])
        if day in work_data_extracted:
            work_data_extracted.remove(day)
        elif location_calendar_day in work_data_extracted_string:
            for work_day in work_data_extracted:
                work_day_index = work_data_extracted.index(work_day)
                if location_calendar_day in work_day:
                    work_day_hours = work_day.split("/")[2:]
                    day_hours = day.split("/")[2:]
                    new_work_day = work_day.split("/")[:2]
                    new_hours_couples = ""
                    for hours_couple in work_day_hours:
                        if hours_couple not in day_hours:
                            new_hours_couples += f"/{hours_couple}"
                    new_work_day = '/'.join(new_work_day) + new_hours_couples
                    if len(new_work_day.split("/")) > 2:
                        work_data_extracted[work_day_index] = new_work_day
                    else:
                        work_data_extracted.remove(work_day)
                    break

    work_data_extracted.sort(key=take_date)
    for work_day in work_data_extracted:
        work_data.append(work_day.strip())

    db.sp_users_configs_update_user(conn=conn, sp_uid=sp_uid, shifts=json.dumps(work_data))


def get_bytes_file(conn: CMySQLConnection, sp_uid: int) -> Optional[bytes]:
    # conn > sp_users_db
    sp_user_data = db.sp_users_get_user(conn=conn, sp_uid=sp_uid)
    work_data_extracted_string = sp_user_data["shifts"]
    if work_data_extracted_string:
        work_data_extracted = json.loads(work_data_extracted_string)
        return bytes('\n'.join(work_data_extracted), encoding="utf8")
    else:
        return None
