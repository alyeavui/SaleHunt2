from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Language Selection
language_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="English")],
        [KeyboardButton(text="Русский")],
        [KeyboardButton(text="Қазақша")]
    ],
    resize_keyboard=True
)

# English Menu
english_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Discount Categories")],
        [KeyboardButton(text="Help")],
        [KeyboardButton(text="Back")]
    ],
    resize_keyboard=True
)

# Russian Menu
russian_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Категории скидок")],
        [KeyboardButton(text="Помощь")],
        [KeyboardButton(text="Назад")]
    ],
    resize_keyboard=True
)

# Kazakh Menu
kazakh_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Жеңілдіктер санаттары")],
        [KeyboardButton(text="Көмек")],
        [KeyboardButton(text="Артқа")]
    ],
    resize_keyboard=True
)
