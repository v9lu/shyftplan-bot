# Version 1.0.0 release

from configparser import ConfigParser


def get_bot_token(config: ConfigParser) -> str:
    config.read('settings.ini')
    return config.get("TELEGRAM", "bot_token")


def get_db(config: ConfigParser) -> dict:
    config.read('settings.ini')
    return {"ip": config.get("DATABASE", "ip"),
            "password": config.get("DATABASE", "password")}
