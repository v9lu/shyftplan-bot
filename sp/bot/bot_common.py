# Version 2.1.3 release

import configparser
import mysql.connector as mysql
from aiogram import Router, types
from aiogram.filters import Command, Text
from aiogram.fsm.context import FSMContext
from datetime import datetime

import config_data
import db
from bot_keyboards import *

router = Router()


@router.message(Command(commands=["start"]))
@router.message(Text(text="🎛 Menu"))
@router.message(Text(text="📊 Statistic"))
async def bot_start(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"],
                               database="users_db")
    db.users_add_user(conn=db_connect, user_id=message.from_user.id)
    user_data = db.users_get_user(conn=db_connect, user_id=message.from_user.id)
    if user_data["sp_uid"]:
        db_connect.connect(database="sp_users_db")
        sp_user_data = db.sp_users_sub_info(conn=db_connect, sp_uid=user_data["sp_uid"])
        keyboard = await create_menu_keyboard(sp_user_data)
        if sp_user_data["expire"]:
            expire_text = datetime.strftime(sp_user_data["expire"],
                                            "<code>%d</code> <code>%B</code> <code>%Y</code>, <code>%H:%M</code>")
            if sp_user_data["subscription"] == "admin":
                subscription_text = "🖥 <b>Subscription</b>: <code>Admin</code>\n" \
                                    f"     ├─ 📅 <b>Expire:</b> {expire_text}"
            elif sp_user_data["subscription"] == "friend":
                subscription_text = "👑 <b>Subscription</b>: <code>Friend</code>\n" \
                                    f"     ├─ 📅 <b>Expire:</b> {expire_text}"
            elif sp_user_data["subscription"] == "premium":
                subscription_text = "💎 <b>Subscription</b>: <code>Premium</code>\n" \
                                    f"     ├─ 📅 <b>Expire:</b> {expire_text}"
            elif sp_user_data["subscription"] == "standard":
                subscription_text = "🔹 <b>Subscription</b>: <code>Standard</code>\n" \
                                    f"     ├─ 📅 <b>Expire:</b> {expire_text}"
            elif sp_user_data["subscription"] == "trial":
                subscription_text = "🆓 <b>Subscription</b>: <code>Trial</code>\n" \
                                    f"     ├─ 📅 <b>Expire:</b> {expire_text}"
            else:
                subscription_text = "❌ <b>Subscription</b>: <code>None</code>"
        else:
            subscription_text = "❌ <b>Subscription</b>: <code>None</code>"
    else:
        keyboard = await create_menu_keyboard()
        subscription_text = "❌ <b>Subscription</b>: <code>None</code>"
    await message.answer("📊 <u>Statistic:</u>\n"
                         f"👤 <b>User ID</b>: <code>{user_data['user_id']}</code>\n"
                         f"{subscription_text}\n"
                         f"✅ <b>Successful shifted:</b> ~<code>{user_data['shifted_shifts']}</code>\n"
                         f"🕐 <b>Shifted hours</b>: ~<code>{user_data['shifted_hours']}</code>\n"
                         f"💰 <b>Earned with this bot</b>: ~<code>{user_data['earned']}</code> zł",
                         reply_markup=keyboard, parse_mode="HTML")
    db_connect.close()


@router.message(Text(text="♻️ Update shifts"))
async def update_shifts(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    keyboard = await create_update_shifts_keyboard()
    await message.answer("⏳ Select an action", reply_markup=keyboard)


@router.message(Text(text="💳️ Buy subscription"))
async def buy_subscription(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"],
                               database="users_db")
    user_data = db.users_get_user(conn=db_connect, user_id=message.from_user.id)
    if user_data["sp_uid"]:
        db_connect.connect(database="sp_users_db")
        sp_user_data = db.sp_users_sub_info(conn=db_connect, sp_uid=user_data["sp_uid"])
        keyboard = await create_subscriptions_keyboard(sp_user_data=sp_user_data)
        await message.answer("💳 Available plans", reply_markup=keyboard)
    else:
        keyboard = await create_subscriptions_keyboard()
        await message.answer("💳 Available plans", reply_markup=keyboard)
    db_connect.close()


@router.callback_query()
async def change_config(call: types.CallbackQuery) -> None:
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"],
                               database="users_db")
    user_data = db.users_get_user(conn=db_connect, user_id=call.from_user.id)
    db_connect.connect(database="sp_users_db")
    sp_user_data = db.sp_users_sub_info(conn=db_connect, sp_uid=user_data["sp_uid"])
    sp_user_subscription = sp_user_data["subscription"]
    if call.data == "prog_status" or call.data == "prog_open_shifts" or call.data == "prog_shift_offers":
        db_connect.connect(database="users_db")
        db.users_configs_update_user(conn=db_connect, user_id=call.from_user.id,
                                     **{call.data: not bool(user_data[call.data])})
        updated_user_data = db.users_get_user(conn=db_connect, user_id=call.from_user.id)
        keyboard = await create_settings_keyboard(user_data=updated_user_data)
        await call.message.edit_text("🚦Settings:", reply_markup=keyboard)
        await call.answer()
    elif sp_user_subscription == 'premium' or sp_user_subscription == "friend" or sp_user_subscription == "admin":
        db_connect.connect(database="users_db")
        if call.data == "prog_news":
            db.users_configs_update_user(conn=db_connect, user_id=call.from_user.id,
                                         **{call.data: not bool(user_data[call.data])})
            updated_user_data = db.users_get_user(conn=db_connect, user_id=call.from_user.id)
            keyboard = await create_settings_keyboard(user_data=updated_user_data)
            await call.message.edit_text("🚦Settings:", reply_markup=keyboard)
            await call.answer()
        else:
            if user_data["prog_sleep"] == 5.0:
                db.users_configs_update_user(conn=db_connect, user_id=call.from_user.id,
                                             **{call.data: 1.0})
            elif user_data["prog_sleep"] == 1.0:
                db.users_configs_update_user(conn=db_connect, user_id=call.from_user.id,
                                             **{call.data: 0.3})
            elif user_data["prog_sleep"] == 0.3:
                db.users_configs_update_user(conn=db_connect, user_id=call.from_user.id,
                                             **{call.data: 5.0})
            updated_user_data = db.users_get_user(conn=db_connect, user_id=call.from_user.id)
            keyboard = await create_settings_keyboard(user_data=updated_user_data)
            await call.message.edit_text("🚦Settings:", reply_markup=keyboard)
            await call.answer()
    else:
        await call.answer(text="💎 Only for premium subscription!")
    db_connect.close()