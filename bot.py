import os

from dotenv import load_dotenv
import redis
from telegram.ext import Filters, Updater
from telegram.ext import CommandHandler, MessageHandler

_database = None


def start(bot, update):
    update.message.reply_text('Привет!')

    return 'ECHO'


def echo(bot, update):
    update.message.reply_text(update.message.text)

    return 'ECHO'


def user_reply_handler(bot, update):
    db = get_database_connection()
    user_reply = update.message.text
    chat_id = update.message.chat_id

    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode('utf-8')

    states_handlers = {
        'START': start,
        'ECHO': echo
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


if __name__ == '__main__':
    load_dotenv()

    tg_token = os.getenv('TG_BOT_TOKEN')
    updater = Updater(tg_token)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text, user_reply_handler))
    dp.add_handler(CommandHandler('start', user_reply_handler))

    updater.start_polling()
    updater.idle()
