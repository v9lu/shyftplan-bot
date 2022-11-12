# Version 1.2.0 release

from configparser import ConfigParser


def get_bot(config: ConfigParser) -> dict:
    config.read('settings.ini')
    return {"bot_token": config.get("TELEGRAM", "bot_token"),
            "pay_token": config.get("TELEGRAM", "pay_token")}


def get_db(config: ConfigParser) -> dict:
    config.read('settings.ini')
    return {"ip": config.get("DATABASE", "ip"),
            "port": config.getint("DATABASE", "port"),
            "password": config.get("DATABASE", "password")}
