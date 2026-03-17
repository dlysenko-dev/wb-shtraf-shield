"""Utility functions — formatters, helpers."""

from datetime import datetime


def format_penalty_alert(penalty: dict, store_name: str = "") -> str:
    """Format a penalty into a Telegram alert message (HTML)."""
    amount = penalty.get("amount", 0)
    reason = penalty.get("reason", "Не указана")
    penalty_date = penalty.get("penalty_date", "—")
    appeal_deadline = penalty.get("appeal_deadline", "—")
    supply_id = penalty.get("supply_id", "—")
    nm_id = penalty.get("nm_id", "—")
    sa_name = penalty.get("sa_name", "")
    brand_name = penalty.get("brand_name", "")
    subject_name = penalty.get("subject_name", "")

    store_line = f"\nМагазин: <b>{store_name}</b>" if store_name else ""

    product_info = ""
    if sa_name:
        product_info += f"\nАртикул: <code>{sa_name}</code>"
    if nm_id and nm_id != "—":
        product_info += f"\nNM ID: <code>{nm_id}</code>"
    if brand_name:
        product_info += f"\nБренд: {brand_name}"
    if subject_name:
        product_info += f"\nТовар: {subject_name}"

    # Days left for appeal
    days_left = ""
    if appeal_deadline and appeal_deadline != "—":
        try:
            dl = datetime.strptime(appeal_deadline, "%Y-%m-%d")
            delta = (dl - datetime.now()).days
            if delta > 0:
                days_left = f" ({delta} дн. осталось)"
            elif delta == 0:
                days_left = " (СЕГОДНЯ!)"
            else:
                days_left = " (ПРОСРОЧЕН)"
        except ValueError:
            pass

    return (
        f"<b>ШТРАФ {amount:,.0f} руб.</b>\n"
        f"{'=' * 24}{store_line}\n"
        f"Причина: {reason}\n"
        f"Дата: {penalty_date}\n"
        f"Поставка: <code>{supply_id}</code>"
        f"{product_info}\n\n"
        f"Дедлайн обжалования: <b>{appeal_deadline}</b>{days_left}\n\n"
        f"Обжалуйте в ЛК WB: Финансы - Штрафы"
    )


def format_penalty_row(penalty: dict, index: int = 0) -> str:
    """Short penalty line for list view."""
    amount = penalty.get("amount", 0)
    date = penalty.get("penalty_date", "—")
    reason = penalty.get("reason", "")[:30]
    return f"{index}. {date} — <b>{amount:,.0f} руб.</b> ({reason})"


def format_stats(stats: dict) -> str:
    """Format penalty statistics."""
    return (
        "<b>Статистика штрафов</b>\n\n"
        f"Всего штрафов: {stats['total_count']}\n"
        f"Общая сумма: <b>{stats['total_amount']:,.0f} руб.</b>\n"
        f"За 30 дней: <b>{stats['month_amount']:,.0f} руб.</b>\n"
        f"За 7 дней: <b>{stats['week_amount']:,.0f} руб.</b>"
    )


def mask_api_key(key: str) -> str:
    """Mask API key for display: show first 8 and last 4 chars."""
    if len(key) <= 12:
        return key[:4] + "..." + key[-2:]
    return key[:8] + "..." + key[-4:]
