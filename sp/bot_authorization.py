# Version 2.1.0 release

import configparser
import json
import requests
from aiogram import F, Router, types
from aiogram.filters import Command, Text
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

import config_data
from bot_keyboards import *


admins = {1630691291}
admins.add(config_data.get_user(configparser.ConfigParser())["telegram_id"])
router = Router()


class Authorization(StatesGroup):
    waiting_for_email = State()
    waiting_for_password = State()


async def authorization(config: ConfigParser, email: str, password: str = None, token: str = None) -> bool:
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
            employee_id = str(json_items["items"][0]["id"])
            user_id = str(json_items["items"][0]["user_id"])
            config.read("settings.ini")
            config.set("AUTH_CONFIG", "shyftplan_email", email)
            config.set("AUTH_CONFIG", "shyftplan_token", token)
            config.set("AUTH_CONFIG", "shyftplan_employee_id", employee_id)
            config.set("AUTH_CONFIG", "shyftplan_user_id", user_id)
            with open("settings.ini", 'w') as configfile:
                config.write(configfile)
            return True
        else:
            return False


@router.message(Command(commands=["auth"]), F.from_user.id.in_(admins))
async def auth(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    user_data = config_data.get_user(configparser.ConfigParser())
    shyftplan_email = user_data["shyftplan_email"]
    shyftplan_token = user_data["shyftplan_token"]
    if shyftplan_email == "None" or shyftplan_token == "None":
        await message.answer("🔐 Please enter your program email", reply_markup=ReplyKeyboardRemove())
        await state.set_state(Authorization.waiting_for_email)
    else:
        if await authorization(config=configparser.ConfigParser(), email=shyftplan_email, token=shyftplan_token):
            keyboard = await create_menu_keyboard()
            await message.answer("🔓 You are already authorized", reply_markup=keyboard)
            keyboard = await create_settings_keyboard(configparser.ConfigParser())
            await message.answer("🚦Settings:", reply_markup=keyboard)
        else:
            await message.answer("🔐 Please enter your program email", reply_markup=ReplyKeyboardRemove())
            await state.set_state(Authorization.waiting_for_email)


@router.message(Text(text="⚙️ Settings"), F.from_user.id.in_(admins))
async def settings(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    user_data = config_data.get_user(configparser.ConfigParser())
    shyftplan_email = user_data["shyftplan_email"]
    shyftplan_token = user_data["shyftplan_token"]
    if shyftplan_email == "None" or shyftplan_token == "None":
        await message.answer("🔐 Hey, I see that you aren't authorized. Please enter your program email",
                             reply_markup=ReplyKeyboardRemove())
        await state.set_state(Authorization.waiting_for_email)
    else:
        if await authorization(config=configparser.ConfigParser(), email=shyftplan_email, token=shyftplan_token):
            keyboard = await create_settings_keyboard(configparser.ConfigParser())
            await message.answer("🚦Settings:",
                                 reply_markup=keyboard)
        else:
            await message.answer("🔐 Your data is outdated. Please authorize again, enter your program email",
                                 reply_markup=ReplyKeyboardRemove())
            await state.set_state(Authorization.waiting_for_email)


@router.message(Authorization.waiting_for_email)
async def email_waiting(message: types.Message, state: FSMContext) -> None:
    await state.update_data(email=message.text)
    await message.answer("🔐 Now enter your program password", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Authorization.waiting_for_password)


@router.message(Authorization.waiting_for_password)
async def password_waiting(message: types.Message, state: FSMContext) -> None:
    await state.update_data(password=message.text)
    config = configparser.ConfigParser()
    auth_data = await state.get_data()
    keyboard = await create_menu_keyboard()
    if await authorization(config=config, email=auth_data["email"], password=auth_data["password"]):
        await message.answer("🔓 Good, you are authorized successfully",
                             reply_markup=keyboard)
        keyboard = await create_settings_keyboard(config)
        await message.answer("🚦Settings:",
                             reply_markup=keyboard)
    else:
        await message.answer("🔒 Unfortunately email or password isn't correct. Try again using /auth command",
                             reply_markup=keyboard)
    await state.clear()
