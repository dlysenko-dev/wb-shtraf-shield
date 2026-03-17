"""Penalty history and stats handlers."""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

import db
from keyboards import back_to_menu
from utils import format_penalty_row, format_stats

router = Router()


@router.message(Command("penalties"))
@router.callback_query(F.data == "penalties")
async def show_penalties(event: Message | CallbackQuery):
    user_id = event.from_user.id
    penalties = await db.get_user_penalties(user_id, limit=15)

    if not penalties:
        text = "Штрафов пока не обнаружено.\n\nМониторинг работает — как только появится штраф, вы получите уведомление."
    else:
        lines = ["<b>Последние штрафы:</b>\n"]
        for i, p in enumerate(penalties, 1):
            lines.append(format_penalty_row(p, i))
        text = "\n".join(lines)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, parse_mode="HTML", reply_markup=back_to_menu())
        await event.answer()
    else:
        await event.answer(text, parse_mode="HTML", reply_markup=back_to_menu())


@router.message(Command("stats"))
@router.callback_query(F.data == "stats")
async def show_stats(event: Message | CallbackQuery):
    user_id = event.from_user.id
    stats = await db.get_user_penalty_stats(user_id)
    stores = await db.get_user_stores(user_id)

    text = format_stats(stats)
    text += f"\n\nАктивных магазинов: {len(stores)}"

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, parse_mode="HTML", reply_markup=back_to_menu())
        await event.answer()
    else:
        await event.answer(text, parse_mode="HTML", reply_markup=back_to_menu())
