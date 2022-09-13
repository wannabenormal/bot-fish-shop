import os
from textwrap import dedent

import redis
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler

from moltin_connection import MoltinConnection

_database = None
_moltin = None


def get_user_response(update):
    chat_id = update.effective_message.chat.id
    message_id = update.effective_message.message_id

    if update.message:
        user_reply = update.message.text
    else:
        user_reply = update.callback_query.data

    return user_reply, chat_id, message_id


def show_menu(bot, update):
    moltin = get_moltin_connection()
    products = moltin.get_products()

    keyboard = [
        [
            InlineKeyboardButton(product['name'], callback_data=product['id'])
        ] for product in products['data']
    ]

    keyboard.append([
        InlineKeyboardButton('Корзина', callback_data='show_cart'),
    ])

    bot.send_message(
        text='Меню:',
        chat_id=update.effective_chat.id,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_cart(bot, update):
    _, chat_id, _ = get_user_response(update)
    moltin = get_moltin_connection()
    cart = moltin.get_user_cart(update.effective_chat.id)

    cart_items = [
        dedent(
            f'''
                {item["name"]}
                {item["description"]}
                {item["meta"]["display_price"]["with_tax"]["unit"]["formatted"]} per kg
                {item["quantity"]}kg in cart for {item["meta"]["display_price"]["with_tax"]["value"]["formatted"]}
            '''
        )
        for item in cart['data']
    ]

    keyboard = [
        [
            InlineKeyboardButton(
                'Удалить {}'.format(item['name']),
                callback_data='delete_{}'.format(item['id'])
            )

        ] for item in cart['data']
    ]

    keyboard.append(
        [
            InlineKeyboardButton('Оплатить', callback_data='get_contact'),
            InlineKeyboardButton('В меню', callback_data='show_menu'),
        ]
    )

    message = (
        '{}'
        '\n Total: {}'
    ).format(
        ''.join(cart_items),
        cart['meta']['display_price']['with_tax']['formatted']
    )

    bot.send_message(
        text=message,
        chat_id=update.effective_chat.id,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def start(bot, update):
    show_menu(bot, update)

    return 'HANDLE_MENU'


def handle_menu(bot, update):
    if not update.callback_query:
        return

    user_reply, chat_id, message_id = get_user_response(update)

    if user_reply == 'show_cart':
        bot.delete_message(
            chat_id=chat_id,
            message_id=message_id
        )
        show_cart(bot, update)
        return 'HANDLE_CART'

    moltin = get_moltin_connection()
    product_id = user_reply
    chat_id = update.callback_query.message.chat_id

    product = moltin.get_product(product_id)

    message = dedent(
        f'''
            {product["data"]["name"]}
            {product["data"]["meta"]["display_price"]["with_tax"]["formatted"]} per kg
            {product["data"]["meta"]["stock"]["level"]}kg on stock
            {product["data"]["description"]}
        '''
    )

    bot.delete_message(
        chat_id=chat_id,
        message_id=update.callback_query.message.message_id
    )

    keyboard = [
        [
            InlineKeyboardButton('1kg', callback_data=f'{product_id}_1'),
            InlineKeyboardButton('5kg', callback_data=f'{product_id}_5'),
            InlineKeyboardButton('10kg', callback_data=f'{product_id}_10'),

        ],
        [
            InlineKeyboardButton('Корзина', callback_data='show_cart'),
            InlineKeyboardButton('Назад', callback_data='show_menu')
        ]
    ]

    if 'included' in product and 'main_images' in product['included']:
        image_url = product['included']['main_images'][0]['link']['href']
        bot.send_photo(
            chat_id=chat_id,
            photo=image_url,
            caption=message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        bot.send_message(
            chat_id=chat_id,
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    return 'HANDLE_DESCRIPTION'


def handle_description(bot, update):
    user_reply, chat_id, message_id = get_user_response(update)

    if user_reply == 'show_menu':
        bot.delete_message(
            chat_id=chat_id,
            message_id=message_id
        )
        show_menu(bot, update)

        return 'HANDLE_MENU'
    elif user_reply == 'show_cart':
        bot.delete_message(
            chat_id=chat_id,
            message_id=message_id
        )
        show_cart(bot, update)

        return 'HANDLE_CART'
    else:
        moltin = get_moltin_connection()
        product_id, quantity = user_reply.split('_')

        moltin.add_to_cart(chat_id, product_id, int(quantity))

        return 'HANDLE_DESCRIPTION'


def handle_email(bot, update):
    user_reply, chat_id, _ = get_user_response(update)

    moltin = get_moltin_connection()

    moltin.add_customer(
        update['message']['chat']['username'],
        user_reply
    )

    bot.send_message(
        chat_id=chat_id,
        text=f'Вы отправили следующий email: {user_reply}'
    )

    return 'START'


def handle_cart(bot, update):
    user_reply, chat_id, message_id = get_user_response(update)
    moltin = get_moltin_connection()

    bot.delete_message(
        chat_id=chat_id,
        message_id=message_id
    )

    if user_reply == 'show_menu':
        show_menu(bot, update)
        return 'HANDLE_MENU'

    elif user_reply == 'get_contact':
        bot.send_message(
            chat_id=chat_id,
            text='Пожалуйста, введите ваш email:'
        )

        return 'WAITING_EMAIL'

    else:
        product_id = user_reply.replace('delete_', '')
        moltin.delete_from_cart(chat_id, product_id)
        show_cart(bot, update)

        return 'HANDLE_CART'


def user_reply_handler(bot, update):
    db = get_database_connection()

    user_reply, chat_id, _ = get_user_response(update)

    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode('utf-8')

    states_handlers = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'WAITING_EMAIL': handle_email
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
    dp.add_handler(CallbackQueryHandler(user_reply_handler))
    dp.add_handler(CommandHandler('start', user_reply_handler))

    updater.start_polling()
    updater.idle()
