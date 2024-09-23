from telethon import TelegramClient
import getpass
import os

# Запрашиваем данные у пользователя
api_id = input("Введите ваш API ID: ")
api_hash = input("Введите ваш API Hash: ")
phone_number = input("Введите номер телефона: ")

# Создаем клиента
client = TelegramClient(f"{phone_number}.session", api_id, api_hash)

async def main():
    await client.start(phone=phone_number)

    # Проверка на 2FA
    if client.session.is_bot:
        print("Вы используете бот-аккаунт.")
        return

    try:
        await client.sign_in(phone_number)
    except Exception as e:
        print("Ошибка входа:", e)
        return

    # Если включен 2FA, запрашиваем пароль
    if client.session.user_id and not client.session.auth_key:
        twofa_password = getpass.getpass("Введите 2FA пароль: ")
        await client.sign_in(password=twofa_password)

    print("Вход выполнен успешно!")

with client:
    client.loop.run_until_complete(main())