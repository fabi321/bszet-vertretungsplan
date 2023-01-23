import sqlite3
from pathlib import Path
from typing import Optional


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
        except sqlite3.Error as e:
            print(f'Error while adding credentials: {e}')

    def add_user(self, user_id: int) -> None:
        try:
            with self.conn as transaction:
                transaction.execute('insert into users values (?)', (user_id,))
        except sqlite3.Error as e:
            print(f'Error while adding user: {e}')

    def get_user(self, user_id: int) -> tuple[Optional[str], bool]:
        cur: sqlite3.Cursor = self.conn.execute('select gid, trusted from users where uid = ?', (user_id,))
        result = cur.fetchone()
        return result[0], bool(result[1])

    def trust_user(self, user_id: int) -> None:
        try:
            with self.conn as transaction:
                transaction.execute('update users set trusted = 1 where uid = ?', (user_id,))
        except sqlite3.Error as e:
            print(f'Error while trusting user: {e}')

    def user_exists(self, user_id: int) -> bool:
        cur: sqlite3.Cursor = self.conn.execute('select 1 from users where uid = ?', (user_id,))
        return bool(cur.fetchone())

    def add_user_to_group(self, user_id: int, group_id: str) -> None:
        try:
            with self.conn as transaction:
                transaction.execute('insert or ignore into groups values (?)', (group_id,))
                transaction.execute('update users set gid = ? where uid = ?', (group_id, user_id))
        except sqlite3.Error as e:
            print(f'Error while trying to add user to group: {e}')
