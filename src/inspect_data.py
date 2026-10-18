from pathlib import Path

import pandas as pd


CUSTOMERS_PATH = Path("data/raw/customers.csv")
ACCOUNTS_PATH = Path("data/raw/accounts.csv")
TRANSACTIONS_PATH = Path("data/raw/transactions.csv")


def load_data():
    customers = pd.read_csv(CUSTOMERS_PATH)
    accounts = pd.read_csv(ACCOUNTS_PATH)
    transactions = pd.read_csv(TRANSACTIONS_PATH)

    return customers, accounts, transactions


def main():
    customers, accounts, transactions = load_data()

    print("DATASET SUMMARY")
    print("-" * 40)

    print(f"Customers:    {len(customers)}")
    print(f"Accounts:     {len(accounts)}")
    print(f"Transactions: {len(transactions)}")

    print("\nTRANSACTION TYPES")
    print("-" * 40)
    print(transactions["transaction_type"].value_counts())

    print("\nTRANSACTION CATEGORIES")
    print("-" * 40)
    print(transactions["category"].value_counts())

    print("\nMISSING VALUES")
    print("-" * 40)
    print(transactions.isnull().sum())

    print("\nTRANSACTION AMOUNT SUMMARY")
    print("-" * 40)
    print(transactions["amount"].describe())


if __name__ == "__main__":
    main()