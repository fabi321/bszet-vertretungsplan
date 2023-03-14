from os import getenv
from pathlib import Path
from threading import Thread

from dotenv import load_dotenv

from util.DB import DB
from substitution_parsing import update_substitutions
from tg_bot import tg_bot


def main():
    load_dotenv()
    DB.init_db(Path(getenv('DATABASE_FILE')))
    Thread(target=update_substitutions.continuous_update)
    tg_bot.main()


if __name__ == "__main__":
    main()
