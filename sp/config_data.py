# Version 1.1.1 release

from configparser import ConfigParser


def get_bot_token(config: ConfigParser) -> str:
    config.read('settings.ini')
    return config.get("TELEGRAM", "bot_token")


def get_db(config: ConfigParser) -> dict:
    config.read('settings.ini')
    return {"ip": config.get("DATABASE", "ip"),
            "port": config.getint("DATABASE", "port"),
            "password": config.get("DATABASE", "password")}


def get_user(config: ConfigParser) -> dict:
    config.read('settings.ini')
    return {"shyftplan_email": config.get("AUTH_CONFIG", "shyftplan_email"),
            "shyftplan_token": config.get("AUTH_CONFIG", "shyftplan_token"),
            "shyftplan_employee_id": config.getint("AUTH_CONFIG", "shyftplan_employee_id"),
            "shyftplan_user_id": config.getint("AUTH_CONFIG", "shyftplan_user_id"),
            "telegram_id": config.getint("AUTH_CONFIG", "telegram_id")}
