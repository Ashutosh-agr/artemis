import asyncpg
import os
from fastapi import Request
from .config import settings

class Database:
    def __init__(self):
        self.pool = None
        self._connecting = False

    async def connect(self):
        if(self.pool is None):
            self.pool = await asyncpg.create_pool(dsn=settings.DATABASE_URL, min_size=10, max_size=10)
            print("Connected to the database")

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            print("Disconnected from the database")

db = Database()

async def get_db_conn():
    async with db.pool.acquire() as connection:
        yield connection
    

