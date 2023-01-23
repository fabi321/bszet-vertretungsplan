from __future__ import annotations

import re
from typing import Optional
from pathlib import Path

from PyPDF2 import PdfReader

from table_parser import parse_tables, Table


DOT_REGEX: re.Pattern = re.compile(r'\.+$')


class PDF:
    def __init__(self, reader: PdfReader):
        self.reader: PdfReader = reader
        self.tables: list[Table] = parse_tables(reader)
        self.__cleanup_tables()
        for table in self.tables:
            print(str(table))

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


    @staticmethod
    def from_file(file: Path) -> PDF:
        reader: PdfReader = PdfReader(file)
        return PDF(reader)


if __name__ == '__main__':
    pdf = PDF.from_file(Path('vertretungsplan-bs-it.pdf'))
