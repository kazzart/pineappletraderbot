from typing import List

import telebot
from telebot.types import Message
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

        def handle_ticker_pair(message: Message):
            idx: int = message.from_user.id
            if message.text is not None:
                self.clients[idx].set_pair(message.text.split())
                self.api.send_message(idx, 'Пара тикеров установлена')
            else:
                self.api.send_message(
                    idx, 'Не получилось установить пару тикеров')

        @self.api.message_handler(commands=['setpair'])
        def set_pair(message):
            idx: int = message.from_user.id
            self.api.send_message(idx, 'Введи пару тикеров через пробел')
            self.api.register_next_step_handler(message, handle_ticker_pair)

        def handle_bounds(message: Message):
            idx: int = message.from_user.id
            if message.text is not None:
                try:
                    first_bound, second_bound = message.text.split()
                    self.clients[idx].set_bounds(
                        float(first_bound), float(second_bound))
                    self.api.send_message(idx, 'Границы установлены')
                except ValueError as ex:
                    print(ex.__class__)
                    self.api.send_message(
                        idx, 'Введены некорректные значения')
            else:
                self.api.send_message(
                    idx, 'Не получилось установить границы')

        @self.api.message_handler(commands=['setbounds'])
        def set_bounds(message):
            idx: int = message.from_user.id
            self.api.send_message(idx, 'Введите границы отслеживания')
            self.api.register_next_step_handler(message, handle_bounds)

        @self.api.message_handler(commands=['getdifference'])
        def get_difference(message):
            idx: int = message.from_user.id
            prices = self.clients[idx].get_pair_difference()
            text_message = self.generate_message_price_differ(prices, idx)
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
            else:
                self.api.send_message(
                    idx, 'Только админ может запустить проверки')

        def handle_set_tinkoff_token(message: Message, idx: int, admin_idx: int):
            self.clients[idx].tinkoff_token = message.text
            self.clients[idx].role = Role.MODERATOR
            self.clients[idx].get_accounts()
            self.api.send_message(
                idx, 'Поздравляю с получением роли модератора')
            self.api.send_message(
                admin_idx, f'Пользователь с id \'{idx}\' теперь модератор')

        def handle_add_moder(message: Message):
            idx: int = message.from_user.id
            if message.text is not None:
                try:
                    self.api.send_message(
                        int(message.text), 'Введите свой Tinkoff token')
                    self.api.register_next_step_handler_by_chat_id(
                        int(message.text), handle_set_tinkoff_token, int(message.text), idx)
                except Exception:
                    self.api.send_message(idx, 'Введен неверный токен')
                    self.api.send_message(
                        int(message.text), 'Введен неверный токен')
            else:
                self.api.send_message(idx, 'Не вышло добавить модератора')

        @self.api.message_handler(commands=['addmoder'])
        def add_moder(message):
            idx: int = message.from_user.id
            self.api.send_message(idx, 'Введите id нового модератора')
            self.api.register_next_step_handler(message, handle_add_moder)

        @self.api.message_handler(commands=['removemoder'])
        def remove_moder(message):
            idx: int = message.from_user.id
            self.api.send_message(idx, 'Введите id модератора для удаления')
            self.api.register_next_step_handler(message, handle_add_moder)
            figi: str | None = self.clients[idx].get_figi_for_ticker('SiH3')
            futures = self.clients[idx].get_last_price(figi)
            print(futures)

    def generate_message_price_differ(self, prices: List[float] | None, idx: int) -> str:
        if prices is not None:
            if prices[2] >= 0:
                text_message = f'{self.clients[idx].pair[0]} - {prices[0]}\n{self.clients[idx].pair[1]} - {prices[1]}\n\n{self.clients[idx].pair[0]} дороже {self.clients[idx].pair[1]} на {prices[2]:.2f}%'
            else:
                text_message = f'{self.clients[idx].pair[0]} - {prices[0]}\n{self.clients[idx].pair[1]} - {prices[1]}\n\n{self.clients[idx].pair[0]} дешевле {self.clients[idx].pair[1]} на {-prices[2]:.2f}%'
        else:
            raise exceptions.NoPrices()
        return text_message

    def send_reminder(self, idx: int):
        while not self.event.is_set():
            prices = self.clients[idx].get_pair_difference()
            for client in self.clients.values():
                if client.checking:
                    self.api.send_message(
                        client.client_id, self.generate_message_price_differ(prices, idx))

    def run(self):
        self.api.polling()
