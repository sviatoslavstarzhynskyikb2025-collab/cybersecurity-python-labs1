import csv
import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# налаштовуємо глобальну систему логування, встановлюємо рівень INFO та формат виведення
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)  # створюємо об'єкт логера для поточного модуля


class UserActivityAnalyzer:  # оголошуємо клас для аналізу логів активності користувачів
    """аналізатор логів для виявлення аномальної активності користувачів"""

    def __init__(
        self, log_file_path: str | Path
    ) -> None:  # конструктор класу, приймає шлях до лог-файлу
        """ініціалізація аналізатора шляхом до файлу логів"""
        self.log_file_path = Path(
            log_file_path
        )  # перетворюємо введений шлях на об'єкт Path
        self.logs: list[
            dict[str, str]
        ] = []  # ініціалізуємо порожній список для збереження зчитаних логів

    def load_logs(self) -> None:  # метод для зчитування даних із CSV-файлу
        """читає CSV-файл дій користувачів (Timestamp, UserID, Action, Resource, IP)"""
        if (
            not self.log_file_path.exists()
        ):  # перевіряємо, чи існує файл за вказаним шляхом
            raise FileNotFoundError(
                f"файл не знайдено: {self.log_file_path}"
            )  # якщо ні — викликаємо помилку

        logger.info(
            f"reading user activity log {self.log_file_path}..."
        )  # виводимо повідомлення про початок читання

        with open(
            self.log_file_path, mode="r", encoding="utf-8"
        ) as file:  # відкриваємо файл для читання у кодуванні UTF-8
            reader = csv.DictReader(
                file
            )  # створюємо CSV-рідер, що перетворює рядки на словники
            self.logs = [
                row for row in reader
            ]  # зберігаємо всі рядки таблиці у список self.logs

        logger.info(
            f"total records processed: {len(self.logs)}."
        )  # виводимо загальну кількість успішно оброблених рядків

    def group_by_user(
        self,
    ) -> defaultdict[
        str, list[dict[str, str]]
    ]:  # метод для групування подій за користувачами
        """групує дії за користувачами за допомогою collections.defaultdict"""
        user_actions = defaultdict(
            list
        )  # створюємо словник, де значення за замовчуванням — порожній список

        for log in self.logs:  # проходимо циклом по кожному зафіксованому логу
            user_id = log.get(
                "UserID", "unknown"
            )  # отримуємо ID користувача або "unknown", якщо поле відсутнє
            user_actions[user_id].append(
                log
            )  # додаємо поточну подію до списку відповідного користувача

        return user_actions  # повертаємо сформований згрупований словник

    def detect_after_hours(
        self,
    ) -> list[dict[str, Any]]:  # метод для пошуку дій у позаробочий час
        """виявляє дії, виконані у позаробочий час (22:00 - 06:00 або вихідні)"""
        alerts = []  # створюємо порожній список для збереження знайдених аномалій

        for log in self.logs:  # перебираємо кожен окремий рядок логу
            timestamp_str = log.get(
                "Timestamp", ""
            )  # отримуємо текстове значення дати та часу події

            try:  # захист від збоїв при конвертації дати
                dt = datetime.strptime(
                    timestamp_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc
                )  # перетворюємо рядок у формат datetime
            except ValueError:  # якщо формат дати у файлі пошкоджений
                continue  # пропускаємо цей рядок і переходимо до наступного

            is_night = (
                dt.hour >= 22 or dt.hour < 6
            )  # умова нічного часу: пізніше 22:00 або раніше 06:00 ранку
            is_weekend = (
                dt.weekday() >= 5
            )  # умова вихідного дня: субота (5) або неділя (6) у Python

            if is_night or is_weekend:  # якщо дія відбулася вночі або у вихідний день
                alert = {  # формуємо словник з інформацією про підозрілу подію
                    "UserID": log.get("UserID"),
                    "Action": log.get("Action"),
                    "Resource": log.get("Resource"),
                    "Timestamp": timestamp_str,
                    "IP": log.get("IP"),
                    "Reason": "After-hours activity",
                }
                alerts.append(alert)  # додаємо тривогу до загального списку аномалій

                logger.warning(  # виводимо попередження жовтим/червоним кольором у консоль
                    f"[ALERT] User '{log.get('UserID')}' performed {log.get('Action')} "
                    f"at {timestamp_str} (Resource: {log.get('Resource')})"
                )

        return alerts  # повертаємо список усіх знайдених позаробочих активностей

    def save_report(
        self, report_path: str | Path, data: Any
    ) -> None:  # метод для збереження результатів у JSON-файл
        """Зберігає підозрілі події у JSON-файл."""
        path = Path(report_path)  # перетворюємо шлях збереження у безпечний об'єкт Path
        path.parent.mkdir(
            parents=True, exist_ok=True
        )  # автоматично створюємо проміжні папки, якщо їх не існує

        with open(
            path, mode="w", encoding="utf-8"
        ) as f:  # відкриваємо файл для запису даних у кодуванні UTF-8
            json.dump(
                data, f, indent=4, ensure_ascii=False
            )  # серіалізуємо дані у JSON з відступами у 4 пробіли та кирилицею

        logger.info(
            f"Anomalous activity report written to {path}"
        )  # виводимо лог про успішне збереження звіту


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="User Activity Log Analyzer")
    parser.add_argument(
        "--activity-log", required=True, help="Path to activity log CSV"
    )
    parser.add_argument(
        "--out-report", required=True, help="Path to output JSON report"
    )
    args = parser.parse_args()

    analyzer = UserActivityAnalyzer(args.activity_log)
    analyzer.load_logs()
    anomalies = analyzer.detect_after_hours()
    analyzer.save_report(args.out_report, anomalies)
