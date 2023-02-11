# Version 1.0.0 release

import configparser
import mysql.connector as mysql
from aiogram import Bot, Router, types
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import Text
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from bot_keyboards import *
from tools import config_data
from tools import db

router = Router()


class Newsletter(StatesGroup):
    waiting_for_news_text = State()


async def send_news(bot: Bot, users_ids: list, news_text: str) -> None:
    for user_id in users_ids:
        try:
            await bot.send_message(user_id, news_text, parse_mode="HTML")
            print("[GOOD, SENDED] ID:", user_id)
        except TelegramForbiddenError:
            print("[BAD, BOT WAS BLOCKED] ID:", user_id)


@router.message(Text(text="✉️ Newsletter"))
async def newsletter(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"])
    user_data = db.users_get_user(conn=db_connect, user_id=message.from_user.id)
    if user_data["sp_uid"]:
        sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
        if sp_user_data["subscription"] == "admin":
            keyboard = await create_menu_button_keyboard()
            await message.answer("✉️ Now enter the text to send", reply_markup=keyboard)
            await state.set_state(Newsletter.waiting_for_news_text)
    db_connect.close()


@router.message(Newsletter.waiting_for_news_text)
async def news_text_waiting(message: types.Message, state: FSMContext, bot: Bot) -> None:
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"])
    users_ids = db.users_get_users_ids(conn=db_connect)
    await send_news(bot=bot, users_ids=users_ids, news_text=message.html_text)
    await state.clear()
    db_connect.close()
