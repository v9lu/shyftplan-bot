# Version 2.5.0 release

import aiohttp
import configparser
import mysql.connector as mysql
import pytz
from aiogram import Router, types
from aiogram.filters import Command, Text
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from datetime import datetime, timedelta
from mysql.connector import MySQLConnection

from bot_keyboards import create_menu_keyboard, create_settings_keyboard
from tools import config_data
from tools import db

router = Router()


class Authorization(StatesGroup):
    waiting_for_email = State()
    waiting_for_password = State()


async def authorization(conn: MySQLConnection, user_id: int,
                        email: str, password: str = None, token: str = None) -> bool:
    async with aiohttp.ClientSession() as session:
        if token:
            async with session.get("https://shyftplan.com/api/v1/employments/my",
                                   params={"user_email": email,
                                           "authentication_token": token}
                                   ) as response:
                if response.status == 200:
                    return True
                else:
                    return False
        elif password:
            async with session.post("https://shyftplan.com/api/v1/login",
                                    data={"user[email]": email,
                                          "user[password]": password}
                                    ) as response:
                json_response = await response.json()
            if response.status == 201:
                token = json_response["authentication_token"]
                params = {
                    "user_email": email,
                    "authentication_token": token
                }
                async with session.get("https://shyftplan.com/api/v1/employments/my", params=params) as response:
                    json_response = await response.json()
                sp_eid = json_response["items"][0]["id"]
                sp_uid = json_response["items"][0]["user_id"]

                # Editing params
                timezone = pytz.timezone("Europe/Warsaw")
                trusted_loc_pos_ids = [170251, 170258, 170254  # Warsaw
                                       ]  # Gdansk
                params["page"], params["per_page"] = 1, 1
                params["starts_at"] = timezone.localize(datetime.now()).isoformat()
                params["ends_at"] = timezone.localize(datetime.now() + timedelta(days=2)).isoformat()
                params["locations_position_ids[]"] = trusted_loc_pos_ids

                async with session.get("https://shyftplan.com/api/v1/shifts", params=params) as response:
                    json_response = await response.json()
                if json_response["total"]:
                    is_trusted = True
                else:
                    is_trusted = False
                db.users_auth_update_user(
                    conn=conn,
                    user_id=user_id,
                    sp_email=email,
                    sp_token=token,
                    sp_eid=sp_eid,
                    sp_uid=sp_uid,
                    trusted=is_trusted
                )
                db.sp_users_add_user(conn=conn, sp_uid=sp_uid)
                return True
            else:
                return False


@router.message(Command(commands=["auth"]))
@router.message(Text(text="🔐️ Login Shyftplan"))
async def auth(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"])
    user_data = db.users_get_user(conn=db_connect, user_id=message.from_user.id)
    shyftplan_email = user_data["sp_email"]
    shyftplan_token = user_data["sp_token"]
    if not shyftplan_email or not shyftplan_token:
        await message.answer("🔐 Please enter your shyftplan email", reply_markup=ReplyKeyboardRemove())
        await state.set_state(Authorization.waiting_for_email)
    else:
        if await authorization(conn=db_connect,
                               user_id=message.from_user.id, email=shyftplan_email, token=shyftplan_token):
            sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
            keyboard = await create_menu_keyboard(sp_user_data=sp_user_data)
            await message.answer("🔓 You are already authorized", reply_markup=keyboard)
            keyboard = await create_settings_keyboard(sp_user_data=sp_user_data)
            await message.answer("🚦Settings:", reply_markup=keyboard)
        else:
            await message.answer("🔐 Please enter your shyftplan email", reply_markup=ReplyKeyboardRemove())
            await state.set_state(Authorization.waiting_for_email)
    db_connect.close()


@router.message(Text(text="⚙️ Settings"))
async def settings(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"])
    user_data = db.users_get_user(conn=db_connect, user_id=message.from_user.id)
    shyftplan_email = user_data["sp_email"]
    shyftplan_token = user_data["sp_token"]
    if not shyftplan_email or not shyftplan_token:
        await message.answer("🔐 You aren't authorized. Please enter your shyftplan email",
                             reply_markup=ReplyKeyboardRemove())
        await state.set_state(Authorization.waiting_for_email)
    else:
        if await authorization(conn=db_connect,
                               user_id=message.from_user.id, email=shyftplan_email, token=shyftplan_token):
            sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
            keyboard = await create_settings_keyboard(sp_user_data=sp_user_data)
            await message.answer("🚦Settings:", reply_markup=keyboard)
        else:
            await message.answer("🔐 Your data is outdated. Please authorize again, enter your shyftplan email",
                                 reply_markup=ReplyKeyboardRemove())
            await state.set_state(Authorization.waiting_for_email)
    db_connect.close()


@router.message(Authorization.waiting_for_email)
async def email_waiting(message: types.Message, state: FSMContext) -> None:
    await state.update_data(email=message.text)
    await message.answer("🔐 Now enter your shyftplan password", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Authorization.waiting_for_password)


@router.message(Authorization.waiting_for_password)
async def password_waiting(message: types.Message, state: FSMContext) -> None:
    await state.update_data(password=message.text)
    auth_data = await state.get_data()
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"])
    if await authorization(conn=db_connect,
                           user_id=message.from_user.id, email=auth_data["email"], password=auth_data["password"]):
        user_data = db.users_get_user(conn=db_connect, user_id=message.from_user.id)
        sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
        keyboard = await create_menu_keyboard(sp_user_data=sp_user_data)
        await message.answer("🔓 Good, you are authorized successfully!", reply_markup=keyboard)
        keyboard = await create_settings_keyboard(sp_user_data=sp_user_data)
        await message.answer("🚦Settings:", reply_markup=keyboard)
    else:
        keyboard = await create_menu_keyboard()
        await message.answer("🔒 Unfortunately email or password isn't correct. Try again using /auth command",
                             reply_markup=keyboard)
    await state.clear()
    db_connect.close()
