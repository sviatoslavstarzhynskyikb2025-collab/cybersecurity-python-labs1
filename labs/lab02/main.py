import sys
from datetime import timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from labs.lab02.task1 import Admin, AuditLog, User, UserAccount
from labs.lab02.task2 import UserActivityAnalyzer


def run_demo():
    print("демонстрація роботи LAB 02 (Task 1)")

    # 1.створення користувача та перевіряємо пароль
    user = User(username="svyatoslav", email="svyatoslav@example.com")
    user.set_password("SecurePassword123")
    print(f"створено користувача: {user}")

    is_valid = user.check_password("SecurePassword123")
    print(f"перевірка правильного пароля: {is_valid}")

    # 2.створення адміністратора та прав
    admin = Admin(
        username="admin_boss",
        email="emailadmin@example.com",
        permissions={"read", "write"},
    )
    print(f"створено адміністратора: {admin}")
    admin.grant_permission("delete")
    print(f"права після додавання 'delete': {admin.permissions}")

    # 3.робота з журналом аудиту та обліковим записом
    audit_log = AuditLog()
    account = UserAccount(user, audit_log)

    login_success = account.login("SecurePassword123", "192.168.1.50")
    print(f"спроба входу в систему: {'успішно' if login_success else 'помилка'}")
    print(f"користувач аутентифікований: {account.is_authenticated()}")

    # 4.невдалий вхід
    wrong = account.login("WrongPassword", "10.0.0.5")
    print(f"вхід з неправильним паролем: {'успішно' if wrong else 'відмова'}")

    # 5.зміна email з валідацією
    try:
        account["email"] = "bad_email"
        print("email змінено")
    except ValueError as e:
        print(f"валідація email спрацювала: {e}")
    account["email"] = "new_mail@example.com"
    print(f"новий email: {account['user'].email}")

    # 6.завершення сеансу за таймаутом (зсуваємо час активності в минуле)
    account["session"].last_activity -= timedelta(seconds=1000)
    print(f"після простою 1000 сек аутентифікований: {account.is_authenticated()}")

    # 7.новий вхід і вихід із системи
    account.login("SecurePassword123", "192.168.1.50")
    account.logout()
    print(f"після виходу аутентифікований: {account.is_authenticated()}")

    # виводимо логи аудиту
    print("\n журнал подій (AuditLog):")
    for record in audit_log.show_all():
        print(f"[{record.timestamp}] користувач '{record.username}': {record.action}")

    # виводимо логи аудиту
    print("\n журнал подій (AuditLog):")
    for record in audit_log.show_all():
        print(f"[{record.timestamp}] користувач '{record.username}': {record.action}")


def run_analyze(activity_log_path: str, out_report_path: str):
    print("\n запсук аналізу логів  (Task 2) ")
    analyzer = UserActivityAnalyzer(activity_log_path)
    analyzer.load_logs()
    anomalies = analyzer.detect_after_hours()
    analyzer.save_report(out_report_path, anomalies)
    print(
        f"аналіз завершено, знайдено аномалій: {len(anomalies)}. звіт збережено у {out_report_path}"
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("використання:")
        print("  python -m labs.lab02.main demo")
        print("  python -m labs.lab02.main analyze <path_to_csv> <path_to_json>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "demo":
        run_demo()
    elif command == "analyze":
        if len(sys.argv) < 4:
            print("помилка: вкажіть шлях до CSV логів та шлях для вихідного JSON звіту")
            print(
                "приклад: python -m labs.lab02.main analyze labs/lab02/data/activity.csv labs/lab02/data/report.json"
            )
            sys.exit(1)
        run_analyze(sys.argv[2], sys.argv[3])
    else:
        print(f"невідома команда: {command}")
        print("використовуйте 'demo' або 'analyze'")
