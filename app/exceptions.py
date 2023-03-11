from telebot import ExceptionHandler


class MyExceptionHandler(ExceptionHandler):
    def __init__(self, admin_id, logger):
        self.admin_id = admin_id
        self.logger = logger
        super().__init__()

    def handle(self, exception):
        self.logger.post(method='sendMessage', err=exception,
                         chat_id=self.admin_id)
        return True


class NoTelegramTokenException(Exception):
    def __init__(self, message='No telegram token'):
        self.message = message
        super().__init__(self.message)


class NoTelegramLogTokenException(Exception):
    def __init__(self, message='No telegram token'):
        self.message = message

        super().__init__(self.message)


class NoAdminIdException(Exception):
    def __init__(self, message='No admin id'):
        self.message = message
        super().__init__(self.message)


class NoTinkoffTokenException(Exception):
    def __init__(self, message='No tinkoff token'):
        self.message = message
        super().__init__(self.message)


class NoDelay(Exception):
    def __init__(self, message='No delay'):
        self.message = message
        super().__init__(self.message)


class WrongNumberOfArgs(Exception):
    def __init__(self, message='Wrong number of args'):
        self.message = message
        super().__init__(self.message)


class NoPrices(Exception):
    def __init__(self, message='No prices'):
        self.message = message
        super().__init__(self.message)


class NoInstrumentId(Exception):
    def __init__(self, message='No instrument id'):
        self.message = message
        super().__init__(self.message)


class NoFuturesMargin(Exception):
    def __init__(self, message='No futures margin'):
        self.message = message
        super().__init__(self.message)


class PairIsNotSet(Exception):
    def __init__(self, message='Pair is not set'):
        self.message = message
        super().__init__(self.message)
