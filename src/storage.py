# -*- coding: UTF-8 -*-
"""
    Unit Test Lab
    2025-04-07
    Description:
    
"""

import asyncpg


class StorageDriver:
    def __init__(self, dsn: str):
        self._dsn = dsn
        self._pool = None

    async def connect(self):
        self._pool = await asyncpg.create_pool(self._dsn)

    async def disconnect(self):
        await self._pool.close()

    async def execute(self, query: str, *args):
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(query, *args)

    async def fetchone(self, query: str, *args):
        async with self._pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchall(self, query: str, *args):
        async with self._pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def insert(self, query: str, *args):
        await self.execute(query, *args)

    async def update(self, query: str, *args):
        await self.execute(query, *args)

    async def delete(self, query: str, *args):
        await self.execute(query, *args)


class Storage:
    __TABLE = "es_numeros"

    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self._driver: StorageDriver = StorageDriver(f"postgresql://{user}:{password}@{host}:{port}/{database}")

    async def connect(self):
        await self._driver.connect()

    async def disconnect(self):
        await self._driver.disconnect()

    async def get_users_count(self) -> int:
        query = f"SELECT count(user_id) FROM {self.__TABLE}"
        res = await self._driver.fetchone(query)
        return res[0]

    async def is_user_exists(self, user_id: int) -> bool:
        query = f"SELECT user_id FROM {self.__TABLE} WHERE user_id = $1"
        res = await self._driver.fetchone(query, user_id)
        return res is not None

    async def insert_user(self, user_id: int):
        try:
            query = f"INSERT INTO {self.__TABLE} (user_id) VALUES ($1)"
            await self._driver.insert(query, user_id)
        except asyncpg.PostgresError:
            pass

    async def get_user_level(self, user_id: int) -> int:
        query = f"SELECT level FROM {self.__TABLE} WHERE user_id = $1"
        res = await self._driver.fetchone(query, user_id)
        return res[0] if res else None

    async def increase_user_level(self, user_id: int):
        query = f"UPDATE {self.__TABLE} SET level = level + 1 WHERE user_id = $1"
        await self._driver.update(query, user_id)

    async def decrease_user_level(self, user_id: int):
        query = f"UPDATE {self.__TABLE} SET level = level - 1 WHERE user_id = $1 AND level > 0"
        await self._driver.update(query, user_id)

    async def get_user_stats(self, user_id: int) -> dict | None:
        query = f"SELECT * FROM {self.__TABLE} WHERE user_id = $1"
        res = await self._driver.fetchone(query, user_id)
        return dict(res) if res else None

    async def update_user_stats(self, user_id: int, correct: int, wrong: int):
        query = f"UPDATE {self.__TABLE} SET correct = correct + $1, wrong = wrong + $2 WHERE user_id = $3"
        await self._driver.update(query, correct, wrong, user_id)

    async def clear_user_stats(self, user_id: int):
        query = f"UPDATE {self.__TABLE} SET correct = 0, wrong = 0, level = 0 WHERE user_id = $1"
        await self._driver.delete(query, user_id)
