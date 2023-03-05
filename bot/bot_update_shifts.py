# Version 3.1.0 release

import asyncio
import configparser
import mysql.connector as mysql
from aiogram import Router, types
from aiogram.filters import Text
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from bot_keyboards import create_menu_keyboard, create_ds_keyboard, create_years_keyboard, create_months_keyboard
from bot_keyboards import create_days_keyboard, create_hours_keyboard
from tools import config_data, db, work_data

router = Router()


class UpdateShifts(StatesGroup):
    waiting_for_ds = State()
    waiting_for_year = State()
    waiting_for_month = State()
    waiting_for_day = State()
    waiting_for_hours = State()


@router.message(Text(text="♻️ Update shifts"))
async def update_shifts(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"])
    user_data = db.users_get_user(conn=db_connect, user_id=message.from_user.id)
    if user_data["sp_uid"]:
        sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
        keyboard = await create_ds_keyboard(sp_user_data["shifts"])
        await message.answer("♻️ Please select the DS where you would like to set or cancel auto-shifting",
                             reply_markup=keyboard, parse_mode="HTML")
        await state.set_state(UpdateShifts.waiting_for_ds)
    else:
        keyboard = await create_menu_keyboard()
        await message.answer("🚫 You aren't authorized! For a login, use a special button or /auth command",
                             reply_markup=keyboard)
    db_connect.close()


@router.callback_query(UpdateShifts.waiting_for_ds)
async def update_shifts_ds(call: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.update_data(ds=call.data)
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"])
    user_data = db.users_get_user(conn=db_connect, user_id=call.from_user.id)
    sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
    keyboard = await create_years_keyboard(user_shifts=sp_user_data["shifts"],
                                           ds_name=call.data)
    try:
        await call.message.edit_text("♻️ Now select auto-shifting year for current DS", reply_markup=keyboard)
        await state.set_state(UpdateShifts.waiting_for_year)
    except TelegramBadRequest:
        pass
    await call.answer()
    db_connect.close()


@router.callback_query(UpdateShifts.waiting_for_year)
async def update_shifts_year(call: types.CallbackQuery, state: FSMContext) -> None:
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"])
    user_data = db.users_get_user(conn=db_connect, user_id=call.from_user.id)
    sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
    state_data = await state.get_data()
    if call.data != "step_back":
        await state.update_data(year=call.data)
        keyboard = await create_months_keyboard(user_shifts=sp_user_data["shifts"],
                                                ds_name=state_data["ds"], year=call.data)
        try:
            await call.message.edit_text("♻️ Now select month", reply_markup=keyboard)
            await state.set_state(UpdateShifts.waiting_for_month)
        except TelegramBadRequest:
            pass
        await call.answer()
    else:
        keyboard = await create_ds_keyboard(user_shifts=sp_user_data["shifts"])
        try:
            await call.message.edit_text("♻️ Please select the DS where you would like to set or cancel auto-shifting",
                                         reply_markup=keyboard)
            await state.set_state(UpdateShifts.waiting_for_ds)
        except TelegramBadRequest:
            pass
        await call.answer()
    db_connect.close()


@router.callback_query(UpdateShifts.waiting_for_month)
async def update_shifts_month(call: types.CallbackQuery, state: FSMContext) -> None:
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"])
    user_data = db.users_get_user(conn=db_connect, user_id=call.from_user.id)
    sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
    state_data = await state.get_data()
    if call.data != "step_back":
        await state.update_data(month=call.data)
        keyboard = await create_days_keyboard(user_shifts=sp_user_data["shifts"],
                                              ds_name=state_data["ds"], year=state_data["year"],
                                              month=call.data)
        try:
            await call.message.edit_text("♻️ Select day", reply_markup=keyboard)
            await state.set_state(UpdateShifts.waiting_for_day)
        except TelegramBadRequest:
            pass
        await call.answer()
    else:
        keyboard = await create_years_keyboard(user_shifts=sp_user_data["shifts"], ds_name=state_data["ds"])
        try:
            await call.message.edit_text("♻️ Now select auto-shifting year for current DS", reply_markup=keyboard)
            await state.set_state(UpdateShifts.waiting_for_year)
        except TelegramBadRequest:
            pass
        await call.answer()
    db_connect.close()


@router.callback_query(UpdateShifts.waiting_for_day)
async def update_shifts_day(call: types.CallbackQuery, state: FSMContext) -> None:
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"])
    user_data = db.users_get_user(conn=db_connect, user_id=call.from_user.id)
    sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
    state_data = await state.get_data()
    if call.data != "step_back":
        await state.update_data(day=call.data)
        keyboard = await create_hours_keyboard(user_shifts=sp_user_data["shifts"],
                                               ds_name=state_data["ds"], year=state_data["year"],
                                               month=state_data["month"], day=call.data)
        try:
            await call.message.edit_text("♻️ Now click on hours couple to set/unset auto-shifting time",
                                         reply_markup=keyboard)
            await state.set_state(UpdateShifts.waiting_for_hours)
        except TelegramBadRequest:
            pass
        await call.answer()
    else:
        keyboard = await create_months_keyboard(user_shifts=sp_user_data["shifts"],
                                                ds_name=state_data["ds"], year=state_data["year"])
        try:
            await call.message.edit_text("♻️ Now select month", reply_markup=keyboard)
            await state.set_state(UpdateShifts.waiting_for_month)
        except TelegramBadRequest:
            pass
        await call.answer()
    db_connect.close()


@router.callback_query(UpdateShifts.waiting_for_hours)
async def update_shifts_hours(call: types.CallbackQuery, state: FSMContext) -> None:
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"])
    user_data = db.users_get_user(conn=db_connect, user_id=call.from_user.id)
    sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
    state_data = await state.get_data()
    if call.data != "step_back":
        if call.data == "select_all":
            composed_data = f"{state_data['ds']}/" \
                            f"{state_data['day']}.{state_data['month']}.{state_data['year']}/" \
                            f"07:00-11:00/11:00-15:00/15:00-19:00/19:00-23:30/19:00-00:30_add"
        elif call.data == "deselect_all":
            composed_data = f"{state_data['ds']}/" \
                            f"{state_data['day']}.{state_data['month']}.{state_data['year']}/" \
                            f"07:00-11:00/11:00-15:00/15:00-19:00/19:00-23:30/19:00-00:30_remove"
        else:
            composed_data = f"{state_data['ds']}/" \
                            f"{state_data['day']}.{state_data['month']}.{state_data['year']}/" \
                            f"{call.data}"
        composed_data_fragments = composed_data.split("_")
        shift = composed_data_fragments[0]
        action = composed_data_fragments[1]
        if sp_user_data["prog_status"]:
            # pause program
            db.sp_users_configs_update_user(conn=db_connect, sp_uid=user_data["sp_uid"], prog_status=False)
            await call.message.edit_text("🌀 Please wait, update in progress")
            await asyncio.sleep(sp_user_data["prog_sleep"] * 1.5)
            # update shifts
            if action == "add":
                work_data.add_days(conn=db_connect, sp_uid=user_data["sp_uid"], days=shift)
            elif action == "remove":
                work_data.remove_days(conn=db_connect, sp_uid=user_data["sp_uid"], days=shift)
            # unpause program
            db.sp_users_configs_update_user(conn=db_connect, sp_uid=user_data["sp_uid"], prog_status=True)
        else:
            # update shifts
            if action == "add":
                work_data.add_days(conn=db_connect, sp_uid=user_data["sp_uid"], days=shift)
            elif action == "remove":
                work_data.remove_days(conn=db_connect, sp_uid=user_data["sp_uid"], days=shift)
        sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
        keyboard = await create_hours_keyboard(user_shifts=sp_user_data["shifts"],
                                               ds_name=state_data["ds"], year=state_data["year"],
                                               month=state_data["month"], day=state_data["day"])
        try:
            await call.message.edit_text("♻️ Now click on hours couple to set/unset auto-shifting time",
                                         reply_markup=keyboard)
            await state.set_state(UpdateShifts.waiting_for_hours)
        except TelegramBadRequest:
            pass
        await call.answer()
    else:
        keyboard = await create_days_keyboard(user_shifts=sp_user_data["shifts"],
                                              ds_name=state_data["ds"], year=state_data["year"],
                                              month=state_data["month"])
        try:
            await call.message.edit_text("♻️ Select day", reply_markup=keyboard)
            await state.set_state(UpdateShifts.waiting_for_day)
        except TelegramBadRequest:
            pass
        await call.answer()
    db_connect.close()
