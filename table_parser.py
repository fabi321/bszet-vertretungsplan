import re
from statistics import median_high
from typing import Optional

from PyPDF2 import PdfReader

Elements = dict[float, dict[float, str]]

DATE_REGEX: re.Pattern = re.compile(r'[a-zA-Z] [0-9]{2}\.[0-9]{2}\.[0-9]{2,4}')


class Table:
    def __init__(self):
        self.rows: list[list[Optional[str]]] = []
        self.head: list[str] = []
        self.__column_positions: list[float] = []
        self.title: Optional[str] = None

    def __get_row_index(self, position: float) -> int:
        return min(((abs(position - v), i) for i, v in enumerate(self.__column_positions)), key=lambda x: x[0])[1]

    def __format_row(self, row: dict[float, str]) -> list[Optional[str]]:
        result: list[Optional[str]] = [None for _ in range(len(self.__column_positions))]
        for column in row.items():
            idx: int = self.__get_row_index(column[0])
            result[idx] = column[1]
        return result

    def add_row(self, row: dict[float, str]):
        if not self.head:
            self.__column_positions = list(sorted(row.keys()))
        formatted_row: list[Optional[str]] = self.__format_row(row)
        if self.head:
            self.rows.append(formatted_row)
        else:
            self.head = formatted_row

    def __bool__(self) -> bool:
        return bool(self.head or self.rows)

    def __str__(self) -> str:
        result: str = str(self.title) + '\n'
        result += '|' + '|'.join(str(i) for i in self.head) + '|\n'
        result += '|' + '|'.join('-' * len(i) for i in self.head) + '|\n'
        for row in self.rows:
            result += '|' + '|'.join(str(i) for i in row) + '|\n'
        return result


def create_visitor(elements: Elements, page_offset: int):
    def visitor(text: str, cm, tm, *_):
        text = text.strip()
        if not text:
            return
        x: float = cm[4]
        y: float = -cm[5] + page_offset
        if tm[5] < 1000:
            x += tm[4]
            y += tm[5]
        if not elements.get(y):
            elements[y] = {}
        elements[y][x] = text

    return visitor


def parse_tables(file: PdfReader) -> list[Table]:
    elements: Elements = {}
    page_offset: int = 0

    for page in file.pages:
        page.extract_text(visitor_text=create_visitor(elements, page_offset))
        page_offset += float(page.mediabox.height)

    lines: list[float] = list(sorted(k for k, v in elements.items() if len(v) > 2))
    distances: list[float] = [f - c for c, f in zip(lines, lines[1:])]
    median_dist: float = median_high(distances)

    results: list[Table] = []
    last_y: float = 0.0
    current_table: Table = Table()

    for y in sorted(elements.keys()):
        row: dict[float, str] = elements[y]
        is_distant: bool = y - last_y > 30
        if is_distant and current_table:
            results.append(current_table)
            current_table = Table()
        if len(row) <= 2:
            joined: str = ' '.join(row.values())
            if DATE_REGEX.search(joined):
                current_table.title = joined
        else:
            if current_table.title:
                current_table.add_row(row)
            else:
                results[-1].add_row(row)
            last_y = y

    if current_table:
        results.append(current_table)

    return results
