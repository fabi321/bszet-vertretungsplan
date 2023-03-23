from pathlib import Path

from substitution_parsing.PDFHandling import PDF

if __name__ == '__main__':
    pdf = PDF.from_file(Path('vertretungsplan-bs-et.pdf'), 'bs-et')
    for table in pdf.tables:
        print(str(table))
    print(pdf.to_substitutions())

