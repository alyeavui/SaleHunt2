import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
import asyncpg
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DB_URL = os.getenv("PG_LINK")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

db_pool = None

async def create_db_pool():
    global db_pool
    db_pool = await asyncpg.create_pool(DB_URL)

async def on_startup():
    await create_db_pool()

lang_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🇰🇿 Қазақша"), KeyboardButton(text="🇷🇺 Русский"), KeyboardButton(text="🇺🇸 English")]
    ],
    resize_keyboard=True
)

categories = {
    "Қазақша": ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍 Жеңілдіктер санаттары")],
            [KeyboardButton(text="📍 Көмек"), KeyboardButton(text="🔙 Артқа")]
        ],
        resize_keyboard=True
    ),
    "Русский": ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍 Категории скидок")],
            [KeyboardButton(text="📍 Помощь"), KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    ),
    "English": ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍 Discount Categories")],
            [KeyboardButton(text="📍 Help"), KeyboardButton(text="🔙 Back")]
        ],
        resize_keyboard=True
    )
}

discount_categories = {
    "Қазақша": ["🍔 Еда", "🏋️ Спорт", "👕 Одежда", "🔙 Артқа"],
    "Русский": ["🍔 Еда", "🏋️ Спорт", "👕 Одежда", "🔙 Назад"],
    "English": ["🍔 Food", "🏋️ Sports", "👕 Clothing", "🔙 Back"]
}

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("Выберите язык / Тілді таңдаңыз / Choose a language:", reply_markup=lang_keyboard)

@dp.message(F.text.in_(["🇰🇿 Қазақша", "🇷🇺 Русский", "🇺🇸 English"]))
async def language_handler(message: types.Message):
    lang_map = {
        "🇰🇿 Қазақша": "Қазақша",
        "🇷🇺 Русский": "Русский",
        "🇺🇸 English": "English"
    }
    selected_lang = lang_map[message.text]  
    await message.answer("Выберите категорию / Санатты таңдаңыз / Choose a category:", reply_markup=categories[selected_lang])

@dp.message(F.text.in_(["🛍 Жеңілдіктер санаттары", "🛍 Категории скидок", "🛍 Discount Categories"]))
async def discount_handler(message: types.Message):
    lang_map = {
        "🛍 Жеңілдіктер санаттары": "Қазақша",
        "🛍 Категории скидок": "Русский",
        "🛍 Discount Categories": "English"
    }
    selected_lang = lang_map[message.text]
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=cat)] for cat in discount_categories[selected_lang]],
        resize_keyboard=True
    )
    await message.answer("Выберите подкатегорию скидок:", reply_markup=keyboard)

@dp.message(F.text.in_(sum(discount_categories.values(), [])))
async def discount_subcategory_handler(message: types.Message):
    if not db_pool:
        await message.answer("Ошибка: нет соединения с базой данных.")
        return
    
    subcategory = message.text
    async with db_pool.acquire() as conn:
        discounts = await conn.fetch("SELECT name, discount, link FROM discounts WHERE category = $1", subcategory)
    
    if discounts:
        response = "\n\n".join([f"<b>{d['name']}</b>\nСкидка: {d['discount']}%\n<a href='{d['link']}'>Подробнее</a>" for d in discounts])
    else:
        response = "В этой категории пока нет скидок."

    await message.answer(response, disable_web_page_preview=True)

@dp.message(F.text.in_(["📍 Көмек", "📍 Помощь", "📍 Help"]))
async def help_handler(message: types.Message):
    await message.answer("Для получения информации о скидках выберите категорию и подкатегорию. Если у вас есть вопросы, обратитесь к администратору.")

@dp.message(F.text.in_(["🔙 Артқа", "🔙 Назад", "🔙 Back"]))
async def back_handler(message: types.Message):
    lang_map = {
        "🔙 Артқа": "Қазақша",
        "🔙 Назад": "Русский",
        "🔙 Back": "English"
    }
    selected_lang = lang_map[message.text]
    await message.answer("Выберите категорию / Санатты таңдаңыз / Choose a category:", reply_markup=categories[selected_lang])

async def main():
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main() )