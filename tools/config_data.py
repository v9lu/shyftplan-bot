# Version 1.3.0 release

from configparser import ConfigParser


def get_bot(config: ConfigParser) -> dict:
    config.read('tools/settings.ini')
    return {"bot_token": config.get("TELEGRAM", "bot_token"),
            "pay_token": config.get("TELEGRAM", "pay_token")}


def get_db(config: ConfigParser) -> dict:
    config.read('tools/settings.ini')
    return {"ip": config.get("DATABASE", "ip"),
            "port": config.getint("DATABASE", "port"),
            "password": config.get("DATABASE", "password")}


def get_subs(config: ConfigParser) -> dict:
    config.read('tools/settings.ini')
    return {"trial": config.getint("SUBSCRIPTION", "trial"),
            "standard": config.getint("SUBSCRIPTION", "standard"),
            "premium": config.getint("SUBSCRIPTION", "premium")}
