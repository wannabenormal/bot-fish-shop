# Бот для продажи рыбы
Данный бот написан исключительно в учебных целях.
Для работы бота необходим магазин, созданный на [Moltin](https://elasticpath.com).

# Подготовка
1. Заведите базу данных на [Redis](https://redislabs.com/).
1. Заведите бота в [Telegram](https://t.me/botfather).
1. Создайте в корне проекта `.env`-файл следующего содержания:
```
export MOLTIN_BASE_URL='<URL для запросов Moltin, выданный в кабинете>'
export MOLTIN_CLIENT_ID='<CLIENT ID вашего магазина Moltin>'
export TG_BOT_TOKEN='<ТОКЕН ВАШЕГО ТЕЛЕГРАМ-БОТА>'
export REDIS_HOST='<REDIS_HOST>'
export REDIS_PORT='<REDIS_PORT>'
export REDIS_PASSWORD='<REDIS_PASSWORD>'
```

# Запуск
```
python bot.py
```

# Онлайн-версия
Данный бот выложен на Heroku и доступен по следующей [ссылке](https://t.me/dvmn_fish_bot).