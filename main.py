from pathlib import Path

from DB import DB


def main():
    db: DB = DB(Path('Database.db'))
    print(db.get_latest_credential())


if __name__ == "__main__":
    main()
