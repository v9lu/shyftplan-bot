# Version 3.5.0 release

import calendar
import datetime
import json
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from typing import Optional


async def create_menu_button_keyboard() -> ReplyKeyboardMarkup:
    menu_btn = KeyboardButton(text="🎛 Menu")
    menu_button_keyboard = ReplyKeyboardBuilder()
    menu_button_keyboard.row(menu_btn)
    return menu_button_keyboard.as_markup(resize_keyboard=True)


async def create_menu_keyboard(sp_user_data: Optional[dict] = None) -> ReplyKeyboardMarkup:
    authorize_btn = KeyboardButton(text="🔐️ Login Shyftplan")
    update_shifts_btn = KeyboardButton(text="♻️ Update shifts")
    settings_btn = KeyboardButton(text="⚙️ Settings")
    exploit_btn = KeyboardButton(text="💥 Shift workers [Exploit]")
    buy_subscription_btn = KeyboardButton(text="💳️ Buy subscription")
    activate_key_btn = KeyboardButton(text="🔑 Activate key")
    create_key_btn = KeyboardButton(text="🔑 Create key")
    newsletter_btn = KeyboardButton(text="✉️ Newsletter")
    deactivate_key_btn = KeyboardButton(text="🚫 Deactivate key")
    statistic_btn = KeyboardButton(text="📊 Statistic")
    menu_keyboard = ReplyKeyboardBuilder()
    if sp_user_data is None:
        menu_keyboard.row(authorize_btn)
    else:
        menu_keyboard.row(update_shifts_btn, settings_btn)
        if sp_user_data["subscription"] == "admin":
            menu_keyboard.row(exploit_btn)
            menu_keyboard.row(create_key_btn, newsletter_btn, deactivate_key_btn)
        elif sp_user_data["subscription"] == "friend":
            menu_keyboard.row(exploit_btn)
            menu_keyboard.row(activate_key_btn)
        else:
            menu_keyboard.row(buy_subscription_btn, activate_key_btn)
        menu_keyboard.row(statistic_btn)
    return menu_keyboard.as_markup(resize_keyboard=True)


async def create_subscriptions_keyboard(sp_user_data: dict, allocated_subs: dict,
                                        sub_counts: dict) -> ReplyKeyboardMarkup:
    if sp_user_data["subscription"] == "standard" or sp_user_data["subscription"] == "premium":
        buy_30_standard_btn = KeyboardButton(text=f"🔹 30 day's standard")
        buy_30_premium_btn = KeyboardButton(text=f"💎 30 day's premium")
    else:
        buy_30_standard_btn = KeyboardButton(text=f"[{allocated_subs['standard'] - sub_counts['standard']}] "
                                                  f"🔹 30 day's standard")
        buy_30_premium_btn = KeyboardButton(text=f"[{allocated_subs['premium'] - sub_counts['premium']}] "
                                                 f"💎 30 day's premium")
    trial_btn = KeyboardButton(text=f"[{allocated_subs['trial'] - sub_counts['trial']}] 🆓 7 day's trial")
    menu_btn = KeyboardButton(text="🎛 Menu")
    subscriptions_keyboard = ReplyKeyboardBuilder()
    if not sp_user_data["used_trial_btn"]:
        subscriptions_keyboard.row(buy_30_standard_btn, buy_30_premium_btn)
        subscriptions_keyboard.row(trial_btn)
    else:
        subscriptions_keyboard.row(buy_30_standard_btn)
        subscriptions_keyboard.row(buy_30_premium_btn)
    subscriptions_keyboard.row(menu_btn)
    return subscriptions_keyboard.as_markup(resize_keyboard=True)


async def create_cutoff_times_keyboard(sp_user_data: dict) -> InlineKeyboardMarkup:
    cutoff_times = {
        4: ("4 hours", "set_cutoff_4"),
        3: ("3 hours", "set_cutoff_3"),
        2: ("2 hours", "set_cutoff_2"),
        1: ("1 hour", "set_cutoff_1"),
        30: ("30 minutes", "set_cutoff_30"),
        0: ("Without Cut-Off", "set_cutoff_0")
    }

    rows = [[] for _ in range(4)]

    for cutoff_time, (text, callback_data) in cutoff_times.items():
        if sp_user_data["prog_cutoff_time"] == cutoff_time:
            text = "🔥 " + text
        if cutoff_time in [4, 3]:
            rows[0].append(InlineKeyboardButton(text=text, callback_data=callback_data))
        elif cutoff_time in [2, 1]:
            rows[1].append(InlineKeyboardButton(text=text, callback_data=callback_data))
        elif cutoff_time == 30:
            rows[2].append(InlineKeyboardButton(text=text, callback_data=callback_data))
        else:
            rows[3].append(InlineKeyboardButton(text=text, callback_data=callback_data))

    cutoff_times_keyboard = InlineKeyboardBuilder()
    for row in rows:
        cutoff_times_keyboard.row(*row)
    return cutoff_times_keyboard.as_markup()


async def create_settings_keyboard(sp_user_data: dict) -> InlineKeyboardMarkup:
    status_template = "{emoji} Status"
    prog_statuses_template = ["{emoji} Open Shifts", "{emoji} Shift Offers", "{emoji} News"]
    transport_statuses_template = ["{emoji} Bike", "{emoji} E-Bike", "{emoji} Scooter", "{emoji} Car"]
    speed_template = "{emoji} Check Speed"
    cutoff_time_template = "{emoji} Cut-Off Time"

    if sp_user_data["prog_status"]:
        status_template = status_template.format(emoji="✅")
    else:
        status_template = status_template.format(emoji="⛔️")
    
    prog_statuses = [sp_user_data["prog_open_shifts"], sp_user_data["prog_shift_offers"], sp_user_data["prog_news"]]
    for index in range(len(prog_statuses)):
        if prog_statuses[index]:
            prog_statuses_template[index] = prog_statuses_template[index].format(emoji="✅")
        else:
            prog_statuses_template[index] = prog_statuses_template[index].format(emoji="❌")

    transport_statuses = [sp_user_data["bike_status"], sp_user_data["ebike_status"],
                          sp_user_data["scooter_status"], sp_user_data["car_status"]]
    for index in range(len(transport_statuses)):
        if transport_statuses[index]:
            transport_statuses_template[index] = transport_statuses_template[index].format(emoji="✅")
        else:
            transport_statuses_template[index] = transport_statuses_template[index].format(emoji="❌")

    if sp_user_data["prog_sleep"] == 0.3:
        speed_template = speed_template.format(emoji="⚡ (0.3 sec)")
    elif sp_user_data["prog_sleep"] == 1.0:
        speed_template = speed_template.format(emoji="🐝 (1.0 sec)")
    elif sp_user_data["prog_sleep"] == 5.0:
        speed_template = speed_template.format(emoji="🐢 (5.0 sec)")
    else:
        raise Exception("sleeptime must be 0.3 or 1.0 or 5.0")  # Другого значения быть не может

    if not sp_user_data["prog_cutoff_time"]:
        cutoff_time_template = "🧯 Without Cut-Off"
    elif sp_user_data["prog_cutoff_time"] == 30:
        cutoff_time_template = cutoff_time_template.format(emoji="🔥 (30 minutes)")
    elif sp_user_data["prog_cutoff_time"] == 1:
        cutoff_time_template = cutoff_time_template.format(emoji=f"🔥 ({sp_user_data['prog_cutoff_time']} hour)")
    else:
        cutoff_time_template = cutoff_time_template.format(emoji=f"🔥 ({sp_user_data['prog_cutoff_time']} hours)")

    settings_keyboard = InlineKeyboardBuilder()
    status_btn = InlineKeyboardButton(text=status_template, callback_data="prog_status")
    open_shifts_status_btn = InlineKeyboardButton(text=prog_statuses_template[0], callback_data="prog_open_shifts")
    shift_offers_status_btn = InlineKeyboardButton(text=prog_statuses_template[1], callback_data="prog_shift_offers")
    news_status_btn = InlineKeyboardButton(text=prog_statuses_template[2], callback_data="prog_news")
    bike_status_btn = InlineKeyboardButton(text=transport_statuses_template[0], callback_data="bike_status")
    ebike_status_btn = InlineKeyboardButton(text=transport_statuses_template[1], callback_data="ebike_status")
    scooter_status_btn = InlineKeyboardButton(text=transport_statuses_template[2], callback_data="scooter_status")
    car_status_btn = InlineKeyboardButton(text=transport_statuses_template[3], callback_data="car_status")
    speed_btn = InlineKeyboardButton(text=speed_template, callback_data="prog_sleep")
    cutoff_time_btn = InlineKeyboardButton(text=cutoff_time_template, callback_data="prog_cutoff_time")
    settings_keyboard.row(status_btn)
    settings_keyboard.row(open_shifts_status_btn, shift_offers_status_btn, news_status_btn)
    settings_keyboard.row(bike_status_btn, ebike_status_btn, scooter_status_btn, car_status_btn)
    settings_keyboard.row(speed_btn)
    settings_keyboard.row(cutoff_time_btn)
    return settings_keyboard.as_markup()


async def create_ds_keyboard(user_shifts: str) -> InlineKeyboardMarkup:
    locations = {
        "czluchowska": "Człuchowska 35",
        "dolna": "Dolna 41",
        "elektryczna": "Elektryczna 2",
        "europlex": "Europlex (Puławska 17)",
        "grenadierow": "Grenadierów 11",
        "grochowskiego": "Grochowskiego 5 [Piaseczno]",
        "hawajska": "Hawajska 11",
        "herbu": "Herbu Janina 5",
        "kamienna": "Kamienna 1",
        "konstruktorska": "Konstruktorska 13A",
        "lekka": "Lekka 3",
        "lirowa": "Lirowa 26",
        "miedzynarodowa": "Międzynarodowa 42",
        "rydygiera": "Rydygiera 13",
        "sielecka": "Sielecka 35",
        "sikorskiego": "Sikorskiego 3A",
        "solidarnosci": "Solidarności 155",
        "szarych": "Szarych Szeregów 11",
        "tarnowiecka": "Tarnowiecka 13",
    }
    keyboard_buttons = []

    for ds_name, ds_fullname in locations.items():
        if ds_name in user_shifts:
            ds_fullname = "🟢 " + ds_fullname
        keyboard_buttons.append(InlineKeyboardButton(text=ds_fullname, callback_data=ds_name))

    ds_keyboard = InlineKeyboardBuilder()
    ds_keyboard.row(*keyboard_buttons, width=4)
    return ds_keyboard.as_markup()


async def create_years_keyboard(user_shifts: str, ds_name: str) -> InlineKeyboardMarkup:
    shifts_extracted = json.loads(user_shifts) if user_shifts else []
    current_year = datetime.datetime.now().year
    years = [str(current_year), str(current_year + 1)]
    keyboard_buttons = []

    for year in years:
        year_call = year
        for shift in shifts_extracted:
            shift_components = shift.split("/")
            shift_ds_name = shift_components[0]
            if shift_ds_name == ds_name:
                shift_date_str = shift_components[1]
                shift_date_obj = datetime.datetime.strptime(shift_date_str, "%d.%m.%Y")
                shift_year = shift_date_obj.year
                if shift_year == int(year):
                    year = "🟢 " + year
                    break
            else:
                continue
        keyboard_buttons.append(InlineKeyboardButton(text=year, callback_data=year_call))

    years_keyboard = InlineKeyboardBuilder()
    years_keyboard.row(*keyboard_buttons, width=1)
    years_keyboard.row(InlineKeyboardButton(text="◀️ Back to DS", callback_data="step_back"))
    return years_keyboard.as_markup()


async def create_months_keyboard(user_shifts: str, ds_name: str, year: str) -> InlineKeyboardMarkup:
    shifts_extracted = json.loads(user_shifts) if user_shifts else []
    now = datetime.datetime.now()
    current_year = now.year
    if current_year == int(year):
        current_month = now.month
    else:
        current_month = 1
    keyboard_buttons = []

    for month_num in range(current_month, 13):
        month_name = datetime.date(current_year, month_num, 1).strftime('%B')
        for shift in shifts_extracted:
            shift_components = shift.split("/")
            shift_ds_name = shift_components[0]
            if shift_ds_name == ds_name:
                shift_date_str = shift_components[1]
                shift_date_obj = datetime.datetime.strptime(shift_date_str, "%d.%m.%Y")
                shift_year = shift_date_obj.year
                shift_month = shift_date_obj.month
                if shift_year == int(year) and shift_month == month_num:
                    month_name = "🟢 " + month_name
                    break
            else:
                continue
        keyboard_buttons.append(InlineKeyboardButton(text=month_name, callback_data=f"{month_num:02d}"))

    months_keyboard = InlineKeyboardBuilder()
    months_keyboard.row(*keyboard_buttons, width=3)
    months_keyboard.row(InlineKeyboardButton(text="◀️ Back to years", callback_data="step_back"))
    return months_keyboard.as_markup()


async def create_days_keyboard(selection_mode: bool, user_shifts: str, ds_name: str, year: str,
                               month: str) -> InlineKeyboardMarkup:
    shifts_extracted = json.loads(user_shifts) if user_shifts else []
    now = datetime.datetime.now()
    current_year = now.year
    current_month = now.month
    if current_year == int(year) and current_month == int(month):
        current_day = now.day
    else:
        current_day = 1
    num_days = calendar.monthrange(int(year), int(month))[1]
    keyboard_buttons = []

    for day in range(current_day, num_days + 1):
        day_text = f"{day:02d}"
        for shift in shifts_extracted:
            shift_components = shift.split("/")
            shift_ds_name = shift_components[0]
            if shift_ds_name == ds_name:
                shift_date_str = shift_components[1]
                shift_date_obj = datetime.datetime.strptime(shift_date_str, "%d.%m.%Y")
                shift_year = shift_date_obj.year
                shift_month = shift_date_obj.month
                shift_day = shift_date_obj.day
                if shift_year == int(year) and shift_month == int(month) and shift_day == day:
                    day_text = "🟢 " + day_text
                    day_call = f"{day:02d}_remove"
                    break
            else:
                continue
        else:
            day_call = f"{day:02d}_add"
        if selection_mode:
            keyboard_buttons.append(InlineKeyboardButton(text=day_text, callback_data=day_call))
        else:
            keyboard_buttons.append(InlineKeyboardButton(text=day_text, callback_data=f"{day:02d}"))

    days_keyboard = InlineKeyboardBuilder()
    days_keyboard.row(*keyboard_buttons, width=7)
    if selection_mode:
        days_keyboard.row(InlineKeyboardButton(text="🔘 Selection Mode", callback_data="selection_mode_off"))
    else:
        days_keyboard.row(InlineKeyboardButton(text="🎯 Standard Mode", callback_data="selection_mode_on"))
    days_keyboard.row(InlineKeyboardButton(text="◀️ Back to months", callback_data="step_back"))
    return days_keyboard.as_markup()


async def create_hours_keyboard(user_shifts: str, ds_name: str, year: str, month: str,
                                day: str) -> InlineKeyboardMarkup:
    shifts_extracted = json.loads(user_shifts) if user_shifts else []
    hours_couples = ["07:00-11:00", "10:00-15:00", "11:00-15:00",
                     "14:00-18:00", "15:00-19:00", "18:00-22:00",
                     "19:00-23:30", "19:00-00:30"]
    keyboard_buttons = []

    for hours_couple in hours_couples:
        for shift in shifts_extracted:
            shift_components = shift.split("/")
            shift_ds_name = shift_components[0]
            if shift_ds_name == ds_name:
                shift_date_str = shift_components[1]
                shift_date_obj = datetime.datetime.strptime(shift_date_str, "%d.%m.%Y")
                shift_year = shift_date_obj.year
                shift_month = shift_date_obj.month
                shift_day = shift_date_obj.day
                if hours_couple in shift and \
                   shift_year == int(year) and shift_month == int(month) and shift_day == int(day):
                    hours_text = "✅ " + hours_couple
                    hours_call = hours_couple + "_remove"
                    break
            else:
                continue
        else:
            hours_text = hours_couple
            hours_call = hours_couple + "_add"
        keyboard_buttons.append(InlineKeyboardButton(text=hours_text, callback_data=hours_call))

    hours_keyboard = InlineKeyboardBuilder()
    hours_keyboard.row(*keyboard_buttons, width=3)
    hours_keyboard.row(InlineKeyboardButton(text="🟩️ Select all", callback_data="select_all"),
                       InlineKeyboardButton(text="🟥️ Deselect all", callback_data="deselect_all"))
    hours_keyboard.row(InlineKeyboardButton(text="◀️ Back to days", callback_data="step_back"))
    return hours_keyboard.as_markup()
