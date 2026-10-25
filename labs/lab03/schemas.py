from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Status = Literal["new", "in_progress", "done"]


class CategoryCreate(BaseModel):
    """Дані для створення категорії."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=2, max_length=40)


class CategoryRead(CategoryCreate):
    """Категорія у відповіді API."""

    id: int


class RecordCreate(BaseModel):
    """Дані для створення запису (час реагування в хвилинах)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    code: str = Field(min_length=3, max_length=40)
    title: str = Field(min_length=3, max_length=120)
    category_id: int = Field(gt=0)
    value: float = Field(ge=0, allow_inf_nan=False)
    status: Status


class RecordReplace(RecordCreate):
    """Повна заміна запису: усі змінювані поля обов'язкові."""


class RecordRead(RecordCreate):
    """Запис у відповіді API."""

    id: int
    category_name: str
