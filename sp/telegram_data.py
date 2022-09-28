# Version 1.0.0 release

from configparser import ConfigParser


def get(config: ConfigParser) -> dict:
    config.read('settings.ini')
    return {"account_id": config.getint("TELEGRAM", "account_id"),
            "bot_token": config.get("TELEGRAM", "bot_token")}
