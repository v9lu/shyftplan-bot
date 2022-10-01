# Version 2.0.1 release

from configparser import ConfigParser
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


async def create_menu_button_keyboard() -> ReplyKeyboardMarkup:
    menu_button_keyboard = ReplyKeyboardBuilder()
    menu_btn = KeyboardButton(text="🎛 Menu")
    menu_button_keyboard.row(menu_btn)
    return menu_button_keyboard.as_markup(resize_keyboard=True)


async def create_menu_keyboard() -> ReplyKeyboardMarkup:
    menu_keyboard = ReplyKeyboardBuilder()
    update_shifts_btn = KeyboardButton(text="♻️ Update shifts")
    settings_btn = KeyboardButton(text="⚙️ Settings")
    menu_keyboard.row(update_shifts_btn)
    menu_keyboard.row(settings_btn)
    return menu_keyboard.as_markup(resize_keyboard=True)


async def create_settings_keyboard(config: ConfigParser) -> InlineKeyboardMarkup:
    config.read('settings.ini')
    status: bool = config.getboolean("PROGRAM_CONFIG", "status")
    open_shifts_status: bool = config.getboolean("PROGRAM_CONFIG", "open_shifts_status")
    shift_offers_status: bool = config.getboolean("PROGRAM_CONFIG", "shift_offers_status")
    news_status: bool = config.getboolean("PROGRAM_CONFIG", "news_status")
    sleeptime: float = config.getfloat("PROGRAM_CONFIG", "sleeptime")

    status_template: str = "Status: {emoji}"
    other_statuses_templates: list = ["Open Shifts: {emoji}", "Shift Offers: {emoji}", "News: {emoji}"]
    speed_template: str = "Speed: {emoji}"

    if status:
        status_template = status_template.format(emoji="✅")
    else:
        status_template = status_template.format(emoji="⛔️")
    
    other_statuses = [open_shifts_status, shift_offers_status, news_status]
    for index in range(len(other_statuses)):
        if other_statuses[index]:
            other_statuses_templates[index] = other_statuses_templates[index].format(emoji="✅")
        else:
            other_statuses_templates[index] = other_statuses_templates[index].format(emoji="❌")

    if sleeptime == 0.3:
        speed_template = speed_template.format(emoji="🐝 (0.3 sec)")
    elif sleeptime == 1.0:
        speed_template = speed_template.format(emoji="🐢(1.0 sec)")
    else:
        raise Exception("sleeptime must be 0.3 or 1.0")  # Другого значения быть не может

    settings_keyboard = InlineKeyboardBuilder()
    status_btn = InlineKeyboardButton(text=status_template,
                                      callback_data="status")
    open_shifts_status_btn = InlineKeyboardButton(text=other_statuses_templates[0],
                                                  callback_data="open_shifts_status")
    shift_offers_status_btn = InlineKeyboardButton(text=other_statuses_templates[1],
                                                   callback_data="shift_offers_status")
    news_status_btn = InlineKeyboardButton(text=other_statuses_templates[2],
                                           callback_data="news_status")
    speed_btn = InlineKeyboardButton(text=speed_template,
                                     callback_data="speed")
    settings_keyboard.row(status_btn)
    settings_keyboard.row(open_shifts_status_btn, shift_offers_status_btn, news_status_btn)
    settings_keyboard.row(speed_btn)
    return settings_keyboard.as_markup()


async def create_update_shifts_keyboard() -> ReplyKeyboardMarkup:
    update_shifts_keyboard = ReplyKeyboardBuilder()
    row_shifts_btn = KeyboardButton(text="📗 Add shifts")
    delete_shifts_btn = KeyboardButton(text="📕 Remove shifts")
    my_shifts_btn = KeyboardButton(text="📋 My shifts")
    menu_btn = KeyboardButton(text="🎛 Menu")
    update_shifts_keyboard.row(row_shifts_btn, delete_shifts_btn)
    update_shifts_keyboard.row(my_shifts_btn)
    update_shifts_keyboard.row(menu_btn)
    return update_shifts_keyboard.as_markup(resize_keyboard=True)
