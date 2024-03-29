import sqlite3
import time
from pathlib import Path
from typing import Optional

from substitution_parsing.Substitution import Substitution


def password_to_credentials_id(password: str) -> int:
    return int(password.split('#')[-1])


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
    def add_user(cls, user_id: int, platform: str = 'tg') -> None:
        with cls.conn as transaction:
            transaction.execute('insert or ignore into user (uid, platform) values (?, ?)', (user_id, platform))

    @classmethod
    def get_user(cls, user_id: int, platform: str = 'tg') -> tuple[Optional[str], bool]:
        cur: sqlite3.Cursor = cls.conn.execute('select gid, trusted from user where uid = ? and platform = ?', (user_id, platform))
        result = cur.fetchone()
        return result[0], bool(result[1])

    @classmethod
    def trust_user(cls, user_id: int, platform: str = 'tg') -> None:
        with cls.conn as transaction:
            transaction.execute('update user set trusted = 1 where uid = ? and platform = ?', (user_id, platform))

    @classmethod
    def is_trusted_user(cls, user_id: int, platform: str = 'tg') -> bool:
        cur: sqlite3.Cursor = cls.conn.execute('select 1 from user where uid = ? and trusted = 1 and platform = ?', (user_id, platform))
        return bool(cur.fetchone())

    @classmethod
    def user_exists(cls, user_id: int, platform: str = 'tg') -> bool:
        cur: sqlite3.Cursor = cls.conn.execute('select 1 from user where uid = ? and platform = ?', (user_id, platform))
        return bool(cur.fetchone())

    @classmethod
    def delete_user(cls, user_id: int, platform: str = 'tg') -> None:
        with cls.conn as transaction:
            transaction.execute('delete from user where uid = ? and platform = ?', (user_id, platform))

    @classmethod
    def get_areas(cls) -> list[str]:
        cur: sqlite3.Cursor = cls.conn.execute('select distinct area from class')
        return [i[0] for i in cur.fetchall()]

    @classmethod
    def get_all_recent_classes_for_area(cls, area: str) -> list[str]:
        # only selects groups that have been active in the last 3 months
        cur: sqlite3.Cursor = cls.conn.execute(
            "select gid from class where area = ? and last_update > strftime('%s', 'now') - 7777777",
            (area,)
        )
        return [i[0] for i in cur.fetchall()]

    @classmethod
    def check_if_class_exists(cls, area: str, class_id: str) -> bool:
        cur: sqlite3.Cursor = cls.conn.execute('select 1 from class where area = ? and gid = ?', (area, class_id))
        return bool(cur.fetchone())

    @classmethod
    def add_user_to_class(cls, user_id: int, class_id: str, platform: str = 'tg') -> None:
        with cls.conn as transaction:
            transaction.execute('update user set gid = ? where uid = ? and platform = ?', (class_id, user_id, platform))

    @classmethod
    def clear_user_class(cls, user_id: int, platform: str = 'tg') -> None:
        with cls.conn as transaction:
            transaction.execute('update user set gid = null where uid = ? and platform = ?', (user_id, platform))

    @classmethod
    def get_all_substitutions_for_user(cls, uid: int, platform: str = 'tg') -> list[Substitution]:
        cur: sqlite3.Cursor = cls.conn.execute(
            "select gid, day, lesson, teacher, subject, room, notes, area, u.last_update < s.last_update from user u"
            " join substitution s using (gid) join class using (gid) where uid = ? and platform = ? and "
            "day > strftime('%s', 'now') - 86200 order by day, lesson asc",
            (uid, platform)
        )
        return [Substitution(*row) for row in cur.fetchall()]

    @classmethod
    def get_all_updated_users(cls, platform: str = 'tg') -> list[int]:
        cur: sqlite3.Cursor = cls.conn.execute(
            "select distinct uid from user u join substitution s using (gid) "
            "where platform = ? and s.last_update > u.last_update and day > strftime('%s', 'now') - 86200",
            (platform,)
        )
        return [i[0] for i in cur.fetchall()]

    @classmethod
    def update_user(cls, user_id: int, platform: str = 'tg', is_zero: bool = False) -> None:
        with cls.conn as transaction:
            target: int = 0 if is_zero else time.time()
            transaction.execute("update user set last_update = ? where uid = ? and platform = ?", (target, user_id, platform))

    @classmethod
    def add_class_if_not_exists(cls, gid: str, area: str) -> None:
        with cls.conn as transaction:
            transaction.execute('insert into class (gid, area) values (?, ?) on conflict do nothing', (gid, area))

    @classmethod
    def insert_or_modify_substitution(cls, s: Substitution) -> bool:
        with cls.conn as transaction:
            cls.add_class_if_not_exists(s.group, s.area)
            transaction.execute("update class set last_update = strftime('%s', 'now') where gid = ?", (s.group,))
            cur: sqlite3.Cursor = transaction.execute(
                "insert into substitution (gid, day, lesson, teacher, subject, room, notes) "
                "values (?, ?, ?, ?, ?, ?, ?) on conflict (gid, day, lesson) do update set teacher = excluded.teacher, "
                "subject = excluded.subject, room = excluded.room, notes = excluded.notes, "
                "last_update = strftime('%s', 'now') where teacher <> excluded.teacher or "
                "subject <> excluded.subject or room <> excluded.room or notes <> excluded.notes returning *",
                (s.group, s.day, s.lesson, s.teacher, s.subject, s.room, s.notes)
            )
            return bool(cur.fetchone())
