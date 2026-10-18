from pathlib import Path

import pandas as pd


RAW_TRANSACTIONS_PATH = Path("data/raw/transactions.csv")
PROCESSED_ACCOUNTS_PATH = Path("data/processed/accounts.csv")
PROCESSED_TRANSACTIONS_PATH = Path("data/processed/transactions.csv")
REJECTED_TRANSACTIONS_PATH = Path("data/rejected/transactions.csv")


def load_data():
    transactions = pd.read_csv(RAW_TRANSACTIONS_PATH)
    accounts = pd.read_csv(PROCESSED_ACCOUNTS_PATH)

    return transactions, accounts


def validate_transactions(transactions, accounts):
    validated = transactions.copy()

    validated["rejection_reason"] = ""

    # TXN-001: transaction_id must not be missing.
    missing_transaction_id = validated["transaction_id"].isna()

    validated.loc[
        missing_transaction_id,
        "rejection_reason",
    ] += "TXN-001: missing transaction_id; "

    # TXN-001: transaction_id must be unique.
    duplicate_transaction_id = validated["transaction_id"].duplicated(
        keep=False
    )

    validated.loc[
        duplicate_transaction_id,
        "rejection_reason",
    ] += "TXN-001: duplicate transaction_id; "

    # TXN-002: account_id must reference an existing valid account.
    valid_account_ids = set(accounts["account_id"])

    invalid_account_reference = (
        validated["account_id"].isna()
        | ~validated["account_id"].isin(valid_account_ids)
    )

    validated.loc[
        invalid_account_reference,
        "rejection_reason",
    ] += "TXN-002: invalid account reference; "

    # TXN-003: transaction_date must be a valid date.
    transaction_dates = pd.to_datetime(
        validated["transaction_date"],
        errors="coerce",
    )

    invalid_transaction_date = transaction_dates.isna()

    validated.loc[
        invalid_transaction_date,
        "rejection_reason",
    ] += "TXN-003: invalid transaction_date; "

    # TXN-004: transaction_date must not be earlier than account open_date.
    account_open_dates = accounts.set_index(
        "account_id"
    )["open_date"]

    mapped_open_dates = pd.to_datetime(
        validated["account_id"].map(account_open_dates),
        errors="coerce",
    )

    invalid_date_relationship = (
        ~invalid_account_reference
        & ~invalid_transaction_date
        & (transaction_dates < mapped_open_dates)
    )

    validated.loc[
        invalid_date_relationship,
        "rejection_reason",
    ] += "TXN-004: transaction occurred before account opened; "

    # TXN-005: transaction_type must be CREDIT or DEBIT.
    valid_transaction_types = {"CREDIT", "DEBIT"}

    invalid_transaction_type = (
        validated["transaction_type"].isna()
        | ~validated["transaction_type"].isin(
            valid_transaction_types
        )
    )

    validated.loc[
        invalid_transaction_type,
        "rejection_reason",
    ] += "TXN-005: invalid transaction_type; "

    # TXN-006: category must not be missing.
    missing_category = validated["category"].isna()

    validated.loc[
        missing_category,
        "rejection_reason",
    ] += "TXN-006: missing category; "

    # TXN-007: amount must be greater than 0.
    invalid_amount = (
        validated["amount"].isna()
        | (validated["amount"] <= 0)
    )

    validated.loc[
        invalid_amount,
        "rejection_reason",
    ] += "TXN-007: invalid amount; "

    valid_transactions = validated[
        validated["rejection_reason"] == ""
    ].copy()

    rejected_transactions = validated[
        validated["rejection_reason"] != ""
    ].copy()

    valid_transactions = valid_transactions.drop(
        columns=["rejection_reason"]
    )

    return valid_transactions, rejected_transactions


def save_results(valid_transactions, rejected_transactions):
    valid_transactions.to_csv(
        PROCESSED_TRANSACTIONS_PATH,
        index=False,
    )

    rejected_transactions.to_csv(
        REJECTED_TRANSACTIONS_PATH,
        index=False,
    )


def main():
    transactions, accounts = load_data()

    valid_transactions, rejected_transactions = validate_transactions(
        transactions,
        accounts,
    )

    save_results(valid_transactions, rejected_transactions)

    print(f"Raw transactions:      {len(transactions)}")
    print(f"Valid transactions:    {len(valid_transactions)}")
    print(f"Rejected transactions: {len(rejected_transactions)}")

    print(
        "Saved valid transactions to "
        "data/processed/transactions.csv"
    )
    print(
        "Saved rejected transactions to "
        "data/rejected/transactions.csv"
    )


if __name__ == "__main__":
    main()