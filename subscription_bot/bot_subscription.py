# Version 2.0.0 release

from aiogram import F, Router, types
from aiogram.filters import Command, Text, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import LabeledPrice, ReplyKeyboardRemove

import bot_keyboards
import server_db

admins = {1630691291}
STRIPE_TOKEN = "284685063:TEST:OWI2MzFmMjMzMDhh"  # TEST
router = Router()


@router.message(Command(commands=["start"]))
async def bot_start(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    if message.from_user.id in admins:
        await message.answer("🔑 Key generator for admins:\n"
                             "1. Type [standard/premium].\n"
                             "2. Days [15]\n\n"
                             "Example: /key standard 30", reply_markup=ReplyKeyboardRemove())
    else:
        keyboard = await bot_keyboards.create_menu_keyboard()
        await message.answer("💳 This bot was created for you can buy a subscription.\n\n"
                             "Plans:\n\n"
                             "1. 💎 Premium 30 day's\n"
                             "2. 🔹 Standard 30 day's\n"
                             "3. 🆓 Standard 7 day's", reply_markup=keyboard)


@router.message(Command(commands=["key"]), F.from_user.id.in_(admins))
async def keygen(command: CommandObject, state: FSMContext) -> None:
    await state.clear()
    parameters = command.args.split()
    key_type = parameters[0]
    key_days = parameters[1]
    # connect to db
    # add key server_db.add_key()
    # success message

    print(1)


@router.message(Text(text="💎 30 day's premium"))
async def sub_30_prem(message: types.Message, state: FSMContext) -> None:
    await message.answer_invoice(title="📅 30 day subscription (premium)",
                                 description="⚠️ When paying indicate your telegram username to receiver (name) field. "
                                             "Bot works in full automatic mode. In order to prevent account blocking, "
                                             "I'm not recommend to inform someone about purchase of a subscription.",
                                 payload=f"{message.from_user.id}:sub_prem:30d",
                                 provider_token=STRIPE_TOKEN,
                                 currency="PLN",
                                 prices=[LabeledPrice(label="💎 Premium 30 day's", amount=30000)],
                                 max_tip_amount=10000,
                                 suggested_tip_amounts=[500, 1000, 2000],
                                 photo_url="https://i.imgur.com/aNKX0gH.jpeg",
                                 need_name=True)


@router.message(Text(text="🔹 30 day's standard"))
async def sub_30(message: types.Message, state: FSMContext) -> None:
    await message.answer_invoice(title="📅 30 day subscription (standard)",
                                 description="⚠️ When paying indicate your telegram username to receiver (name) field. "
                                             "Bot works in full automatic mode. In order to prevent account blocking, "
                                             "I'm not recommend to inform someone about purchase of a subscription.",
                                 payload=f"{message.from_user.id}:sub_prem:30d",
                                 provider_token=STRIPE_TOKEN,
                                 currency="PLN",
                                 prices=[LabeledPrice(label="🔹 Standard 30 day's", amount=10000)],
                                 max_tip_amount=10000,
                                 suggested_tip_amounts=[500, 1000, 2000],
                                 photo_url="https://i.imgur.com/aNKX0gH.jpeg",
                                 need_name=True)
