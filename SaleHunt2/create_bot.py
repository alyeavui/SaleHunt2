import os
import asyncio
import asyncpg
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv 

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("Bot token is missing! Check your .env file.")

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def init_db():
    return await asyncpg.create_pool(
        dsn=os.getenv("PG_LINK")  
    )

async def main():
    global db_pool
    db_pool = await init_db()
    print("✅ Database connected successfully!")

asyncio.run(main())
