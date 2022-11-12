# Version 2.2.2 release

import configparser
import json
import mysql.connector as mysql
import requests
from aiogram import Router, types
from aiogram.filters import Command, Text
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from mysql.connector import CMySQLConnection

import config_data
import db
from bot_keyboards import *

router = Router()


class Authorization(StatesGroup):
    waiting_for_email = State()
    waiting_for_password = State()


async def authorization(conn: CMySQLConnection, user_id: int, email: str, password: str = None, token: str = None) -> bool:
    if token:
        response = requests.get("https://shyftplan.com/api/v1/employments/my",
                                params={"user_email": email,
                                        "authentication_token": token})
        if "error" not in response.text:
            return True
        else:
            return False
    elif password:
        response = requests.post("https://shyftplan.com/api/v1/login",
                                 data={"user[email]": email,
                                       "user[password]": password})
        json_items = json.loads(response.text)
        if "authentication_token" in json_items:
            token = json_items["authentication_token"]
            response = requests.get("https://shyftplan.com/api/v1/employments/my",
                                    params={"user_email": email,
                                            "authentication_token": token})
            json_items = json.loads(response.text)
            sp_eid = json_items["items"][0]["id"]
            sp_uid = json_items["items"][0]["user_id"]
            db.users_configs_update_user(conn=conn, user_id=user_id,
                                         sp_email=email, sp_token=token, sp_eid=sp_eid, sp_uid=sp_uid)
            conn.connect(database="sp_users_db")
            db.sp_users_add_user(conn=conn, sp_uid=sp_uid)
            conn.connect(database="users_db")
            return True
        else:
            return False


@router.message(Command(commands=["auth"]))
async def auth(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"],
                               database="users_db")
    user_data = db.users_get_user(conn=db_connect, user_id=message.from_user.id)
    shyftplan_email = user_data["sp_email"]
    shyftplan_token = user_data["sp_token"]
    if not shyftplan_email or not shyftplan_token:
        await message.answer("🔐 Please enter your shyftplan email", reply_markup=ReplyKeyboardRemove())
        await state.set_state(Authorization.waiting_for_email)
    else:
        if await authorization(conn=db_connect,
                               user_id=message.from_user.id, email=shyftplan_email, token=shyftplan_token):
            db_connect.connect(database="sp_users_db")
            sp_user_data = db.sp_users_sub_info(conn=db_connect, sp_uid=user_data["sp_uid"])
            keyboard = await create_menu_keyboard(sp_user_data=sp_user_data)
            await message.answer("🔓 You are already authorized", reply_markup=keyboard)
            keyboard = await create_settings_keyboard(user_data=user_data)
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
                               password=db_data["password"],
                               database="users_db")
    user_data = db.users_get_user(conn=db_connect, user_id=message.from_user.id)
    db_connect.close()
    shyftplan_email = user_data["sp_email"]
    shyftplan_token = user_data["sp_token"]
    if not shyftplan_email or not shyftplan_token:
        await message.answer("🔐 You aren't authorized. Please enter your shyftplan email",
                             reply_markup=ReplyKeyboardRemove())
        await state.set_state(Authorization.waiting_for_email)
    else:
        if await authorization(conn=db_connect,
                               user_id=message.from_user.id, email=shyftplan_email, token=shyftplan_token):
            keyboard = await create_settings_keyboard(user_data=user_data)
            await message.answer("🚦Settings:", reply_markup=keyboard)
        else:
            await message.answer("🔐 Your data is outdated. Please authorize again, enter your shyftplan email",
                                 reply_markup=ReplyKeyboardRemove())
            await state.set_state(Authorization.waiting_for_email)


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
                               password=db_data["password"],
                               database="users_db")
    if await authorization(conn=db_connect,
                           user_id=message.from_user.id, email=auth_data["email"], password=auth_data["password"]):
        user_data = db.users_get_user(conn=db_connect, user_id=message.from_user.id)
        db_connect.connect(database="sp_users_db")
        sp_user_data = db.sp_users_sub_info(conn=db_connect, sp_uid=user_data["sp_uid"])
        keyboard = await create_menu_keyboard(sp_user_data=sp_user_data)
        await message.answer("🔓 Good, you are authorized successfully!", reply_markup=keyboard)
        keyboard = await create_settings_keyboard(user_data=user_data)
        await message.answer("🚦Settings:", reply_markup=keyboard)
    else:
        keyboard = await create_menu_keyboard()
        await message.answer("🔒 Unfortunately email or password isn't correct. Try again using /auth command",
                             reply_markup=keyboard)
    db_connect.close()
    await state.clear()
