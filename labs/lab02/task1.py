import hashlib
import hmac
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

# іменовані константи замість
SESSION_TIMEOUT_SEC = 900  # час життя сеансу без активності в секундах (15 хвилин)
HASH_ITERATIONS = 100_000  # кількість ітерацій


class User:
    """базовий клас, що описує користувача системи"""

    def __init__(  # конструк авт. запуску
        self, username: str, email: str, role: str = "user", active: bool = True
    ):
        self.username = username
        # цей рядок автоматично викликає setter email, тому пошта перевіряється вже при створенні
        self.email = email
        self.role = role  # роль користувача
        self.active = active  # чи активний обліковий запис

        self.__password_hash = None  # приховане поле для хешу пароля
        self.__password_salt = None  # приховане поле для солі пароля

    @property
    def email(self) -> str:
        """властивість (getter) для отримання значення електронної пошти"""
        # повертаємо значення з захищеного поля _email захищене поле за домовленістю
        return self._email

    @email.setter
    def email(self, value: str):
        """властивість (setter) для валідації та зміни електронної пошти"""
        # перша літера латинська, потім 2-64 символи (літери, цифри, _), далі @ і домен з крапкою
        pattern = r"^[a-zA-Z][a-zA-Z0-9_]{2,63}@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        # re.match перевіряє, чи весь рядок відповідає шаблону
        if not re.match(pattern, value):
            # якщо формат невірний, зупиняємо виконання помилкою ValueError
            raise ValueError(f"невірний формат email: {value}")
        # якщо перевірка пройшла, зберігаємо пошту
        self._email = value

    def set_password(self, password: str):
        """метод для безпечної установки пароля із застосуванням солі та хешування"""
        # перевіряємо мінімальну довжину пароля
        if len(password) < 6:
            raise ValueError("пароль занадто короткий (мінімум 6 символів)")
        # сіль: випадкові 16 байт, у кожного користувача своя, тому однакові паролі дають різні хеші
        self.__password_salt = os.urandom(16)
        # рахуємо хеш пароля алгоритмом pbkdf2 (sha256, сіль, 100 000 ітерацій)
        # пароль у відкритому вигляді ніде не зберігається, лише хеш і сіль
        self.__password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), self.__password_salt, HASH_ITERATIONS
        )

    def check_password(self, password: str) -> bool:
        """метод для перевірки правильності введеного пароля"""
        # якщо пароль ще не встановлювали, перевіряти нема з чим
        if not self.__password_hash or not self.__password_salt:
            return False
        # рахуємо хеш введеного пароля з тією самою збереженою сіллю та кількістю ітерацій
        test_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), self.__password_salt, HASH_ITERATIONS
        )
        # compare_digest порівнює за сталий час, це захист від timing attack
        return hmac.compare_digest(test_hash, self.__password_hash)

    def deactivate(self):
        """метод для деактивації користувача"""
        # після деактивації login буде відхиляти цього користувача
        self.active = False

    def __str__(self):
        """рядкове представлення об'єкта User для виведення в консоль"""
        # пароль і хеш сюди не потрапляють навмисно
        return f"User(username='{self.username}', email='{self.email}', role='{self.role}', active={self.active})"


class Admin(User):
    """клас адміністратора, що наслідує функціонал базового класу User"""

    # permissions=None, а не set(): змінюваний типовий аргумент був би спільним для всіх об'єктів
    def __init__(self, username: str, email: str, permissions: set | None = None):
        # super() викликає конструктор User, роль одразу "admin"
        super().__init__(username, email, role="admin", active=True)
        # set(permissions) робить копію, щоб не залежати від зовнішньої множини
        self.permissions = set(permissions) if permissions is not None else set()

    def grant_permission(self, permission: str):
        """додати новий привілей адміністратору"""
        # add не створює дубліката, якщо право вже є
        self.permissions.add(permission)

    def revoke_permission(self, permission: str):
        """забрати привілей у адміністратора"""
        # discard не викликає помилку, якщо такого права немає (на відміну від remove)
        self.permissions.discard(permission)

    def has_permission(self, permission: str) -> bool:
        """перевірити, чи володіє адміністратор певним привілеєм"""
        # оператор in повертає True або False
        return permission in self.permissions

    def __str__(self):
        """розширене рядкове представлення для адміністратора з його правами"""
        # беремо рядок з батьківського класу
        base_str = super().__str__()
        # порядок прав може бути різним, бо множина (set) не зберігає порядок
        return f"{base_str[:-1]}, permissions={list(self.permissions)})"


class Session:
    """клас для керування сеансом роботи користувача"""

    def __init__(self, ip: str, timeout_sec: int = SESSION_TIMEOUT_SEC):
        # таймаут має бути додатним, інакше сеанс не мав би сенсу
        if timeout_sec <= 0:
            raise ValueError("timeout має бути позитивним числом")
        self.ip = ip  # IP-адреса клієнта
        # час у UTC з часовим поясом, щоб не було плутанини з локальним часом
        self.login_time = datetime.now(UTC)
        self.last_activity = (
            self.login_time
        )  # на початку остання активність = момент входу
        self.timeout_sec = timeout_sec  # скільки секунд сеанс може бути неактивним

    def touch(self):
        """оновлює час останньої активності користувача на поточний"""
        # викликається при вході та при дії користувача, "продовжує" сеанс
        self.last_activity = datetime.now(UTC)

    def is_active(self) -> bool:
        """перевіряє, чи не закінчився час сеансу (таймаут)"""
        now = datetime.now(UTC)  # поточний час
        # різниця між зараз і останньою активністю порівнюється з допустимим таймаутом
        return (now - self.last_activity) <= timedelta(seconds=self.timeout_sec)


# @dataclass сам генерує __init__, __repr__ та __eq__, тому не треба писати їх вручну
@dataclass
class AuditRecord:
    """структура даних для збереження одного запису в журналі подій"""

    timestamp: datetime  # час події (UTC)
    username: str  # ім'я користувача, якого стосується подія
    action: str  # опис дії (наприклад, login_success, logout)


class AuditLog:
    """клас для керування журналом подій аудиту"""

    def __init__(self):
        # список, у якому зберігаються всі записи аудиту
        self.records: list[AuditRecord] = []

    def add_log(self, username: str, action: str):
        """створює новий запис аудиту з поточним часом та додає до списку"""
        # час ставиться автоматично в момент запису, паролі в журнал не потрапляють
        record = AuditRecord(
            timestamp=datetime.now(UTC), username=username, action=action
        )
        self.records.append(record)  # додаємо запис у кінець списку

    def show_all(self) -> list[AuditRecord]:
        """повертає весь список записів журналу аудиту"""
        return self.records


class UserAccount:
    """клас облікового запису, що об'єднує користувача, сеанс та журнал"""

    # композиція (Has-A): акаунт містить User, Session та AuditLog, але не є ними
    def __init__(self, user: User, audit_log: AuditLog = None):
        self._user = user  # об'єкт користувача (передається ззовні)
        self._session: Session | None = None  # поточний сеанс, поки нема входу = None
        # якщо журнал не передали, створюємо новий
        self._audit_log = audit_log if audit_log is not None else AuditLog()

    def login(self, password: str, ip: str) -> bool:
        """спроба авторизації користувача в системі"""
        # 1. неактивний користувач не може увійти, навіть з правильним паролем
        if not self._user.active:
            self._audit_log.add_log(self._user.username, "login_failure_inactive")
            return False

        # 2. перевіряємо пароль через check_password
        if self._user.check_password(password):
            # сеанс створюється лише після успішної перевірки
            self._session = Session(ip)
            self._session.touch()  # фіксуємо час активності
            self._audit_log.add_log(self._user.username, "login_success")
            return True
        else:
            # 3. невірний пароль: пишемо в журнал і не створюємо та не продовжуємо сеанс
            self._audit_log.add_log(self._user.username, "login_failure_wrong_password")
            return False

    def is_authenticated(self) -> bool:
        """перевіряє, чи користувач зараз аутентифікований та має активну сесію"""
        # сеансу немає, значить не увійшов
        if self._session is None:
            return False
        # сеанс є і не прострочений
        if self._session.is_active():
            return True
        else:
            # час вийшов: скидаємо сеанс, вхід треба повторити
            self._session = None
            return False

    def logout(self):
        """завершення сеансу роботи (вихід з системи)"""
        # якщо сеансу немає, виходити нема з чого і в журнал нічого не пишемо
        if self._session is not None:
            self._audit_log.add_log(self._user.username, "logout")
            self._session = None  # завершуємо сеанс

    def __getitem__(self, key: str):
        """магічний метод для доступу до внутрішніх компонентів через квадратні дужки (наприклад, account["user"])"""
        # дозволені тільки три ключі, хеш і сіль пароля через ключі недоступні навмисно
        if key == "user":
            return self._user
        elif key == "session":
            return self._session
        elif key == "audit_log":
            return self._audit_log
        else:
            # невідомий ключ дає KeyError
            raise KeyError(f"невідомий ключ: {key}")

    def __setitem__(self, key: str, value):
        """магічний метод для зміни внутрішніх значень через квадратні дужки (наприклад, account["email"] = "...")."""
        if key == "user":
            # перевірка типу: підміняти користувача можна лише об'єктом User
            if not isinstance(value, User):
                raise TypeError("значення повинно бути екземпляром класу User")
            self._user = value
        elif key == "email":
            # це йде через setter email, тому валідація працює і тут
            self._user.email = value
        else:
            # інші ключі змінювати заборонено
            raise KeyError(
                f"неможливо встановити значення для ключа або ключ не дозволений: {key}"
            )
