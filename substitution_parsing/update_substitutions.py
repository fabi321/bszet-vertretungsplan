import re
from datetime import datetime
from time import sleep

import requests
from bs4 import BeautifulSoup

from util.DB import DB
from .PDFHandling import PDF

VERTRETUNGSPLAN_REGEX: re.Pattern = re.compile(r'vertretungsplan-([a-z-]+)\.pdf')


def is_updated(last_updated: dict[str, datetime]) -> set[str]:
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
        last_modified = datetime.strptime(last_updated_txt, '%d.%m.%Y, %H:%M:%S')
        if last_modified > last_updated.get(href, datetime.min) and not href.endswith('fs.pdf'):
            to_update.add(href)
    return to_update


def do_update(last_updated: dict[str, datetime], to_update: set[str]) -> None:
    auth: tuple[str, str] = DB.get_latest_credential()
    for plan in to_update:
        resp: requests.Response = requests.get(f'https://geschuetzt.bszet.de/{plan}', auth=auth)
        if resp.status_code != 200:
            print(f'Error fetching document, {resp.text}')
            return
        pdf: PDF = PDF.from_bytes(resp.content, VERTRETUNGSPLAN_REGEX.search(plan).group(1))
        for substitution in pdf.to_substitutions():
            DB.insert_or_modify_substitution(substitution)
        last_updated[plan] = datetime.now()


def update(last_updated: dict[str, datetime]):
    if to_update := is_updated(last_updated):
        do_update(last_updated, to_update)


def continuous_update():
    last_updated: dict[str, datetime] = {}
    while True:
        update(last_updated)
        sleep(5 * 60)
