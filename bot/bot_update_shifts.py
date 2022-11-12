# Version 2.1.1 release

import configparser
import mysql.connector as mysql
from aiogram import Router, types
from aiogram.filters import Text
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile

import config_data
import db
import work_data
from bot_keyboards import *

router = Router()


class UpdateShifts(StatesGroup):
    waiting_for_shifts_add = State()
    waiting_for_shifts_remove = State()


@router.message(Text(text="📗 Add shifts"))
async def add_shifts(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    keyboard = await create_menu_button_keyboard()
    await message.answer("📗 Now enter shifts to add. For example:\n\n"
                         "<i>lekka/15.12.2022/19:00-23:30/19:00-00:30</i>\n"
                         "<i>szarych/16.12.2022/07:00-11:00</i>",
                         reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(UpdateShifts.waiting_for_shifts_add)


@router.message(Text(text="📕 Remove shifts"))
async def remove_shifts(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    keyboard = await create_menu_button_keyboard()
    await message.answer("📕 Now enter shifts to remove. For example:\n\n"
                         "<i>lekka/15.12.2022/19:00-23:30/19:00-00:30</i>\n"
                         "<i>szarych/16.12.2022/07:00-11:00</i>",
                         reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(UpdateShifts.waiting_for_shifts_remove)


@router.message(Text(text="📋 My shifts"))
async def my_shifts(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"],
                               database="users_db")
    bytes_file = work_data.get_bytes_file(conn=db_connect, user_id=message.from_user.id)
    db_connect.close()
    if bytes_file:
        shifts_file = BufferedInputFile(bytes_file, "shifts.txt")
        await message.answer_document(document=shifts_file, caption="📋 This is a list of your shifts")
    else:
        await message.answer("📄 You have no shifts!")


@router.message(UpdateShifts.waiting_for_shifts_add)
@router.message(UpdateShifts.waiting_for_shifts_remove)
async def shifts_waiting(message: types.Message, state: FSMContext) -> None:
    state_name = await state.get_state()
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"],
                               database="users_db")
    user_data = db.users_get_user(conn=db_connect, user_id=message.from_user.id)
    if state_name == "UpdateShifts:waiting_for_shifts_add":
        work_data.add_days(conn=db_connect, user_id=message.from_user.id, days=message.text)
    elif state_name == "UpdateShifts:waiting_for_shifts_remove":
        work_data.remove_days(conn=db_connect, user_id=message.from_user.id, days=message.text)
    if user_data["sp_uid"]:
        db_connect.connect(database="sp_users_db")
        sp_user_data = db.sp_users_sub_info(conn=db_connect, sp_uid=user_data["sp_uid"])
        keyboard = await create_menu_keyboard(sp_user_data=sp_user_data)
    else:
        keyboard = await create_menu_keyboard()
    db_connect.close()
    await message.answer("✅ Shifts updated successful", reply_markup=keyboard)
    await state.clear()
