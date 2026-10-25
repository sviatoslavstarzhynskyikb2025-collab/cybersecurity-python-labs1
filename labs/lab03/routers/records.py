import logging
import sqlite3
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, Response
from fastapi import status as http_status

from labs.lab03 import repository
from labs.lab03.schemas import RecordCreate, RecordRead, RecordReplace, Status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/records", tags=["records"])

NOT_FOUND = {404: {"description": "Запис або категорію не знайдено"}}
CONFLICT = {409: {"description": "Запис з таким code вже існує"}}
SERVER_ERROR = "Внутрішня помилка сервера"


@router.get(
    "",
    response_model=list[RecordRead],
    summary="Список записів із фільтрами",
)
def list_records(
    category_id: Annotated[
        int | None, Query(gt=0, description="Лише записи цієї категорії")
    ] = None,
    status: Annotated[
        Status | None, Query(description="Лише записи з цим статусом")
    ] = None,
    min_value: Annotated[
        float | None,
        Query(ge=0, allow_inf_nan=False, description="value >= min_value (хвилини)"),
    ] = None,
    q: Annotated[
        str | None,
        Query(min_length=1, max_length=120, description="Підрядок у title"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Макс. кількість")] = 20,
    offset: Annotated[int, Query(ge=0, description="Скільки пропустити")] = 0,
) -> list[dict]:
    """Повернути записи, відсортовані за id."""
    try:
        return repository.list_records(
            category_id=category_id,
            status=status,
            min_value=min_value,
            q=q,
            limit=limit,
            offset=offset,
        )
    except sqlite3.Error as error:
        logger.exception("Помилка читання записів")
        raise HTTPException(500, SERVER_ERROR) from error


@router.post(
    "/bulk",
    response_model=list[RecordRead],
    status_code=http_status.HTTP_201_CREATED,
    summary="Пакетне створення записів",
    responses={**NOT_FOUND, **CONFLICT},
)
def create_records_bulk(payload: list[RecordCreate]) -> list[dict]:
    """Атомарно створити від 1 до 100 записів."""
    if not 1 <= len(payload) <= 100:
        raise HTTPException(422, "Пакет має містити від 1 до 100 елементів")
    try:
        return repository.create_records_bulk([item.model_dump() for item in payload])
    except repository.NotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except repository.ConflictError as error:
        raise HTTPException(409, str(error)) from error
    except sqlite3.Error as error:
        logger.exception("Помилка пакетного створення")
        raise HTTPException(500, SERVER_ERROR) from error


@router.get(
    "/{record_id}",
    response_model=RecordRead,
    summary="Отримати запис",
    responses=NOT_FOUND,
)
def get_record(
    record_id: int = Path(gt=0, description="Ідентифікатор запису"),
) -> dict:
    """Повернути один запис."""
    try:
        return repository.get_record(record_id)
    except repository.NotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except sqlite3.Error as error:
        logger.exception("Помилка читання запису")
        raise HTTPException(500, SERVER_ERROR) from error


@router.post(
    "",
    response_model=RecordRead,
    status_code=http_status.HTTP_201_CREATED,
    summary="Створити запис",
    responses={**NOT_FOUND, **CONFLICT},
)
def create_record(payload: RecordCreate) -> dict:
    """Створити запис."""
    try:
        return repository.create_record(**payload.model_dump())
    except repository.NotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except repository.ConflictError as error:
        raise HTTPException(409, str(error)) from error
    except sqlite3.Error as error:
        logger.exception("Помилка створення запису")
        raise HTTPException(500, SERVER_ERROR) from error


@router.put(
    "/{record_id}",
    response_model=RecordRead,
    summary="Повністю замінити запис",
    responses={**NOT_FOUND, **CONFLICT},
)
def replace_record(
    payload: RecordReplace,
    record_id: int = Path(gt=0, description="Ідентифікатор запису"),
) -> dict:
    """Замінити всі змінювані поля запису; id не змінюється."""
    try:
        return repository.replace_record(record_id, **payload.model_dump())
    except repository.NotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except repository.ConflictError as error:
        raise HTTPException(409, str(error)) from error
    except sqlite3.Error as error:
        logger.exception("Помилка заміни запису")
        raise HTTPException(500, SERVER_ERROR) from error


@router.delete(
    "/{record_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    summary="Видалити запис",
    responses=NOT_FOUND,
)
def delete_record(
    record_id: int = Path(gt=0, description="Ідентифікатор запису"),
) -> Response:
    """Видалити запис."""
    try:
        repository.delete_record(record_id)
    except repository.NotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except sqlite3.Error as error:
        logger.exception("Помилка видалення запису")
        raise HTTPException(500, SERVER_ERROR) from error
    return Response(status_code=http_status.HTTP_204_NO_CONTENT)
