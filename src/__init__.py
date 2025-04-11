# -*- coding: UTF-8 -*-
"""
    Unit Test Lab
    2025-04-04
    Description:
    
"""

import os
import asyncio

from .tgbot import TgBot

async def main():
    token = os.getenv("BOT_TOKEN")
    host = os.getenv("HOST")
    port = os.getenv("PORT")
    postgres_db = os.getenv("POSTGRES_DB")
    postgres_user = os.getenv("POSTGRES_USER")
    postgres_password = os.getenv("POSTGRES_PASSWORD")
    bot = TgBot(token, host, int(port), postgres_user, postgres_password, postgres_db)
    try:
        await bot.run()
    except asyncio.CancelledError:
        pass
    finally:
        pass
