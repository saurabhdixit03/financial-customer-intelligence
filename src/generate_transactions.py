import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path


CUSTOMERS_PATH = Path("data/raw/customers.csv")
ACCOUNTS_PATH = Path("data/raw/accounts.csv")
TRANSACTIONS_PATH = Path("data/raw/transactions.csv")

ANALYSIS_END_DATE = date(2026, 6, 30)
HISTORY_MONTHS = 6

DEBIT_CATEGORIES = [
    "GROCERIES",
    "UTILITIES",
    "TRANSPORT",
    "SHOPPING",
    "ENTERTAINMENT",
    "HEALTHCARE",
    "OTHER",
]


def load_csv(path):
    with path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def random_date(start_date, end_date):
    total_days = (end_date - start_date).days

    if total_days <= 0:
        return start_date

    return start_date + timedelta(days=random.randint(0, total_days))


def generate_transactions(customers, accounts):
    transactions = []
    transaction_number = 1

    customers_by_id = {
        customer["customer_id"]: customer
        for customer in customers
    }

    history_start_date = date(2026, 1, 1)

    for account in accounts:
        if account["account_type"] != "SAVINGS":
            continue

        customer = customers_by_id[account["customer_id"]]

        annual_income = int(customer["annual_income"])
        monthly_income = annual_income / 12

        account_open_date = datetime.strptime(
            account["open_date"], "%Y-%m-%d"
        ).date()

        transaction_start_date = max(
            history_start_date,
            account_open_date,
        )

        if transaction_start_date > ANALYSIS_END_DATE:
            continue

        # Generate one approximate monthly income credit.
        for month in range(1, HISTORY_MONTHS + 1):
            month_start = date(2026, month, 1)

            if month == 6:
                month_end = ANALYSIS_END_DATE
            else:
                month_end = date(2026, month + 1, 1) - timedelta(days=1)

            if month_end < transaction_start_date:
                continue

            effective_month_start = max(
                month_start,
                transaction_start_date,
            )

            income_amount = round(
                monthly_income * random.uniform(0.90, 1.10),
                2,
            )

            income_date = random_date(
                effective_month_start,
                min(
                    effective_month_start + timedelta(days=4),
                    month_end,
                ),
            )

            transaction = {
                "transaction_id": f"TXN{transaction_number:07d}",
                "account_id": account["account_id"],
                "transaction_date": income_date.isoformat(),
                "transaction_type": "CREDIT",
                "category": "INCOME",
                "amount": income_amount,
            }

            transactions.append(transaction)
            transaction_number += 1

            # Generate normal monthly spending.
            number_of_expenses = random.randint(8, 18)

            for _ in range(number_of_expenses):
                expense_amount = round(
                    random.uniform(
                        monthly_income * 0.01,
                        monthly_income * 0.08,
                    ),
                    2,
                )

                expense = {
                    "transaction_id": f"TXN{transaction_number:07d}",
                    "account_id": account["account_id"],
                    "transaction_date": random_date(
                        effective_month_start,
                        month_end,
                    ).isoformat(),
                    "transaction_type": "DEBIT",
                    "category": random.choice(DEBIT_CATEGORIES),
                    "amount": expense_amount,
                }

                transactions.append(expense)
                transaction_number += 1

    transactions.sort(
        key=lambda transaction: (
            transaction["transaction_date"],
            transaction["transaction_id"],
        )
    )

    return transactions


def save_transactions(transactions):
    fieldnames = [
        "transaction_id",
        "account_id",
        "transaction_date",
        "transaction_type",
        "category",
        "amount",
    ]

    with TRANSACTIONS_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(transactions)


def main():
    customers = load_csv(CUSTOMERS_PATH)
    accounts = load_csv(ACCOUNTS_PATH)

    transactions = generate_transactions(customers, accounts)
    save_transactions(transactions)

    print(f"Loaded {len(customers)} customers.")
    print(f"Loaded {len(accounts)} accounts.")
    print(f"Generated {len(transactions)} transactions.")
    print("Saved to data/raw/transactions.csv")


if __name__ == "__main__":
    main()