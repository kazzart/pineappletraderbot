import os
from dotenv import load_dotenv

from telegram_bot import TelegramBot
from telegram_logger_bot import TelegramLoggerBot
import serializer
import exceptions


if __name__ == "__main__":
    load_dotenv()
    TOKEN: str | None = os.getenv('TELEGRAM_BOT_TOKEN')
    LOG_TOKEN: str | None = os.getenv('TELEGRAM_LOGGER_BOT_TOKEN')
    BASE_URL: str = 'https://api.telegram.org'
    ADMIN_ID: int
    ADMIN_ID_STR: str | None = os.getenv('ADMIN_ID_STR')
    ADMIN_TINKOFF_TOKEN: str | None = os.getenv('ADMIN_TINKOFF_TOKEN')
    DELAY: int
    DELAY_STR: str | None = os.getenv('DELAY_STR')
    logger: TelegramLoggerBot
    exception_handler: exceptions.MyExceptionHandler
    if TOKEN is None:
        raise exceptions.NoTelegramTokenException()
    if LOG_TOKEN is None:
        raise exceptions.NoTelegramLogTokenException()
    if ADMIN_ID_STR is None:
        raise exceptions.NoAdminIdException()
    if ADMIN_TINKOFF_TOKEN is None:
        raise exceptions.NoTinkoffTokenException()
    if DELAY_STR is None:
        raise exceptions.NoDelay()

    ADMIN_ID = int(ADMIN_ID_STR)

    DELAY = int(DELAY_STR)

    logger = TelegramLoggerBot(LOG_TOKEN, BASE_URL)
    exception_handler = exceptions.MyExceptionHandler(ADMIN_ID, logger)
    bot = TelegramBot(TOKEN, ADMIN_ID, ADMIN_TINKOFF_TOKEN,
                      DELAY, logger, exception_handler)
    bot.run()
