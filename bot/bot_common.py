# Version 3.1.2 release

import configparser
import mysql.connector as mysql
from aiogram import F, Router, types
from aiogram.filters import Command, Text
from aiogram.fsm.context import FSMContext
from datetime import datetime

from bot_keyboards import create_menu_keyboard, create_subscriptions_keyboard
from tools import config_data, db

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
                               password=db_data["password"])
    db.users_add_user(conn=db_connect, user_id=message.from_user.id)
    user_data = db.users_get_user(conn=db_connect, user_id=message.from_user.id)
    if user_data["sp_uid"]:
        sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
        keyboard = await create_menu_keyboard(sp_user_data=sp_user_data)
        subscription_text = "❌ <b>Subscription</b>: <code>None</code>"
        if sp_user_data["subscription"] and sp_user_data["expire"]:
            if datetime.now() < sp_user_data["expire"]:
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


@router.message(Text(text="💳️ Buy subscription"))
async def buy_subscription(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"])
    user_data = db.users_get_user(conn=db_connect, user_id=message.from_user.id)
    if user_data["sp_uid"]:
        sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
        allocated_subs = config_data.get_subs(config=configparser.ConfigParser())
        subs_count = db.sp_users_get_subs_count(conn=db_connect)
        keyboard = await create_subscriptions_keyboard(sp_user_data=sp_user_data,
                                                       allocated_subs=allocated_subs, sub_counts=subs_count)
        await message.answer("💳 Available plans", reply_markup=keyboard)
    else:
        keyboard = await create_menu_keyboard()
        await message.answer("🚫 You aren't authorized! Use a special button for login or the command /auth",
                             reply_markup=keyboard)
    db_connect.close()


@router.message(F.photo)
async def photo_id(message: types.Message) -> None:
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"])
    user_data = db.users_get_user(conn=db_connect, user_id=message.from_user.id)
    sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
    if sp_user_data["subscription"] == "admin":
        await message.answer_photo(photo=message.photo[-1].file_id,
                                   caption=f"🌄 <b>Photo ID:</b> <code>{message.photo[-1].file_id}</code>",
                                   parse_mode="HTML")
    db_connect.close()
