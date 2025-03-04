import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, 
    InlineKeyboardButton, InputMediaPhoto
)
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
import asyncpg
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN", "7731456763:AAECo25LUH8lNgv5a2-dvwYIjvj0-k6UZIY")
DB_URL = os.getenv("PG_LINK", "postgresql://postgres:1234@localhost:5432/salehunt")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

db_pool = None

class FeedbackStates(StatesGroup):
    waiting_for_feedback = State()

async def create_db_pool():
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(DB_URL)
        logging.info("Successfully connected to the database")
        
        async with db_pool.acquire() as conn:
            table_exists = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'feedback')"
            )
            
            if not table_exists:
                await conn.execute('''
                CREATE TABLE feedback (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    username TEXT,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                logging.info("Created feedback table")
                
    except Exception as e:
        logging.error(f"Database connection error: {e}")
        raise

async def on_startup():
    await create_db_pool()
    logging.info("Bot started")

lang_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🇰🇿 Қазақша"), KeyboardButton(text="🇷🇺 Русский"), KeyboardButton(text="🇺🇸 English")]
    ],
    resize_keyboard=True
)

messages = {
    "kz": {
        "choose_category": "Керекті батырманы таңдаңыз:",
        "choose_subcategory": "Санатты таңдаңыз:",
        "no_discounts": "Бұл санатта жеңілдіктер жоқ.",
        "help_intro": "Сұрағыңызды немесе пікіріңізді жазыңыз. Біз сізге жауап береміз.",
        "feedback_sent": "Сіздің пікіріңіз жіберілді. Рахмет!",
        "of": "/",  
        "discount_text": "Жеңілдік",
        "more_info": "Толығырақ"
    },
    "ru": {
        "choose_category": "Выберите нужную кнопку:",
        "choose_subcategory": "Выберите категорию:",
        "no_discounts": "В этой категории пока нет скидок.",
        "help_intro": "Напишите ваш вопрос или отзыв. Мы ответим вам в ближайшее время.",
        "feedback_sent": "Ваш отзыв отправлен. Спасибо!",
        "of": "из",  
        "discount_text": "Скидка",
        "more_info": "Подробнее"
    },
    "en": {
        "choose_category": "Choose a needed button:",
        "choose_subcategory": "Choose a category:",
        "no_discounts": "There are no discounts in this category yet.",
        "help_intro": "Write your question or feedback. We will reply to you soon.",
        "feedback_sent": "Your feedback has been sent. Thank you!",
        "of": "of", 
        "discount_text": "Discount",
        "more_info": "More info"
    }
}

categories = {
    "kz": ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍️ Жеңілдіктер санаттары")],
            [KeyboardButton(text="📍 Көмек"), KeyboardButton(text="🔙 Артқа")]
        ],
        resize_keyboard=True
    ),
    "ru": ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍️ Категории скидок")],
            [KeyboardButton(text="📍 Помощь"), KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    ),
    "en": ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍️ Discount Categories")],
            [KeyboardButton(text="📍 Help"), KeyboardButton(text="🔙 Back")]
        ],
        resize_keyboard=True
    )
}

discount_categories = {
    "kz": [
        ["🥗 Тамақ", "Food"],
        ["👕 Киім", "Clothes"],
        ["🏋🏻‍♀️ Спорт", "Sport"],
        ["🔙 Артқа", "Back"]
    ],
    "ru": [
        ["🥗 Еда", "Food"],
        ["👕 Одежда", "Clothes"],
        ["🏋🏻‍♀️ Спорт", "Sport"],
        ["🔙 Назад", "Back"]
    ],
    "en": [
        ["🥗 Food", "Food"],
        ["👕 Clothes", "Clothes"],
        ["🏋🏻‍♀️ Sport", "Sport"],
        ["🔙 Back", "Back"]
    ]
}

user_galleries = {}

@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    await state.clear()
    
    try:
        async with db_pool.acquire() as conn:
            user_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM users WHERE telegram_id = $1)",
                message.from_user.id
            )
            
            if not user_exists:
                await conn.execute(
                    "INSERT INTO users (username, telegram_id) VALUES ($1, $2)",
                    message.from_user.username or "unknown", message.from_user.id
                )
                logging.info(f"New user registered: {message.from_user.id}")
    except Exception as e:
        logging.error(f"Error registering user: {e}")
    
    await message.answer("Выберите язык / Тілді таңдаңыз / Choose a language:", reply_markup=lang_keyboard)

@dp.message(F.text.in_(["🇰🇿 Қазақша", "🇷🇺 Русский", "🇺🇸 English"]))
async def language_handler(message: types.Message, state: FSMContext):
    lang_map = {
        "🇰🇿 Қазақша": "kz",
        "🇷🇺 Русский": "ru",
        "🇺🇸 English": "en"
    }
    
    selected_lang = lang_map[message.text]
    
    await state.update_data(language=selected_lang)
    
    await message.answer(messages[selected_lang]["choose_category"], reply_markup=categories[selected_lang])

@dp.message(F.text.in_(["🛍️ Жеңілдіктер санаттары", "🛍️ Категории скидок", "🛍️ Discount Categories"]))
async def discount_categories_handler(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("language", "ru") 
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=cat[0])] for cat in discount_categories[lang]],
        resize_keyboard=True
    )
    
    await message.answer(messages[lang]["choose_subcategory"], reply_markup=keyboard)

@dp.message(F.text.in_(["🔙 Артқа", "🔙 Назад", "🔙 Back"]))
async def back_handler(message: types.Message, state: FSMContext):
    lang_map = {
        "🔙 Артқа": "kz",
        "🔙 Назад": "ru",
        "🔙 Back": "en"
    }
    
    current_state = await state.get_state()
    user_data = await state.get_data()
    selected_lang = lang_map.get(message.text, user_data.get("language", "ru"))
    
    await state.clear()
    await state.update_data(language=selected_lang)
    
    if current_state == FeedbackStates.waiting_for_feedback.state:
        await message.answer(messages[selected_lang]["choose_category"], reply_markup=categories[selected_lang])
    else:
        await message.answer("Выберите язык / Тілді таңдаңыз / Choose a language:", reply_markup=lang_keyboard)

@dp.message(lambda message: any(message.text == cat[0] for lang in discount_categories for cat in discount_categories[lang]))
async def discount_subcategory_handler(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("language", "ru") 
    
    back_buttons = {"kz": "🔙 Артқа", "ru": "🔙 Назад", "en": "🔙 Back"}
    if message.text == back_buttons[lang]:
        await back_handler(message, state)
        return
    
    category_db = None
    for cat in discount_categories[lang]:
        if message.text == cat[0]:
            category_db = cat[1] 
            break
    
    if not category_db or not db_pool:
        await message.answer("Произошла ошибка при получении данных.")
        return
    
    user_id = message.from_user.id
    
    try:
        async with db_pool.acquire() as conn:
            discounts = await conn.fetch(
                """
                SELECT id, name, discount, link, image_url 
                FROM discounts 
                WHERE category = $1
                ORDER BY id
                """, 
                category_db
            )
    except Exception as e:
        logging.error(f"Database error when fetching discounts: {e}")
        await message.answer("Произошла ошибка при получении данных.")
        return
    
    if not discounts:
        await message.answer(messages[lang]["no_discounts"])
        return
    
    user_galleries[user_id] = {
        "discounts": discounts,
        "current_index": 0,
        "lang": lang
    }
    
    await show_discount_gallery(message.chat.id, user_id)

async def show_discount_gallery(chat_id, user_id):
    if user_id not in user_galleries:
        await bot.send_message(chat_id, "Произошла ошибка. Попробуйте выбрать категорию заново.")
        return
    
    gallery = user_galleries[user_id]
    discounts = gallery["discounts"]
    current_index = gallery["current_index"]
    lang = gallery["lang"]
    
    if not discounts:
        await bot.send_message(chat_id, messages[lang]["no_discounts"])
        return
    
    discount = discounts[current_index]
    
    caption = (
        f"<b>{discount['name']}</b>\n"
        f"{messages[lang]['discount_text']}: {discount['discount']}%\n"
        f"<a href='{discount['link']}'>{messages[lang]['more_info']}</a>"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="◀️", callback_data=f"prev_{current_index}"),
            InlineKeyboardButton(text=f"{current_index + 1} {messages[lang]['of']} {len(discounts)}", callback_data="count"),
            InlineKeyboardButton(text="▶️", callback_data=f"next_{current_index}")
        ]
    ])
    
    image_url = discount.get('image_url')
    if image_url:
        try:
            await bot.send_photo(
                chat_id=chat_id,
                photo=image_url,
                caption=caption,
                reply_markup=keyboard
            )
        except Exception as e:
            logging.error(f"Error sending photo: {e}")
            await bot.send_message(
                chat_id=chat_id,
                text=f"{caption}\n\n(Ошибка загрузки изображения)",
                reply_markup=keyboard
            )
    else:
        await bot.send_message(
            chat_id=chat_id,
            text=caption,
            reply_markup=keyboard
        )

@dp.callback_query(lambda query: query.data.startswith(("prev_", "next_")))
async def process_gallery_buttons(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    if user_id not in user_galleries:
        await callback_query.answer("Данные устарели. Выберите категорию заново.")
        return
    
    gallery = user_galleries[user_id]
    discounts = gallery["discounts"]
    current_index = gallery["current_index"]
    
    if callback_query.data.startswith("prev_"):
        gallery["current_index"] = (current_index - 1) % len(discounts)
    elif callback_query.data.startswith("next_"):
        gallery["current_index"] = (current_index + 1) % len(discounts)
    
    await show_discount_gallery(callback_query.message.chat.id, user_id)
    
    try:
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    except Exception as e:
        logging.error(f"Error deleting message: {e}")
    
    await callback_query.answer()

@dp.message(F.text.in_(["📍 Көмек", "📍 Помощь", "📍 Help"]))
async def help_handler(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("language", "ru")
    
    await state.set_state(FeedbackStates.waiting_for_feedback)
    
    back_button = {"kz": "🔙 Артқа", "ru": "🔙 Назад", "en": "🔙 Back"}[lang]
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=back_button)]],
        resize_keyboard=True
    )
    
    await message.answer(messages[lang]["help_intro"], reply_markup=keyboard)

@dp.message(FeedbackStates.waiting_for_feedback)
async def process_feedback(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("language", "ru")
    
    back_buttons = {"kz": "🔙 Артқа", "ru": "🔙 Назад", "en": "🔙 Back"}
    if message.text == back_buttons[lang]:
        await back_handler(message, state)
        return
    
    user_id = message.from_user.id
    username = message.from_user.username
    feedback_text = message.text
    
    try:
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO feedback (user_id, username, message)
                VALUES ($1, $2, $3)
                """,
                user_id, username, feedback_text
            )
    except Exception as e:
        logging.error(f"Error saving feedback: {e}")
    
    try:
        async with db_pool.acquire() as conn:
            admins = await conn.fetch("SELECT admin_id FROM admins")
            
            for admin in admins:
                admin_id = admin['admin_id']
                admin_notification = (
                    f"Новый отзыв от пользователя:\n"
                    f"ID: {user_id}\n"
                    f"Username: @{username or 'нет'}\n"
                    f"Сообщение: {feedback_text}"
                )
                
                try:
                    await bot.send_message(chat_id=admin_id, text=admin_notification)
                except Exception as e:
                    logging.error(f"Error sending notification to admin {admin_id}: {e}")
    except Exception as e:
        logging.error(f"Error fetching admins: {e}")
    
    await message.answer(messages[lang]["feedback_sent"], reply_markup=categories[lang])
    
    await state.clear()
    await state.update_data(language=lang)

@dp.message()
async def unknown_message(message: types.Message, state: FSMContext):
    await message.answer("Выберите язык / Тілді таңдаңыз / Choose a language:", reply_markup=lang_keyboard)

async def main():
    try:
        await on_startup()
        await dp.start_polling(bot)
    except Exception as e:
        logging.critical(f"Critical error: {e}")
    finally:
        if db_pool:
            await db_pool.close()

if __name__ == "__main__":
    asyncio.run(main())