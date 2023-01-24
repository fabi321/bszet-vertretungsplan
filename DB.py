import sqlite3
import time
from pathlib import Path
from typing import Optional

from Substitution import Substitution


def password_to_credentials_id(password: str) -> int:
    return int(password.split('#')[1])


class DB:
    def __init__(self, db_location: Path) -> None:
        self.conn: sqlite3.Connection = sqlite3.connect(db_location)

    def get_latest_credential(self) -> tuple[str, str]:
        cur: sqlite3.Cursor = self.conn.execute('select username, password from credentials order by yid desc limit 1')
        return cur.fetchone()

    def add_new_credential(self, username: str, password: str) -> None:
        with self.conn as transaction:
            yid: int = password_to_credentials_id(password)
            transaction.execute('insert into credentials values (?, ?, ?)', (yid, username, password))

    def add_credentials_if_new(self, username: str, password: str) -> None:
        yid = password_to_credentials_id(password)
        cur: sqlite3.Cursor = self.conn.execute('select 1 from credentials where yid = ?', (yid,))
        if not cur.fetchone():
            self.add_new_credential(username, password)

    def add_user(self, user_id: int) -> None:
        with self.conn as transaction:
            transaction.execute('insert or ignore into user (uid) values (?)', (user_id,))

    def get_user(self, user_id: int) -> tuple[Optional[str], bool]:
        cur: sqlite3.Cursor = self.conn.execute('select gid, trusted from user where uid = ?', (user_id,))
        result = cur.fetchone()
        return result[0], bool(result[1])

    def trust_user(self, user_id: int) -> None:
        with self.conn as transaction:
            transaction.execute('update user set trusted = 1 where uid = ?', (user_id,))

    def is_trusted_user(self, user_id: int) -> bool:
        cur: sqlite3.Cursor = self.conn.execute('select 1 from user where uid = ? and trusted = 1', (user_id,))
        return bool(cur.fetchone())

    def user_exists(self, user_id: int) -> bool:
        cur: sqlite3.Cursor = self.conn.execute('select 1 from user where uid = ?', (user_id,))
        return bool(cur.fetchone())

    def get_all_recent_classes(self) -> list[str]:
        cur: sqlite3.Cursor = self.conn.execute('select gid from class')
        return [i[0] for i in cur.fetchall()]

    def add_user_to_class(self, user_id: int, class_id: str) -> None:
        with self.conn as transaction:
            transaction.execute('update user set gid = ? where uid = ?', (class_id, user_id))

    def clear_user_class(self, user_id: int) -> None:
        with self.conn as transaction:
            transaction.execute('update user set gid = null where uid = ?', (user_id,))

    def get_all_substitutions_for_user(self, uid: int) -> list[Substitution]:
        cur: sqlite3.Cursor = self.conn.execute(
            "select gid, day, lesson, teacher, subject, room, notes, u.last_update < s.last_update from user u join substitution s using (gid) where uid = ? and day > strftime('%s', 'now') - 86200 order by day, lesson asc",
            (uid,)
        )
        return [Substitution(*row) for row in cur.fetchall()]

    def update_user(self, user_id: int, is_zero: bool = False) -> None:
        with self.conn as transaction:
            target: int = 0 if is_zero else time.time()
            transaction.execute("update user set last_update = ? where uid = ?", (target, user_id))

    def get_all_users_in_class(self, gid: str) -> list[int]:
        cur: sqlite3.Cursor = self.conn.execute('select uid from user where gid = ?', (gid,))
        return [i[0] for i in cur.fetchall()]

    def __add_class_if_not_exists(self, gid: str) -> None:
        cur: sqlite3.Cursor = self.conn.execute('select 1 from class where gid = ?', (gid,))
        if cur.fetchone():
            return
        with self.conn as transaction:
            transaction.execute('insert or ignore into class values (?)', (gid,))

    def insert_or_modify_substitution(self, s: Substitution) -> bool:
        with self.conn as transaction:
            self.__add_class_if_not_exists(s.group)
            cur: sqlite3.Cursor = transaction.execute(
                "insert into substitution (gid, day, lesson, teacher, subject, room, notes) "
                "values (?, ?, ?, ?, ?, ?, ?) on conflict (gid, day, lesson) do update set "
                "teacher = excluded.teacher, subject = excluded.subject, room = excluded.room, "
                "notes = excluded.notes, last_update = strftime('%s', 'now') "
                "where teacher <> excluded.teacher or subject <> excluded.subject or "
                "room <> excluded.room or notes <> excluded.notes returning *",
                (s.group, s.day, s.lesson, s.teacher, s.subject, s.room, s.notes)
            )
            return bool(cur.fetchone())
