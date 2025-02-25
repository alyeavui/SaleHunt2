from aiogram import Router, types
from aiogram.filters import Command
from keyboards.all_keyboards import language_keyboard, english_menu, russian_menu, kazakh_menu

start_router = Router()

# /start command handler
@start_router.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("Choose language:", reply_markup=language_keyboard)

# Language selection handler
@start_router.message()
async def handle_menu_selection(message: types.Message):
    if message.text == "English":
        await message.answer("You selected English.", reply_markup=english_menu)
    elif message.text == "Русский":
        await message.answer("Вы выбрали русский.", reply_markup=russian_menu)
    elif message.text == "Қазақша":
        await message.answer("Сіз қазақ тілін таңдадыңыз.", reply_markup=kazakh_menu)
    elif message.text in ["Back", "Назад", "Артқа"]: 
        await message.answer("Choose language:", reply_markup=language_keyboard)
