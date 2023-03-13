import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.constants import ParseMode
from telegram.ext import CallbackContext
from telegram.helpers import escape_markdown
from telegram.error import Forbidden

from DB import DB
from PDFHandling import PDF

VERTRETUNGSPLAN_REGEX: re.Pattern = re.compile(r'vertretungsplan-([a-z-]+)\.pdf')


class CustomContext:
    def __init__(self) -> None:
        self.last_updated: dict[str, datetime] = {}


def is_updated(context: CustomContext) -> set[str]:
    auth: tuple[str, str] = DB.get_latest_credential()
    resp: requests.Response = requests.get('https://geschuetzt.bszet.de/index.php?dir=/Vertretungsplaene', auth=auth)
    if resp.status_code != 200:
        print(f'Error fetching status, {resp.text}')
        return set()
    soup: BeautifulSoup = BeautifulSoup(resp.text, 'html.parser')
    to_update: set[str] = set()
    for a in soup.find_all(href=VERTRETUNGSPLAN_REGEX):
        tr = a.find_parent('tr')
        href: str = a['href']
        last_updated_txt: str = tr.find(class_='FileListCellInfo').text.strip()
        last_updated = datetime.strptime(last_updated_txt, '%d.%m.%Y, %H:%M:%S')
        if last_updated > context.last_updated.get(href, datetime.min) and not href.endswith('fs.pdf'):
            to_update.add(href)
    return to_update


def do_update(context: CustomContext, to_update: set[str]) -> list[str]:
    updated_groups: set[str] = set()
    auth: tuple[str, str] = DB.get_latest_credential()
    for plan in to_update:
        resp: requests.Response = requests.get(f'https://geschuetzt.bszet.de/{plan}', auth=auth)
        if resp.status_code != 200:
            print(f'Error fetching document, {resp.text}')
            return []
        pdf: PDF = PDF.from_bytes(resp.content, VERTRETUNGSPLAN_REGEX.search(plan).group(1))
        for substitution in pdf.to_substitutions():
            if DB.insert_or_modify_substitution(substitution):
                updated_groups.add(substitution.group)
        context.last_updated[plan] = datetime.now()
    return list(updated_groups)


async def update_user(uid: int, bot: Bot) -> None:
    result: str = 'Aktuelle Vertretungen:\n\n'
    is_new: bool = False
    for substitution in DB.get_all_substitutions_for_user(uid):
        line: str = datetime.fromtimestamp(substitution.day).strftime('%a, %d.%m')
        line += f', {substitution.lesson}: {substitution.teacher} {substitution.subject} {substitution.room}'
        if substitution.notes:
            line += f' ({substitution.notes})'
        line = escape_markdown(line, version=2)
        if substitution.is_new:
            line = f'*{line}*'
            is_new = True
        result += line + '\n'
    if is_new:
        try:
            await bot.send_message(chat_id=uid, text=result, parse_mode=ParseMode.MARKDOWN_V2)
            DB.update_user(uid)
        except Forbidden:
            DB.delete_user(uid)


async def message_users(context: CallbackContext, updated: list[str]) -> None:
    for gid in updated:
        users: list[int] = DB.get_all_users_in_class(gid)
        for uid in users:
            await update_user(uid, context.bot)


async def update(context: CallbackContext):
    if to_update := is_updated(context.job.data):
        updated: list[str] = do_update(context.job.data, to_update)
        await message_users(context, updated)
