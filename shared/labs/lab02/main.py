import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from labs.lab02.task1 import User, Admin, Session, AuditLog, UserAccount
from labs.lab02.task2 import UserActivityAnalyzer

def run_demo():
    print("демонстрація роботи LAB 02 (Task 1)")

    #1.створення користувача та перевіряємо пароль
    user = User(username="svyatoslav", email="svyatoslav@example.com")
    user.set_password("SecurePassword123")
    print(f"створено користувача: {user}")

    is_valid = user.check_password("SecurePassword123")
    print(f"перевірка правильного пароля: {is_valid}")

    #2.створення адміністратора та прав
    admin = Admin(username="admin_boss", email="emailadmin@example.com", permissions={"read", "write"})
    print(f"створено адміністратора: {admin}")
    admin.grant_permission("delete")
    print(f"права після додавання 'delete': {admin.permissions}")

    #3.робота з журналом аудиту та обліковим записом
    audit_log = AuditLog()
    account = UserAccount(user, audit_log)
    
    login_success = account.login("SecurePassword123", "192.168.1.50")
    print(f"спроба входу в систему: {'успішно' if login_success else 'помилка'}")
    print(f"користувач аутентифікований: {account.is_authenticated()}")
    
    #виводимо логи аудиту
    print("\n журнал подій (AuditLog):")
    for record in audit_log.show_all():
        print(f"[{record.timestamp}] користувач '{record.username}': {record.action}")

def run_analyze(activity_log_path: str, out_report_path: str):
    print(f"\n запсук аналізу логів  (Task 2) ")
    analyzer = UserActivityAnalyzer(activity_log_path)
    analyzer.load_logs()
    anomalies = analyzer.detect_after_hours()
    analyzer.save_report(out_report_path, anomalies)
    print(f"аналіз завершено, знайдено аномалій: {len(anomalies)}. звіт збережено у {out_report_path}")


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
            print("приклад: python -m labs.lab02.main analyze labs/lab02/data/activity.csv labs/lab02/data/report.json")
            sys.exit(1)
        run_analyze(sys.argv[2], sys.argv[3])
    else:
        print(f"невідома команда: {command}")
        print("використовуйте 'demo' або 'analyze'")