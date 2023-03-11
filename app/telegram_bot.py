from typing import List

import telebot
import threading

from telegram_bot_client import TelegramBotClient
from telegram_logger_bot import TelegramLoggerBot
from enums import Role
import exceptions
import serializer

from exceptions import MyExceptionHandler


class TelegramBot:
    api: telebot.TeleBot
    admin_id: int
    clients: dict[int, TelegramBotClient]
    event: threading.Event
    thread: threading.Thread
    delay: int
    logger: TelegramLoggerBot

    def __init__(self, token: str, admin_id: int, admin_tinkoff_token: str, delay: int, logger: TelegramLoggerBot, exception_handler: MyExceptionHandler):
        self.api = telebot.TeleBot(token, exception_handler=exception_handler)
        self.admin_id = admin_id
        self.clients = {admin_id: TelegramBotClient(
            admin_id, role=Role.ADMIN, tinkoff_token=admin_tinkoff_token)}
        serializer.write_pickle('clients', self.clients)
        self.delay = delay
        self.logger = logger
        self.init_handlers()

    def init_handlers(self):
        def extract_arg(arg: str, number_of_args: int | None = None) -> List[str] | None:
            arguments: List[str] = arg.split()[1:]
            if len(arguments) == number_of_args or number_of_args is None:
                return arguments
            elif number_of_args is not None:
                raise exceptions.WrongNumberOfArgs()

        @self.api.message_handler(commands=['start'])
        def send_welcome(message):
            idx: int = message.from_user.id
            if idx not in self.clients:
                self.clients[idx] = TelegramBotClient(idx, Role.USER)
                self.api.send_message(idx, 'Ну привет)')
            else:
                self.api.send_message(idx, 'Я тебя уже знаю')
            print(idx)

        @self.api.message_handler(commands=['stop'])
        def send_goodbye(message):
            idx: int = message.from_user.id
            del self.clients[idx]
            self.api.send_message(idx, 'Пока(')

        @self.api.message_handler(commands=['setpair'])
        def set_pair(message):
            idx: int = message.from_user.id
            pair = extract_arg(message.text)
            self.clients[idx].set_pair(pair)

        @self.api.message_handler(commands=['setbounds'])
        def set_bounds(message):
            idx: int = message.from_user.id
            number_of_args = 2
            bounds = extract_arg(message.text, number_of_args)
            if bounds is not None:
                self.clients[idx].set_bounds(
                    float(bounds[0]), float(bounds[1]))
                self.api.send_message(idx, 'Границы установленны')
            else:
                self.api.send_message(
                    idx, f'Нужно указать {number_of_args} аргумента')

        @self.api.message_handler(commands=['getdifference'])
        def get_difference(message):
            idx: int = message.from_user.id
            prices = self.clients[idx].get_pair_difference()
            text_message = self.generate_message_price_differ(prices)
            self.api.send_message(idx, text_message)

        @self.api.message_handler(commands=['startpolling'])
        def start_polling(message):
            idx = message.from_user.id
            if self.clients[idx].role == Role.ADMIN:
                self.event = threading.Event()
                self.thread = threading.Thread(
                    target=self.send_reminder, args=(idx,))
                self.thread.start()
                self.api.send_message(
                    idx, f'Начинаю чекать инфу раз в {self.delay / 60:.1f} минут')
                checking = True
            else:
                self.api.send_message(
                    idx, 'Только админ может запустить проверки')

        @self.api.message_handler(commands=['test'])
        def send_test(message):
            idx: int = message.from_user.id
            self.api.send_message(idx, 'тестик')
            figi: str | None = self.clients[idx].get_figi_for_ticker('SiH3')
            futures = self.clients[idx].get_last_price(figi)
            print(futures)

    def generate_message_price_differ(self, prices: List[float] | None) -> str:
        if prices is not None:
            if prices[2] >= 0:
                text_message = f'SiH3 - {prices[0]}\nUSDRUBF - {prices[1]}\n\nSiH3 дороже USDRUBF на {prices[2]:.2f}%'
            else:
                text_message = f'SiH3 - {prices[0]}\nUSDRUBF - {prices[1]}\n\nSiH3 дешевле USDRUBF на {-prices[2]:.2f}%'
        else:
            raise exceptions.NoPrices()
        return text_message

    def send_reminder(self, idx: int):
        while not self.event.is_set():
            prices = self.clients[idx].get_pair_difference()
            for client in self.clients.values():
                if client.checking:
                    self.api.send_message(
                        client.client_id, self.generate_message_price_differ(prices))

    def run(self):
        self.api.polling()
