import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import sys
import os
import asyncio
from datetime import datetime
import requests  # Для получения информации о городе и провайдере
import subprocess  # Для выполнения системных команд
import time  # Для добавления задержки

# Конфигурация
TOKEN = 'Ваш токен'
CHAT_ID = 'id чата'
IP_INFO_URL = 'http://ipinfo.io/{}/json'

# Создаем объект бота с использованием токена
bot = telegram.Bot(token=TOKEN)

# Словарь для хранения запросов на подтверждение
request_data = {}

def get_local_ip():
    try:
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
        return result.stdout.strip().split()[0]
    except Exception as e:
        print(f"Error getting local IP: {e}")
        return 'Неизвестен'

def get_hostname():
    try:
        result = subprocess.run(['hostname'], capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"Error getting hostname: {e}")
        return 'Неизвестен'

async def send_telegram_message(username, remote_ip, request_id):
    ip_info = {}
    try:
        response = requests.get(IP_INFO_URL.format(remote_ip))
        ip_info = response.json()
    except Exception as e:
        print(f"Error getting IP info: {e}")
        ip_info = {}

    city = ip_info.get('city', 'Неизвестно')
    provider = ip_info.get('org', 'Неизвестно')
    login_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    local_ip = get_local_ip()
    hostname = get_hostname()

    message = (f"🕒 Login Time: {login_time}\n"
               f"🏠 Hostname: {hostname}\n"
               f"📍 Remote IP: {remote_ip}\n"
               f"🌐 System IP: {local_ip}\n"
               f"🔌 Provider: {provider}\n"
               f"🏙️ City: {city}\n"
               f"👤 Username: {username}")

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Разрешить", callback_data=f"allow_{request_id}"),
         InlineKeyboardButton("Запретить", callback_data=f"deny_{request_id}")]
    ])
    try:
        # Отправляем сообщение и сохраняем ID сообщения
        sent_message = await bot.send_message(chat_id=CHAT_ID, text=message, reply_markup=reply_markup)
        print("Message sent.")
        return sent_message.message_id  # Возвращаем ID отправленного сообщения
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

async def delete_message(chat_id, message_id):
    """
    Функция для удаления сообщения.
    """
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        print(f"Message {message_id} deleted.")
    except Exception as e:
        print(f"Error deleting message: {e}")

async def send_success_message(username, hostname, remote_ip, local_ip):
    """
    Функция для отправки сообщения об успешной аутентификации.
    """
    success_message = (f"✅ Успешная аутентификация!\n"
                       f"👤 Пользователь: {username}\n"
                       f"🏠 Hostname: {hostname}\n"
                       f"📍 Remote IP: {remote_ip}\n"
                       f"🌐 System IP: {local_ip}")
    try:
        await bot.send_message(chat_id=CHAT_ID, text=success_message)
        print("Success message sent.")
    except Exception as e:
        print(f"Error sending success message: {e}")

async def send_failed_message(username, hostname, remote_ip, local_ip):
    """
    Функция для отправки сообщения о неудачной аутентификации.
    """
    failed_message = (f"❌ Неудачная попытка входа!\n"
                      f"👤 Пользователь: {username}\n"
                      f"🏠 Hostname: {hostname}\n"
                      f"📍 Remote IP: {remote_ip}\n"
                      f"🌐 System IP: {local_ip}")
    try:
        await bot.send_message(chat_id=CHAT_ID, text=failed_message)
        print("Failed message sent.")
    except Exception as e:
        print(f"Error sending failed message: {e}")

async def main():
    global request_data
    username = os.getenv('PAM_USER')
    remote_ip = os.getenv('PAM_RHOST')

    if not username or not remote_ip:
        print("Missing username or remote IP.")
        sys.exit(1)

    request_id = str(int(datetime.now().timestamp()))
    request_data[request_id] = {'username': username, 'remote_ip': remote_ip, 'timestamp': datetime.now().isoformat()}

    # Отправляем сообщение и сохраняем ID сообщения
    message_id = await send_telegram_message(username, remote_ip, request_id)

    update_id = None
    start_time = datetime.now()

    while True:
        try:
            if (datetime.now() - start_time).total_seconds() > 60:
                print("Exiting after 60 seconds.")
                sys.exit(1)

            updates = await bot.get_updates(offset=update_id, timeout=30)
            for update in updates:
                update_id = update.update_id + 1
                if update.callback_query:
                    callback_data = update.callback_query.data
                    if callback_data.startswith('allow_') or callback_data.startswith('deny_'):
                        req_id = callback_data.split('_')[1]
                        if req_id in request_data:
                            # Удаляем исходное сообщение с кнопками
                            if message_id:
                                await delete_message(CHAT_ID, message_id)

                            if callback_data.startswith('allow_'):
                                del request_data[req_id]
                                print("Access allowed.")

                                # Отправляем сообщение об успешной аутентификации
                                local_ip = get_local_ip()
                                hostname = get_hostname()
                                await send_success_message(username, hostname, remote_ip, local_ip)

                                sys.exit(0)

                            elif callback_data.startswith('deny_'):
                                del request_data[req_id]
                                print("Access denied.")

                                # Отправляем сообщение о неудачной аутентификации
                                local_ip = get_local_ip()
                                hostname = get_hostname()
                                await send_failed_message(username, hostname, remote_ip, local_ip)

                                sys.exit(1)
        except Exception as e:
            print(f"Exception occurred: {e}")
        await asyncio.sleep(1)

if __name__ == "__main__":
    print("Running script...")
    asyncio.run(main())
