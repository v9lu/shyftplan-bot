# Version 2.1.1 release

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from typing import Optional


async def create_menu_button_keyboard() -> ReplyKeyboardMarkup:
    menu_button_keyboard = ReplyKeyboardBuilder()
    menu_btn = KeyboardButton(text="🎛 Menu")
    menu_button_keyboard.row(menu_btn)
    return menu_button_keyboard.as_markup(resize_keyboard=True)


async def create_menu_keyboard(sp_user_data: Optional[dict] = None) -> ReplyKeyboardMarkup:
    menu_keyboard = ReplyKeyboardBuilder()
    if sp_user_data is None:
        update_shifts_btn = KeyboardButton(text="♻️ Update shifts")
        settings_btn = KeyboardButton(text="⚙️ Settings")
        menu_keyboard.row(update_shifts_btn)
        menu_keyboard.row(settings_btn)
    else:
        if sp_user_data["subscription"] == "friend":
            update_shifts_btn = KeyboardButton(text="♻️ Update shifts")
            settings_btn = KeyboardButton(text="⚙️ Settings")
            menu_keyboard.row(update_shifts_btn)
            menu_keyboard.row(settings_btn)
        elif sp_user_data["subscription"] == "admin":
            update_shifts_btn = KeyboardButton(text="♻️ Update shifts")
            settings_btn = KeyboardButton(text="⚙️ Settings")
            create_key_btn = KeyboardButton(text="🔑 Create key")
            deactivate_key_btn = KeyboardButton(text="🚫 Deactivate key")
            menu_keyboard.row(update_shifts_btn)
            menu_keyboard.row(settings_btn)
            menu_keyboard.row(create_key_btn, deactivate_key_btn)
        else:
            update_shifts_btn = KeyboardButton(text="♻️ Update shifts")
            settings_btn = KeyboardButton(text="⚙️ Settings")
            buy_subscription_btn = KeyboardButton(text="💳️ Buy subscription")
            activate_key_btn = KeyboardButton(text="🔑 Activate key")
            menu_keyboard.row(update_shifts_btn)
            menu_keyboard.row(settings_btn)
            menu_keyboard.row(buy_subscription_btn, activate_key_btn)
    return menu_keyboard.as_markup(resize_keyboard=True)


async def create_subscriptions_keyboard(sp_user_data: dict) -> ReplyKeyboardMarkup:
    subscriptions_keyboard = ReplyKeyboardBuilder()
    buy_30_premium_btn = KeyboardButton(text="💎 30 day's premium")
    buy_30_standard_btn = KeyboardButton(text="🔹 30 day's standard")
    trial_btn = KeyboardButton(text="🆓 7 day's trial")
    menu_btn = KeyboardButton(text="🎛 Menu")
    if not sp_user_data["used_trial_btn"]:
        subscriptions_keyboard.row(buy_30_premium_btn, buy_30_standard_btn)
        subscriptions_keyboard.row(trial_btn)
    else:
        subscriptions_keyboard.row(buy_30_premium_btn)
        subscriptions_keyboard.row(buy_30_standard_btn)
    subscriptions_keyboard.row(menu_btn)
    return subscriptions_keyboard.as_markup(resize_keyboard=True)


async def create_settings_keyboard(user_data: dict) -> InlineKeyboardMarkup:
    status_template: str = "Status: {emoji}"
    other_statuses_templates: list = ["Open Shifts: {emoji}", "Shift Offers: {emoji}", "News: {emoji}"]
    speed_template: str = "Check Speed: {emoji}"

    if user_data["prog_status"]:
        status_template = status_template.format(emoji="✅")
    else:
        status_template = status_template.format(emoji="⛔️")
    
    other_statuses = [user_data["prog_open_shifts"], user_data["prog_shift_offers"], user_data["prog_news"]]
    for index in range(len(other_statuses)):
        if other_statuses[index]:
            other_statuses_templates[index] = other_statuses_templates[index].format(emoji="✅")
        else:
            other_statuses_templates[index] = other_statuses_templates[index].format(emoji="❌")

    if user_data["prog_sleep"] == 0.3:
        speed_template = speed_template.format(emoji="⚡ (0.3 sec)")
    elif user_data["prog_sleep"] == 1.0:
        speed_template = speed_template.format(emoji="🐝 (1.0 sec)")
    elif user_data["prog_sleep"] == 5.0:
        speed_template = speed_template.format(emoji="🐢 (5.0 sec)")
    else:
        raise Exception("sleeptime must be 0.3 or 1.0 or 5.0")  # Другого значения быть не может

    settings_keyboard = InlineKeyboardBuilder()
    status_btn = InlineKeyboardButton(text=status_template, callback_data="prog_status")
    open_shifts_status_btn = InlineKeyboardButton(text=other_statuses_templates[0], callback_data="prog_open_shifts")
    shift_offers_status_btn = InlineKeyboardButton(text=other_statuses_templates[1], callback_data="prog_shift_offers")
    news_status_btn = InlineKeyboardButton(text=other_statuses_templates[2], callback_data="prog_news")
    speed_btn = InlineKeyboardButton(text=speed_template, callback_data="prog_sleep")
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
