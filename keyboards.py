"""Inline keyboards for the bot."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Мои магазины", callback_data="stores")],
        [InlineKeyboardButton(text="Штрафы", callback_data="penalties"),
         InlineKeyboardButton(text="Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="Подписка", callback_data="subscription")],
    ])


def stores_menu(stores: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for s in stores:
        name = s.get("name") or f"Магазин #{s['id']}"
        buttons.append([InlineKeyboardButton(
            text=f"{name}",
            callback_data=f"store_{s['id']}",
        )])
    buttons.append([InlineKeyboardButton(text="+ Добавить магазин", callback_data="add_store")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def store_detail(store_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Проверить сейчас", callback_data=f"check_{store_id}")],
        [InlineKeyboardButton(text="Удалить магазин", callback_data=f"del_{store_id}")],
        [InlineKeyboardButton(text="Назад", callback_data="stores")],
    ])


def confirm_delete(store_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да, удалить", callback_data=f"confirm_del_{store_id}"),
         InlineKeyboardButton(text="Отмена", callback_data=f"store_{store_id}")],
    ])


def back_to_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Меню", callback_data="menu")],
    ])


def subscription_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить PRO (3000 руб/мес)", callback_data="pay_pro")],
        [InlineKeyboardButton(text="Назад", callback_data="menu")],
    ])
