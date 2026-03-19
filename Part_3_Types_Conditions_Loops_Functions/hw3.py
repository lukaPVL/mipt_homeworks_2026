#!/usr/bin/env python

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
OP_SUCCESS_MSG = "Added"
ALLOWED_SYMBOLS = "0123456789."
AMOUNT_KEY = "amount"
DATE_KEY = "date"
CATEGORY_KEY = "category"

DATE_FRAGMENTS = 3
MONTHS_NUMBER = 12
FEBRUARY_NUMBER = 2
FEBRUARY_DAYS_COUNT = 29
INCOME_ARGS = 3
COST_ARGS = 4
STATS_ARGS = 2

MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


ParsedDate = tuple[int, int, int]
StatsData = tuple[str, float, float, float, float, dict[str, float]]


def is_leap_year(year: int) -> bool:
    first_check = (year % 4 == 0) and (year % 100 != 0)
    second_check = (year % 400 == 0)
    return first_check or second_check


def get_days_in_month(month: int, year: int) -> int:
    if month == FEBRUARY_NUMBER and is_leap_year(year):
        return FEBRUARY_DAYS_COUNT

    return MONTH_DAYS[month - 1]


def extract_date(maybe_dt: str) -> ParsedDate | None:
    fragments = maybe_dt.split("-")
    if len(fragments) != DATE_FRAGMENTS:
        return None

    if any(not fragment.isdigit() for fragment in fragments):
        return None

    day = int(fragments[0])
    month = int(fragments[1])
    year = int(fragments[2])

    if not (1 <= month <= MONTHS_NUMBER and year > 0):
        return None

    max_days = get_days_in_month(month, year)
    if not (1 <= day <= max_days):
        return None

    return day, month, year


def parse_amount(amount_str: str) -> float | None:
    amount_str = amount_str.replace(",", ".")

    for char in amount_str:
        if char not in ALLOWED_SYMBOLS:
            return None

    if amount_str.count(".") > 1:
        return None

    amount = float(amount_str) if "." in amount_str else int(amount_str)

    if amount <= 0:
        return None

    return amount


def validate_category(category: str) -> bool:
    return all(ch not in " .," for ch in category)


def process_income(parts: list[str], incomes: list[dict]) -> str:
    if len(parts) != INCOME_ARGS:
        return UNKNOWN_COMMAND_MSG

    amount = parse_amount(parts[1])
    if amount is None:
        return NONPOSITIVE_VALUE_MSG

    date = extract_date(parts[2])
    if date is None:
        return INCORRECT_DATE_MSG

    incomes.append({
        AMOUNT_KEY: amount,
        DATE_KEY: date
    })
    return OP_SUCCESS_MSG


def process_cost(parts: list[str], expenses: list[dict]) -> str:
    if len(parts) != COST_ARGS:
        return UNKNOWN_COMMAND_MSG

    amount = parse_amount(parts[2])
    if amount is None:
        return NONPOSITIVE_VALUE_MSG

    date = extract_date(parts[3])
    if date is None:
        return INCORRECT_DATE_MSG

    category = parts[1]
    if not validate_category(category):
        return UNKNOWN_COMMAND_MSG

    expenses.append({
        CATEGORY_KEY: category,
        AMOUNT_KEY: amount,
        DATE_KEY: date
    })

    return OP_SUCCESS_MSG


def is_before_or_equal(date1: ParsedDate, date2: ParsedDate) -> bool:
    if date1[2] != date2[2]:
        return date1[2] < date2[2]

    if date1[1] != date2[1]:
        return date1[1] < date2[1]

    return date1[0] <= date2[0]


def is_same_month(date1: ParsedDate, date2: ParsedDate) -> bool:
    return date1[1] == date2[1] and date1[2] == date2[2]


def calc_incomes(incomes: list[dict], target_date: ParsedDate) -> float:
    total = 0
    for income in incomes:
        if is_before_or_equal(income[DATE_KEY], target_date):
            total += income[AMOUNT_KEY]
    return total


def monthly_incomes(incomes: list[dict], target_date: ParsedDate) -> float:
    total = 0
    for income in incomes:
        if is_same_month(income[DATE_KEY], target_date):
            total += income[AMOUNT_KEY]
    return total


def calc_expenses(expenses: list[dict], target_date: ParsedDate) -> float:
    total = 0
    for expense in expenses:
        if is_before_or_equal(expense[DATE_KEY], target_date):
            total += expense[AMOUNT_KEY]
    return total


def monthly_expenses(expenses: list[dict], target_date: ParsedDate) -> tuple[float, dict[str, float]]:
    total = 0
    categories: dict[str, float] = {}

    for expense in expenses:
        if not is_same_month(expense[DATE_KEY], target_date):
            continue
        total += expense[AMOUNT_KEY]
        cat = expense[CATEGORY_KEY]
        categories[cat] = categories.get(cat, 0) + expense[AMOUNT_KEY]

    return float(total), categories


def build_output(stats: StatsData) -> list[str]:
    date_str, capital, month_result, month_inc, month_exp, categories = stats

    lines = [
        f"Ваша статистика по состоянию на {date_str}:",
        f"Суммарный капитал: {capital:.2f} рублей",
    ]

    if month_result >= 0:
        lines.append(f"В этом месяце прибыль составила {month_result:.2f} рублей")
    else:
        lines.append(f"В этом месяце убыток составил {abs(month_result):.2f} рублей")

    lines.extend([
        f"Доходы: {month_inc:.2f} рублей",
        f"Расходы: {month_exp:.2f} рублей",
        "",
        "Детализация (категория: сумма):",
    ])

    if categories:
        for i, cat in enumerate(sorted(categories), 1):
            lines.append(f"{i}. {cat}: {categories[cat]:.0f}")

    return lines


def process_stats(parts: list[str], incomes: list[dict], expenses: list[dict]) -> str:
    if len(parts) != STATS_ARGS:
        return UNKNOWN_COMMAND_MSG

    date = extract_date(parts[1])
    if date is None:
        return INCORRECT_DATE_MSG

    total_inc = calc_incomes(incomes, date)
    total_exp = calc_expenses(expenses, date)
    month_inc = monthly_incomes(incomes, date)
    month_exp, categories = monthly_expenses(expenses, date)

    stats: StatsData = (
        parts[1],
        total_inc - total_exp,
        month_inc - month_exp,
        month_inc,
        month_exp,
        categories
    )

    lines = build_output(stats)
    return "\n".join(lines)


def main() -> None:
    incomes: list[dict] = []
    expenses: list[dict] = []

    while True:
        try:
            line = input().strip()
        except EOFError:
            break

        if not line:
            continue

        parts = line.split()
        command = parts[0].lower()

        if command == "income":
            result = process_income(parts, incomes)
        elif command == "cost":
            result = process_cost(parts, expenses)
        elif command == "stats":
            result = process_stats(parts, incomes, expenses)
        else:
            result = UNKNOWN_COMMAND_MSG
        
        print(result)


if __name__ == "__main__":
    main()
