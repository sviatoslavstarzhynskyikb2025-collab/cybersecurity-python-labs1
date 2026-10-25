import json
import sqlite3
from contextlib import closing
from pathlib import Path

from labs.lab03.database import get_connection, initialize_database

SEED_PATH = Path(__file__).resolve().parent / "data" / "seed.json"

EXPECTED_CATEGORIES = 3
EXPECTED_RECORDS = 8
REQUIRED_RECORD_FIELDS = {"code", "title", "category_id", "value", "status"}


def load_seed_data() -> dict:
    """Прочитати seed.json і перевірити його структуру."""
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))

    categories = data.get("categories")
    records = data.get("records")
    if not isinstance(categories, list) or not isinstance(records, list):
        raise TypeError("seed.json має містити масиви categories і records")
    if len(categories) != EXPECTED_CATEGORIES:
        raise ValueError(f"Очікується категорій: {EXPECTED_CATEGORIES}")
    if len(records) != EXPECTED_RECORDS:
        raise ValueError(f"Очікується записів: {EXPECTED_RECORDS}")

    for category in categories:
        if set(category) != {"id", "name"}:
            raise ValueError(f"Некоректна категорія: {category}")
    for record in records:
        if set(record) != REQUIRED_RECORD_FIELDS:
            raise ValueError(f"Некоректний запис: {record}")

    return data


def is_database_empty(connection: sqlite3.Connection) -> bool:
    """Перевірити, що в обох таблицях немає даних."""
    categories_count = connection.execute("SELECT COUNT(*) FROM categories").fetchone()[
        0
    ]
    records_count = connection.execute("SELECT COUNT(*) FROM records").fetchone()[0]
    return categories_count == 0 and records_count == 0


def seed_database() -> None:
    """Заповнити порожню базу початковими даними в одній транзакції."""
    try:
        data = load_seed_data()
    except (OSError, TypeError, ValueError) as error:
        print(f"Помилка початкових даних: {error}")
        return

    initialize_database()

    with closing(get_connection()) as connection:
        if not is_database_empty(connection):
            print("База не порожня: початкове заповнення пропущено.")
            return

        try:
            with connection:
                connection.executemany(
                    "INSERT INTO categories (id, name) VALUES (?, ?)",
                    [(item["id"], item["name"]) for item in data["categories"]],
                )
                connection.executemany(
                    "INSERT INTO records (code, title, category_id, value, status) "
                    "VALUES (?, ?, ?, ?, ?)",
                    [
                        (
                            item["code"],
                            item["title"],
                            item["category_id"],
                            item["value"],
                            item["status"],
                        )
                        for item in data["records"]
                    ],
                )
        except sqlite3.Error as error:
            print(f"Помилка запису в базу, зміни скасовано: {error}")
            return

    print(f"Додано категорій: {EXPECTED_CATEGORIES}, записів: {EXPECTED_RECORDS}.")


if __name__ == "__main__":
    seed_database()
