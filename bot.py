import os

import redis
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler

from moltin_connection import MoltinConnection

_database = None
_moltin = None


def start(bot, update):
    moltin = get_moltin_connection()
    products = moltin.get_products()

    keyboard = [
        [
            InlineKeyboardButton(product['name'], callback_data=product['id'])
        ] for product in products['data']
    ]

    update.message.reply_text(
        'Привет!',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return 'ECHO'


def echo(bot, update):
    update.message.reply_text(update.message.text)

    return 'ECHO'


def user_reply_handler(bot, update):
    db = get_database_connection()

    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return

    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode('utf-8')

    states_handlers = {
        'START': start,
        'ECHO': echo,
    }

    state_handler = states_handlers[user_state]

    try:
        next_state = state_handler(bot, update)
        db.set(chat_id, next_state)
    except Exception as err:
        print(err)


def get_database_connection():
    global _database
    if _database is None:
        database_password = os.getenv('REDIS_PASSWORD')
        database_host = os.getenv('REDIS_HOST')
        database_port = os.getenv('REDIS_PORT')

        _database = redis.Redis(
            host=database_host,
            port=database_port,
            password=database_password
        )
    return _database


def get_moltin_connection():
    global _moltin

    if _moltin is None:
        base_url = os.getenv('MOLTIN_BASE_URL')
        client_id = os.getenv('MOLTIN_CLIENT_ID')
        _moltin = MoltinConnection(base_url, client_id)

    return _moltin


if __name__ == '__main__':
    load_dotenv()

    tg_token = os.getenv('TG_BOT_TOKEN')
    updater = Updater(tg_token)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text, user_reply_handler))
    dp.add_error_handler(CallbackQueryHandler(user_reply_handler))
    dp.add_handler(CommandHandler('start', user_reply_handler))

    updater.start_polling()
    updater.idle()
