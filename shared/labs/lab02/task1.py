import hashlib
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

# константи
SESSION_TIMEOUT_SEC = 900  # час життя сеансу в секундах(15 хвилин)
HASH_ITERATIONS = 100_000  # кількість ітерацій для алгоритму хешування PBKDF2


class User:
    """базовий клас, що описує користувача системи"""

    def __init__(
        self, username: str, email: str, role: str = "user", active: bool = True
    ):
        self.username = username  # ім'я користувача
        self.email = email  # електронна пошта
        self.role = role  # роль користувача
        self.active = active  # статус активності
        self.__password_hash = None  # приховане поле для зберігання хешу пароля
        self.__password_salt = None  # приховане поле для зберігання солі пароля

    @property
    def email(self) -> str:
        """властивість (getter) для отримання значення електронної пошти"""
        return self._email

    @email.setter
    def email(self, value: str):
        """властивість (setter) для валідації та зміни електронної пошти"""
        # вираз перевіряє правильність структури email
        pattern = r"^[a-zA-Z][a-zA-Z0-9_]{2,63}@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, value):
            raise ValueError(
                f"невірний формат email: {value}"
            )  # викидаємо помилку, якщо формат невірний
        self._email = value

    def set_password(self, password: str):
        """метод для безпечної установки пароля із застосуванням солі та хешування"""
        if len(password) < 6:
            raise ValueError("пароль занадто короткий (мінімум 6 символів)")
        self.__password_salt = os.urandom(16)  # генеруємо випадкову 16-байтну сіль
        self.__password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), self.__password_salt, HASH_ITERATIONS
        )  # створюємо захищений хеш пароля за стандартом PBKDF2

    def check_password(self, password: str) -> bool:
        """метод для перевірки правильності введеного пароля"""
        if not self.__password_hash or not self.__password_salt:
            return False
        test_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), self.__password_salt, HASH_ITERATIONS
        )
        # безпечне порівняння двох хешів для захисту від timing attacks
        return hashlib.compare_digest(test_hash, self.__password_hash)

    def deactivate(self):
        """метод для деактивації користувача"""
        self.active = False

    def __str__(self):
        """рядкове представлення об'єкта User для виведення в консоль"""
        return f"User(username='{self.username}', email='{self.email}', role='{self.role}', active={self.active})"


class Admin(User):
    """клас адміністратора, що наслідує функціонал базового класу User"""

    def __init__(self, username: str, email: str, permissions: set | None = None):
        super().__init__(
            username, email, role="admin", active=True
        )  # виклик конструктора батьківського класу з роллю admin
        self.permissions = (
            set(permissions) if permissions is not None else set()
        )  # множина привілеїв

    def grant_permission(self, permission: str):
        """додати новий привілей адміністратору"""
        self.permissions.add(permission)

    def revoke_permission(self, permission: str):
        """забрати привілей у адміністратора"""
        self.permissions.discard(permission)

    def has_permission(self, permission: str) -> bool:
        """перевірити, чи володіє адміністратор певним привілеєм"""
        return permission in self.permissions

    def __str__(self):
        """розширене рядкове представлення для адміністратора з його правами"""
        base_str = super().__str__()
        return f"{base_str[:-1]}, permissions={list(self.permissions)})"


class Session:
    """клас для керування сеансом роботи користувача"""

    def __init__(self, ip: str, timeout_sec: int = SESSION_TIMEOUT_SEC):
        if timeout_sec <= 0:
            raise ValueError("timeout має бути позитивним числом")
        self.ip = ip  # IP-адреса клієнта
        self.login_time = datetime.now(timezone.utc)  # час створення сеансу в utc
        self.last_activity = self.login_time  # час останньої активності
        self.timeout_sec = timeout_sec  # допустимий час неактивності

    def touch(self):
        """оновлює час останньої активності користувача на поточний"""
        self.last_activity = datetime.now(timezone.utc)

    def is_active(self) -> bool:
        """перевіряє, чи не закінчився час сеансу (таймаут)"""
        now = datetime.now(timezone.utc)
        return (now - self.last_activity) <= timedelta(seconds=self.timeout_sec)


@dataclass
class AuditRecord:
    """структура даних для збереження одного запису в журналі подій"""

    timestamp: datetime  # час події
    username: str  # ім'я користувача, якого стосується подія
    action: str  # опис дії (наприклад, успішний вхід, вихід


class AuditLog:
    """клас для керування журналом подій аудиту"""

    def __init__(self):
        self.records: list[
            AuditRecord
        ] = []  # список для зберігання об'єктів AuditRecord

    def add_log(self, username: str, action: str):
        """створює новий запис аудиту з поточним часом та додає до списку"""
        record = AuditRecord(
            timestamp=datetime.now(timezone.utc), username=username, action=action
        )
        self.records.append(record)

    def show_all(self) -> list[AuditRecord]:
        """повертає весь список записів журналу аудиту"""
        return self.records


class UserAccount:
    """клас облікового запису, що об'єднує користувача, сеанс та журнал"""

    def __init__(self, user: User, audit_log: AuditLog = None):
        self._user = user  # об'єкт користувача
        self._session: Session | None = None  # поточний сеанс
        self._audit_log = (
            audit_log if audit_log is not None else AuditLog()
        )  # журнал аудиту

    def login(self, password: str, ip: str) -> bool:
        """спроба авторизації користувача в системі"""
        if not self._user.active:
            self._audit_log.add_log(self._user.username, "login_failure_inactive")
            return False

        if self._user.check_password(password):
            self._session = Session(ip)  # створюємо новий сеанс при успішному вході
            self._session.touch()
            self._audit_log.add_log(self._user.username, "login_success")
            return True
        else:
            self._audit_log.add_log(self._user.username, "login_failure_wrong_password")
            return False

    def is_authenticated(self) -> bool:
        """перевіряє, чи користувач зараз аутентифікований та має активну сесію"""
        if self._session is None:
            return False
        if self._session.is_active():
            return True
        else:
            # якщо час сеансу вийшов, скидаємо сесію
            self._session = None
            return False

    def logout(self):
        """завершення сеансу роботи (вихід з системи)"""
        if self._session is not None:
            self._audit_log.add_log(self._user.username, "logout")
            self._session = None

    def __getitem__(self, key: str):
        """магічний метод для доступу до внутрішніх компонентів через квадратні дужки (наприклад, account["user"])"""
        if key == "user":
            return self._user
        elif key == "session":
            return self._session
        elif key == "audit_log":
            return self._audit_log
        else:
            raise KeyError(f"евідомий ключ: {key}")

    def __setitem__(self, key: str, value):
        """магічний метод для зміни внутрішніх значень через квадратні дужки (наприклад, account["email"] = "...")."""
        if key == "user":
            if not isinstance(value, User):
                raise TypeError("значення повинно бути екземпляром класу User")
            self._user = value
        elif key == "email":
            # зміна пошти безпосередньо через індексатор із валідацією
            self._user.email = value
        else:
            raise KeyError(
                f"неможливо встановити значення для ключа або ключ не дозволений: {key}"
            )
