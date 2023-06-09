from telebot import ExceptionHandler
from telegram_logger_bot import TelegramLoggerBot


class MyExceptionHandler(ExceptionHandler):
    def __init__(self, admin_id: int, logger: TelegramLoggerBot):
        self.admin_id = admin_id
        self.logger = logger
        super().__init__()

    def handle(self, exception):
        self.logger.post(method="sendMessage", err=exception, chat_id=self.admin_id)
        return True


class NoEnvironmentVariable(Exception):
    def __init__(self, message: str = "No environment variable"):
        self.message = message
        super().__init__(self.message)


class NoTinkoffTokenException(Exception):
    def __init__(self, message: str = "No tinkoff token"):
        self.message = message
        super().__init__(self.message)


class WrongNumberOfArgs(Exception):
    def __init__(self, message: str = "Wrong number of args"):
        self.message = message
        super().__init__(self.message)


class NoPrices(Exception):
    def __init__(self, message: str = "No prices"):
        self.message = message
        super().__init__(self.message)


class NoInstrumentId(Exception):
    def __init__(self, message: str = "No instrument id"):
        self.message = message
        super().__init__(self.message)


class NoFuturesMargin(Exception):
    def __init__(self, message: str = "No futures margin"):
        self.message = message
        super().__init__(self.message)


class PairIsNotSet(Exception):
    def __init__(self, message: str = "Pair is not set"):
        self.message = message
        super().__init__(self.message)


class NoTicker(Exception):
    def __init__(
        self, message: str = "There is no such ticker", ticker: str | None = None
    ):
        self.message = message
        if ticker is not None:
            self.message += f"\nThere is no '{ticker}'"
        super().__init__(self.message)
