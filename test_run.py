"""Тест воронки без Telegram — прогоняет логику подсчета"""
from bot import get_result

tests = [8, 22, 45]
for s in tests:
    title, desc, link, label = get_result(s)
    print(f"\n--- {s} баллов ---")
    print(title)
    print(desc)
    print(f"Кнопка: {label} -> {link}")
print("\n✅ Логика ок")
