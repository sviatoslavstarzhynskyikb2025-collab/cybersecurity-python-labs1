import logging
import sqlite3

from fastapi import APIRouter, HTTPException, Path, Response, status

from labs.lab03 import repository
from labs.lab03.schemas import CategoryCreate, CategoryRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get(
    "",
    response_model=list[CategoryRead],
    summary="Список категорій",
)
def list_categories() -> list[dict]:
    """Повернути всі категорії за зростанням id."""
    try:
        return repository.list_categories()
    except sqlite3.Error as error:
        logger.exception("Помилка читання категорій")
        raise HTTPException(500, "Внутрішня помилка сервера") from error


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Створити категорію",
    responses={409: {"description": "Категорія з такою назвою вже існує"}},
)
def create_category(payload: CategoryCreate) -> dict:
    """Створити нову категорію."""
    try:
        return repository.create_category(payload.name)
    except repository.ConflictError as error:
        raise HTTPException(409, str(error)) from error
    except sqlite3.Error as error:
        logger.exception("Помилка створення категорії")
        raise HTTPException(500, "Внутрішня помилка сервера") from error


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити порожню категорію",
    responses={
        404: {"description": "Категорію не знайдено"},
        409: {"description": "Категорія містить записи"},
    },
)
def delete_category(
    category_id: int = Path(gt=0, description="Ідентифікатор категорії"),
) -> Response:
    """Видалити категорію, якщо в ній немає записів."""
    try:
        repository.delete_category(category_id)
    except repository.NotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except repository.ConflictError as error:
        raise HTTPException(409, str(error)) from error
    except sqlite3.Error as error:
        logger.exception("Помилка видалення категорії")
        raise HTTPException(500, "Внутрішня помилка сервера") from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
