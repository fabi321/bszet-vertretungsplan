import sqlite3
import time
from pathlib import Path
from typing import Optional

from Substitution import Substitution


def password_to_credentials_id(password: str) -> int:
    return int(password.split('#')[1])


class DB:
    conn: sqlite3.Connection = sqlite3.connect(':memory:')

    @classmethod
    def init_db(cls, db_location: Path) -> None:
        cls.conn: sqlite3.Connection = sqlite3.connect(db_location)

    @classmethod
    def get_latest_credential(cls) -> tuple[str, str]:
        cur: sqlite3.Cursor = cls.conn.execute('select username, password from credentials order by yid desc limit 1')
        return cur.fetchone()

    @classmethod
    def add_new_credential(cls, username: str, password: str) -> None:
        with cls.conn as transaction:
            yid: int = password_to_credentials_id(password)
            transaction.execute(
                'insert into credentials values (?, ?, ?) on conflict do nothing', (yid, username, password)
                )

    @classmethod
    def add_user(cls, user_id: int) -> None:
        with cls.conn as transaction:
            transaction.execute('insert or ignore into user (uid) values (?)', (user_id,))

    @classmethod
    def get_user(cls, user_id: int) -> tuple[Optional[str], bool]:
        cur: sqlite3.Cursor = cls.conn.execute('select gid, trusted from user where uid = ?', (user_id,))
        result = cur.fetchone()
        return result[0], bool(result[1])

    @classmethod
    def trust_user(cls, user_id: int) -> None:
        with cls.conn as transaction:
            transaction.execute('update user set trusted = 1 where uid = ?', (user_id,))

    @classmethod
    def is_trusted_user(cls, user_id: int) -> bool:
        cur: sqlite3.Cursor = cls.conn.execute('select 1 from user where uid = ? and trusted = 1', (user_id,))
        return bool(cur.fetchone())

    @classmethod
    def user_exists(cls, user_id: int) -> bool:
        cur: sqlite3.Cursor = cls.conn.execute('select 1 from user where uid = ?', (user_id,))
        return bool(cur.fetchone())

    @classmethod
    def get_all_recent_classes(cls) -> list[str]:
        cur: sqlite3.Cursor = cls.conn.execute('select gid from class')
        return [i[0] for i in cur.fetchall()]

    @classmethod
    def add_user_to_class(cls, user_id: int, class_id: str) -> None:
        with cls.conn as transaction:
            transaction.execute('update user set gid = ? where uid = ?', (class_id, user_id))

    @classmethod
    def clear_user_class(cls, user_id: int) -> None:
        with cls.conn as transaction:
            transaction.execute('update user set gid = null where uid = ?', (user_id,))

    @classmethod
    def get_all_substitutions_for_user(cls, uid: int) -> list[Substitution]:
        cur: sqlite3.Cursor = cls.conn.execute(
            "select gid, day, lesson, teacher, subject, room, notes, u.last_update < s.last_update from user u"
            " join substitution s using (gid) where uid = ? and day > strftime('%s', 'now') - 86200"
            " order by day, lesson asc",
            (uid,)
        )
        return [Substitution(*row) for row in cur.fetchall()]

    @classmethod
    def update_user(cls, user_id: int, is_zero: bool = False) -> None:
        with cls.conn as transaction:
            target: int = 0 if is_zero else time.time()
            transaction.execute("update user set last_update = ? where uid = ?", (target, user_id))

    @classmethod
    def get_all_users_in_class(cls, gid: str) -> list[int]:
        cur: sqlite3.Cursor = cls.conn.execute('select uid from user where gid = ?', (gid,))
        return [i[0] for i in cur.fetchall()]

    @classmethod
    def __add_class_if_not_exists(cls, gid: str) -> None:
        with cls.conn as transaction:
            transaction.execute('insert into class values (?) on conflict do nothing', (gid,))

    @classmethod
    def insert_or_modify_substitution(cls, s: Substitution) -> bool:
        with cls.conn as transaction:
            cls.__add_class_if_not_exists(s.group)
            cur: sqlite3.Cursor = transaction.execute(
                "insert into substitution (gid, day, lesson, teacher, subject, room, notes) "
                "values (?, ?, ?, ?, ?, ?, ?) on conflict (gid, day, lesson) do update set teacher = excluded.teacher, "
                "subject = excluded.subject, room = excluded.room, notes = excluded.notes, "
                "last_update = strftime('%s', 'now') where teacher <> excluded.teacher or "
                "subject <> excluded.subject or room <> excluded.room or notes <> excluded.notes returning *",
                (s.group, s.day, s.lesson, s.teacher, s.subject, s.room, s.notes)
            )
            return bool(cur.fetchone())
