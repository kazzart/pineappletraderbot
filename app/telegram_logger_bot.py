import requests
from datetime import datetime


class TelegramLoggerBot:
    token: str
    base_url: str

    def __init__(self, token: str, base_url: str) -> None:
        self.token = token
        self.base_url = base_url

    def prepare_url(self, method: str | None) -> str:
        result_url = f'{self.base_url}/bot{self.token}/'
        if method is not None:
            result_url += method
        return result_url

    def creat_err_message(self, err: Exception):
        return f'{datetime.now()}\n{str(err.__class__).split()[1][1:-2]} ::: {err}'

    def post(self, method: str | None = None, params: dict | None = None, body: dict | None = None, err: Exception | None = None, chat_id: int | None = None):
        url = self.prepare_url(method)
        if err is not None and chat_id is not None:
            params = {'text': self.creat_err_message(err), 'chat_id': chat_id}
        print(url)
        resp = requests.post(url, params=params, data=body)
        return resp.json()
