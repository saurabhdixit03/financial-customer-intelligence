from pathlib import Path

import pandas as pd


RAW_CUSTOMERS_PATH = Path("data/raw/customers.csv")
PROCESSED_CUSTOMERS_PATH = Path("data/processed/customers.csv")
REJECTED_CUSTOMERS_PATH = Path("data/rejected/customers.csv")


def load_customers():
    return pd.read_csv(RAW_CUSTOMERS_PATH)


def validate_customers(customers):
    validated = customers.copy()

    validated["rejection_reason"] = ""

    # CUST-001: customer_id must not be missing.
    missing_customer_id = validated["customer_id"].isna()

    validated.loc[
        missing_customer_id,
        "rejection_reason",
    ] += "CUST-001: missing customer_id; "

    # CUST-001: customer_id must be unique.
    duplicate_customer_id = validated["customer_id"].duplicated(
        keep=False
    )

    validated.loc[
        duplicate_customer_id,
        "rejection_reason",
    ] += "CUST-001: duplicate customer_id; "

    # CUST-002: age must be between 18 and 100.
    invalid_age = (
        validated["age"].isna()
        | (validated["age"] < 18)
        | (validated["age"] > 100)
    )

    validated.loc[
        invalid_age,
        "rejection_reason",
    ] += "CUST-002: invalid age; "

    # CUST-003: city must not be missing.
    missing_city = validated["city"].isna()

    validated.loc[
        missing_city,
        "rejection_reason",
    ] += "CUST-003: missing city; "

    # CUST-004: occupation must not be missing.
    missing_occupation = validated["occupation"].isna()

    validated.loc[
        missing_occupation,
        "rejection_reason",
    ] += "CUST-004: missing occupation; "

    # CUST-005: annual_income must be greater than 0.
    invalid_income = (
        validated["annual_income"].isna()
        | (validated["annual_income"] <= 0)
    )

    validated.loc[
        invalid_income,
        "rejection_reason",
    ] += "CUST-005: invalid annual_income; "

    # CUST-006: join_date must be a valid date.
    parsed_join_date = pd.to_datetime(
        validated["join_date"],
        errors="coerce",
    )

    invalid_join_date = parsed_join_date.isna()

    validated.loc[
        invalid_join_date,
        "rejection_reason",
    ] += "CUST-006: invalid join_date; "

    valid_customers = validated[
        validated["rejection_reason"] == ""
    ].copy()

    rejected_customers = validated[
        validated["rejection_reason"] != ""
    ].copy()

    valid_customers = valid_customers.drop(
        columns=["rejection_reason"]
    )

    return valid_customers, rejected_customers


def save_results(valid_customers, rejected_customers):
    valid_customers.to_csv(
        PROCESSED_CUSTOMERS_PATH,
        index=False,
    )

    rejected_customers.to_csv(
        REJECTED_CUSTOMERS_PATH,
        index=False,
    )


def main():
    customers = load_customers()

    valid_customers, rejected_customers = validate_customers(
        customers
    )

    save_results(valid_customers, rejected_customers)

    print(f"Raw customers:      {len(customers)}")
    print(f"Valid customers:    {len(valid_customers)}")
    print(f"Rejected customers: {len(rejected_customers)}")

    print("Saved valid customers to data/processed/customers.csv")
    print("Saved rejected customers to data/rejected/customers.csv")


if __name__ == "__main__":
    main()