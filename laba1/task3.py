import csv
import datetime
import hashlib
import json
import os
import sys  # імпорт сист. шляху

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

try:
    from shared.student import STUDENT_NAME, VARIANT_NUMBER  # імпортуємо дані з модуля
except ImportError:
    STUDENT_NAME = "студент"
    VARIANT_NUMBER = 7


class ValidationError(Exception):
    """кастомний виняток для помилок валідації довжини пароля."""



def generate_hash(
    password: str, salt: str = "00007"
) -> str:  # функц. хешування (варіант 7: sha384, мін. довжина = 15 символів)
    """генерує sha384 хеш для пароля з додаванням персональної солі."""

    if (
        not password or not salt
    ):  # перевірка на порожній пароль або сіль (вимога: згенерувати ValueError)
        raise ValueError("Пароль та сіль не можуть бути порожніми!")

    if (
        len(password) < 15
    ):  # Перевірка на мінімальну довжину для Варіанта 7 (Вимога: згенерувати ValidationError)
        raise ValidationError("Пароль коротший за мінімальну довжину (15 символів)!")

    salted_password = password + salt  # об'єднання пароля та солі

    return (
        hashlib.sha384(salted_password.encode("utf-8")).hexdigest()
    )  # перетворення рядка в байти (utf-8) та обчислення sha384 у 16-нковому вигляді


def log_event(func):  # декоратор логування подій @log_event
    """декоратор, який перехоплює результат роботи login() та записує спробу в log.json."""

    def wrapper(username, password):
        result, status_str = func(
            username, password
        )  # виконуємо безпосередньо функцію входу login()

        log_entry = {  # формуємо структуру логу
            "event": "login",
            "user": username,
            "result": status_str,  # "success" або "failure"
            "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),  # точна дата й час
            "args": [username],
            "kwargs": {},
        }

        os.makedirs(
            "laba1/data", exist_ok=True
        )  # автоматичне створення директорії laba1/data, якщо її немає
        log_file_path = "laba1/data/log.json"

        logs = []  # читаємо існуючі логи з файлу, якщо файл уже існує
        if os.path.exists(log_file_path):
            try:
                with open(log_file_path, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            except json.JSONDecodeError:
                logs = []

        logs.append(log_entry)  # додаємо новий запис до загального списку

        # записуємо оновлений список назад у log.json
        with open(log_file_path, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=4, ensure_ascii=False)

        # повертаємо підсумковий результат автентифікації (True або False)
        return result

    return wrapper


# реєстр. корист та збереження в csv
def create_user(username: str, password: str) -> tuple:
    """створює кортеж (логін, хеш_пароля) для одного користувача."""
    hash_value = generate_hash(password)
    return (username, hash_value)


def create_users_db():
    """створює базу даних користувачів та зберігає її у laba1/data/users.csv."""
    os.makedirs("laba1/data", exist_ok=True)

    # кортеж із 10 користувачів (паролі мають довжину >= 15 символів відповідно до мого варіанту)
    users_to_register = (
        ("admin_user", "SuperSecurePass123!"),
        ("sec_analyst", "CyberSecurity_2023#"),
        ("dev_master", "CodeDeveloper_99!"),
        ("net_admin", "NetworkShield_384#"),
        ("auditor", "AuditAccess_777!"),
        ("sys_op", "SystemOperation_12"),
        ("threat_hunter", "HuntingThreats_007"),
        ("incident_mgr", "IncidentControl_911"),
        ("crypto_expert", "CryptoHashing_384!"),
        ("guest_user", "GuestAccountPass_1"),
    )

    db_path = "laba1/data/users.csv"
    # відкриваємо файл на запис CSV
    with open(db_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for username, password in users_to_register:
            user_entry = create_user(username, password)
            writer.writerow(user_entry)  # записуємо рядок "логін,хеш"

    print(" Базу даних створено: laba1/data/users.csv")


# читання бази даних з csv
def read_users_db() -> dict:
    """зчитує вміст CSV-файлу та повертає словник {логін: хеш}."""
    db_path = "laba1/data/users.csv"
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"файл {db_path} не знайдено!")

    users_db = {}
    with open(db_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                users_db[row[0]] = row[1]  # row[0] - логін, row[1] - хеш
    return users_db


# функція аутентифікації сполучена з декоратором
@log_event  # викликає декоратор log_event під час кожної спроби входу
def login(username: str, password: str) -> tuple:
    """перевіряє введений логін і пароль проти збереженого хешу в CSV."""
    if not username or not password:
        raise ValueError("логін або пароль не можуть бути порожніми!")

    users_db = read_users_db()

    if username not in users_db:  # перевірка, чи є такий користувач у базі даних
        return False, "failure"

    try:
        input_hash = generate_hash(
            password
        )  # хешуємо пароль, який ввів користувач при вході
        if (
            users_db[username] == input_hash
        ):  # порівнюємо його із хешем, що збережений у CSV
            return True, "success"
    except ValidationError:
        pass  # якщо пароль занадто короткий, вхід просто відхиляється

    return False, "failure"


# головна функція
def main():
    print(f"виконання Завдання 3 | Студент: {STUDENT_NAME} (Варіант {VARIANT_NUMBER})")

    try:
        create_users_db()  # крок A: генеруємо CSV базу

        print(
            "\nЗчитаний вміст CSV-бази даних"
        )  # крок B: виводимо вміст бази у баченні таблиці
        users_db = read_users_db()
        for user, pwd_hash in users_db.items():
            print(f"користувач: {user:<15} | хеш: {pwd_hash[:30]}...")

        print("\n Спроби аутентифікації")  # Крок C: тестуємо успішний та невдалий вхід

        # 1.тест з правильним паролем
        res1 = login("admin_user", "SuperSecurePass123!")
        print(
            f"спроба 1 (admin_user + вірний пароль): {' УСПІШНО' if res1 else ' ПОМИЛКА'}"
        )

        # 2.тест з неправильним паролем
        res2 = login("admin_user", "WrongPassword123!")
        print(
            f"спроба 2 (admin_user + невірний пароль): {' УСПІШНО' if res2 else ' ВІДХИЛЕНО'}"
        )

        print("\n події успішно відлоговано у файл laba1/data/log.json")

    except (OSError, FileNotFoundError, PermissionError, ValidationError, ValueError) as e:
        print(f"перехоплено виняток: {e}")


if __name__ == "__main__":
    main()
