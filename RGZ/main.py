from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove
from datetime import datetime
import psycopg2
import requests
import asyncio
import logging
import os

API_TOKEN = os.getenv("API_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# Database connection
def get_connection():
    return psycopg2.connect(dbname="rgzrpp", user="postgres", password="5522369", host="localhost")

# FSM States
class RegState(StatesGroup):
    waiting_for_login = State()

class AddOperationState(StatesGroup):
    waiting_for_type = State()
    waiting_for_sum = State()
    waiting_for_date = State()

class OperationViewState(StatesGroup):
    waiting_for_currency = State()
    waiting_for_type_filter = State()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! 👋\n"
        "Я бот для учета финансовых операций.\n\n"
        "📌 Используй команды:\n"
        "/reg – регистрация\n"
        "/add_operation – добавить операцию\n"
        "/operations – посмотреть операции"
    )


# Registration
@router.message(Command("reg"))
async def register_user(message: Message, state: FSMContext):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE chat_id = %s", (message.chat.id,))
    if cur.fetchone():
        await message.answer("Вы уже зарегистрированы.")
        cur.close()
        conn.close()
        return
    await message.answer("Введите ваш логин:")
    await state.set_state(RegState.waiting_for_login)
    cur.close()
    conn.close()

@router.message(RegState.waiting_for_login)
async def process_login(message: Message, state: FSMContext):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (name, chat_id) VALUES (%s, %s)", (message.text, message.chat.id))
    conn.commit()
    cur.close()
    conn.close()
    await message.answer("Вы успешно зарегистрированы!")
    await state.clear()

# Add operation
@router.message(Command("add_operation"))
async def add_operation(message: Message, state: FSMContext):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE chat_id = %s", (message.chat.id,))
    if not cur.fetchone():
        await message.answer("Вы не зарегистрированы. Используйте команду /reg.")
        cur.close()
        conn.close()
        return
    cur.close()
    conn.close()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ДОХОД", callback_data="INCOME"),
         InlineKeyboardButton(text="РАСХОД", callback_data="EXPENSE")]
    ])
    await message.answer("Выберите тип операции:", reply_markup=kb)
    await state.set_state(AddOperationState.waiting_for_type)

@router.callback_query(AddOperationState.waiting_for_type)
async def choose_type(callback: CallbackQuery, state: FSMContext):
    await state.update_data(type_operation=callback.data)
    await callback.message.answer("Введите сумму операции:")
    await state.set_state(AddOperationState.waiting_for_sum)
    await callback.answer()

@router.message(AddOperationState.waiting_for_sum)
async def input_sum(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Введите корректную сумму.")
        return
    await state.update_data(sum=amount)
    await message.answer("Введите дату операции в формате ГГГГ-ММ-ДД:")
    await state.set_state(AddOperationState.waiting_for_date)

@router.message(AddOperationState.waiting_for_date)
async def input_date(message: Message, state: FSMContext):
    try:
        date = datetime.strptime(message.text, "%Y-%m-%d").date()
    except ValueError:
        await message.answer("Неверный формат даты. Пример: 2024-12-31")
        return
    user_data = await state.get_data()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO operations (date, sum, chat_id, type_operation)
        VALUES (%s, %s, %s, %s)
    """, (date, user_data["sum"], message.chat.id, user_data["type_operation"]))
    conn.commit()
    cur.close()
    conn.close()
    await message.answer("Операция успешно добавлена!")
    await state.clear()

# View operations
@router.message(Command("operations"))
async def view_operations(message: Message, state: FSMContext):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE chat_id = %s", (message.chat.id,))
    if not cur.fetchone():
        await message.answer("Вы не зарегистрированы. Используйте команду /reg.")
        cur.close()
        conn.close()
        return
    cur.close()
    conn.close()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="RUB", callback_data="RUB"),
            InlineKeyboardButton(text="USD", callback_data="USD"),
            InlineKeyboardButton(text="EUR", callback_data="EUR")
        ]
    ])
    await message.answer("Выберите валюту:", reply_markup=kb)
    await state.set_state(OperationViewState.waiting_for_currency)

@router.callback_query(OperationViewState.waiting_for_currency)
async def process_currency(callback: CallbackQuery, state: FSMContext):
    await state.update_data(currency=callback.data)
    type_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="ВСЕ", callback_data="ALL"),
            InlineKeyboardButton(text="ДОХОДНЫЕ ОПЕРАЦИИ", callback_data="INCOME"),
            InlineKeyboardButton(text="РАСХОДНЫЕ ОПЕРАЦИИ", callback_data="EXPENSE"),
        ]
    ])
    await callback.message.answer("Выберите тип операций для вывода:", reply_markup=type_kb)
    await state.set_state(OperationViewState.waiting_for_type_filter)
    await callback.answer()

@router.callback_query(OperationViewState.waiting_for_type_filter)
async def process_operation_filter(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    currency = user_data["currency"]
    op_type = callback.data
    chat_id = callback.message.chat.id

    conn = get_connection()
    cur = conn.cursor()

    if op_type == "ALL":
        cur.execute("""
            SELECT date, sum, type_operation FROM operations
            WHERE chat_id = %s ORDER BY date DESC;
        """, (chat_id,))
    else:
        cur.execute("""
            SELECT date, sum, type_operation FROM operations
            WHERE chat_id = %s AND type_operation = %s ORDER BY date DESC;
        """, (chat_id, op_type))

    operations = cur.fetchall()
    cur.close()
    conn.close()

    if not operations:
        await callback.message.answer("Нет операций по выбранному типу.")
        await state.clear()
        await callback.answer()
        return

    if currency != "RUB":
        try:
            response = requests.get(f"http://localhost:5000/rate?currency={currency}")
            if response.status_code == 200:
                rate = response.json().get("rate")
            else:
                await callback.message.answer(f"Ошибка получения курса: {response.json().get('message')}")
                await state.clear()
                await callback.answer()
                return
        except Exception:
            await callback.message.answer("Ошибка при обращении к серверу курса.")
            await state.clear()
            await callback.answer()
            return
    else:
        rate = 1.0

    msg = f"Операции ({op_type if op_type != 'ALL' else 'ВСЕ'}) в валюте {currency}:\n\n"
    for date, amount, typ in operations:
        converted = round(float(amount) / rate, 2)
        msg += f"📅 {date}, 💰 {converted} {currency}, 📌 {typ}\n"

    await callback.message.answer(msg)
    await state.clear()
    await callback.answer()

# Запуск
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
