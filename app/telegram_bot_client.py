from typing import List

from pandas import DataFrame

from tinkoff.invest import Client, GetFuturesMarginResponse
from tinkoff.invest.constants import INVEST_GRPC_API_SANDBOX
from tinkoff.invest.services import InstrumentsService

from tinkoff.invest.sandbox.client import SandboxClient

from enums import Role
import exceptions


class TelegramBotClient:
    client_id: int
    role: Role
    tinkoff_token: str | None
    pair: List[str]
    bounds: List[float]
    checking: bool

    def __init__(self, client_id: int, role: Role = Role.USER, tinkoff_token: str | None = None):
        self.client_id = client_id
        self.role = role
        self.pair = ['', '']
        self.bounds = [-1, 1]
        self.checking = False
        if self.role == Role.ADMIN or self.role == Role.MODERATOR:
            self.tinkoff_token = tinkoff_token
        else:
            self.tinkoff_token = None

    def get_accounts(self) -> None:
        if self.tinkoff_token is not None:
            with Client(self.tinkoff_token, target=INVEST_GRPC_API_SANDBOX) as client:
                print(client.users.get_accounts())
        else:
            raise exceptions.NoTinkoffTokenException('Can\'t get accounts')

    def get_sandbox_info(self) -> None:
        if self.tinkoff_token is not None:
            with SandboxClient(self.tinkoff_token) as client:
                print(client.users.get_info())
        else:
            raise exceptions.NoTinkoffTokenException('Can\'t get info')

    def get_figi_for_ticker(self, ticker: str) -> str:
        if self.tinkoff_token is not None:
            with Client(self.tinkoff_token) as client:
                instruments: InstrumentsService = client.instruments
                tickers: list = []
                for method in ["shares", "bonds", "etfs", "currencies", "futures"]:
                    for item in getattr(instruments, method)().instruments:
                        tickers.append(
                            {
                                "name": item.name,
                                "ticker": item.ticker,
                                "class_code": item.class_code,
                                "figi": item.figi
                            }
                        )
                tickers_df = DataFrame(tickers)
                ticker_df = tickers_df[tickers_df["ticker"] == ticker]
                figi = ticker_df["figi"].iloc[0]
                print(ticker_df.iloc[0])
            return figi
        else:
            raise exceptions.NoTinkoffTokenException(
                f'Can\'t get figi by ticker {ticker}')

    def get_last_price(self, instrument_id: str | None) -> float:
        if self.tinkoff_token is not None and instrument_id is not None:
            with Client(self.tinkoff_token) as client:
                instrument_price = client.market_data.get_last_prices(
                    figi=[instrument_id]).last_prices[0].price
                instrument_price = instrument_price.units + \
                    (instrument_price.nano / 1000000000)
                print('\n\n', client.market_data.get_last_prices(
                    figi=[instrument_id]), '\n\n\n')
                print('\n\n', client.market_data.get_trading_status(
                    figi=instrument_id), '\n\n')
            return instrument_price
        elif self.tinkoff_token is None:
            raise exceptions.NoTinkoffTokenException('Can\'t get last prices')
        else:
            raise exceptions.NoInstrumentId('Can\'t get last prices')

    def get_basic_asset_size(self, figi: str) -> float:
        if self.tinkoff_token is not None:
            with Client(self.tinkoff_token) as client:
                instruments: InstrumentsService = client.instruments
                tickers: list = []
                futures_margin: GetFuturesMarginResponse
                for item in instruments.futures().instruments:
                    tickers.append(
                        {
                            "name": item.name,
                            "ticker": item.ticker,
                            "class_code": item.class_code,
                            "figi": item.figi,
                            "basic_asset_size": item.basic_asset_size
                        }
                    )
                tickers_df = DataFrame(tickers)
                ticker_df = tickers_df[tickers_df["figi"] == figi]
                basic_asset_size = ticker_df["basic_asset_size"].iloc[0]
                basic_asset_size = basic_asset_size.units + \
                    (basic_asset_size.nano / 1000000000)

                futures_margin = client.instruments.get_futures_margin(
                    figi=figi)
                if futures_margin is not None:
                    min_price_increment = futures_margin.min_price_increment
                    min_price_increment = min_price_increment.units + \
                        (min_price_increment.nano / 1000000000)
                    min_price_increment_amount = futures_margin.min_price_increment_amount
                    min_price_increment_amount = min_price_increment_amount.units + \
                        (min_price_increment_amount.nano / 1000000000)
                    print('min_price_increment = ', min_price_increment,
                          '\nmin_price_increment_amount = ', min_price_increment_amount)
                    basic_asset_size = basic_asset_size * \
                        min_price_increment / min_price_increment_amount
                    return basic_asset_size
                else:
                    raise exceptions.NoFuturesMargin(
                        'Can\'t get basic asset size')
        else:
            raise exceptions.NoTinkoffTokenException(
                'Can\'t get basic asset size')

    def set_pair(self, tickers: List[str] | None) -> None:
        if tickers is not None:
            self.pair = [tickers[0], tickers[1]]

    def set_bounds(self, first_bound: float, second_bound: float) -> None:
        self.bounds = [min(first_bound, second_bound),
                       max(first_bound, second_bound)]

    def check_bounds(self, perc_diff: float) -> bool:
        return perc_diff >= self.bounds[0] or perc_diff <= self.bounds[1]

    def get_pair_difference(self) -> List[float]:
        if all(self.pair):
            first_figi = self.get_figi_for_ticker(self.pair[0])
            second_figi = self.get_figi_for_ticker(self.pair[1])
            first_price_of_asset = self.get_last_price(first_figi)
            second_price_of_asset = self.get_last_price(second_figi)
            first_basic_asset_size = self.get_basic_asset_size(first_figi)
            second_basic_asset_size = self.get_basic_asset_size(second_figi)
            price = [first_price_of_asset / first_basic_asset_size,
                     second_price_of_asset / second_basic_asset_size]
            print(price)
            perc_diff = price[0] / price[1] * 100 - 100

            return [*price, perc_diff]
        else:
            raise exceptions.PairIsNotSet('Can\'t get pair difference')
