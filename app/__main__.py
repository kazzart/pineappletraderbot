import os
from dotenv import load_dotenv

from telegram_bot import TelegramBot
from telegram_logger_bot import TelegramLoggerBot
import serializer
from exceptions import MyExceptionHandler, NoEnvironmentVariable


if __name__ == "__main__":
    load_dotenv()
    TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
    LOG_TOKEN: str | None = os.getenv("TELEGRAM_LOGGER_BOT_TOKEN")
    BASE_URL: str = "https://api.telegram.org"
    ADMIN_ID: int
    ADMIN_ID_STR: str | None = os.getenv("ADMIN_ID_STR")
    ADMIN_TINKOFF_TOKEN: str | None = os.getenv("ADMIN_TINKOFF_TOKEN")
    DELAY: int
    DELAY_STR: str | None = os.getenv("DELAY_STR")
    ADMIN_DB_CONNECTION_STRING: str | None = os.getenv("ADMIN_DB_CONNECTION_STRING")
    logger: TelegramLoggerBot
    exception_handler: MyExceptionHandler
    if TOKEN is None:
        raise NoEnvironmentVariable("No telegram bot token")
    if LOG_TOKEN is None:
        raise NoEnvironmentVariable("No telegram logger bot token")
    if ADMIN_ID_STR is None:
        raise NoEnvironmentVariable("No admin id")
    if ADMIN_TINKOFF_TOKEN is None:
        raise NoEnvironmentVariable("No admin tinkoff token")
    if DELAY_STR is None:
        raise NoEnvironmentVariable("No delay")
    if ADMIN_DB_CONNECTION_STRING is None:
        raise NoEnvironmentVariable("No admin db connection string")

    ADMIN_ID = int(ADMIN_ID_STR)

    DELAY = int(DELAY_STR)

    logger = TelegramLoggerBot(LOG_TOKEN, BASE_URL)
    exception_handler = MyExceptionHandler(ADMIN_ID, logger)
    bot = TelegramBot(
        TOKEN, ADMIN_ID, ADMIN_TINKOFF_TOKEN, DELAY, logger, exception_handler
    )
    bot.run()
