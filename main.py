from os import getenv
from pathlib import Path
from threading import Thread
import asyncio

from dotenv import load_dotenv

from util.DB import DB
from substitution_parsing import update_substitutions
from tg_bot import tg_bot


async def main():
    load_dotenv()
    DB.init_db(Path(getenv('DATABASE_FILE')))
    updater = update_substitutions.continuous_update()
    telegram_bot = tg_bot.main()
    await asyncio.gather(updater, telegram_bot)


if __name__ == "__main__":
    asyncio.run(main())
