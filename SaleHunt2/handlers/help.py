from aiogram import Router, F
from aiogram.types import Message
from db_handler.db_class import PostgresHandler

help_router = Router()
db = PostgresHandler()

@help_router.message(F.text == "Help")
async def help_section(message: Message):
    await message.answer("Please describe your issue. We will get back to you soon.")

@help_router.message()
async def collect_feedback(message: Message):
    await db.save_feedback(message.from_user.id, message.text)
    await message.answer("Thank you! Your feedback has been sent.")
