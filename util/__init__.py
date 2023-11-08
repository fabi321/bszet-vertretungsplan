import requests

from .DB import DB


def check_credentials(username: str, password: str) -> bool:
    if len(username) > 20 or len(password) > 20:
        return False
    r: requests.Response = requests.get('https://geschuetzt.bszet.de', auth=(username, password))
    success: bool = r.status_code == 200
    if success:
        DB.add_new_credential(username, password)
    return success
