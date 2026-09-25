def run_task2():
    users = {
        "incident_commander": {
            "role": "incident_response",
            "clearance": 4,
            "department": "CSIRT",
            "active": True,
        },
        "malware_analyst": {
            "role": "malware_researcher",
            "clearance": 3,
            "department": "Research",
            "active": True,
        },
        "monitoring_tech": {
            "role": "monitoring",
            "clearance": 2,
            "department": "NOC",
            "active": True,
        },
        "customer_rep": {
            "role": "customer_service",
            "clearance": 1,
            "department": "Customer",
            "active": True,
        },
        "backup_service": {
            "role": "service_account",
            "clearance": 2,
            "department": "System",
            "active": False,
        },
    }

    resources = [
        ("incident_playbook", 4),
        ("malware_lab", 3),
        ("monitoring_dashboards", 2),
        ("customer_portal", 1),
        ("emergency_procedures", 4),
        ("service_desk", 1),
        ("reverse_engineering", 3),
        ("alert_systems", 2),
        ("escalation_matrix", 3),
        ("knowledge_base", 1),
    ]

    security_levels = (
        "Public Access",
        "Authorized",
        "Privileged",
        "Critical",
    )  # перетворюємо цифри від 1 до 4 на зрозумілі текстові назви(Кортеж рівнів безпеки)
    blocked_users = {
        "backup_service",
        "deactivated_svc",
        "policy_violation",
    }  # множина заблокованих користувачів

    print("рівні безпеки")  # вивід усіх ресур. із заміною чисел
    for res_name, level_num in resources:
        level_text = security_levels[level_num - 1]
        print(f"Ресурс: {res_name:<23} | Рівень: {level_text}")

    print("результат перевірки")

    for (
        username,
        user_info,
    ) in users.items():  # перевірка прав доступу для кожного користувача
        print(f"таблиця дозволів для: {username}")

        for res_name, req_clearance in resources:
            # перевірка 1: користувач у списку заблокованих
            if username in blocked_users:
                print(f"user={username} resource={res_name} -> DENY (User is blocked)")
            # перевірка 2: обліковий запис неактивний
            elif not user_info["active"]:
                print(f"user={username} resource={res_name} -> DENY (Account inactive)")
            # перевірка 3: числовий рівень доступу достатній
            elif user_info["clearance"] >= req_clearance:
                print(f"user={username} resource={res_name} -> ALLOW")

            # перевірка 4: рівень доступу замалий
            else:
                print(
                    f"user={username} resource={res_name} -> DENY (Insufficient clearance)"
                )


# точка входу для прямого запуску файлу
if __name__ == "__main__":
    run_task2()
