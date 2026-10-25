import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from labs.lab03 import config
from labs.lab03.database import initialize_database
from labs.lab03.routers import categories, records
from shared import student

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Створити відсутні таблиці під час запуску; дані не змінюються."""
    initialize_database()
    yield


app = FastAPI(
    title="Облік часу реагування на інциденти",
    description=(
        f"{config.DOMAIN}. Кожен запис містить час реагування у хвилинах "
        f"(поле value, одиниця: {config.UNIT}, не менше 0). "
        f"Орієнтовний поріг: {config.THRESHOLD} хв."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(categories.router)
app.include_router(records.router)


@app.get("/ping", summary="Перевірка доступності API", tags=["service"])
def ping() -> dict[str, str]:
    """Повернути стан сервісу."""
    return {"status": "ok"}


@app.get("/student", summary="Дані студента", tags=["service"])
def get_student() -> dict:
    """Повернути ПІБ, групу та номер варіанта."""
    return {
        "student_name": student.STUDENT_NAME,
        "group_name": student.GROUP_NAME,
        "variant_number": student.VARIANT_NUMBER,
    }
