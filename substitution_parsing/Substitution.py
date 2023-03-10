from typing import Optional


class Substitution:
    def __init__(
        self, group: str, day: int, lesson: int, teacher: str, subject: str, room: str, notes: Optional[str], area: str,
        is_new: bool
    ) -> None:
        self.group: str = group
        self.day: int = day
        self.lesson: int = lesson
        self.teacher: str = teacher
        self.subject: str = subject
        self.room: str = room
        self.notes: Optional[str] = notes
        self.area: str = area
        self.is_new: bool = is_new

    def __repr__(self) -> str:
        return (
            f'Substitution('
            f'group={self.group!r}, '
            f'day={self.day!r}, '
            f'lesson={self.lesson!r}, '
            f'teacher={self.teacher!r}, '
            f'subject={self.subject!r}, '
            f'room={self.room!r}, '
            f'notes={self.notes!r})'
        )
