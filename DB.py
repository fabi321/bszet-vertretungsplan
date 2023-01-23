import sqlite3
from pathlib import Path


class DB:
    def __init__(self, db_location: Path) -> None:
        self.conn: sqlite3.Connection = sqlite3.connect(db_location)

    def get_latest_credential(self) -> tuple[str, str]:
        cur: sqlite3.Cursor = self.conn.execute('select username, password from credentials order by yid desc limit 1')
        return cur.fetchone()

    def add_new_credential(self, username: str, password: str) -> None:
        try:
            with self.conn as transaction:
                yid: int = int(password.split('#')[1])
                transaction.execute('insert into credentials values (?, ?, ?)', (yid, username, password))
        except sqlite3.Error:
            print('tried to add credential twice')

    def add_user(self):
