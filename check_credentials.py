import requests


def check(username: str, password: str) -> bool:
    if len(username) > 20 or len(password) > 20:
        return False
    r: requests.Response = requests.get('https://geschuetzt.bszet.de', auth=(username, password))
    return r.status_code == 200
