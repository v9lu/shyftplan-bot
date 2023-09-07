# Version 1.8.0 release

import copy
import json
from datetime import datetime, timedelta
from mysql.connector import MySQLConnection
from typing import Optional
from unidecode import unidecode

from tools import db

locations_sample_warsaw = [{"name": "szarych",
                            "fullname": "Szarych Szeregów 11",
                            "ids": {"bike": {163056, 170251}, "ebike": {167474, 207569}, "scooter": {178048, 207550}, "car": {168652}},
                            "dates": []},
                           {"name": "hawajska",
                            "fullname": "Hawajska 11",
                            "ids": {"bike": {165605, 170252}, "ebike": {167475, 207600}, "scooter": {178049, 207551}, "car": {168653}},
                            "dates": []},
                           {"name": "lirowa",
                            "fullname": "Lirowa 26",
                            "ids": {"bike": {165606, 170254}, "ebike": {167477, 207602}, "scooter": {178051, 207553}, "car": {168655}, "lite": {200368}},
                            "dates": []},
                           {"name": "tarnowiecka",
                            "fullname": "Tarnowiecka 13",
                            "ids": {"bike": {165607, 170255}, "ebike": {167478, 207603}, "scooter": {178052, 207554}, "car": {168656}},
                            "dates": []},
                           {"name": "kamienna",
                            "fullname": "Kamienna 1",
                            "ids": {"bike": {165608, 170253}, "ebike": {167476, 207601}, "scooter": {178050, 207552}, "car": {168654}},
                            "dates": []},
                           {"name": "miedzynarodowa",
                            "fullname": "Międzynarodowa 42",
                            "ids": {"bike": {166576, 170256}, "ebike": {167479, 207604}, "scooter": {178053, 207555}, "car": {168657}},
                            "dates": []},
                           {"name": "sikorskiego",
                            "fullname": "Sikorskiego 3A",
                            "ids": {"bike": {166585, 170257}, "ebike": {167480, 207605}, "scooter": {178054, 207556}, "car": {168658}},
                            "dates": []},
                           {"name": "solidarnosci",
                            "fullname": "Solidarności 155",
                            "ids": {"bike": {166586, 170258}, "ebike": {167481, 207608}, "scooter": {178057, 207559}, "car": {168659}},
                            "dates": []},
                           {"name": "herbu",
                            "fullname": "Herbu Janina 5",
                            "ids": {"bike": {166587, 170259}, "ebike": {167482, 207609}, "scooter": {178058, 207560}, "car": {168660}},
                            "dates": []},
                           {"name": "czluchowska",
                            "fullname": "Człuchowska 35",
                            "ids": {"bike": {168928, 170260}, "ebike": {168929, 207610}, "scooter": {178059, 207561}, "car": {168930}},
                            "dates": []},
                           {"name": "rydygiera",
                            "fullname": "Rydygiera 13",
                            "ids": {"bike": {169661, 170261}, "ebike": {169694, 207611}, "scooter": {178060, 207562}, "car": {169695}},
                            "dates": []},
                           {"name": "europlex",
                            "fullname": "Europlex (Puławska 17)",
                            "ids": {"bike": {170617, 170618}, "ebike": {170858, 207612}, "scooter": {178061, 207563}, "car": {170619}},
                            "dates": []},
                           {"name": "grochowskiego",
                            "fullname": "Grochowskiego 5 [Piaseczno]",
                            "ids": {"bike": {170856, 170860}, "ebike": {170859}, "scooter": {178056}, "car": {170861}},
                            "dates": []},
                           {"name": "dolna",
                            "fullname": "Dolna 41",
                            "ids": {"bike": {171705, 171707}, "ebike": {171708, 207614}, "scooter": {178063, 207565}, "car": {171706}},
                            "dates": []},
                           {"name": "sielecka",
                            "fullname": "Sielecka 35",
                            "ids": {"bike": {174110, 174116}, "ebike": {174120, 207613}, "scooter": {178062, 207564}, "car": {174124}},
                            "dates": []},
                           {"name": "lekka",
                            "fullname": "Lekka 3",
                            "ids": {"bike": {174113, 174117}, "ebike": {174121, 207615}, "scooter": {178064, 207566}, "car": {174125}},
                            "dates": []},
                           {"name": "elektryczna",
                            "fullname": "Elektryczna 2",
                            "ids": {"bike": {174114, 174118}, "ebike": {174122, 207616}, "scooter": {178065, 207567}, "car": {174126}},
                            "dates": []
                            },
                           {"name": "konstruktorska",
                            "fullname": "Konstruktorska 13A",
                            "ids": {"bike": {174153, 174154}, "ebike": {174155, 207606}, "scooter": {178055, 207557}, "car": {174156}},
                            "dates": []
                            },
                           {"name": "grenadierow",
                            "fullname": "Grenadierów 11",
                            "ids": {"bike": {177820, 177821}, "ebike": {177823, 207617}, "scooter": {178066, 207568}, "car": {177822}},
                            "dates": []
                            }]

locations_sample_gdansk = [{"name": "rakoczego",
                            "fullname": "Rakoczego 19",
                            "ids": {"bike": {177425, 174597}, "scooter": {178572}, "car": {178580}},
                            "dates": []
                            },
                           {"name": "wilcza",
                            "fullname": "Wilcza 1",
                            "ids": {"bike": {182250}, "scooter": {}, "car": {}},
                            "dates": []
                            },
                           {"name": "fieldorfa",
                            "fullname": "Fieldorfa 2",
                            "ids": {"bike": {177423, 170312}, "scooter": {178570}, "car": {178578}},
                            "dates": []
                            },
                           {"name": "arkonska",
                            "fullname": "Arkońska 6",
                            "ids": {"bike": {177424}, "scooter": {178571}, "car": {178579}},
                            "dates": []
                            }]


def take_date(element):
    element = element.split("/")
    element = datetime.strptime(element[1], "%d.%m.%Y")
    return element


def converter(conn: MySQLConnection, sp_uid: int) -> list:
    # conn > sp_users_db
    locations = copy.deepcopy(locations_sample_warsaw)

    # READ SHIFTS
    sp_user_data = db.sp_users_get_user(conn=conn, sp_uid=sp_uid)
    shifts_extracted = json.loads(sp_user_data["shifts"]) if sp_user_data["shifts"] else []

    # REMOVE OUTDATED DAYS
    shifts_to_keep = []
    for shift in shifts_extracted:
        shift_date_str = shift.split("/")[1]
        shift_date = datetime.strptime(shift_date_str, "%d.%m.%Y")
        if shift_date >= datetime.combine(datetime.now(), datetime.min.time()):
            shifts_to_keep.append(shift)

    # OTHER ACTIONS
    shifts = []
    for shift in shifts_to_keep:
        shift_components = shift.split("/")
        template = '/'.join(shift_components[:2])  # '/'.join(["szarych", "09.09.2020"]) >>> "szarych/09.09.2020"
        if template not in shifts and not shift.isspace() and len(shift_components) > 2:
            shifts.append(template)
    for shift in shifts_to_keep:
        shift_components = shift.split("/")
        template = '/'.join(shift_components[:2])  # '/'.join(["szarych", "09.09.2020"]) >>> "szarych/09.09.2020"
        for index in range(len(shifts)):
            if template in shifts[index]:
                shift = shift.split()[0]
                # work_data[work_data.index(work_data[index])] >>> work_data[0]
                # '/'.join(work_day.split('/')[2:]) >>> '/'.join(WORK_DAY_HOURS_ONLY) >>> '/'.join(["07:00-11:00", ...])
                # >>> work_data[0] += '/' + "07:00-11:00/11:00-15:00"
                shifts[shifts.index(shifts[index])] += '/' + '/'.join(shift.split('/')[2:])

    # WRITE RESULT
    shifts.sort(key=take_date)
    db.sp_users_configs_update_user(conn=conn, sp_uid=sp_uid, shifts=json.dumps(shifts))

    # WORK WITH LOCATIONS LIST
    for index in range(len(locations)):
        for shift in shifts:
            shift_components = shift.split("/")  # "name/date/15-19" > ["name", "date", "15:00-19:00"]
            shift_location = shift_components[0]
            if shift_location == locations[index]["name"]:
                shift_date_str = shift_components[1]
                shift_hours: list = shift_components[2:]
                for hours_couple in shift_hours:
                    starts_time, ends_time = hours_couple.split("-")
                    dt_starts = datetime.strptime(f"{shift_date_str}{starts_time}", '%d.%m.%Y%H:%M')
                    dt_ends = datetime.strptime(f"{shift_date_str}{ends_time}", '%d.%m.%Y%H:%M')
                    if ends_time in ["00:00", "00:30"]:
                        dt_ends += timedelta(days=1)
                    locations[index]["dates"].append((dt_starts, dt_ends))
    return locations


def easy_converter(shifts: str) -> list:
    locations = copy.deepcopy(locations_sample_warsaw)

    # READ SHIFTS
    shifts = json.loads(shifts) if shifts else []

    # WORK WITH LOCATIONS LIST
    for index in range(len(locations)):
        for shift in shifts:
            shift_components = shift.split("/")  # "name/date/15-19" > ["name", "date", "15:00-19:00"]
            shift_location = shift_components[0]
            if shift_location == locations[index]["name"]:
                shift_date_str = shift_components[1]
                shift_hours: list = shift_components[2:]
                for hours_couple in shift_hours:
                    starts_time, ends_time = hours_couple.split("-")
                    dt_starts = datetime.strptime(f"{shift_date_str}{starts_time}", '%d.%m.%Y%H:%M')
                    dt_ends = datetime.strptime(f"{shift_date_str}{ends_time}", '%d.%m.%Y%H:%M')
                    if ends_time in ["00:00", "00:30"]:
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
