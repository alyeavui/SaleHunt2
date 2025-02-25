import asyncpg
import os
from dotenv import load_dotenv

load_dotenv("/Users/ayauka/Desktop/SaleHunt2/.env")

DB_URL = os.getenv("PG_LINK")  

if not DB_URL:
    raise ValueError("PG_LINK is not set. Check your .env file!")

async def create_pool():
    return await asyncpg.create_pool(DB_URL)

pg_db = None  

async def init_db():
    global pg_db
    pg_db = await create_pool()  
    print("✅ Database connected successfully!")
