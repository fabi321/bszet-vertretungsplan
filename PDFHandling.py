from __future__ import annotations

import re
from pathlib import Path

from PyPDF2 import PdfReader


CELL_REGEX: str = r'([^.]+)\.{3}\s*'
DATE_REGEX: str = r'[0-9]{2}\.[0-9]{2}\.[0-9]{4}'
LINE_REGEX: re.Pattern = re.compile(fr'{CELL_REGEX*7}\.?[0-9]*\.*\s*(?:([a-zA-Z]+)\.{{3}}\s*({DATE_REGEX})\.{{3}})?')


class PDF:
    def __init__(self, pdf_string: str):
        self.pdf_string: str = pdf_string

    def parse_string_content(self):
        for line in reversed(LINE_REGEX.findall(self.pdf_string)):
            print(line)

    @staticmethod
    def from_file(file: Path) -> PDF:
        reader: PdfReader = PdfReader(file)
        pdf_string: str = '\n'.join(page.extract_text() for page in reader.pages)
        return PDF(pdf_string)


if __name__ == '__main__':
    pdf = PDF('''
Dammmüller... Aufgaben Herr Ränsch... C_IT 20/3... A302... IT-LF11b... +Dammmüller (Ränsch)... 6....6....Dammmüller... Aufgaben Herr Ränsch... C_IT 20/3... A302... IT-LF11b... +Dammmüller (Ränsch)... 5....5.... Di... 24.01.2023...VLehrer Kürzel... Mitteilung... Klasse... Raum... Fach... Lehrer... Pos... Tag... Datum...Mo 23.01.2023 bis Di 24.01.2023C_IT 20/3
Wittkopf... Aufgaben Herr Poppe... C_MI 21/3... B411... FBP-FE... +Wittkopf (Poppe)... 6....6....Wittkopf... Aufgaben Herr Poppe... C_MI 21/3... B411... FBP-FE... +Wittkopf (Poppe)... 5....5....Wittkopf... statt 1./2. Stunde... C_MI 21/3... B411... FBP-FE... +Wittkopf (Poppe)... 4....4....Wittkopf... statt 1./2. Stunde... C_MI 21/3... B411... FBP-FE... +Wittkopf (Poppe)... 3....3.... fällt aus... C_MI 21/3... B406... FP-FV... (Wittkopf)... 2....2.... fällt aus... C_MI 21/3... B406... FP-FV... (Wittkopf)... 1....1.... Mo... 23.01.2023...VLehrer Kürzel... Mitteilung... Klasse... Raum... Fach... Lehrer... Pos... Tag... Datum...Mo 23.01.2023 bis Di 24.01.2023C_MI 21/3
 Aufgaben über LernSax... C_MI 22/3... B9, B404... FP-CHE... (Kunitzsch)... 8....8.... Aufgaben über LernSax... C_MI 22/3... B9, B404... FP-CHE... (Kunitzsch)... 7....7.... fällt aus... C_MI 22/3... B405... FP-RR... (Wollmann)... 2....2.... fällt aus... C_MI 22/3... B405... FP-RR... (Wollmann)... 1....1.... Mo... 23.01.2023...VLehrer Kürzel... Mitteilung... Klasse... Raum... Fach... Lehrer... Pos... Tag... Datum...Mo 23.01.2023 bis Di 24.01.2023C_MI 22/3'''
              )
    pdf.parse_string_content()
