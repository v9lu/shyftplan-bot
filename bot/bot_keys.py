# Version 1.4.3 release

import configparser
import mysql.connector as mysql
import random
import string
from aiogram import Bot, Router, types
from aiogram.filters import Command, Text, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup
from datetime import datetime, timedelta

from bot_keyboards import create_menu_keyboard, create_menu_button_keyboard
from tools import config_data, db

router = Router()


class WaitKey(StatesGroup):
    waiting_for_key = State()


@router.message(Text(text="🔑 Activate key"))
async def activate_key_btn(message: types.Message, state: FSMContext) -> None:
    await state.set_state(WaitKey.waiting_for_key)
    keyboard = await create_menu_button_keyboard()
    await message.answer("🔑 Please enter your key", reply_markup=keyboard)


@router.message(Text(text="🔑 Create key"))
async def create_key_btn(message: types.Message) -> None:
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"])
    user_data = db.users_get_user(conn=db_connect, user_id=message.from_user.id)
    sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
    if sp_user_data["subscription"] == "admin":
        keyboard = await create_menu_keyboard(sp_user_data=sp_user_data)
        await message.answer("🔑 Key generator:\n"
                             "1. Type [standard/premium].\n"
                             "2. Days [15]\n\n"
                             "Usage: /key <b>standard</b> <b>30</b>",
                             reply_markup=keyboard, parse_mode="HTML")
    db_connect.close()


@router.message(Text(text="🚫 Deactivate key"))
async def deactivate_key_btn(message: types.Message) -> None:
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"])
    user_data = db.users_get_user(conn=db_connect, user_id=message.from_user.id)
    sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
    if sp_user_data["subscription"] == "admin":
        keyboard = await create_menu_keyboard(sp_user_data=sp_user_data)
        await message.answer("🚫 Key deactivator:\n\n"
                             "Usage: /deactivate <b>key</b>",
                             reply_markup=keyboard, parse_mode="HTML")
    db_connect.close()


@router.message(Command(commands=["key"]))
async def key_generator(message: types.Message, command: CommandObject) -> None:
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"])
    user_data = db.users_get_user(conn=db_connect, user_id=message.from_user.id)
    sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
    if sp_user_data["subscription"] == "admin" and command.args:
        parameters = command.args.split()
        if len(parameters) == 2:
            key_type = parameters[0]
            if key_type == "standard" or key_type == "premium" or key_type == "friend" or key_type == "admin":
                try:
                    key_days = int(parameters[1])
                    letters = string.ascii_lowercase + string.digits
                    key = ''.join(random.choice(letters) for i in range(16))
                    db.keys_add_key(conn=db_connect, key=key, key_type=key_type, key_days=key_days)
                    if key_type == "premium":
                        await message.reply(f"🔑 <b>Key</b>: <code>{key}</code>\n"
                                            f"     ├─ 💎 <b>Type</b>: <code>Premium</code>\n"
                                            f"     └─ 📅 <b>Days</b>: <code>{key_days}</code>", parse_mode="HTML")
                    elif key_type == "standard":
                        await message.reply(f"🔑 <b>Key</b>: <code>{key}</code>\n"
                                            f"     ├─ 🔹 <b>Type</b>: <code>Standard</code>\n"
                                            f"     └─ 📅 <b>Days</b>: <code>{key_days}</code>", parse_mode="HTML")
                    elif key_type == "friend":
                        await message.reply(f"🔑 <b>Key</b>: <code>{key}</code>\n"
                                            f"     ├─ 👑 <b>Type</b>: <code>Friend</code>\n"
                                            f"     └─ 📅 <b>Days</b>: {key_days}", parse_mode="HTML")
                    elif key_type == "admin":
                        await message.reply(f"🔑 <b>Key</b>: <code>{key}</code>\n"
                                            f"     ├─ 🖥 <b>Type</b>: <code>Admin</code>\n"
                                            f"     └─ 📅 <b>Days</b>: {key_days}", parse_mode="HTML")
                except ValueError:
                    pass
    db_connect.close()


@router.message(Command(commands=["deactivate"]))
async def key_deactivator(message: types.Message, command: CommandObject, state: FSMContext) -> None:
    await state.clear()
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"])
    user_data = db.users_get_user(conn=db_connect, user_id=message.from_user.id)
    sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
    if sp_user_data["subscription"] == "admin" and command.args:
        parameters = command.args.split()
        if len(parameters) == 1:
            key = parameters[0]
            db.keys_remove_key(conn=db_connect, key=key)
            await message.reply("✅ The key was successfully removed!")
    db_connect.close()


@router.message(WaitKey.waiting_for_key)
async def key_waiting(message: types.Message, state: FSMContext, bot: Bot) -> None:
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"])
    user_data = db.users_get_user(conn=db_connect, user_id=message.from_user.id)
    if user_data["sp_uid"]:
        key_data = db.keys_activate_key(conn=db_connect, key=message.text)
        sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
        if key_data:
            key_type = key_data["key_type"]
            key_days = key_data["key_days"]
            key_type_priority = {None: 0, "trial": 1, "standard": 1, "premium": 2, "friend": 3, "admin": 4}
            expire_date = datetime.now() + timedelta(days=key_days)
            if sp_user_data["expire"]:
                if sp_user_data["expire"] > datetime.now():
                    if key_type_priority[sp_user_data["subscription"]] >= key_type_priority[key_type]:
                        expire_date = sp_user_data["expire"] + timedelta(days=key_days)
            expire_text = datetime.strftime(expire_date,
                                            "<code>%d</code> <code>%B</code> <code>%Y</code>, <code>%H:%M</code>")
            photo_id = "AgACAgIAAxkBAAJNV2QjEe1WJSZOtAOXh3dsGog7zOqSAAIVyjEbsLQZSYiHj_di2VgSAQADAgADeQADLwQ"
            if key_type == "trial":
                if not sp_user_data["used_trial"]:
                    db.sp_users_subscriptions_update_user(conn=db_connect, sp_uid=user_data["sp_uid"],
                                                          subscription="trial", expire=expire_date.isoformat(),
                                                          used_trial=True, is_notified=False)
                    db.sp_users_configs_update_user(conn=db_connect, sp_uid=user_data["sp_uid"],
                                                    prog_news=0,
                                                    scooter_status=0, car_status=0,
                                                    prog_sleep=5)
                    sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
                    keyboard = await create_menu_keyboard(sp_user_data=sp_user_data)
                    await message.answer_photo(photo=photo_id,
                                               caption=f"✅ <b>Successfully activated!</b>\n"
                                                       f"     ├─ 🆓 <b>Subscription</b>: <code>Trial</code>\n"
                                                       f"     ├─ 📅 <b>Days</b>: <code>{key_days}</code>\n"
                                                       f"     └─ 🔥 <b>Expire</b>: {expire_text}\n"
                                                       "❤️‍🔥 <b>Within 24 hours you'll be connected to our bot system "
                                                       "(if you aren't already connected), "
                                                       "now you can configure your bot</b>",
                                               reply_markup=keyboard,
                                               parse_mode="HTML")
                    await bot.send_message(1630691291, f"⚡ <b>User <code>{message.from_user.id}</code> has "
                                                       f"successfully activated the <code>{key_type}</code> key, "
                                                       f"now you can connect him to the bot</b>",
                                           parse_mode="HTML")
                else:
                    keyboard = await create_menu_keyboard(sp_user_data=sp_user_data)
                    await message.answer("🚫 You have already used the trial period", reply_markup=keyboard)
            else:
                db.sp_users_subscriptions_update_user(conn=db_connect, sp_uid=user_data["sp_uid"],
                                                      subscription=key_type, expire=expire_date.isoformat(),
                                                      is_notified=False)
                sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
                keyboard = await create_menu_keyboard(sp_user_data=sp_user_data)
                if key_type == "standard":
                    db.sp_users_configs_update_user(conn=db_connect, sp_uid=user_data["sp_uid"],
                                                    prog_news=0,
                                                    scooter_status=0, car_status=0,
                                                    prog_sleep=5)
                    await message.answer_photo(photo=photo_id,
                                               caption=f"✅ <b>Successfully activated!</b>\n"
                                                       f"     ├─ 🔹 <b>Subscription</b>: <code>Standard</code>\n"
                                                       f"     ├─ 📅 <b>Days</b>: <code>{key_days}</code>\n"
                                                       f"     └─ 🔥 <b>Expire</b>: {expire_text}\n"
                                                       "❤️‍🔥 <b>Within 24 hours you'll be connected to our bot system "
                                                       "(if you aren't already connected), "
                                                       "now you can configure your bot</b>",
                                               reply_markup=keyboard,
                                               parse_mode="HTML")
                    await bot.send_message(1630691291, f"⚡ <b>User <code>{message.from_user.id}</code> has "
                                                       f"successfully activated the <code>{key_type}</code> key, "
                                                       f"now you can connect him to the bot</b>",
                                           parse_mode="HTML")
                elif key_type == "premium":
                    await message.answer_photo(photo=photo_id,
                                               caption=f"✅ <b>Successfully activated!</b>\n"
                                                       f"     ├─ 💎 <b>Subscription</b>: <code>Premium</code>\n"
                                                       f"     ├─ 📅 <b>Days</b>: <code>{key_days}</code>\n"
                                                       f"     └─ 🔥 <b>Expire</b>: {expire_text}\n"
                                                       "❤️‍🔥 <b>Within 24 hours you'll be connected to our bot system "
                                                       "(if you aren't already connected), "
                                                       "now you can configure your bot</b>",
                                                       reply_markup=keyboard, parse_mode="HTML")
                    await bot.send_message(1630691291, f"⚡ <b>User <code>{message.from_user.id}</code> has "
                                                       f"successfully activated the <code>{key_type}</code> key, "
                                                       f"now you can connect him to the bot</b>",
                                           parse_mode="HTML")
                elif key_type == "friend":
                    await message.answer_photo(photo=photo_id,
                                               caption=f"✅ <b>Successfully activated!</b>\n"
                                                       f"     ├─ 👑 <b>Subscription</b>: <code>Friend</code>\n"
                                                       f"     ├─ 📅 <b>Days</b>: <code>{key_days}</code>\n"
                                                       f"     └─ 🔥 <b>Expire</b>: {expire_text}\n"
                                                       "❤️‍🔥 <b>Within 24 hours you'll be connected to our bot system "
                                                       "(if you aren't already connected), "
                                                       "now you can configure your bot</b>",
                                               reply_markup=keyboard,
                                               parse_mode="HTML")
                    await bot.send_message(1630691291, f"⚡ <b>User <code>{message.from_user.id}</code> has "
                                                       f"successfully activated the <code>{key_type}</code> key, "
                                                       f"now you can connect him to the bot</b>",
                                           parse_mode="HTML")
                elif key_type == "admin":
                    await message.answer_photo(photo=photo_id,
                                               caption=f"✅ <b>Successfully activated!</b>\n"
                                                       f"     ├─ 🖥 <b>Subscription</b>: <code>Admin</code>\n"
                                                       f"     ├─ 📅 <b>Days</b>: <code>{key_days}</code>\n"
                                                       f"     └─ 🔥 <b>Expire</b>: {expire_text}\n"
                                                       "❤️‍🔥 <b>Within 24 hours you'll be connected to our bot system "
                                                       "(if you aren't already connected), "
                                                       "while you can configure your bot</b>",
                                               reply_markup=keyboard,
                                               parse_mode="HTML")
                    await bot.send_message(1630691291, f"⚡ <b>User <code>{message.from_user.id}</code> has "
                                                       f"successfully activated the <code>{key_type}</code> key, "
                                                       f"now you can connect him to the bot</b>",
                                           parse_mode="HTML")
        else:
            keyboard = await create_menu_keyboard(sp_user_data=sp_user_data)
            await message.answer("❌ Key not found!", reply_markup=keyboard)
    else:
        keyboard = await create_menu_keyboard()
        await message.answer("🚫 You aren't authorized! Use a special button for login or the command /auth",
                             reply_markup=keyboard)
    await state.clear()
    db_connect.close()
