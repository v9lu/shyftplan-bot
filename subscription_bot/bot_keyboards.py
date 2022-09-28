# Version 2.0.0 release

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
    buy_30_premium_btn = KeyboardButton(text="💎 30 day's premium")
    buy_30_standard_btn = KeyboardButton(text="🔹 30 day's standard")
    trial_btn = KeyboardButton(text="🆓 7 day's trial")
    menu_keyboard.row(buy_30_premium_btn)
    menu_keyboard.row(buy_30_standard_btn)
    menu_keyboard.row(trial_btn)
    return menu_keyboard.as_markup(resize_keyboard=True)


# async def create_settings_keyboard(config: ConfigParser) -> InlineKeyboardMarkup:
#     config.read('settings.ini')
#     status: bool = config.getboolean("PROGRAM_CONFIG", "status")
#     open_shifts_status: bool = config.getboolean("PROGRAM_CONFIG", "open_shifts_status")
#     shift_offers_status: bool = config.getboolean("PROGRAM_CONFIG", "shift_offers_status")
#     news_status: bool = config.getboolean("PROGRAM_CONFIG", "news_status")
#     sleeptime: int = config.getint("PROGRAM_CONFIG", "sleeptime")
#
#     status_template: str = "Status: {emoji}"
#     other_statuses_templates: list = ["Open Shifts: {emoji}", "Shift Offers: {emoji}", "News: {emoji}"]
#     speed_template: str = "Speed: {emoji}"
#
#     if status:
#         status_template = status_template.format(emoji="✅")
#     else:
#         status_template = status_template.format(emoji="⛔️")
#
#     other_statuses = [open_shifts_status, shift_offers_status, news_status]
#     for index in range(len(other_statuses)):
#         if other_statuses[index]:
#             other_statuses_templates[index] = other_statuses_templates[index].format(emoji="✅")
#         else:
#             other_statuses_templates[index] = other_statuses_templates[index].format(emoji="❌")
#
#     if sleeptime == 1:
#         speed_template = speed_template.format(emoji="🐝")
#     elif sleeptime == 5:
#         speed_template = speed_template.format(emoji="🐢")
#     else:
#         raise Exception("sleeptime must be 1 or 5")  # Другого значения быть не может
#
#     settings_keyboard = InlineKeyboardMarkup()
#     status_btn = InlineKeyboardButton(status_template, callback_data="status")
#     open_shifts_status_btn = InlineKeyboardButton(other_statuses_templates[0], callback_data="open_shifts_status")
#     shift_offers_status_btn = InlineKeyboardButton(other_statuses_templates[1], callback_data="shift_offers_status")
#     news_status_btn = InlineKeyboardButton(other_statuses_templates[2], callback_data="news_status")
#     speed_btn = InlineKeyboardButton(speed_template, callback_data="speed")
#     # settings_keyboard.add(InlineKeyboardButton(text="Pay 100.00 PLN", pay=True))
#     settings_keyboard.add(status_btn)
#     settings_keyboard.add(open_shifts_status_btn, shift_offers_status_btn, news_status_btn)
#     settings_keyboard.add(speed_btn)
#     return settings_keyboard
