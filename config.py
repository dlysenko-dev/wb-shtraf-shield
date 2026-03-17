"""Конфигурация WB Штраф-Щит."""

import os
from pathlib import Path

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

# Database
DB_PATH = os.getenv("DB_PATH", str(Path(__file__).parent / "data" / "bot.db"))

# WB API
WB_STATS_BASE = "https://statistics-api.wildberries.ru"
WB_REPORT_ENDPOINT = "/api/v5/supplier/reportDetailByPeriod"

# Scheduler
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL", "30"))

# Freemium limits
FREE_STORES_LIMIT = 1
PRO_STORES_LIMIT = 20
PRO_PRICE_RUB = 3000

# Appeal deadline (days from penalty date)
APPEAL_DAYS = 7

# Report lookback (days) — how far back to check for penalties
REPORT_LOOKBACK_DAYS = int(os.getenv("REPORT_LOOKBACK_DAYS", "7"))
