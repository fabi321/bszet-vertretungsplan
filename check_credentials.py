import re

import requests

# potential regular expressions for sanity check. Might be too strict
USERNAME_REGEX: re.Pattern = re.compile(r'^bsz-et-[0-9]{4}$')
PASSWORD_REGEX: re.Pattern = re.compile(r'^[a-z]+#[0-9]{2}$')


def check(username: str, password: str) -> bool:
    if len(username) > 20 or len(password) > 20:
        return False
    r: requests.Response = requests.get('https://geschuetzt.bszet.de', auth=(username, password))
    return r.status_code == 200
