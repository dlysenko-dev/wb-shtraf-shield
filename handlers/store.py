"""Store management handlers — add, remove, list API keys."""

import logging

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import db
from wb_api import validate_api_key, WBApiError, fetch_penalties
from keyboards import stores_menu, store_detail, confirm_delete, back_to_menu
from utils import mask_api_key, format_penalty_alert
from config import FREE_STORES_LIMIT, PRO_STORES_LIMIT

logger = logging.getLogger(__name__)

router = Router()


class AddStoreStates(StatesGroup):
    waiting_api_key = State()
    waiting_store_name = State()


# --- List stores ---

@router.message(F.text == "/stores")
@router.callback_query(F.data == "stores")
async def show_stores(event: Message | CallbackQuery):
    user_id = event.from_user.id
    stores = await db.get_user_stores(user_id)
    user = await db.get_user(user_id)
    limit = user.get("stores_limit", FREE_STORES_LIMIT) if user else FREE_STORES_LIMIT

    text = (
        f"<b>Мои магазины</b> ({len(stores)}/{limit})\n\n"
    )
    if not stores:
        text += "Пока нет магазинов. Добавьте первый!"
    else:
        for s in stores:
            name = s.get("name") or f"Магазин #{s['id']}"
            last = s.get("last_check", "никогда")
            text += f"• {name} (проверка: {last})\n"

    kb = stores_menu(stores)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await event.answer()
    else:
        await event.answer(text, parse_mode="HTML", reply_markup=kb)


# --- Add store ---

@router.callback_query(F.data == "add_store")
async def add_store_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    limit = user.get("stores_limit", FREE_STORES_LIMIT) if user else FREE_STORES_LIMIT
    count = await db.get_user_store_count(user_id)

    if count >= limit:
        plan = user.get("subscription", "free") if user else "free"
        if plan == "free":
            await callback.message.edit_text(
                f"Лимит бесплатного плана: {FREE_STORES_LIMIT} магазин.\n"
                f"Оформите PRO для мониторинга до {PRO_STORES_LIMIT} магазинов.",
                reply_markup=back_to_menu(),
            )
        else:
            await callback.message.edit_text(
                f"Достигнут лимит магазинов ({limit}).",
                reply_markup=back_to_menu(),
            )
        await callback.answer()
        return

    await callback.message.edit_text(
        "<b>Добавление магазина</b>\n\n"
        "Отправьте API-ключ WB (тип: Статистика).\n\n"
        "<i>Где взять: seller.wildberries.ru → Настройки → Доступ к API → "
        "Создать ключ (Статистика)</i>",
        parse_mode="HTML",
    )
    await state.set_state(AddStoreStates.waiting_api_key)
    await callback.answer()


@router.message(AddStoreStates.waiting_api_key)
async def add_store_key(message: Message, state: FSMContext):
    api_key = message.text.strip()

    # Delete the message with API key for security
    try:
        await message.delete()
    except Exception:
        pass

    if len(api_key) < 20:
        await message.answer("Ключ слишком короткий. Отправьте полный API-ключ WB.")
        return

    status_msg = await message.answer("Проверяю ключ...")

    valid = await validate_api_key(api_key)
    if not valid:
        await status_msg.edit_text(
            "API-ключ недействителен или не имеет доступа к статистике.\n"
            "Проверьте, что тип ключа — «Статистика» и он активен.\n\n"
            "Попробуйте ещё раз или /start для отмены.",
        )
        return

    await state.update_data(api_key=api_key)
    await status_msg.edit_text(
        "Ключ валиден! Введите название магазина (или отправьте «-» чтобы пропустить):"
    )
    await state.set_state(AddStoreStates.waiting_store_name)


@router.message(AddStoreStates.waiting_store_name)
async def add_store_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if name == "-":
        name = ""

    data = await state.get_data()
    api_key = data.get("api_key", "")

    store_id = await db.add_store(message.from_user.id, api_key, name)
    await state.clear()

    display_name = name or f"Магазин #{store_id}"
    await message.answer(
        f"Магазин «{display_name}» добавлен!\n"
        f"Мониторинг штрафов запущен (проверка каждые 30 мин).\n\n"
        f"Ключ: <code>{mask_api_key(api_key)}</code>",
        parse_mode="HTML",
        reply_markup=back_to_menu(),
    )


# --- Store detail ---

@router.callback_query(F.data.startswith("store_"))
async def show_store(callback: CallbackQuery):
    store_id = int(callback.data.split("_")[1])
    store = await db.get_store(store_id)
    if not store:
        await callback.answer("Магазин не найден", show_alert=True)
        return

    name = store.get("name") or f"Магазин #{store_id}"
    last_check = store.get("last_check", "ещё не проверялся")

    await callback.message.edit_text(
        f"<b>{name}</b>\n\n"
        f"ID: {store_id}\n"
        f"Ключ: <code>{mask_api_key(store['api_key'])}</code>\n"
        f"Последняя проверка: {last_check}",
        parse_mode="HTML",
        reply_markup=store_detail(store_id),
    )
    await callback.answer()


# --- Manual check ---

@router.callback_query(F.data.startswith("check_"))
async def manual_check(callback: CallbackQuery, bot: Bot):
    store_id = int(callback.data.split("_")[1])
    store = await db.get_store(store_id)
    if not store:
        await callback.answer("Магазин не найден", show_alert=True)
        return

    await callback.answer("Проверяю...")
    await callback.message.edit_text("Запрашиваю данные у WB API...")

    try:
        penalties = await fetch_penalties(store["api_key"])
    except WBApiError as e:
        await callback.message.edit_text(
            f"Ошибка WB API: {e.message}",
            reply_markup=back_to_menu(),
        )
        return

    new_count = 0
    for p in penalties:
        srid = p.get("srid", "")
        if not srid or await db.penalty_exists(store_id, srid):
            continue
        penalty_id = await db.save_penalty(store_id, p)
        await db.mark_penalty_notified(penalty_id)
        new_count += 1

        alert = format_penalty_alert(p, store.get("name", ""))
        await bot.send_message(callback.from_user.id, alert, parse_mode="HTML")

    await db.update_store_last_check(store_id)

    name = store.get("name") or f"Магазин #{store_id}"
    await callback.message.edit_text(
        f"Проверка «{name}» завершена.\n"
        f"Всего операций: {len(penalties)}\n"
        f"Новых штрафов: {new_count}",
        reply_markup=store_detail(store_id),
    )


# --- Delete store ---

@router.callback_query(F.data.startswith("del_"))
async def ask_delete(callback: CallbackQuery):
    store_id = int(callback.data.split("_")[1])
    store = await db.get_store(store_id)
    name = store.get("name", f"Магазин #{store_id}") if store else f"#{store_id}"

    await callback.message.edit_text(
        f"Удалить магазин «{name}»?\nМониторинг штрафов будет остановлен.",
        reply_markup=confirm_delete(store_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_del_"))
async def do_delete(callback: CallbackQuery):
    store_id = int(callback.data.split("_")[2])
    await db.delete_store(store_id)
    await callback.message.edit_text(
        "Магазин удалён.",
        reply_markup=back_to_menu(),
    )
    await callback.answer()
