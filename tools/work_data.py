# Version 1.5.1 release

import copy
import json
import time
from datetime import datetime, timedelta
from mysql.connector import MySQLConnection
from typing import Optional
from unidecode import unidecode

from tools import db

locations_sample = [{"name": "szarych",
                     "fullname": "Szarych Szeregów 11",
                     "ids": {"bike": {163056, 170251}, "scooter": {178048}, "car": {168652}},
                     "dates": []},
                    {"name": "hawajska",
                     "fullname": "Hawajska 11",
                     "ids": {"bike": {165605, 170252}, "scooter": {178049}, "car": {168653}},
                     "dates": []},
                    {"name": "lirowa",
                     "fullname": "Lirowa 26",
                     "ids": {"bike": {165606, 170254}, "scooter": {178051}, "car": {168655}},
                     "dates": []},
                    {"name": "tarnowiecka",
                     "fullname": "Tarnowiecka 13",
                     "ids": {"bike": {165607, 170255}, "scooter": {178052}, "car": {168656}},
                     "dates": []},
                    {"name": "kamienna",
                     "fullname": "Kamienna 1",
                     "ids": {"bike": {165608, 170253}, "scooter": {178050}, "car": {168654}},
                     "dates": []},
                    {"name": "miedzynarodowa",
                     "fullname": "Międzynarodowa 42",
                     "ids": {"bike": {166576, 170256}, "scooter": {178053}, "car": {168657}},
                     "dates": []},
                    {"name": "sikorskiego",
                     "fullname": "Sikorskiego 3A",
                     "ids": {"bike": {166585, 170257}, "scooter": {178054}, "car": {168658}},
                     "dates": []},
                    {"name": "solidarnosci",
                     "fullname": "Solidarności 155",
                     "ids": {"bike": {166586, 170258}, "scooter": {178057}, "car": {168659}},
                     "dates": []},
                    {"name": "herbu",
                     "fullname": "Herbu Janina 5",
                     "ids": {"bike": {166587, 170259}, "scooter": {178058}, "car": {168660}},
                     "dates": []},
                    {"name": "czluchowska",
                     "fullname": "Człuchowska 35",
                     "ids": {"bike": {168928, 170260}, "scooter": {178059}, "car": {168930}},
                     "dates": []},
                    {"name": "rydygiera",
                     "fullname": "Rydygiera 13",
                     "ids": {"bike": {169661, 170261}, "scooter": {178060}, "car": {169695}},
                     "dates": []},
                    {"name": "europlex",
                     "fullname": "Europlex (Puławska 17)",
                     "ids": {"bike": {170617, 170618}, "scooter": {178061}, "car": {170619}},
                     "dates": []},
                    {"name": "grochowskiego",
                     "fullname": "Grochowskiego 5 [Piaseczno]",
                     "ids": {"bike": {170856, 170860}, "scooter": {178056}, "car": {170861}},
                     "dates": []},
                    {"name": "dolna",
                     "fullname": "Dolna 41",
                     "ids": {"bike": {171705, 171707}, "scooter": {178063}, "car": {171706}},
                     "dates": []},
                    {"name": "sielecka",
                     "fullname": "Sielecka 35",
                     "ids": {"bike": {174110, 174116}, "scooter": {178062}, "car": {174124}},
                     "dates": []},
                    {"name": "lekka",
                     "fullname": "Lekka 3",
                     "ids": {"bike": {174113, 174117}, "scooter": {178064}, "car": {174125}},
                     "dates": []},
                    {"name": "elektryczna",
                     "fullname": "Elektryczna 2",
                     "ids": {"bike": {174114, 174118}, "scooter": {178065}, "car": {174126}},
                     "dates": []
                     },
                    {"name": "konstruktorska",
                     "fullname": "Konstruktorska 13A",
                     "ids": {"bike": {174153, 174154}, "scooter": {178055}, "car": {174156}},
                     "dates": []
                     },
                    {"name": "grenadierow",
                     "fullname": "Grenadierów 11",
                     "ids": {"bike": {177820, 177821}, "scooter": {178066}, "car": {177822}},
                     "dates": []
                     }
                    ]


def take_date(element):
    element = element.split("/")
    element = datetime.strptime(element[1], "%d.%m.%Y")
    return element


def converter(conn: MySQLConnection, sp_uid: int, today: str) -> list:
    # conn > sp_users_db
    locations = copy.deepcopy(locations_sample)

    # READ SHIFTS
    sp_user_data = db.sp_users_get_user(conn=conn, sp_uid=sp_uid)
    work_data_extracted = json.loads(sp_user_data["shifts"]) if sp_user_data["shifts"] else []
    work_data = []

    # REMOVE OUTDATED DAYS
    for work_day in work_data_extracted:
        if today in work_day:
            work_data_extracted = work_data_extracted[work_data_extracted.index(work_day):]
            break

    # OTHER ACTIONS
    for work_day in work_data_extracted:
        list_from_work_day = work_day.split("/")
        template = '/'.join(list_from_work_day[:2])  # '/'.join(["szarych", "09.09.2020"]) >>> "szarych/09.09.2020"
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
            work_day = work_day.split("/")  # "name/date/15-19" > ["name", "date", "15:00-19:00"]
            work_day_location_name = work_day[0]
            if work_day_location_name == locations[index]["name"]:
                work_day_calendar_day = work_day[1]
                work_day_hours = work_day[2:]
                for hours_couple in work_day_hours:  # ["name", "date", "15:00-19:00"] > ["15:00-19:00"]
                    hours_couple = hours_couple.replace(".", ":")  # 15:00-19.00 > 15:00-19:00
                    starts_ends_time = hours_couple.split("-")  # 15:00-19:00 > ["15:00", "19:00"]
                    starts_time = starts_ends_time[0]
                    ends_time = starts_ends_time[1]

                    dt_starts = datetime.strptime(work_day_calendar_day + starts_time, '%d.%m.%Y%H:%M')
                    dt_ends = datetime.strptime(work_day_calendar_day + ends_time, '%d.%m.%Y%H:%M')
                    if ends_time == "00:00" or ends_time == "00:30":
                        dt_ends += timedelta(days=1)

                    locations[index]["dates"].append((dt_starts, dt_ends))

    return locations


def user_converter(conn: MySQLConnection, sp_uid: int, work_data_extracted_string: str) -> list:
    locations = copy.deepcopy(locations_sample)
    work_data_extracted = work_data_extracted_string.split()
    for index in range(len(locations)):
        for work_day in work_data_extracted:
            work_day = work_day.split("/")  # "name/date/15-19" > ["name", "date", "15:00-19:00"]
            work_day_location_name = work_day[0]
            if work_day_location_name == locations[index]["name"]:
                work_day_calendar_day = work_day[1]
                work_day_hours = work_day[2:]
                for hours_couple in work_day_hours:  # ["name", "date", "15-19"] > ["15:00-19:00"]
                    hours_couple = hours_couple.replace(".", ":")  # 15:00-19.00 > 15:00-19:00
                    starts_ends_time = hours_couple.split("-")  # 15:00-19:00 > ["15:00", "19:00"]
                    starts_time = starts_ends_time[0]
                    ends_time = starts_ends_time[1]

                    dt_starts = datetime.strptime(work_day_calendar_day + starts_time, '%d.%m.%Y%H:%M')
                    dt_ends = datetime.strptime(work_day_calendar_day + ends_time, '%d.%m.%Y%H:%M')
                    if ends_time == "00:00" or ends_time == "00:30":
                        dt_ends += timedelta(days=1)

                    locations[index]["dates"].append((dt_starts, dt_ends))

    return locations


def add_days(conn: MySQLConnection, sp_uid: int, days: str) -> None:
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

    if sp_user_data["prog_status"]:
        # pause program
        db.sp_users_configs_update_user(conn=conn, sp_uid=sp_uid, prog_status=False)
        # update shifts
        db.sp_users_configs_update_user(conn=conn, sp_uid=sp_uid, shifts=json.dumps(work_data))
        # unpause program
        db.sp_users_configs_update_user(conn=conn, sp_uid=sp_uid, prog_status=True)
    else:
        db.sp_users_configs_update_user(conn=conn, sp_uid=sp_uid, shifts=json.dumps(work_data))


def remove_days(conn: MySQLConnection, sp_uid: int, days: str) -> None:
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

    if sp_user_data["prog_status"]:
        # pause program
        db.sp_users_configs_update_user(conn=conn, sp_uid=sp_uid, prog_status=False)
        # update shifts
        db.sp_users_configs_update_user(conn=conn, sp_uid=sp_uid, shifts=json.dumps(work_data))
        # unpause program
        db.sp_users_configs_update_user(conn=conn, sp_uid=sp_uid, prog_status=True)
    else:
        db.sp_users_configs_update_user(conn=conn, sp_uid=sp_uid, shifts=json.dumps(work_data))


def get_bytes_file(conn: MySQLConnection, sp_uid: int) -> Optional[bytes]:
    # conn > sp_users_db
    sp_user_data = db.sp_users_get_user(conn=conn, sp_uid=sp_uid)
    work_data_extracted_string = sp_user_data["shifts"]
    if work_data_extracted_string:
        work_data_extracted = json.loads(work_data_extracted_string)
        return bytes('\n'.join(work_data_extracted), encoding="utf8")
    else:
        return None
