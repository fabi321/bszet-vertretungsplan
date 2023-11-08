from os import getenv
from pathlib import Path
import asyncio

from dotenv import load_dotenv
import discord

from util.DB import DB
from substitution_parsing import update_substitutions
from tg_bot import tg_bot
from dc_bot import dc_bot


async def main():
    load_dotenv()
    DB.init_db(Path(getenv('DATABASE_FILE')))
    futures = [update_substitutions.continuous_update()]
    discord.utils.setup_logging()
    if getenv('BOT_API_TOKEN'):
        futures.append(tg_bot.main())
    if getenv('DISCORD_BOT_TOKEN'):
        futures.append(dc_bot.main())
    await asyncio.gather(*futures)


if __name__ == "__main__":
    asyncio.run(main())
