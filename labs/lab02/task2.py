import csv
import json
import logging
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# налаштовуємо логування
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
# логер для цього модуля, через нього пишемо всі повідомлення
logger = logging.getLogger(__name__)


class UserActivityAnalyzer:
    """аналізатор логів для виявлення аномальної активності користувачів"""

    def __init__(self, log_file_path: str | Path) -> None:
        """ініціалізація аналізатора шляхом до файлу логів"""
        # перетворюємо шлях на об'єкт Path (зручніше і безпечніше за звичайний рядок та os.path)
        self.log_file_path = Path(log_file_path)
        # список прочитаних рядків, кожен рядок це словник виду {"UserID": ..., "Action": ...}
        self.logs: list[dict[str, str]] = []

    def load_logs(self) -> None:
        """читає CSV-файл дій користувачів (Timestamp, UserID, Action, Resource, IP)"""
        # спочатку перевіряємо, чи файл існує, щоб дати зрозумілу помилку
        if not self.log_file_path.exists():
            raise FileNotFoundError(f"файл не знайдено: {self.log_file_path}")

        # повідомлення рівня INFO про початок читання
        logger.info(f"reading user activity log {self.log_file_path}...")

        # with автоматично закриє файл, навіть якщо станеться помилка
        # encoding utf-8 потрібен, щоб правильно читалась кирилиця
        with open(self.log_file_path, mode="r", encoding="utf-8") as file:
            # DictReader бере перший рядок як назви колонок і віддає кожен рядок як словник
            reader = csv.DictReader(file)
            # зберігаємо всі рядки таблиці у список
            self.logs = [row for row in reader]

        # повідомляємо, скільки записів прочитано
        logger.info(f"total records processed: {len(self.logs)}.")

    def group_by_user(self) -> defaultdict[str, list[dict[str, str]]]:
        """групує дії за користувачами за допомогою collections.defaultdict"""
        # defaultdict(list): якщо ключа ще немає, автоматично створюється порожній список
        # тому не треба вручну перевіряти "чи є такий користувач"
        user_actions = defaultdict(list)

        # проходимо по всіх записах
        for log in self.logs:
            # get повертає "unknown", якщо в рядку немає поля UserID
            user_id = log.get("UserID", "unknown")
            # додаємо подію до списку цього користувача
            user_actions[user_id].append(log)

        # результат виду {"j_smith": [запис1, запис2], "admin": [запис3]}
        return user_actions

    def detect_after_hours(self) -> list[dict[str, Any]]:
        """виявляє дії, виконані у позаробочий час (22:00 - 06:00 або вихідні)"""
        # сюди збираємо всі знайдені підозрілі події
        alerts = []

        # перебираємо кожен запис журналу
        for log in self.logs:
            # беремо текст дати й часу, якщо поля немає, буде порожній рядок
            timestamp_str = log.get("Timestamp", "")

            try:
                # strptime перетворює рядок на datetime за заданим форматом
                # replace(tzinfo=UTC) додає часовий пояс UTC
                dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=UTC
                )
            except ValueError:
                # якщо формат дати пошкоджений, пропускаємо цей рядок і йдемо до наступного
                continue

            # ніч: з 22:00 до 06:00 (година 22 і більше або менше 6)
            is_night = dt.hour >= 22 or dt.hour < 6
            # вихідний: weekday() дає 0 для понеділка, 5 для суботи, 6 для неділі
            is_weekend = dt.weekday() >= 5

            # достатньо одного з двох умов: або ніч, або вихідний
            if is_night or is_weekend:
                # формуємо словник з даними про підозрілу подію
                alert = {
                    "UserID": log.get("UserID"),
                    "Action": log.get("Action"),
                    "Resource": log.get("Resource"),
                    "Timestamp": timestamp_str,
                    "IP": log.get("IP"),
                    "Reason": "After-hours activity",
                }
                # додаємо подію до загального списку
                alerts.append(alert)

                # пишемо попередження рівня WARNING (воно з'являється в консолі)
                logger.warning(
                    f"[ALERT] User '{log.get('UserID')}' performed {log.get('Action')} "
                    f"at {timestamp_str} (Resource: {log.get('Resource')})"
                )

        # повертаємо список усіх знайдених позаробочих подій
        return alerts

    def save_report(self, report_path: str | Path, data: Any) -> None:
        """Зберігає підозрілі події у JSON-файл."""
        # перетворюємо шлях на Path
        path = Path(report_path)
        # створюємо папку для звіту, якщо її ще немає
        # parents=True створює і проміжні папки, exist_ok=True не дає помилки, якщо папка вже є
        path.parent.mkdir(parents=True, exist_ok=True)

        # відкриваємо файл для запису (mode="w" перезаписує старий вміст)
        with open(path, mode="w", encoding="utf-8") as f:
            # indent=4 робить JSON читабельним з відступами
            # ensure_ascii=False зберігає кирилицю як є, без \u0441
            json.dump(data, f, indent=4, ensure_ascii=False)

        # повідомляємо про успішне збереження
        logger.info(f"Anomalous activity report written to {path}")


if __name__ == "__main__":
    import argparse

    # створюємо розбірник аргументів командного рядка
    parser = argparse.ArgumentParser(description="User Activity Log Analyzer")
    # обов'язковий аргумент: шлях до CSV з активністю
    parser.add_argument(
        "--activity-log", required=True, help="Path to activity log CSV"
    )
    # обов'язковий аргумент: куди зберегти JSON-звіт
    parser.add_argument(
        "--out-report", required=True, help="Path to output JSON report"
    )
    # прапорець: store_true означає, що якщо він є в команді, значення True, якщо ні, False
    parser.add_argument(
        "--after-hours",
        action="store_true",
        help="Detect after-hours activity anomalies",
    )
    # необов'язковий аргумент для файлу логів (зараз прийнятий, але в коді не використовується)
    parser.add_argument("--log-file", help="Path to custom log file")

    args = parser.parse_args()

    analyzer = UserActivityAnalyzer(args.activity_log)
    analyzer.load_logs()

    if args.after_hours:
        anomalies = analyzer.detect_after_hours()
        analyzer.save_report(args.out_report, anomalies)
    else:
        logger.info("No specific analysis flag provided. Use --after-hours.")
