from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlparse

import requests

from paffsteam.exceptions import LoginRequired, ProxyConnectionError

def login_required(func):
    def func_wrapper(self, *args, **kwargs):
        if not self.was_login_executed:
            raise LoginRequired('Use login method first')
        return func(self, *args, **kwargs)

    return func_wrapper


def text_between(text: str, begin: str, end: str) -> str:
    start = text.index(begin) + len(begin)
    end = text.index(end, start)
    return text[start:end]

def ping_proxy(proxies: dict) -> bool:
    try:
        requests.get('https://steamcommunity.com/', proxies=proxies)
        return True
    except Exception:
        raise ProxyConnectionError('Proxy not working for steamcommunity.com')


def create_cookie(name: str, cookie: str, domain: str) -> dict:
    return {'name': name, 'value': cookie, 'domain': domain}
