import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
import asyncpg
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DB_URL = os.getenv("PG_LINK")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

async def create_db_pool():
    return await asyncpg.create_pool(DB_URL)

db_pool = None

async def on_startup():
    global db_pool
    db_pool = await create_db_pool()

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

subcategories = {
    "Жеңілдіктер санаттары": ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🥗 Тамақ"), KeyboardButton(text="👕 Киім"), KeyboardButton(text="🏋🏻‍♀️ Спорт")],
            [KeyboardButton(text="Артқа")]
        ],
        resize_keyboard=True
    ),
    "Категории скидок": ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🥗 Еда"), KeyboardButton(text="👕 Одежда"), KeyboardButton(text="🏋🏻‍♀️ Спорт")],
            [KeyboardButton(text="Назад")]
        ],
        resize_keyboard=True
    ),
    "Discount Categories": ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🥗 Food"), KeyboardButton(text="👕 Clothes"), KeyboardButton(text="🏋🏻‍♀️ Sport")],
            [KeyboardButton(text="Back")]
        ],
        resize_keyboard=True
    )
}

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("Выберите язык / Тілді таңдаңыз / Choose a language:", reply_markup=lang_keyboard)

@dp.message(F.text.in_(categories.keys()))
async def category_handler(message: types.Message):
    await message.answer("Выберите категорию / Санатты таңдаңыз / Choose a category:", reply_markup=categories[message.text])

@dp.message(F.text.in_(subcategories.keys()))
async def subcategory_handler(message: types.Message):
    await message.answer("Выберите подкатегорию / Ішкі санатты таңдаңыз / Choose a subcategory:", reply_markup=subcategories[message.text])

async def get_discounts(category):
    async with db_pool.acquire() as connection:
        return await connection.fetch("SELECT name, discount, link, image_url FROM discounts WHERE category = $1", category)

@dp.message(F.text.in_(["Тамақ", "Киім", "Спорт", "Еда", "Одежда", "Спорт", "Food", "Clothes", "Sport"]))
async def show_discounts(message: types.Message):
    discounts = await get_discounts(message.text)
    if not discounts:
        await message.answer("Нет актуальных скидок.")
        return

    discount = discounts[0] 

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅", callback_data=f"nav_{len(discounts)-1}_{message.text}"),
         InlineKeyboardButton(text="➡", callback_data=f"nav_1_{message.text}")]
    ])

    await message.answer_photo(
        photo=discount["image_url"], 
        caption=f"{discount['name']} - {discount['discount']}%\n<a href='{discount['link']}'>Подробнее</a>",
        reply_markup=keyboard
    )

@dp.callback_query(F.data.startswith("nav_"))
async def navigate_gallery(callback_query: types.CallbackQuery):
    data = callback_query.data.split("_")  
    index = int(data[1])  
    category = data[2]  

    discounts = await get_discounts(category)
    if not discounts:
        await callback_query.answer("Нет актуальных скидок.")
        return

    index = (index + 1) % len(discounts) if "next" in data[0] else (index - 1) % len(discounts)
    
    discount = discounts[index]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅", callback_data=f"nav_{index-1}_{category}"),
         InlineKeyboardButton(text="➡", callback_data=f"nav_{index+1}_{category}")]
    ])

    await callback_query.message.edit_media(
        media=InputMediaPhoto(media=discount["image_url"], caption=f"{discount['name']} - {discount['discount']}%\n<a href='{discount['link']}'>Подробнее</a>"),
        reply_markup=keyboard
    )

async def main():
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
