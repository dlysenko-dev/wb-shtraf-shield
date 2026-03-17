"""Wildberries API client for fetching financial reports with penalties."""

import logging
from datetime import datetime, timedelta

import aiohttp

from config import WB_STATS_BASE, WB_REPORT_ENDPOINT, REPORT_LOOKBACK_DAYS, APPEAL_DAYS

logger = logging.getLogger(__name__)


class WBApiError(Exception):
    """WB API error."""
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(f"WB API {status}: {message}")


async def fetch_penalties(api_key: str, date_from: str | None = None) -> list[dict]:
    """Fetch penalty entries from WB financial report.

    Uses /api/v5/supplier/reportDetailByPeriod — returns all operations
    including penalties. We filter for rows where penalty > 0.

    Args:
        api_key: WB Statistics API key
        date_from: Start date (YYYY-MM-DD). Defaults to REPORT_LOOKBACK_DAYS ago.

    Returns:
        List of penalty dicts with normalized fields.

    Raises:
        WBApiError: on API errors (401, 429, 500, etc.)
    """
    if not date_from:
        date_from = (datetime.now() - timedelta(days=REPORT_LOOKBACK_DAYS)).strftime("%Y-%m-%d")

    date_to = datetime.now().strftime("%Y-%m-%d")

    url = f"{WB_STATS_BASE}{WB_REPORT_ENDPOINT}"
    headers = {"Authorization": api_key}
    params = {"dateFrom": date_from, "dateTo": date_to}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            if resp.status == 401:
                raise WBApiError(401, "Неверный API-ключ или ключ без доступа к статистике")
            if resp.status == 429:
                raise WBApiError(429, "Слишком много запросов, попробуйте позже")
            if resp.status != 200:
                text = await resp.text()
                raise WBApiError(resp.status, text[:200])

            data = await resp.json()

    if not isinstance(data, list):
        return []

    penalties = []
    for row in data:
        penalty_amount = row.get("penalty", 0)
        if not penalty_amount or penalty_amount <= 0:
            continue

        # Calculate appeal deadline
        penalty_date = row.get("rr_dt", "") or row.get("order_dt", "")
        appeal_deadline = ""
        if penalty_date:
            try:
                pd = datetime.strptime(penalty_date[:10], "%Y-%m-%d")
                appeal_deadline = (pd + timedelta(days=APPEAL_DAYS)).strftime("%Y-%m-%d")
            except ValueError:
                pass

        penalties.append({
            "rrd_id": row.get("rrd_id"),
            "srid": str(row.get("srid", row.get("rrd_id", ""))),
            "penalty_date": penalty_date[:10] if penalty_date else "",
            "amount": penalty_amount,
            "reason": row.get("bonus_type_name", "") or row.get("supplier_oper_name", "Штраф"),
            "supply_id": row.get("gi_id"),
            "nm_id": row.get("nm_id"),
            "brand_name": row.get("brand_name", ""),
            "sa_name": row.get("sa_name", ""),
            "subject_name": row.get("subject_name", ""),
            "appeal_deadline": appeal_deadline,
        })

    logger.info(f"WB API: fetched {len(data)} operations, {len(penalties)} penalties")
    return penalties


async def validate_api_key(api_key: str) -> bool:
    """Check if WB API key is valid by making a lightweight request.

    Returns True if key works, False otherwise.
    """
    url = f"{WB_STATS_BASE}{WB_REPORT_ENDPOINT}"
    headers = {"Authorization": api_key}
    # Request just 1 day to minimize response size
    today = datetime.now().strftime("%Y-%m-%d")
    params = {"dateFrom": today, "dateTo": today}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                return resp.status == 200
    except Exception:
        return False
