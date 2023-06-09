from typing import List
import threading
from time import sleep


import telebot
from telebot.types import Message

from telegram_bot_client import TelegramBotClient
from telegram_logger_bot import TelegramLoggerBot
from enums import Role, Mode
import exceptions
import serializer

from exceptions import MyExceptionHandler


class TelegramBot:
    api: telebot.TeleBot
    admin_id: int
    clients: dict[int, TelegramBotClient]
    event: threading.Event | None
    thread: threading.Thread
    delay: int
    logger: TelegramLoggerBot

    def __init__(
        self,
        token: str,
        admin_id: int,
        admin_tinkoff_token: str,
        delay: int,
        logger: TelegramLoggerBot,
        exception_handler: MyExceptionHandler,
    ):
        self.api = telebot.TeleBot(token, exception_handler=exception_handler)
        self.admin_id = admin_id
        self.clients = {
            admin_id: TelegramBotClient(
                admin_id, role=Role.ADMIN, tinkoff_token=admin_tinkoff_token
            )
        }
        serializer.write_pickle("clients", self.clients)
        self.event = None
        self.delay = delay
        self.logger = logger
        self.init_handlers()

    def init_handlers(self):
        @self.api.message_handler(commands=["start"])
        def send_welcome(message: Message):
            idx: int = message.from_user.id
            if idx not in self.clients:
                self.clients[idx] = TelegramBotClient(idx, Role.USER)
                self.api.send_message(idx, "Ну привет)")
            else:
                self.api.send_message(idx, "Я тебя уже знаю")
            print(idx)

        @self.api.message_handler(commands=["stop"])
        def send_goodbye(message: Message):
            idx: int = message.from_user.id
            del self.clients[idx]
            self.api.send_message(idx, "Пока(")

        def handle_ticker_pair(message: Message):
            idx: int = message.from_user.id
            if message.text is not None:
                self.clients[idx].set_pair(message.text.split())
                self.api.send_message(idx, "Пара тикеров установлена")
            else:
                self.api.send_message(idx, "Не получилось установить пару тикеров")

        @self.api.message_handler(commands=["setpair"])
        def set_pair(message: Message):
            idx: int = message.from_user.id
            self.api.send_message(idx, "Введи пару тикеров через пробел")
            self.api.register_next_step_handler(message, handle_ticker_pair)

        def handle_bounds(message: Message):
            idx: int = message.from_user.id
            if message.text is not None:
                try:
                    first_bound, second_bound = message.text.split()
                    self.clients[idx].set_bounds(
                        float(first_bound), float(second_bound)
                    )
                    self.api.send_message(idx, "Границы установлены")
                except ValueError as ex:
                    print(ex.__class__)
                    self.api.send_message(idx, "Введены некорректные значения")
            else:
                self.api.send_message(idx, "Не получилось установить границы")

        @self.api.message_handler(commands=["setbounds"])
        def set_bounds(message: Message):
            idx: int = message.from_user.id
            self.api.send_message(idx, "Введите границы отслеживания")
            self.api.register_next_step_handler(message, handle_bounds)

        @self.api.message_handler(commands=["getdifference"])
        def get_difference(message: Message):
            idx: int = message.from_user.id
            try:
                prices: List[float] = self.clients[idx].get_pair_difference()
                text_message: str = self.generate_message_price_differ(prices, idx)
                self.api.send_message(idx, text_message)
            except exceptions.PairIsNotSet as ex:
                text_message: str = (
                    "Необходимо сначала выбрать пару бумаг при помощи /setpair"
                )
                self.api.send_message(idx, text_message)
                raise ex

        @self.api.message_handler(commands=["startpolling"])
        def start_polling(message: Message):
            idx: int = message.from_user.id
            if self.clients[idx].role == Role.ADMIN:
                if self.clients[idx].pair_set and self.clients[idx].bounds_set:
                    self.clients[idx].checking = True
                if self.event is not None:
                    self.event.set()
                self.event = threading.Event()
                self.thread = threading.Thread(target=self.send_reminder)
                self.thread.start()
                self.api.send_message(
                    idx, f"Начинаю чекать инфу раз в {self.delay / 60:.1f} минут"
                )
            else:
                self.api.send_message(idx, "Только админ может запустить проверки")

        @self.api.message_handler(commands=["stoppolling"])
        def stop_polling(message: Message):
            idx: int = message.from_user.id
            if self.clients[idx].role == Role.ADMIN:
                if self.event is not None:
                    self.event.set()
                    self.event = None
                else:
                    self.api.send_message(idx, "Цикл проверки не запущен")
            else:
                self.api.send_message(
                    idx, "Только админ может остановить цикл проверки"
                )

        @self.api.message_handler(commands=["getnotifications"])
        def get_notifications(message: Message):
            idx: int = message.from_user.id
            if (
                self.clients[idx].role == Role.MODERATOR
                or self.clients[idx].role == Role.ADMIN
            ):
                if self.clients[idx].pair_set and self.clients[idx].bounds_set:
                    self.clients[idx].checking = True
                    self.api.send_message(
                        idx, f"Начинаю чекать инфу раз в {self.delay / 60:.1f} минут"
                    )
                if not self.clients[idx].pair_set:
                    self.api.send_message(idx, "Необходимо выбрать пару бумаг")
                if not self.clients[idx].bounds_set:
                    self.api.send_message(idx, "Необходимо выбрать границы проверки")
            else:
                self.api.send_message(
                    idx, "Только админ или модератор может отслеживать бумаги"
                )

        @self.api.message_handler(commands=["stopnotifications"])
        def stop_notifications(message: Message):
            idx: int = message.from_user.id
            if (
                self.clients[idx].role == Role.MODERATOR
                or self.clients[idx].role == Role.ADMIN
            ):
                self.clients[idx].checking = False
                self.api.send_message(
                    idx, "Перестаю отслеживать изменения ценных бумаг"
                )
            else:
                self.api.send_message(
                    idx, "Только админ или модератор может отслеживать бумаги"
                )

        def handle_set_delay(message: Message):
            idx: int = message.from_user.id
            if message.text is not None:
                try:
                    self.delay = int(message.text)
                    self.api.send_message(idx, "Промежуток установлен")
                except ValueError as ex:
                    print(ex.__class__)
                    self.api.send_message(idx, "Введено некорректное значение")
            else:
                self.api.send_message(idx, "Не получилось установить промежуток")

        @self.api.message_handler(commands=["setdelay"])
        def set_delay(message: Message):
            idx: int = message.from_user.id
            if (
                self.clients[idx].role == Role.MODERATOR
                or self.clients[idx].role == Role.ADMIN
            ):
                self.api.send_message(idx, "Введите новый промежуток в секундах")
                self.api.register_next_step_handler(message, handle_set_delay)
            else:
                self.api.send_message(
                    idx, "Только админ или модератор может установить промежуток"
                )

        def handle_set_tinkoff_token(message: Message, idx: int, admin_idx: int):
            self.clients[idx].tinkoff_token = message.text
            self.clients[idx].role = Role.MODERATOR
            self.clients[idx].get_accounts()
            self.api.send_message(idx, "Поздравляю с получением роли модератора")
            self.api.send_message(
                admin_idx, f"Пользователь с id '{idx}' теперь модератор"
            )

        def handle_add_moder(message: Message):
            idx: int = message.from_user.id
            if message.text is not None:
                try:
                    self.api.send_message(
                        int(message.text), "Введите свой Tinkoff token"
                    )
                    self.api.register_next_step_handler_by_chat_id(
                        int(message.text),
                        handle_set_tinkoff_token,
                        int(message.text),
                        idx,
                    )
                except Exception as ex:
                    print(ex.__class__)
                    self.api.send_message(idx, "Введен неверный токен")
                    self.api.send_message(int(message.text), "Введен неверный токен")
            else:
                self.api.send_message(idx, "Не вышло добавить модератора")

        @self.api.message_handler(commands=["addmoder"])
        def add_moder(message: Message):
            idx: int = message.from_user.id
            self.api.send_message(idx, "Введите id нового модератора")
            self.api.register_next_step_handler(message, handle_add_moder)

        def handle_remove_moder(message: Message):
            idx: int = message.from_user.id
            if message.text is not None and int(message.text) in self.clients:
                self.clients[int(message.text)].role = Role.USER
                self.clients[int(message.text)].tinkoff_token = None
                self.api.send_message(int(message.text), "Вы больше не модератор")
                self.api.send_message(
                    idx, f"Пользователь с id '{int(message.text)}' теперь модератор"
                )

            else:
                self.api.send_message(idx, "Не вышло удалить модератора")

        @self.api.message_handler(commands=["removemoder"])
        def remove_moder(message):
            idx: int = message.from_user.id
            self.api.send_message(idx, "Введите id модератора для удаления")
            self.api.register_next_step_handler(message, handle_remove_moder)

        @self.api.message_handler(commands=["left"])
        def left_mode(message):
            idx: int = message.from_user.id
            self.clients[idx].checking_mode = Mode.LEFT
            self.api.send_message(idx, "Ожидаю отклонения слева")

        @self.api.message_handler(commands=["right"])
        def right_mode(message):
            idx: int = message.from_user.id
            self.clients[idx].checking_mode = Mode.RIGHT
            self.api.send_message(idx, "Ожидаю отклонения справа")

        @self.api.message_handler(commands=["any"])
        def any_mode(message):
            idx: int = message.from_user.id
            self.clients[idx].checking_mode = Mode.ANY
            self.api.send_message(idx, "Ожидаю любого отклонения")

    def generate_message_price_differ(self, prices: List[float], idx: int) -> str:
        if prices[2] >= 0:
            text_message: str = f"{self.clients[idx].pair[0]} - {prices[0]}\n{self.clients[idx].pair[1]} - {prices[1]}\n\n{self.clients[idx].pair[0]} дороже {self.clients[idx].pair[1]} на {prices[2]:.2f}%"
        else:
            text_message: str = f"{self.clients[idx].pair[0]} - {prices[0]}\n{self.clients[idx].pair[1]} - {prices[1]}\n\n{self.clients[idx].pair[0]} дешевле {self.clients[idx].pair[1]} на {-prices[2]:.2f}%"
        return text_message

    def send_reminder(self):
        if self.event is not None:
            while not self.event.is_set():
                for client in self.clients.values():
                    if client.checking:
                        prices: List[float] = client.get_pair_difference()
                        if client.check_bounds(prices[2]):
                            self.api.send_message(
                                client.client_id,
                                self.generate_message_price_differ(
                                    prices, client.client_id
                                ),
                            )
                sleep(self.delay)

    def run(self):
        self.api.polling()
