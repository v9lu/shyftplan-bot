# Version 2.0.0 release

import configparser
from aiogram import F, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Text
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

import telegram_data
import work_data
from bot_keyboards import *

owner_data = telegram_data.get(configparser.ConfigParser())
admins = {1630691291}
admins.add(owner_data["account_id"])

router = Router()


class UpdateShifts(StatesGroup):
    waiting_for_shifts_add = State()
    waiting_for_shifts_remove = State()


@router.message(Text(text="📗 Add shifts"), F.from_user.id.in_(admins))
async def add_shifts(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    keyboard = await create_menu_button_keyboard()
    await message.answer("📗 Now enter shifts to add. For example:\n\n"
                         "<i>lekka/15.12.2022/19:00-23:30/19:00-00:30</i>\n"
                         "<i>szarych/16.12.2022/07:00-11:00</i>",
                         reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(UpdateShifts.waiting_for_shifts_add)


@router.message(Text(text="📕 Remove shifts"), F.from_user.id.in_(admins))
async def remove_shifts(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    keyboard = await create_menu_button_keyboard()
    await message.answer("📕 Now enter shifts to remove. For example:\n\n"
                         "<i>lekka/15.12.2022/19:00-23:30/19:00-00:30</i>\n"
                         "<i>szarych/16.12.2022/07:00-11:00</i>",
                         reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(UpdateShifts.waiting_for_shifts_remove)


@router.message(Text(text="📋 My shifts"), F.from_user.id.in_(admins))
async def my_shifts(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    keyboard = await create_update_shifts_keyboard()
    shifts_file = FSInputFile("work_data.txt", "shifts.txt")
    try:
        await message.answer_document(document=shifts_file, caption="📋 This is a list of your shifts",
                                      reply_markup=keyboard)
    except TelegramBadRequest:
        await message.answer("📄 Your list of shifts empty!")


@router.message(UpdateShifts.waiting_for_shifts_add)
@router.message(UpdateShifts.waiting_for_shifts_remove)
async def shifts_waiting(message: types.Message, state: FSMContext) -> None:
    state_name = await state.get_state()
    if state_name == "UpdateShifts:waiting_for_shifts_add":
        work_data.add_days(message.text)
    elif state_name == "UpdateShifts:waiting_for_shifts_remove":
        work_data.remove_days(message.text)
    keyboard = await create_menu_keyboard()
    await message.answer("✅ Shifts updated successful", reply_markup=keyboard)
    await state.clear()
