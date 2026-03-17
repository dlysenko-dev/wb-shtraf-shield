"""WB Штраф-Щит — Telegram bot for Wildberries penalty monitoring.

Entry point: initializes bot, scheduler, and starts polling.
"""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN, CHECK_INTERVAL_MINUTES
from handlers import setup_routers
import db
from checker import check_all_stores

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set. Export it: export BOT_TOKEN=your_token")
        sys.exit(1)

    # Init DB
    await db.init_db()
    logger.info("Database initialized")

    # Bot + Dispatcher
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(setup_routers())

    # Scheduler — check penalties every N minutes
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_all_stores,
        "interval",
        minutes=CHECK_INTERVAL_MINUTES,
        args=[bot],
        id="penalty_checker",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler started: checking every {CHECK_INTERVAL_MINUTES} min")

    # Start polling
    logger.info("Bot starting...")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
