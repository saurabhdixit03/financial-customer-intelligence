from pathlib import Path

import pandas as pd


RAW_ACCOUNTS_PATH = Path("data/raw/accounts.csv")
PROCESSED_CUSTOMERS_PATH = Path("data/processed/customers.csv")
PROCESSED_ACCOUNTS_PATH = Path("data/processed/accounts.csv")
REJECTED_ACCOUNTS_PATH = Path("data/rejected/accounts.csv")


def load_data():
    accounts = pd.read_csv(RAW_ACCOUNTS_PATH)
    customers = pd.read_csv(PROCESSED_CUSTOMERS_PATH)

    return accounts, customers


def validate_accounts(accounts, customers):
    validated = accounts.copy()

    validated["rejection_reason"] = ""

    # ACC-001: account_id must not be missing.
    missing_account_id = validated["account_id"].isna()

    validated.loc[
        missing_account_id,
        "rejection_reason",
    ] += "ACC-001: missing account_id; "

    # ACC-001: account_id must be unique.
    duplicate_account_id = validated["account_id"].duplicated(
        keep=False
    )

    validated.loc[
        duplicate_account_id,
        "rejection_reason",
    ] += "ACC-001: duplicate account_id; "

    # ACC-002: customer_id must reference an existing customer.
    valid_customer_ids = set(customers["customer_id"])

    invalid_customer_reference = (
        validated["customer_id"].isna()
        | ~validated["customer_id"].isin(valid_customer_ids)
    )

    validated.loc[
        invalid_customer_reference,
        "rejection_reason",
    ] += "ACC-002: invalid customer reference; "

    # ACC-003: account_type must be SAVINGS or CURRENT.
    valid_account_types = {"SAVINGS", "CURRENT"}

    invalid_account_type = (
        validated["account_type"].isna()
        | ~validated["account_type"].isin(valid_account_types)
    )

    validated.loc[
        invalid_account_type,
        "rejection_reason",
    ] += "ACC-003: invalid account_type; "

    # ACC-004: balance must not be negative.
    invalid_balance = (
        validated["balance"].isna()
        | (validated["balance"] < 0)
    )

    validated.loc[
        invalid_balance,
        "rejection_reason",
    ] += "ACC-004: invalid balance; "

    # ACC-005: open_date must be a valid date.
    account_open_dates = pd.to_datetime(
        validated["open_date"],
        errors="coerce",
    )

    invalid_open_date = account_open_dates.isna()

    validated.loc[
        invalid_open_date,
        "rejection_reason",
    ] += "ACC-005: invalid open_date; "

    # ACC-006: open_date must not be earlier than customer join_date.
    customer_join_dates = customers.set_index(
        "customer_id"
    )["join_date"]

    mapped_join_dates = pd.to_datetime(
        validated["customer_id"].map(customer_join_dates),
        errors="coerce",
    )

    invalid_date_relationship = (
        ~invalid_customer_reference
        & ~invalid_open_date
        & (account_open_dates < mapped_join_dates)
    )

    validated.loc[
        invalid_date_relationship,
        "rejection_reason",
    ] += "ACC-006: account opened before customer joined; "

    # ACC-007: status must be ACTIVE or INACTIVE.
    valid_statuses = {"ACTIVE", "INACTIVE"}

    invalid_status = (
        validated["status"].isna()
        | ~validated["status"].isin(valid_statuses)
    )

    validated.loc[
        invalid_status,
        "rejection_reason",
    ] += "ACC-007: invalid status; "

    valid_accounts = validated[
        validated["rejection_reason"] == ""
    ].copy()

    rejected_accounts = validated[
        validated["rejection_reason"] != ""
    ].copy()

    valid_accounts = valid_accounts.drop(
        columns=["rejection_reason"]
    )

    return valid_accounts, rejected_accounts


def save_results(valid_accounts, rejected_accounts):
    valid_accounts.to_csv(
        PROCESSED_ACCOUNTS_PATH,
        index=False,
    )

    rejected_accounts.to_csv(
        REJECTED_ACCOUNTS_PATH,
        index=False,
    )


def main():
    accounts, customers = load_data()

    valid_accounts, rejected_accounts = validate_accounts(
        accounts,
        customers,
    )

    save_results(valid_accounts, rejected_accounts)

    print(f"Raw accounts:      {len(accounts)}")
    print(f"Valid accounts:    {len(valid_accounts)}")
    print(f"Rejected accounts: {len(rejected_accounts)}")

    print("Saved valid accounts to data/processed/accounts.csv")
    print("Saved rejected accounts to data/rejected/accounts.csv")


if __name__ == "__main__":
    main()