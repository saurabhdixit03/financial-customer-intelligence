from pathlib import Path

import pandas as pd


RAW_LOANS_PATH = Path("data/raw/loans.csv")
PROCESSED_CUSTOMERS_PATH = Path("data/processed/customers.csv")
PROCESSED_LOANS_PATH = Path("data/processed/loans.csv")
REJECTED_LOANS_PATH = Path("data/rejected/loans.csv")

AS_OF_DATE = pd.Timestamp("2026-06-30")

VALID_LOAN_TYPES = {
    "PERSONAL",
    "HOME",
    "AUTO",
    "EDUCATION",
}

VALID_LOAN_STATUSES = {
    "ACTIVE",
    "CLOSED",
}


def load_data():
    loans = pd.read_csv(RAW_LOANS_PATH)
    customers = pd.read_csv(PROCESSED_CUSTOMERS_PATH)

    return loans, customers


def validate_loans(loans, customers):
    validated = loans.copy()

    validated["rejection_reason"] = ""

    # LOAN-001: loan_id must not be missing.
    missing_loan_id = validated["loan_id"].isna()

    validated.loc[
        missing_loan_id,
        "rejection_reason",
    ] += "LOAN-001: missing loan_id; "

    # LOAN-001: loan_id must be unique.
    duplicate_loan_id = validated["loan_id"].duplicated(
        keep=False
    )

    validated.loc[
        duplicate_loan_id,
        "rejection_reason",
    ] += "LOAN-001: duplicate loan_id; "

    # LOAN-002: customer_id must reference a valid customer.
    valid_customer_ids = set(customers["customer_id"])

    invalid_customer_reference = (
        validated["customer_id"].isna()
        | ~validated["customer_id"].isin(valid_customer_ids)
    )

    validated.loc[
        invalid_customer_reference,
        "rejection_reason",
    ] += "LOAN-002: invalid customer reference; "

    # LOAN-003: loan_type must be supported.
    invalid_loan_type = (
        validated["loan_type"].isna()
        | ~validated["loan_type"].isin(VALID_LOAN_TYPES)
    )

    validated.loc[
        invalid_loan_type,
        "rejection_reason",
    ] += "LOAN-003: invalid loan_type; "

    # LOAN-004: loan_amount must be greater than 0.
    invalid_loan_amount = (
        validated["loan_amount"].isna()
        | (validated["loan_amount"] <= 0)
    )

    validated.loc[
        invalid_loan_amount,
        "rejection_reason",
    ] += "LOAN-004: invalid loan_amount; "

    # LOAN-005: annual_interest_rate must be greater than 0.
    invalid_interest_rate = (
        validated["annual_interest_rate"].isna()
        | (validated["annual_interest_rate"] <= 0)
    )

    validated.loc[
        invalid_interest_rate,
        "rejection_reason",
    ] += "LOAN-005: invalid annual_interest_rate; "

    # LOAN-006: term_months must be greater than 0.
    invalid_term = (
        validated["term_months"].isna()
        | (validated["term_months"] <= 0)
    )

    validated.loc[
        invalid_term,
        "rejection_reason",
    ] += "LOAN-006: invalid term_months; "

    # LOAN-007: EMI must be greater than 0.
    invalid_emi = (
        validated["emi_amount"].isna()
        | (validated["emi_amount"] <= 0)
    )

    validated.loc[
        invalid_emi,
        "rejection_reason",
    ] += "LOAN-007: invalid emi_amount; "

    # LOAN-008: outstanding balance must be between 0 and loan amount.
    invalid_outstanding = (
        validated["outstanding_amount"].isna()
        | (validated["outstanding_amount"] < 0)
        | (
            validated["outstanding_amount"]
            > validated["loan_amount"]
        )
    )

    validated.loc[
        invalid_outstanding,
        "rejection_reason",
    ] += "LOAN-008: invalid outstanding_amount; "

    # LOAN-009: start_date must be a valid date.
    start_dates = pd.to_datetime(
        validated["start_date"],
        errors="coerce",
    )

    invalid_start_date = start_dates.isna()

    validated.loc[
        invalid_start_date,
        "rejection_reason",
    ] += "LOAN-009: invalid start_date; "

    # LOAN-010: loan cannot start before the customer joined.
    customer_join_dates = customers.set_index(
        "customer_id"
    )["join_date"]

    mapped_join_dates = pd.to_datetime(
        validated["customer_id"].map(customer_join_dates),
        errors="coerce",
    )

    loan_before_customer_joined = (
        ~invalid_customer_reference
        & ~invalid_start_date
        & (start_dates < mapped_join_dates)
    )

    validated.loc[
        loan_before_customer_joined,
        "rejection_reason",
    ] += "LOAN-010: loan started before customer joined; "

    # LOAN-011: loan start date cannot be after the dataset snapshot.
    future_start_date = (
        ~invalid_start_date
        & (start_dates > AS_OF_DATE)
    )

    validated.loc[
        future_start_date,
        "rejection_reason",
    ] += "LOAN-011: start_date after snapshot date; "

    # LOAN-012: status must be ACTIVE or CLOSED.
    invalid_status = (
        validated["status"].isna()
        | ~validated["status"].isin(VALID_LOAN_STATUSES)
    )

    validated.loc[
        invalid_status,
        "rejection_reason",
    ] += "LOAN-012: invalid status; "

    # LOAN-013: CLOSED loans must have zero outstanding balance.
    invalid_closed_balance = (
        (validated["status"] == "CLOSED")
        & (validated["outstanding_amount"] != 0)
    )

    validated.loc[
        invalid_closed_balance,
        "rejection_reason",
    ] += "LOAN-013: CLOSED loan has outstanding balance; "

    # LOAN-014: ACTIVE loans must have positive outstanding balance.
    invalid_active_balance = (
        (validated["status"] == "ACTIVE")
        & (validated["outstanding_amount"] <= 0)
    )

    validated.loc[
        invalid_active_balance,
        "rejection_reason",
    ] += "LOAN-014: ACTIVE loan has no outstanding balance; "

    valid_loans = validated[
        validated["rejection_reason"] == ""
    ].copy()

    rejected_loans = validated[
        validated["rejection_reason"] != ""
    ].copy()

    valid_loans = valid_loans.drop(
        columns=["rejection_reason"]
    )

    return valid_loans, rejected_loans


def save_results(valid_loans, rejected_loans):
    valid_loans.to_csv(
        PROCESSED_LOANS_PATH,
        index=False,
    )

    rejected_loans.to_csv(
        REJECTED_LOANS_PATH,
        index=False,
    )


def main():
    loans, customers = load_data()

    valid_loans, rejected_loans = validate_loans(
        loans,
        customers,
    )

    save_results(
        valid_loans,
        rejected_loans,
    )

    print(f"Raw loans:      {len(loans)}")
    print(f"Valid loans:    {len(valid_loans)}")
    print(f"Rejected loans: {len(rejected_loans)}")

    print(
        "Saved valid loans to "
        "data/processed/loans.csv"
    )
    print(
        "Saved rejected loans to "
        "data/rejected/loans.csv"
    )


if __name__ == "__main__":
    main()