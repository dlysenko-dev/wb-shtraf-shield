"""Penalty checker — core logic for scheduled penalty monitoring."""

import logging
from datetime import datetime

from aiogram import Bot

import db
from wb_api import fetch_penalties, WBApiError
from utils import format_penalty_alert

logger = logging.getLogger(__name__)


async def check_all_stores(bot: Bot):
    """Check all active stores for new penalties. Called by scheduler."""
    stores = await db.get_all_active_stores()
    logger.info(f"Checking {len(stores)} active stores for penalties")

    for store in stores:
        try:
            await check_store(bot, store)
        except Exception as e:
            logger.error(f"Error checking store {store['id']}: {e}")


async def check_store(bot: Bot, store: dict):
    """Check a single store for new penalties."""
    store_id = store["id"]
    user_id = store["owner_id"]
    api_key = store["api_key"]

    # Use last_check as date_from, or None for default lookback
    date_from = store.get("last_check")
    if date_from:
        # Convert datetime to date string
        date_from = date_from[:10]

    try:
        penalties = await fetch_penalties(api_key, date_from=date_from)
    except WBApiError as e:
        if e.status == 401:
            # Invalid API key — notify user
            await bot.send_message(
                user_id,
                f"API-ключ магазина «{store.get('name', store_id)}» недействителен.\n"
                f"Обновите ключ: /stores",
            )
        logger.warning(f"WB API error for store {store_id}: {e}")
        return

    new_count = 0
    total_amount = 0.0

    for penalty_data in penalties:
        srid = penalty_data.get("srid", "")
        if not srid:
            continue

        # Skip if already in DB
        if await db.penalty_exists(store_id, srid):
            continue

        # Save new penalty
        penalty_id = await db.save_penalty(store_id, penalty_data)
        new_count += 1
        total_amount += penalty_data.get("amount", 0)

        # Send alert
        alert_text = format_penalty_alert(penalty_data, store.get("name", ""))
        try:
            await bot.send_message(user_id, alert_text, parse_mode="HTML")
            await db.mark_penalty_notified(penalty_id)
        except Exception as e:
            logger.error(f"Failed to send alert to {user_id}: {e}")

    # Update last check timestamp
    await db.update_store_last_check(store_id)

    if new_count > 0:
        logger.info(
            f"Store {store_id}: {new_count} new penalties, "
            f"total {total_amount:.0f} RUB"
        )
