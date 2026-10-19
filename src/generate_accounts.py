import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


CUSTOMERS_PATH = Path("data/raw/customers.csv")
ACCOUNTS_PATH = Path("data/raw/accounts.csv")

RANDOM_SEED = 42

def load_customers():
    customers = []

    with CUSTOMERS_PATH.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            customers.append(row)

    return customers


def generate_account_open_date(customer_join_date):
    join_date = datetime.strptime(customer_join_date, "%Y-%m-%d").date()

    max_days_after_join = 30
    days_after_join = random.randint(0, max_days_after_join)

    return join_date + timedelta(days=days_after_join)


def generate_accounts(customers):
    accounts = []
    account_number = 1

    for customer in customers:
        customer_id = customer["customer_id"]
        join_date = customer["join_date"]

        savings_account = {
            "account_id": f"ACC{account_number:05d}",
            "customer_id": customer_id,
            "account_type": "SAVINGS",
            "balance": random.randrange(5000, 200001, 1000),
            "open_date": generate_account_open_date(join_date).isoformat(),
            "status": "ACTIVE",
        }

        accounts.append(savings_account)
        account_number += 1

        has_current_account = random.random() < 0.25

        if has_current_account:
            current_account = {
                "account_id": f"ACC{account_number:05d}",
                "customer_id": customer_id,
                "account_type": "CURRENT",
                "balance": random.randrange(10000, 500001, 1000),
                "open_date": generate_account_open_date(join_date).isoformat(),
                "status": "ACTIVE",
            }

            accounts.append(current_account)
            account_number += 1

    return accounts


def save_accounts(accounts):
    fieldnames = [
        "account_id",
        "customer_id",
        "account_type",
        "balance",
        "open_date",
        "status",
    ]

    with ACCOUNTS_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(accounts)


def main():
    random.seed(RANDOM_SEED)
    customers = load_customers()
    accounts = generate_accounts(customers)
    save_accounts(accounts)

    print(f"Loaded {len(customers)} customers.")
    print(f"Generated {len(accounts)} accounts.")
    print("Saved to data/raw/accounts.csv")


if __name__ == "__main__":
    main()