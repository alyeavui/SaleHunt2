import asyncpg
from decouple import config

class PostgresHandler:
    def __init__(self, dsn=None):  # Accept an argument
        self.dsn = dsn or config("PG_LINK")  # Use provided DSN or default from .env
        self.pool = None  # Initialize pool as None

    async def connect(self):
        if not self.pool:  # Only connect if not already connected
            self.pool = await asyncpg.create_pool(self.dsn)

    async def get_discounts(self, category):
        async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT * FROM discounts WHERE category = $1", category)

    async def save_feedback(self, user_id, message):
        async with self.pool.acquire() as conn:
            await conn.execute("INSERT INTO feedback (user_id, message) VALUES ($1, $2)", user_id, message)
