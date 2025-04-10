from pathlib import Path
import configparser

CFG = configparser.ConfigParser()
CFG.read(Path.home() / ".config/telegram_bot/secrets.cfg")


