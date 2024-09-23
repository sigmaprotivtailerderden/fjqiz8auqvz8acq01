
import logging
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import config
from telethon import TelegramClient, functions
from telethon.tl.types import InputReportReasonSpam

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.TOKEN)
dp = Dispatcher()
router = Router()

admins = config.admins

conn = sqlite3.connect('subscriptions.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE)''')
conn.commit()

class Form(StatesGroup):
    waiting_for_link = State()

def check_subscription(user_id: int):
    if user_id in admins:
        return True
    cursor.execute('SELECT * FROM subscriptions WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    return result is not None

@router.message(CommandStart())
async def start_command(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Bot-Net Sn0s", callback_data='botnetsnos'),
         InlineKeyboardButton(text="👤 Профиль", callback_data='profile')]
    ])
    
    await message.answer("<b>👋 Приветствую в сносер бот.</b>\n<blockquote>Купить подписка: @RainSu, @userarchi</blockquote>", reply_markup=keyboard, parse_mode=ParseMode.HTML)

@router.callback_query(lambda c: c.data == 'botnetsnos')
async def handle_botnetsnos(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id

    if check_subscription(user_id):
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="❌ Отмена")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await callback_query.message.answer("📨 Введите ссылку на нарушение:", reply_markup=keyboard)
        await state.set_state(Form.waiting_for_link)
    else:
        await callback_query.message.answer("❌ У вас нет активной подписки!\n<blockquote>Купить подписка: @RainSu, @userarchi</blockquote>", parse_mode=ParseMode.HTML)

async def send_complaints_from_all_accounts(session_files, link, message: Message, report_reason=InputReportReasonSpam()):
    link_parts = link.split('/')
    chat_username = link_parts[-2]
    message_id = int(link_parts[-1])

    progress_message = await message.answer("⏳ Начинаем отправку жалоб...")

    total_complaints = len(session_files) * 50
    sent_complaints = 0

    for session_file in session_files:
        client = TelegramClient(session_file, config.API_ID, config.API_HASH)
        
        async with client:
            chat = await client.get_entity(chat_username)
            
            for i in range(50):
                await client(functions.messages.ReportRequest(
                    peer=chat,
                    id=[message_id],
                    reason=report_reason,
                    message="Report"
                ))
                sent_complaints += 1
                await progress_message.edit_text(f"✅ Отправлено жалоб: {sent_complaints}/{total_complaints}")

    await progress_message.edit_text(f"🎉 Все {total_complaints} жалоб отправлены успешно!")

@router.message(Form.waiting_for_link)
async def handle_link_submission(message: Message, state: FSMContext):
    link = message.text
    session_files = ["+77029244504.session", "+972537097954.session", "+79935140960.session", "+77764221942.session"]
    
    await send_complaints_from_all_accounts(session_files, link, message, report_reason=InputReportReasonSpam())
    await state.clear()

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())