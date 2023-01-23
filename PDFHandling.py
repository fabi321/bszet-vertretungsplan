from __future__ import annotations

import datetime
import io
import re
from pathlib import Path
from typing import Optional

from PyPDF2 import PdfReader

from Substitution import Substitution
from table_parser import parse_tables, Table

DOT_REGEX: re.Pattern = re.compile(r'\.+$')


class PDF:
    def __init__(self, reader: PdfReader):
        self.reader: PdfReader = reader
        self.tables: list[Table] = parse_tables(reader)
        self.__cleanup_tables()

    @staticmethod
    def __remove_dots_from_row(row: list[Optional[str]]):
        for i, cell in enumerate(row):
            if cell:
                row[i] = DOT_REGEX.sub('', cell)

    def __cleanup_tables(self):
        for table in self.tables:
            PDF.__remove_dots_from_row(table.head)
            last_date: str = ''
            last_day: str = ''
            for row in table.rows:
                PDF.__remove_dots_from_row(row)
                if row[0]:
                    last_date = row[0]
                    last_day = row[1]
                else:
                    row[0] = last_date
                    row[1] = last_day

    def to_substitutions(self) -> list[Substitution]:
        substitutions: list[Substitution] = []
        for table in self.tables:
            for row in table.rows:
                date: datetime.datetime = datetime.datetime.strptime(row[0], '%d.%m.%Y')
                substitutions.append(
                    Substitution(
                        row[6],
                        round(date.timestamp()),
                        int(row[2]),
                        row[3],
                        row[4],
                        row[5],
                        row[7],
                    )
                )
        return substitutions

    @staticmethod
    def from_file(file: Path) -> PDF:
        reader: PdfReader = PdfReader(file)
        return PDF(reader)

    @staticmethod
    def from_bytes(content: bytes) -> PDF:
        with io.BytesIO(content) as pdf_file:
            reader: PdfReader = PdfReader(pdf_file)
            return PDF(reader)


if __name__ == '__main__':
    pdf = PDF.from_file(Path('vertretungsplan-bs-it.pdf'))
