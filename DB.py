import sqlite3
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
        try:
            with self.conn as transaction:
                yid: int = password_to_credentials_id(password)
                transaction.execute('insert into credentials values (?, ?, ?)', (yid, username, password))
        except sqlite3.Error as e:
            print(f'Error while adding credentials: {e}')

    def add_credentials_if_new(self, username: str, password: str) -> None:
        yid = password_to_credentials_id(password)
        cur: sqlite3.Cursor = self.conn.execute('select 1 from credentials where yid = ?', (yid,))
        if not cur.fetchone():
            self.add_new_credential(username, password)

    def add_user(self, user_id: int) -> None:
        try:
            with self.conn as transaction:
                transaction.execute('insert or ignore into user (uid) values (?)', (user_id,))
        except sqlite3.Error as e:
            print(f'Error while adding user: {e}')

    def get_user(self, user_id: int) -> tuple[Optional[str], bool]:
        cur: sqlite3.Cursor = self.conn.execute('select gid, trusted from user where uid = ?', (user_id,))
        result = cur.fetchone()
        return result[0], bool(result[1])

    def trust_user(self, user_id: int) -> None:
        try:
            with self.conn as transaction:
                transaction.execute('update user set trusted = 1 where uid = ?', (user_id,))
        except sqlite3.Error as e:
            print(f'Error while trusting user: {e}')

    def user_exists(self, user_id: int) -> bool:
        cur: sqlite3.Cursor = self.conn.execute('select 1 from user where uid = ?', (user_id,))
        return bool(cur.fetchone())

    def get_all_recent_classes(self) -> list[str]:
        cur: sqlite3.Cursor = self.conn.execute('select gid from class')
        return [i[0] for i in cur.fetchall()]

    def add_user_to_class(self, user_id: int, class_id: str) -> None:
        try:
            with self.conn as transaction:
                transaction.execute('update user set gid = ? where uid = ?', (class_id, user_id))
        except sqlite3.Error as e:
            print(f'Error while trying to add user to class: {e}')

    def clear_user_class(self, user_id: int) -> None:
        try:
            with self.conn as transaction:
                transaction.execute('update user set gid = null where uid = ?', (user_id,))
        except sqlite3.Error as e:
            print(f'Error while trying to clear user class: {e}')

    def get_all_substitutions_for_user(self, uid: int) -> list[Substitution]:
        cur: sqlite3.Cursor = self.conn.execute(
            'select gid, day, lesson, teacher, subject, room, notes, u.last_update < s.last_update from user u join substitution s using (gid) where uid = ? and day > current_timestamp - 86400',
            (uid,)
            )
        return [Substitution(*row) for row in cur.fetchall()]

    def __check_if_substitution_exists(self, s: Substitution) -> Optional[int]:
        cur: sqlite3.Cursor = self.conn.execute(
            'select sid from substitution where day = ? and lesson = ? and gid = ?',
            (s.day, s.lesson, s.group)
        )
        if res := cur.fetchone():
            return res[0]
        return None

    def __check_substitution_difference(self, s: Substitution, sid: int) -> bool:
        cur: sqlite3.Cursor = self.conn.execute('select * from substitution where sid = ?', (sid,))
        res = cur.fetchone()
        return (
            res[4] != s.teacher
            or res[5] != s.subject
            or res[6] != s.room
            or res[7] != s.notes
        )

    def __update_substitution(self, s: Substitution, sid: int) -> None:
        try:
            with self.conn as transaction:
                transaction.execute(
                    'update substitution set teacher = ?, subject = ?, room = ?, notes = ?, last_update = current_timestamp where sid = ?',
                    (s.teacher, s.subject, s.room, s.notes, sid)
                )
        except sqlite3.Error as e:
            print(f'Error while trying to update substitution: {e}')

    def __create_substitution(self, s: Substitution) -> None:
        try:
            with self.conn as transaction:
                transaction.execute(
                    'insert into substitution (gid, day, lesson, teacher, subject, room, notes) values (?, ?, ?, ?, ?, ?, ?)',
                    (s.group, s.day, s.lesson, s.teacher, s.subject, s.room, s.notes)
                )
        except sqlite3.Error as e:
            print(f'Error while trying to create substitution: {e}')

    def __add_class_if_not_exists(self, gid: str) -> None:
        cur: sqlite3.Cursor = self.conn.execute('select 1 from class where gid = ?', (gid,))
        if cur.fetchone():
            return
        try:
            with self.conn as transaction:
                transaction.execute('insert or ignore into class values (?)', (gid,))
        except sqlite3.Error as e:
            print(f'Error while trying to add a class: {e}')

    def insert_or_modify_substitution(self, substitution: Substitution) -> bool:
        self.__add_class_if_not_exists(substitution.group)
        if sid := self.__check_if_substitution_exists(substitution) is not None:
            if self.__check_substitution_difference(substitution, sid):
                self.__update_substitution(substitution, sid)
            else:
                return False
        else:
            self.__create_substitution(substitution)
        return True
