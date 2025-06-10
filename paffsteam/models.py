from enum import IntEnum
from typing import NamedTuple


class PredefinedOptions(NamedTuple):
    app_id: str
    context_id: str

class SteamUrl:
    API_URL = "https://api.steampowered.com"
    COMMUNITY_URL = "https://steamcommunity.com"
    STORE_URL = "https://store.steampowered.com"
    LOGIN_URL = "https://login.steampowered.com"
