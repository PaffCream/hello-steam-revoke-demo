from __future__ import annotations

import re
import urllib.parse as urlparse

import requests

from paffsteam import guard
from paffsteam.login import InvalidCredentials, LoginExecutor
from paffsteam.models import SteamUrl
from paffsteam.utils import (
    login_required,
    ping_proxy,
    text_between,
)

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class SteamClient:
    def __init__(
        self,
        api_key: str | None = None,
        username: str | None = None,
        password: str | None = None,
        shared_secret: str | None = None,
        steam_guard: str | None = None,
        login_cookies: dict | None = None,
        proxies: dict | None = None,
    ) -> None:
        self._api_key = api_key
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.85 Safari/537.36"
            }
        )
        self.is_logged_in = False
        
        if proxies:
            self.set_proxies(proxies)
        if shared_secret:
            self.steam_guard = {
                "shared_secret": shared_secret,
                "identity_secret": None,
                "steamid": None,
            }
        self.steam_guard_string = steam_guard
        if self.steam_guard_string is not None:
            self.steam_guard = guard.load_steam_guard(self.steam_guard_string)
        else:
            self.steam_guard = None

        self.was_login_executed = False
        self.username = username
        self._password = password
        self._access_token = None

        if login_cookies:
            self.set_login_cookies(login_cookies)

    def set_proxies(self, proxies: dict) -> dict:
        if not isinstance(proxies, dict):
            raise TypeError(
                "Proxy must be a dict. Example: "
                r'\{"http": "http://login:password@host:port"\, "https": "http://login:password@host:port"\}',
            )

        if ping_proxy(proxies):
            self._session.proxies.update(proxies)

        return proxies

    def set_login_cookies(self, cookies: dict) -> None:
        self._session.cookies.update(cookies)
        self.was_login_executed = True
        if self.steam_guard is None:
            self.steam_guard = {"steamid": str(self.get_steam_id())}

    @login_required
    def get_steam_id(self) -> int:
        url = SteamUrl.COMMUNITY_URL
        response = self._session.get(url)
        if steam_id := re.search(r'g_steamID = "(\d+)";', response.text):
            return int(steam_id.group(1))
        raise ValueError(f"Invalid steam_id: {steam_id}")

    def login(
        self,
        username: str | None = None,
        password: str | None = None,
        steam_guard: str | None = None,
    ) -> None:
        invalid_client_credentials_is_present = None in {
            self.username,
            self._password,
            self.steam_guard_string,
        }
        invalid_login_credentials_is_present = None in {username, password, steam_guard}

        if (
            invalid_client_credentials_is_present
            and invalid_login_credentials_is_present
        ):
            raise InvalidCredentials(
                'You have to pass username, password and steam_guard parameters when using "login" method',
            )

        if invalid_client_credentials_is_present:
            self.steam_guard_string = steam_guard
            self.steam_guard = guard.load_steam_guard(self.steam_guard_string)
            self.username = username
            self._password = password

        if self.was_login_executed and self.is_session_alive():
            return  # Session is alive, no need to login again

        self._session.cookies.set("steamRememberLogin", "true")
        LoginExecutor(
            self.username,
            self._password,
            self.steam_guard["shared_secret"],
            self._session,
        ).login()
        self.was_login_executed = True
        self._access_token = self._set_access_token()
        self.steam_guard["steamid"] = str(self.get_steam_id())
        self.is_logged_in = True

    def _set_access_token(self) -> str:
        steam_login_secure_cookies = [
            cookie
            for cookie in self._session.cookies
            if cookie.name == "steamLoginSecure"
        ]
        cookie_value = steam_login_secure_cookies[0].value
        decoded_cookie_value = urlparse.unquote(cookie_value)
        access_token_parts = decoded_cookie_value.split("||")
        if len(access_token_parts) < 2:
            print(decoded_cookie_value)
            raise ValueError("Access token not found in steamLoginSecure cookie")
        access_token = access_token_parts[1]
        return access_token

    @login_required
    def is_session_alive(self) -> bool:
        steam_login = self.username
        main_page_response = self._session.get(SteamUrl.COMMUNITY_URL)
        return steam_login.lower() in main_page_response.text.lower()

    @login_required
    def deauth_all_devices(self) -> bool:
        logger.info(f"Deauthorizing all devices for account {self.get_steam_id()}...")
        resp = self._session.get(f"{SteamUrl.STORE_URL}/store")
        steam_cookies = self._session.cookies.get_dict(
            domain="store.steampowered.com", path="/"
        )
        sessionid = steam_cookies.get("sessionid")
        form = {"action": "deauthorize", "sessionid": sessionid}
        resp = self._session.post(
            f"{SteamUrl.STORE_URL}/twofactor/manage_action", data=form
        )
        resp.raise_for_status()
        return True
