from datetime import datetime

import requests
from bs4 import BeautifulSoup
from telegram.ext import CallbackContext

from DB import DB
from PDFHandling import PDF


class CustomContext:
    def __init__(self, db: DB) -> None:
        self.last_updated: datetime = datetime.min
        self.db: DB = db


def is_updated(context: CustomContext) -> bool:
    auth: tuple[str, str] = context.db.get_latest_credential()
    resp: requests.Response = requests.get('https://geschuetzt.bszet.de/index.php?dir=/Vertretungsplaene', auth=auth)
    if resp.status_code != 200:
        print(f'Error fetching status, {resp.text}')
        return False
    soup: BeautifulSoup = BeautifulSoup(resp.text, 'html.parser')
    tr = soup.find(string='vertretungsplan-bs-it.pdf').find_parent('tr')
    last_updated_txt: str = tr.find(class_='FileListCellInfo').text.strip()
    last_updated = datetime.strptime(last_updated_txt, '%d.%m.%Y, %H:%M:%S')
    return last_updated > context.last_updated


def do_update(context: CustomContext) -> list[str]:
    updated_groups: set[str] = set()
    auth: tuple[str, str] = context.db.get_latest_credential()
    resp: requests.Response = requests.get(
        'https://geschuetzt.bszet.de/s-lk-vw/Vertretungsplaene/vertretungsplan-bs-it.pdf', auth=auth
        )
    if resp.status_code != 200:
        print(f'Error fetching document, {resp.text}')
        return []
    pdf: PDF = PDF.from_bytes(resp.content)
    for substitution in pdf.to_substitutions():
        if context.db.insert_or_modify_substitution(substitution):
            updated_groups.add(substitution.group)
    context.last_updated = datetime.now()
    return list(updated_groups)


def message_users(context: CallbackContext, updated: list[str]) -> None:
    for gid in updated:
        print(context.job.data.db.get_all_substitutions_for_user(494351437))


async def update(context: CallbackContext):
    if is_updated(context.job.data):
        updated: list[str] = do_update(context.job.data)
