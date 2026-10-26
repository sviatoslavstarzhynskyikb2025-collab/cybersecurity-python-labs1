# Лабораторна робота №3. Облік часу реагування на інциденти (варіант 7)

Web API на FastAPI з базою SQLite (без ORM).

## Предметна область

Сервіс зберігає навчальні вимірювання часу реагування на інциденти.

- **categories**: тип інциденту (`account`, `network`, `endpoint`).
- **records**: вимірювання. Поле `value` це час реагування в **хвилинах** (`minutes`), число не менше 0, без верхньої межі, `NaN` та `inf` відхиляються.
- **status**: `new`, `in_progress`, `done`.
- Орієнтовний поріг: `30.0` хв.

## Встановлення

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Початкове заповнення бази

Запускати з кореня репозиторію:

```bash
python -m labs.lab03.seed
```

Повторний запуск нічого не змінює.

## Запуск API

```bash
uvicorn labs.lab03.main:app --reload --host 127.0.0.1 --port 8000
```

Документація: http://127.0.0.1:8000/docs

## Приклади запитів

```bash
curl -i "http://127.0.0.1:8000/ping"
curl -i "http://127.0.0.1:8000/student"
curl -i "http://127.0.0.1:8000/categories"
curl -i "http://127.0.0.1:8000/records?category_id=1&status=new&limit=5&offset=0"

curl -i -X POST "http://127.0.0.1:8000/records" \
  -H "Content-Type: application/json" \
  -d '{"code":"V07-TEST","title":"Навчальне вимірювання","category_id":1,"value":15.5,"status":"new"}'

curl -i -X POST "http://127.0.0.1:8000/records/bulk" \
  -H "Content-Type: application/json" \
  -d '[{"code":"V07-B1","title":"Пакет перший","category_id":1,"value":10.0,"status":"new"}]'
```

## Перевірка стилю

```bash
ruff check .
ruff format --check .
```