import telebot
from telebot import types
from app.dependencies import supabase
from dotenv import load_dotenv
import os
import random
import bcrypt

load_dotenv()

# Токен вашего бота (замените на свой)
TOKEN =  os.getenv("TELEGRAM_API_TOKEN")
bot = telebot.TeleBot(TOKEN, skip_pending=True)

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Создаем кнопку "Поделиться контактом"
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    share_button = types.KeyboardButton(text="Поделиться", request_contact=True)
    markup.add(share_button)
    
    # Отправляем приветственное сообщение с кнопкой
    bot.send_message(
        message.chat.id,
        "👋 Привет! Для авторизации в приложении нажми кнопку «Поделиться», чтобы отправить свой контакт.",
        reply_markup=markup
    )

# Обработчик полученного контакта
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    send_code(message)
    
def send_code(message):
    try:
        phone_number = message.contact.phone_number
        
        response = supabase.table("verify_codes") \
            .select("id") \
            .eq("phone_number", phone_number) \
            .eq("type_auth", "Telegram") \
            .execute()
        
        if not response.data:
            bot.send_message(
            message.chat.id,
            "В данный момент вы не проходите процесс авторизации с помощью Telegram.\n"
            "Пожалуйста, перейдите в приложение📲",
            )
            return

        code = str(random.randint(10000, 99999)).encode('utf-8') # формат b'12345'
        update_response = supabase.table("verify_codes") \
            .update({"code": str(bcrypt.hashpw(code, bcrypt.gensalt()))}) \
            .eq("phone_number", phone_number) \
            .execute()

        bot.send_message(
            message.chat.id,
            f"Ваш код авторизации: *{code.decode('utf-8')}*",
            parse_mode='MarkdownV2'
        )

    except Exception as e:
        print(f"Ошибка при отправке кода: {e}")
        bot.send_message(
            message.chat.id,
            "В данный момент вы не проходите процесс авторизации с помощью Telegram.\n"
            "Пожалуйста, перейдите в приложение📲",
        )
# Запускаем бота
def start_bot():
    print("Бот запущен!")
    bot.polling(none_stop=True)