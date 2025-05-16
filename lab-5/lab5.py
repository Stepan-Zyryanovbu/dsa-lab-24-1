import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
import logging
import os
import psycopg2
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

logging.basicConfig(level=logging.INFO)

# Подключение к БД
dsn = "dbname='lab-5' user='postgres' password='5522369' host='localhost'"
conn = psycopg2.connect(dsn)
conn.autocommit = True

bot_token = os.getenv("API_TOKEN")
if not bot_token:
    raise ValueError("Переменная окружения API_TOKEN не найдена")

bot = Bot(token=bot_token)
dp = Dispatcher(storage=MemoryStorage())

rates = {}

# Состояния для команды /convert
class ConvertStates(StatesGroup):
    waiting_for_currency_name = State()
    waiting_for_amount = State()

# Состояния для управления валютами (админ)
class ManageStates(StatesGroup):
    choosing_action = State()
    adding_currency_name = State()
    adding_currency_rate = State()
    deleting_currency = State()
    updating_currency_name = State()
    updating_currency_rate = State()

async def is_admin(chat_id: int) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM admins WHERE chat_id = %s", (str(chat_id),))
        return cur.fetchone() is not None

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! Я бот efmkna.\n"
        "Для получения меню команд отправьте /menu"
    )

@dp.message(Command("menu"))
async def menu(message: types.Message):
    user_chat_id = str(message.from_user.id)
    admin_flag = await is_admin(user_chat_id)

    if admin_flag:
        commands_list = [
            "/start — стартовое сообщение",
            "/manage_currency — управление валютами",
            "/get_currencies — показать все валюты",
            "/convert — конвертация валюты в рубли"
        ]
    else:
        commands_list = [
            "/start — стартовое сообщение",
            "/get_currencies — показать все валюты",
            "/convert — конвертация валюты в рубли"
        ]

    text = "Доступные команды:\n" + "\n".join(commands_list)
    await message.answer(text)

# --- Команда /manage_currency (только для админов) ---
@dp.message(Command("manage_currency"))
async def manage_currency(message: types.Message, state: FSMContext):
    user_chat_id = str(message.from_user.id)
    if not await is_admin(user_chat_id):
        await message.answer("Нет доступа к команде")
        return

    buttons = [
        [KeyboardButton(text="Добавить валюту")],
        [KeyboardButton(text="Удалить валюту")],
        [KeyboardButton(text="Изменить курс валюты")]
    ]

    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer("Выберите действие:", reply_markup=keyboard)
    await state.set_state(ManageStates.choosing_action)

@dp.message(ManageStates.choosing_action)
async def handle_manage_choice(message: types.Message, state: FSMContext):
    action = message.text.lower()

    if action == "добавить валюту":
        await message.answer("Введите название валюты:")
        await state.set_state(ManageStates.adding_currency_name)
    elif action == "удалить валюту":
        await message.answer("Введите название валюты:")
        await state.set_state(ManageStates.deleting_currency)
    elif action == "изменить курс валюты":
        await message.answer("Введите название валюты:")
        await state.set_state(ManageStates.updating_currency_name)
    else:
        await message.answer("Пожалуйста, выберите одно из предложенных действий.")

@dp.message(ManageStates.adding_currency_name)
async def handle_add_currency_name(message: types.Message, state: FSMContext):
    currency = message.text.upper()
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM currencies WHERE currency_name = %s", (currency,))
        if cur.fetchone():
            await message.answer("Данная валюта уже существует.")
            await state.clear()
            return
    await state.update_data(currency_name=currency)
    await message.answer("Введите курс валюты к рублю:")
    await state.set_state(ManageStates.adding_currency_rate)

@dp.message(ManageStates.adding_currency_rate)
async def handle_add_currency_rate(message: types.Message, state: FSMContext):
    try:
        rate = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Ошибка! Введите корректное число.")
        return

    data = await state.get_data()
    currency = data["currency_name"]

    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO currencies (currency_name, rate) VALUES (%s, %s)",
            (currency, rate)
        )

    rates[currency] = rate
    await message.answer(f"Валюта: {currency} успешно добавлена.")
    await state.clear()

@dp.message(ManageStates.deleting_currency)
async def handle_delete_currency(message: types.Message, state: FSMContext):
    currency = message.text.upper()

    with conn.cursor() as cur:
        cur.execute("DELETE FROM currencies WHERE currency_name = %s", (currency,))
        if cur.rowcount == 0:
            await message.answer("Такой валюты нет.")
        else:
            rates.pop(currency, None)
            await message.answer(f"Валюта {currency} удалена.")

    await state.clear()

@dp.message(ManageStates.updating_currency_name)
async def handle_update_currency_name(message: types.Message, state: FSMContext):
    currency = message.text.upper()
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM currencies WHERE currency_name = %s", (currency,))
        if not cur.fetchone():
            await message.answer("Валюта не найдена.")
            await state.clear()
            return

    await state.update_data(currency_name=currency)
    await message.answer("Введите курс валюты к рублю:")
    await state.set_state(ManageStates.updating_currency_rate)

@dp.message(ManageStates.updating_currency_rate)
async def handle_update_currency_rate(message: types.Message, state: FSMContext):
    try:
        rate = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Ошибка! Введите корректное число.")
        return

    data = await state.get_data()
    currency = data["currency_name"]

    with conn.cursor() as cur:
        cur.execute(
            "UPDATE currencies SET rate = %s WHERE currency_name = %s",
            (rate, currency)
        )

    rates[currency] = rate
    await message.answer(f"Курс валюты {currency} обновлён.")
    await state.clear()

# --- Команда /get_currencies ---
@dp.message(Command("get_currencies"))
async def get_currencies(message: types.Message):
    with conn.cursor() as cur:
        cur.execute("SELECT currency_name, rate FROM currencies ORDER BY currency_name")
        rows = cur.fetchall()

    if not rows:
        await message.answer("Список валют пуст.")
        return

    response_lines = [f"{name}: {rate:.4f} руб." for name, rate in rows]
    response = "Список сохраненных валют с курсом к рублю:\n" + "\n".join(response_lines)

    await message.answer(response)

# --- Команда /convert ---
@dp.message(Command("convert"))
async def convert_start(message: types.Message, state: FSMContext):
    await message.answer("Введите название валюты:")
    await state.set_state(ConvertStates.waiting_for_currency_name)

@dp.message(ConvertStates.waiting_for_currency_name)
async def convert_currency_name(message: types.Message, state: FSMContext):
    currency = message.text.upper()
    rate = rates.get(currency)
    if rate is None:
        with conn.cursor() as cur:
            cur.execute("SELECT rate FROM currencies WHERE currency_name = %s", (currency,))
            row = cur.fetchone()
            if row:
                rate = float(row[0])
                rates[currency] = rate

    if rate is None:
        await message.answer(
            "Ошибка! Валюта не найдена. Сначала сохраните курс с помощью /manage_currency (для админов)."
        )
        await state.clear()
        return

    await state.update_data(currency_name=currency)
    await message.answer(f"Введите сумму в валюте {currency}:")
    await state.set_state(ConvertStates.waiting_for_amount)

@dp.message(ConvertStates.waiting_for_amount)
async def convert_amount(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    currency = user_data["currency_name"]
    rate = rates.get(currency, 0)

    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Ошибка! Введите корректное число.")
        return

    converted = amount * rate
    await message.answer(
        f"{amount:.2f} {currency} = {converted:.2f} руб."
    )
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
