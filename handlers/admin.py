"""Admin handlers — stats, subscription management, broadcast."""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

import db
from config import ADMIN_IDS, PRO_STORES_LIMIT, PRO_PRICE_RUB
from keyboards import back_to_menu, subscription_kb

router = Router()


# --- Subscription (user-facing) ---

@router.callback_query(F.data == "subscription")
async def show_subscription(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    plan = user.get("subscription", "free") if user else "free"
    until = user.get("subscription_until", "") if user else ""
    limit = user.get("stores_limit", 1) if user else 1

    if plan == "pro":
        text = (
            f"<b>Подписка: PRO</b>\n"
            f"Магазинов: до {limit}\n"
            f"Действует до: {until or 'бессрочно'}"
        )
    else:
        text = (
            f"<b>Подписка: Бесплатная</b>\n"
            f"Магазинов: {limit}\n\n"
            f"<b>PRO — {PRO_PRICE_RUB} руб/мес:</b>\n"
            f"• До {PRO_STORES_LIMIT} магазинов\n"
            f"• Приоритетная проверка\n"
            f"• Поддержка в чате"
        )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=subscription_kb())
    await callback.answer()


@router.callback_query(F.data == "pay_pro")
async def pay_pro(callback: CallbackQuery):
    await callback.message.edit_text(
        f"<b>Оплата PRO — {PRO_PRICE_RUB} руб/мес</b>\n\n"
        "Переведите на карту/СБП и отправьте скриншот оплаты.\n"
        "Подписка активируется в течение 1 часа.\n\n"
        "Реквизиты уточняйте у @admin",
        parse_mode="HTML",
        reply_markup=back_to_menu(),
    )
    await callback.answer()


# --- Admin commands ---

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return

    stats = await db.get_bot_stats()
    await message.answer(
        f"<b>Админ-панель</b>\n\n"
        f"Пользователей: {stats['users']}\n"
        f"Магазинов: {stats['stores']}\n"
        f"Штрафов: {stats['penalties']}\n"
        f"PRO подписок: {stats['pro_users']}\n\n"
        f"Команды:\n"
        f"/grant_pro USER_ID — выдать PRO\n"
        f"/revoke_pro USER_ID — отозвать PRO",
        parse_mode="HTML",
    )


@router.message(Command("grant_pro"))
async def cmd_grant_pro(message: Message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /grant_pro USER_ID")
        return

    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer("USER_ID должен быть числом")
        return

    user = await db.get_user(target_id)
    if not user:
        await message.answer(f"Пользователь {target_id} не найден")
        return

    await db.update_subscription(target_id, "pro", None, PRO_STORES_LIMIT)
    await message.answer(f"PRO выдан пользователю {target_id}")


@router.message(Command("revoke_pro"))
async def cmd_revoke_pro(message: Message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /revoke_pro USER_ID")
        return

    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer("USER_ID должен быть числом")
        return

    await db.update_subscription(target_id, "free", None, 1)
    await message.answer(f"PRO отозван у пользователя {target_id}")
