import logging
import asyncio
import sqlite3
import time
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import config
from telethon import TelegramClient, functions
from telethon.tl.types import InputReportReasonOther
# from keep_alive import keep_alive
logging.basicConfig(level=logging.INFO)
# keep_alive()
bot = Bot(token=config.TOKEN)
dp = Dispatcher()
router = Router()

admins = config.admins
conn = sqlite3.connect('subscriptions.db')
cursor = conn.cursor()

# Only create the table if it doesn't exist
cursor.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE,
                    expiration_date TEXT)''')
conn.commit()

class Form(StatesGroup):
    waiting_for_link = State()

def check_subscription(user_id: int) -> bool:
    if user_id in admins:
        return True
    cursor.execute('SELECT expiration_date FROM subscriptions WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if result:
        expiration_date = datetime.fromisoformat(result[0])
        return expiration_date > datetime.now()
    return False

@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext = None):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Bot-Net Sn0s", callback_data='botnetsnos'),
         InlineKeyboardButton(text="👤 Профиль", callback_data='profile')]
    ])
    await message.answer("<b>👋 Приветствую в сносер бот.</b>\n<blockquote>Купить подписку: @RainSu, @userarchi</blockquote>", reply_markup=keyboard, parse_mode=ParseMode.HTML)

@router.callback_query(lambda c: c.data == 'botnetsnos')
async def handle_botnetsnos(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    await callback_query.message.delete()
    if check_subscription(user_id):
        back_button = InlineKeyboardButton(text="Назад", callback_data="back0")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_button]])
        await callback_query.message.answer(
            "<b>📨 Введите ссылку на нарушение:</b>", 
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        await state.set_state(Form.waiting_for_link)
    else:
        await callback_query.message.answer(
            "❌ У вас нет активной подписки!\nКупить подписку: @RainSu, @userarchi", 
            show_alert=True
        )

@router.callback_query(lambda c: c.data == 'back0')
async def handle_back(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    await start_command(callback_query.message, state)

@router.message(Form.waiting_for_link)
async def handle_link_submission(message: Message, state: FSMContext):
    link = message.text
    session_files = ["+77029244504.session", "+972537097954.session", "+79935140960.session", "+77764221942.session"]
    await send_complaints_from_all_accounts(session_files, link, message)
    await state.clear()

async def send_complaints_from_all_accounts(session_files, link, message):
    link_parts = link.split('/')
    chat_username = link_parts[-2]
    message_id = int(link_parts[-1])

    progress_message = await message.answer("<b>⏳ Начинаем отправку жалоб...</b>", parse_mode=ParseMode.HTML)

    total_complaints = len(session_files) * 150
    complaint_text = "Hello dear telegram support, today I want to complain about this person for violating the telegram rules, I ask you to ban this person in telegram, thanks in advance."

    for session_file in session_files:
        client = TelegramClient(session_file, config.API_ID, config.API_HASH)

        async with client:
            try:
                chat = await client.get_entity(chat_username)

                for i in range(150):
                    await client(functions.messages.ReportRequest(
                        peer=chat,
                        id=[message_id],
                        reason=InputReportReasonOther(),
                        message=complaint_text
                    ))
                    await progress_message.edit_text(f"<b>✅ Отправлено жалоб: {i + 1 + (session_files.index(session_file) * 150)}/{total_complaints}</b>", parse_mode=ParseMode.HTML)

            except ValueError as e:
                if "No user has" in str(e):
                    await message.answer(f"<b>❌ Ошибка: {chat_username} не найден.</b>")
                else:
                    await message.answer(f"<b>❌ Произошла ошибка: {str(e)}</b>")
            except Exception as e:
                await message.answer(f"<b>❌ Произошла неизвестная ошибка: {str(e)}</b>")

    await progress_message.edit_text(f"<b>🎉 Все {total_complaints} жалоб отправлены успешно!</b>", parse_mode=ParseMode.HTML)

@router.callback_query(lambda c: c.data == 'profile')
async def handle_profile(callback_query: CallbackQuery):
    await callback_query.message.delete()
    back = InlineKeyboardButton(text="Назад", callback_data="back")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[back]])
    user_id = callback_query.from_user.id
    cursor.execute('SELECT expiration_date FROM subscriptions WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    if user_id in admins:
        subscription_status = "Навсегда"
    elif result:
        expiration_date = datetime.fromisoformat(result[0])
        remaining_days = (expiration_date - datetime.now()).days
        subscription_status = f"{remaining_days} д." if remaining_days > 0 else "0 д."
    else:
        subscription_status = "Нет подписки"
        
    await callback_query.message.answer(
        f"<b>🆔 ID:</b> <code>{user_id}</code>\n<b>⭐️ Ваша подписка:</b> <code>{subscription_status}</code>",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

@router.callback_query(lambda c: c.data == 'back')
async def handle_back(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    await start_command(callback_query.message, state)

@router.message(Command("addsub"))
async def add_subscription(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in admins:
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return

    args = message.text.split()
    if len(args) != 3:
        await message.answer("❌ Неправильное использование. Пример: /addsub <id> <типа 1d, 7d или 30d>")
        return

    target_user_id = args[1]
    duration = args[2]

    # Calculate expiration date based on duration
    try:
        if duration.endswith('d'):
            days = int(duration[:-1])
            expiration_date = datetime.now() + timedelta(days=days)
        else:
            await message.answer("❌ Неправильный тип. Используйте 1d, 7d или 30d.")
            return
    except ValueError:
        await message.answer("❌ Неправильный тип. Используйте 1d, 7d или 30d.")
        return

    # Insert or update subscription
    cursor.execute('INSERT OR REPLACE INTO subscriptions (user_id, expiration_date) VALUES (?, ?)',
                   (target_user_id, expiration_date.isoformat()))
    conn.commit()

    await message.answer(f"✅ Подписка на пользователя <code>{target_user_id}</code> успешно добавлена до <code>{expiration_date.isoformat()}</code>.")

async def main():
    dp.include_router(router)
    try:
        await dp.start_polling(bot)
    finally:
        conn.close()

if __name__ == '__main__':
    asyncio.run(main())