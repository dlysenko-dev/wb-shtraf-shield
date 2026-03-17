"""Start and help handlers."""

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

import db
from keyboards import main_menu
from config import FREE_STORES_LIMIT

router = Router()

WELCOME = (
    "<b>WB Штраф-Щит</b> — мониторинг штрафов Wildberries\n\n"
    "Бот проверяет штрафы каждые 30 минут и мгновенно уведомляет.\n\n"
    "<b>Как начать:</b>\n"
    "1. Создайте API-ключ в ЛК WB (тип: Статистика)\n"
    "2. Нажмите «Мои магазины» → «Добавить магазин»\n"
    "3. Вставьте API-ключ — мониторинг начнётся автоматически\n\n"
    f"<b>Бесплатно:</b> {FREE_STORES_LIMIT} магазин, неограниченные уведомления\n"
    "<b>PRO:</b> до 20 магазинов — 3 000 руб/мес"
)

HELP = (
    "<b>Команды:</b>\n"
    "/start — главное меню\n"
    "/stores — мои магазины\n"
    "/penalties — последние штрафы\n"
    "/stats — статистика штрафов\n"
    "/help — справка\n\n"
    "<b>Как получить API-ключ WB:</b>\n"
    "1. Зайдите в seller.wildberries.ru\n"
    "2. Настройки → Доступ к API\n"
    "3. Создайте ключ с типом «Статистика»\n"
    "4. Скопируйте ключ и вставьте в бота\n\n"
    "<b>Безопасность:</b> ключ «Статистика» даёт только чтение данных, "
    "изменить товары или цены через него невозможно."
)


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    await db.get_or_create_user(user.id, user.username or "", user.first_name or "")
    await message.answer(WELCOME, parse_mode="HTML", reply_markup=main_menu())


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP, parse_mode="HTML", reply_markup=main_menu())


@router.callback_query(F.data == "menu")
async def cb_menu(callback: CallbackQuery):
    await callback.message.edit_text(WELCOME, parse_mode="HTML", reply_markup=main_menu())
    await callback.answer()
