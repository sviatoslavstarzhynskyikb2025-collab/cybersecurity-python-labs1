import sqlite3
from contextlib import closing

from labs.lab03.database import get_connection


class NotFoundError(Exception):
    """Запис або категорію не знайдено."""


class ConflictError(Exception):
    """Дублікат унікального значення або категорія містить записи."""


RECORD_SELECT = (
    "SELECT r.id, r.code, r.title, r.category_id, r.value, r.status, "
    "c.name AS category_name "
    "FROM records AS r JOIN categories AS c ON c.id = r.category_id "
)


def _category_exists(connection: sqlite3.Connection, category_id: int) -> bool:
    row = connection.execute(
        "SELECT 1 FROM categories WHERE id = ?", (category_id,)
    ).fetchone()
    return row is not None


def _fetch_record(connection: sqlite3.Connection, record_id: int) -> dict:
    row = connection.execute(RECORD_SELECT + "WHERE r.id = ?", (record_id,)).fetchone()
    if row is None:
        raise NotFoundError("Запис не знайдено")
    return dict(row)


def _connect() -> sqlite3.Connection:
    connection = get_connection()
    connection.row_factory = sqlite3.Row
    return connection


# ---------- Категорії ----------


def create_category(name: str) -> dict:
    """Створити категорію."""
    with closing(_connect()) as connection:
        try:
            with connection:
                cursor = connection.execute(
                    "INSERT INTO categories (name) VALUES (?)", (name,)
                )
        except sqlite3.IntegrityError as error:
            raise ConflictError("Категорія з такою назвою вже існує") from error
        return {"id": cursor.lastrowid, "name": name}


def list_categories() -> list[dict]:
    """Список категорій за зростанням id."""
    with closing(_connect()) as connection:
        rows = connection.execute(
            "SELECT id, name FROM categories ORDER BY id ASC"
        ).fetchall()
        return [dict(row) for row in rows]


def delete_category(category_id: int) -> None:
    """Видалити порожню категорію."""
    with closing(_connect()) as connection:
        if not _category_exists(connection, category_id):
            raise NotFoundError("Категорію не знайдено")
        try:
            with connection:
                connection.execute(
                    "DELETE FROM categories WHERE id = ?", (category_id,)
                )
        except sqlite3.IntegrityError as error:
            raise ConflictError("Категорія містить записи") from error


# ---------- Записи ----------


def create_record(
    code: str, title: str, category_id: int, value: float, status: str
) -> dict:
    """Додати запис."""
    with closing(_connect()) as connection:
        if not _category_exists(connection, category_id):
            raise NotFoundError("Категорію не знайдено")
        try:
            with connection:
                cursor = connection.execute(
                    "INSERT INTO records (code, title, category_id, value, status) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (code, title, category_id, value, status),
                )
        except sqlite3.IntegrityError as error:
            raise ConflictError("Запис з таким code вже існує") from error
        return _fetch_record(connection, cursor.lastrowid)


def get_record(record_id: int) -> dict:
    """Отримати запис за id."""
    with closing(_connect()) as connection:
        return _fetch_record(connection, record_id)


def list_records(
    category_id: int | None = None,
    status: str | None = None,
    min_value: float | None = None,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    """Список записів із фільтрами та поділом на сторінки."""
    conditions: list[str] = []
    params: list = []
    if category_id is not None:
        conditions.append("r.category_id = ?")
        params.append(category_id)
    if status is not None:
        conditions.append("r.status = ?")
        params.append(status)
    if min_value is not None:
        conditions.append("r.value >= ?")
        params.append(min_value)
    if q is not None:
        conditions.append("instr(r.title, ?) > 0")
        params.append(q)

    query = RECORD_SELECT
    if conditions:
        query += "WHERE " + " AND ".join(conditions) + " "
    query += "ORDER BY r.id ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with closing(_connect()) as connection:
        rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def replace_record(
    record_id: int,
    code: str,
    title: str,
    category_id: int,
    value: float,
    status: str,
) -> dict:
    """Повністю замінити змінювані поля запису."""
    with closing(_connect()) as connection:
        _fetch_record(connection, record_id)
        if not _category_exists(connection, category_id):
            raise NotFoundError("Категорію не знайдено")
        try:
            with connection:
                connection.execute(
                    "UPDATE records SET code = ?, title = ?, category_id = ?, "
                    "value = ?, status = ? WHERE id = ?",
                    (code, title, category_id, value, status, record_id),
                )
        except sqlite3.IntegrityError as error:
            raise ConflictError("Запис з таким code вже існує") from error
        return _fetch_record(connection, record_id)


def delete_record(record_id: int) -> None:
    """Видалити запис."""
    with closing(_connect()) as connection:
        with connection:
            cursor = connection.execute(
                "DELETE FROM records WHERE id = ?", (record_id,)
            )
        if cursor.rowcount == 0:
            raise NotFoundError("Запис не знайдено")


def create_records_bulk(items: list[dict]) -> list[dict]:
    """Атомарно додати пакет записів в одній транзакції."""
    with closing(_connect()) as connection:
        try:
            with connection:
                new_ids: list[int] = []
                for item in items:
                    if not _category_exists(connection, item["category_id"]):
                        raise NotFoundError("Категорію не знайдено")
                    cursor = connection.execute(
                        "INSERT INTO records "
                        "(code, title, category_id, value, status) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (
                            item["code"],
                            item["title"],
                            item["category_id"],
                            item["value"],
                            item["status"],
                        ),
                    )
                    new_ids.append(cursor.lastrowid)
        except sqlite3.IntegrityError as error:
            raise ConflictError("Дублікат code у пакеті або в базі") from error
        return [_fetch_record(connection, record_id) for record_id in new_ids]
