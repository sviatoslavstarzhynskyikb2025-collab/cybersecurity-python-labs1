def run_task1():
    passwords = [
        "NetworkS3c!",
        "easy",
        "Firewa11@Pass",
        "anonymous",
        "Intrus10n#Detect",
        "sample",
        "Malwar3@Scan",
        "qwerty",
        "Vulnerab1l!ty",
        "common",
    ]

    criteria = {
        "min_lenght": 9,
        "require_digits": True,
        "require_upper": True,
        "require_special": True,
    }

    forbidden_passwords = {
        "easy",
        "anonymous",
        "sample",
        "qwerty",
        "common",
        "password",
    }

    checked_passwords = {}  # словник для зберігання результатів

    for pw in passwords:  # перебираємо пароль зі списку
        if pw in forbidden_passwords or len(pw) < criteria["min_lenght"]:
            checked_passwords[pw] = "Forbidden / Too short"
            continue

        has_digit = any(  # оцінюємо складність паролю
            c.isdigit()
            for c in pw  # чи є цифра
        )
        has_upper = any(
            c.isupper()
            for c in pw  # чи є велика літера
        )
        has_special = any(
            not c.isalnum()
            for c in pw  # чи є спецсимвол
        )

        score = sum([has_digit, has_upper, has_special])  # заг. кіль. викон. умов

        # категорія надійності за балами
        if score == 1:
            checked_passwords[pw] = "Weak"
        elif score == 2:
            checked_passwords[pw] = "Medium"
        elif score == 3:
            checked_passwords[pw] = "Strong"

    print("Результат Завдання 1 ")
    for pwd, status in checked_passwords.items():
        print(f"{pwd:<20} -> {status}")


if __name__ == "__main__":
    run_task1()
