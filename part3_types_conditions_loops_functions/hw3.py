#!/usr/bin/env python

from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"
ALLOWED_SYMBOLS = "0123456789."
AMOUNT_KEY = "amount"
DATE_KEY = "date"
CATEGORY_KEY = "category"


EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("SomeCategory", "SomeOtherCategory"),
}


financial_transactions_storage: list[dict[str, Any]] = []

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


def income_handler(amount: float, income_date: str) -> str:
    date = extract_date(income_date)

    if date is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG

    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG

    financial_transactions_storage.append({
        AMOUNT_KEY: amount,
        DATE_KEY: date
    })

    return OP_SUCCESS_MSG


def is_valid_category(category_name: str) -> bool:
    if "::" in category_name:
        parts = category_name.split("::", 1)
        first_check = parts[0] in EXPENSE_CATEGORIES
        second_check = parts[1] in EXPENSE_CATEGORIES[parts[0]]
        return first_check and second_check

    for main_cat, subcats in EXPENSE_CATEGORIES.items():
        if category_name in subcats or category_name == main_cat:
            return True
    return False


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    date = extract_date(income_date)

    if date is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG

    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG

    if not is_valid_category(category_name):
        financial_transactions_storage.append({})
        return NOT_EXISTS_CATEGORY

    financial_transactions_storage.append({
        CATEGORY_KEY: category_name,
        AMOUNT_KEY: amount,
        DATE_KEY: date
    })

    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    categories_list = []
    for main_category, subcategories in EXPENSE_CATEGORIES.items():
        categories_list.extend([f"{main_category}::{subcategory}" for subcategory in subcategories])

    return "\n".join(categories_list)


def has_required_fields(transaction: dict[str, Any], required_fields: list[str]) -> bool:
    return any(transaction.get(field) is None for field in required_fields)


def collect_expense(transaction: dict[str, Any]) -> ExpenseDict | None:
    if has_required_fields(transaction, [CATEGORY_KEY, AMOUNT_KEY, DATE_KEY]):
        return None

    return {
        CATEGORY_KEY: transaction.get(CATEGORY_KEY),
        AMOUNT_KEY: transaction.get(AMOUNT_KEY),
        DATE_KEY: transaction.get(DATE_KEY)
    }


def collect_income(transaction: dict[str, Any]) -> IncomeDict | None:
    if has_required_fields(transaction, [AMOUNT_KEY, DATE_KEY]):
        return None

    return {
        AMOUNT_KEY: transaction.get(AMOUNT_KEY),
        DATE_KEY: transaction.get(DATE_KEY)
    }


def stats_handler(report_date: str) -> str:
    date = extract_date(report_date)
    if date is None:
        return INCORRECT_DATE_MSG

    incomes: list[IncomeDict] = []
    expenses: list[ExpenseDict] = []

    for transaction in financial_transactions_storage:
        if not isinstance(transaction[DATE_KEY], tuple):
            continue

        if CATEGORY_KEY in transaction:
            expense = collect_expense(transaction)
            if expense is not None:
                expenses.append(expense)
        else:
            income = collect_income(transaction)
            if income is not None:
                incomes.append(income)

    complete_stats = build_complete_stats(report_date, incomes, expenses, date)
    lines = build_output(complete_stats)
    return "\n".join(lines)


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
    total = float(0)
    for income in incomes:
        income_date = income[DATE_KEY]
        income_amount = income[AMOUNT_KEY]

        if not isinstance(income_date, tuple):
            continue
        if not isinstance(income_amount, (int, float)):
            continue

        if is_before_or_equal(income_date, target_date):
            total += float(income_amount)
    return total


def monthly_incomes(incomes: list[IncomeDict], target_date: ParsedDate) -> float:
    total = float(0)
    for income in incomes:
        income_date = income[DATE_KEY]
        income_amount = income[AMOUNT_KEY]

        if not isinstance(income_date, tuple):
            continue
        if not isinstance(income_amount, (int, float)):
            continue

        if is_same_month(income_date, target_date):
            total += float(income_amount)
    return total


def calc_expenses(expenses: list[ExpenseDict], target_date: ParsedDate) -> float:
    total = float(0)
    for expense in expenses:
        expense_date = expense[DATE_KEY]
        expense_amount = expense[AMOUNT_KEY]

        if not isinstance(expense_date, tuple):
            continue
        if not isinstance(expense_amount, (int, float)):
            continue

        if is_before_or_equal(expense_date, target_date):
            total += float(expense_amount)
    return total


def process_single_expense(
    expense: ExpenseDict,
    target_date: ParsedDate,
    categories: dict[str, float]
) -> float:

    expense_date = expense.get(DATE_KEY)
    if not isinstance(expense_date, tuple):
        return float(0)

    if not is_same_month(expense_date, target_date):
        return float(0)

    expense_amount = expense.get(AMOUNT_KEY)
    if not isinstance(expense_amount, (int, float)):
        return float(0)

    expense_category = expense.get(CATEGORY_KEY)
    if not isinstance(expense_category, str):
        return float(0)

    amount_float = float(expense_amount)
    categories[expense_category] = categories.get(expense_category, 0) + amount_float

    return amount_float


def monthly_expenses(expenses: list[ExpenseDict], target_date: ParsedDate) -> MonthlyExpensesResult:
    categories: dict[str, float] = {}

    total = sum(
        process_single_expense(expense, target_date, categories)
        for expense in expenses
    )

    return float(total), categories


def build_monthly_stats(
    incomes: list[IncomeDict],
    expenses: list[ExpenseDict],
    date: ParsedDate
) -> MonthlyStats:
    month_inc = monthly_incomes(incomes, date)
    month_exp, categories = monthly_expenses(expenses, date)
    month_result = month_inc - month_exp

    return (month_result, month_inc, month_exp, categories)


def build_complete_stats(
    date_str: str,
    incomes: list[IncomeDict],
    expenses: list[ExpenseDict],
    date: ParsedDate
) -> CompleteStats:
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


def calc_capital(incomes: list[IncomeDict], expenses: list[ExpenseDict], date: ParsedDate) -> float:
    total_inc = calc_incomes(incomes, date)
    total_exp = calc_expenses(expenses, date)
    return total_inc - total_exp


def process_income(parts: list[str]) -> str:
    if len(parts) != INCOME_ARGS:
        return UNKNOWN_COMMAND_MSG

    amount = parse_amount(parts[1])
    if amount is None:
        return NONPOSITIVE_VALUE_MSG

    return income_handler(amount, parts[2])


def process_cost(parts: list[str]) -> str:
    if len(parts) != COST_ARGS:
        return UNKNOWN_COMMAND_MSG

    amount = parse_amount(parts[2])
    if amount is None:
        return NONPOSITIVE_VALUE_MSG

    category = parts[1]

    return cost_handler(category, amount, parts[3])


def process_stats(
    parts: list[str],
) -> str:
    if len(parts) != STATS_ARGS:
        return UNKNOWN_COMMAND_MSG

    return stats_handler(parts[1])


def handle_command(command: str, parts: list[str]) -> str:
    if command == "income":
        return process_income(parts)
    if command == "cost":
        return process_cost(parts)
    if command == "stats":
        return process_stats(parts)
    if command == "categories":
        return cost_categories_handler()
    return UNKNOWN_COMMAND_MSG


def process_single_line(line: str) -> None:
    if not line:
        return
    parts = line.split()
    command = parts[0].lower()
    result = handle_command(command, parts)
    print(result)


def main() -> None:
    while True:
        try:
            line = input().strip()
        except EOFError:
            break
        if not line:
            continue
        process_single_line(line)


if __name__ == "__main__":
    main()
