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

MONTH_DAYS = (
    31, 28, 31, 30, 31, 30,
    31, 31, 30, 31, 30, 31
)


ParsedDate = tuple[int, int, int]

CategoriesData = dict[str, float]
StatsData = tuple[str, float, float, float, float, CategoriesData]

IncomeDict = dict[str, float | ParsedDate]
ExpenseDict = dict[str, str | float | ParsedDate]

MonthlyExpensesResult = tuple[float, CategoriesData]

MonthlyStats = tuple[float, float, float, CategoriesData]
CompleteStats = tuple[str, float, MonthlyStats]


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


def process_income(parts: list[str], incomes: list[IncomeDict]) -> str:
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


def process_cost(parts: list[str], expenses: list[ExpenseDict]) -> str:
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
    first_check = date1[1] == date2[1]
    second_check = date1[2] == date2[2]
    return first_check and second_check


def calc_incomes(incomes: list[IncomeDict], target_date: ParsedDate) -> float:
    total = 0
    for income in incomes:
        if is_before_or_equal(income[DATE_KEY], target_date):
            total += income[AMOUNT_KEY]
    return float(total)


def monthly_incomes(incomes: list[IncomeDict], target_date: ParsedDate) -> float:
    total = 0
    for income in incomes:
        if is_same_month(income[DATE_KEY], target_date):
            total += income[AMOUNT_KEY]
    return float(total)


def calc_expenses(expenses: list[ExpenseDict], target_date: ParsedDate) -> float:
    total = 0
    for expense in expenses:
        if is_before_or_equal(expense[DATE_KEY], target_date):
            total += expense[AMOUNT_KEY]
    return float(total)


def monthly_expenses(expenses: list[ExpenseDict], target_date: ParsedDate) -> MonthlyExpensesResult:
    total = 0
    categories: dict[str, float] = {}

    for expense in expenses:
        if not is_same_month(expense[DATE_KEY], target_date):
            continue
        total += expense[AMOUNT_KEY]
        cat = expense[CATEGORY_KEY]
        categories[cat] = categories.get(cat, 0) + expense[AMOUNT_KEY]

    return float(total), categories


def build_monthly_stats(incomes: list[IncomeDict], expenses: list[ExpenseDict], date: ParsedDate) -> MonthlyStats:
    month_inc = monthly_incomes(incomes, date)
    month_exp, categories = monthly_expenses(expenses, date)
    month_result = month_inc - month_exp

    return (month_result, month_inc, month_exp, categories)


def build_complete_stats(date_str: str, incomes: list[IncomeDict], expenses: list[ExpenseDict], date: ParsedDate) -> CompleteStats:
    capital = calc_incomes(incomes, date) - calc_expenses(expenses, date)
    monthly_stats = build_monthly_stats(incomes, expenses, date)

    return (date_str, capital, monthly_stats)


def format_categories(categories: dict[str, float]) -> list[str]:
    if not categories:
        return []

    lines = []
    for i, cat in enumerate(sorted(categories), 1):
        lines.append(f"{i}. {cat}: {categories[cat]:.0f}")
    return lines


def build_output(complete_stats: CompleteStats) -> list[str]:
    date_str, capital, monthly_stats = complete_stats

    lines = [
        f"Ваша статистика по состоянию на {date_str}:",
        f"Суммарный капитал: {capital:.2f} рублей",
    ]

    month_result = monthly_stats[0]
    if month_result >= 0:
        lines.append(f"B этом месяце прибыль составила {month_result:.2f} рублей")
    else:
        lines.append(f"B этом месяце убыток составил {abs(month_result):.2f} рублей")

    lines.extend([
        f"Доходы: {monthly_stats[1]:.2f} рублей",
        f"Расходы: {monthly_stats[2]:.2f} рублей",
        "",
        "Детализация (категория: сумма):",
    ])

    lines.extend(format_categories(monthly_stats[3]))

    return lines

def calc_capital(incomes, expenses, date):
    total_inc = calc_incomes(incomes, date)
    total_exp = calc_expenses(expenses, date)
    return total_inc - total_exp

def process_stats(parts: list[str], incomes: list[IncomeDict], expenses: list[ExpenseDict]) -> str:
    if len(parts) != STATS_ARGS:
        return UNKNOWN_COMMAND_MSG

    date = extract_date(parts[1])
    if date is None:
        return INCORRECT_DATE_MSG

    complete_stats = build_complete_stats(parts[1], incomes, expenses, date)

    lines = build_output(complete_stats)
    return "\n".join(lines)

def handle_command(command: str, parts: list[str], incomes: list[IncomeDict], expenses: list[ExpenseDict]) -> str:
    if command == "income":
        return process_income(parts, incomes)
    if command == "cost":
        return process_cost(parts, expenses)
    if command == "stats":
        return process_stats(parts, incomes, expenses)

    return UNKNOWN_COMMAND_MSG

def process_single_line(line: str, incomes: list[IncomeDict], expenses: list[ExpenseDict]) -> None:
    if not line:
        return

    parts = line.split()
    command = parts[0].lower()
    result = handle_command(command, parts, incomes, expenses)
    print(result)

def main() -> None:
    incomes: list[IncomeDict] = []
    expenses: list[ExpenseDict] = []

    while True:
        try:
            line = input().strip()
        except EOFError:
            break

        if not line:
            continue

        process_single_line(line, incomes, expenses)


if __name__ == "__main__":
    main()
