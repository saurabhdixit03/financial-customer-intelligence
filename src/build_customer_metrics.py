from pathlib import Path

import pandas as pd


CUSTOMERS_PATH = Path("data/processed/customers.csv")
ACCOUNTS_PATH = Path("data/processed/accounts.csv")
TRANSACTIONS_PATH = Path("data/processed/transactions.csv")


def load_data():
    customers = pd.read_csv(CUSTOMERS_PATH)
    accounts = pd.read_csv(ACCOUNTS_PATH)
    transactions = pd.read_csv(TRANSACTIONS_PATH)

    return customers, accounts, transactions


def build_customer_metrics(customers, accounts, transactions):
    transactions_with_customer = transactions.merge(
        accounts[["account_id", "customer_id"]],
        on="account_id",
        how="inner",
    )

    if len(transactions_with_customer) != len(transactions):
        raise ValueError(
            "Transaction count changed during account join."
        )

    transactions_with_customer["credit_amount"] = (
        transactions_with_customer["amount"].where(
            transactions_with_customer["transaction_type"] == "CREDIT",
            0,
        )
    )

    transactions_with_customer["debit_amount"] = (
        transactions_with_customer["amount"].where(
            transactions_with_customer["transaction_type"] == "DEBIT",
            0,
        )
    )

    transaction_summary = (
        transactions_with_customer.groupby(
            "customer_id",
            as_index=False,
        )
        .agg(
            total_credit=("credit_amount", "sum"),
            total_debit=("debit_amount", "sum"),
            transaction_count=("transaction_id", "count"),
        )
    )

    customer_metrics = customers.merge(
        transaction_summary,
        on="customer_id",
        how="left",
    )

    customer_metrics[
        ["total_credit", "total_debit", "transaction_count"]
    ] = customer_metrics[
        ["total_credit", "total_debit", "transaction_count"]
    ].fillna(0)

    customer_metrics["net_cash_flow"] = (
        customer_metrics["total_credit"]
        - customer_metrics["total_debit"]
    )

    customer_metrics["spending_ratio"] = (
        customer_metrics["total_debit"]
        / customer_metrics["total_credit"]
    ).where(
        customer_metrics["total_credit"] > 0,
    0,
    )

    return customer_metrics


def main():
    customers, accounts, transactions = load_data()

    customer_metrics = build_customer_metrics(
        customers,
        accounts,
        transactions,
    )

    print(
        customer_metrics[
            [
                "customer_id",
                "total_credit",
                "total_debit",
                "net_cash_flow",
                "spending_ratio",
                "transaction_count",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
