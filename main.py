import asyncio
from dotenv import load_dotenv
from aiogram import Bot

from app.config import load_config
from app.db import DB
from app.bot import build_dispatcher
from app.sweep import sweep_task

async def main():
    load_dotenv()
    cfg = load_config()

    db = DB(cfg.db_path)
    db.init()

    bot = Bot(cfg.bot_token)
    dp = build_dispatcher(bot, cfg, db)

    asyncio.create_task(sweep_task(bot, cfg, db))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
