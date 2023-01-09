from configparser import ConfigParser
from typing import Optional


class Cfg:
    """Singleton class for configuration, in case it needs to be used in multiple locations.

    You should copy `sample-config.ini` to `config.ini` and then fill out important values.
    """
    _instance = None
    cfg: Optional[ConfigParser] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.cfg = ConfigParser()
            cls._instance.cfg.read("config.ini")

        return cls._instance
