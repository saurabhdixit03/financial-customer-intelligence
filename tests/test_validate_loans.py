import pandas as pd

from src.validate_loans import validate_loans


def build_customers():
    return pd.DataFrame(
        [
            {
                "customer_id": "CUST0001",
                "join_date": "2024-01-01",
            },
            {
                "customer_id": "CUST0002",
                "join_date": "2025-01-01",
            },
        ]
    )


def build_valid_loan():
    return {
        "loan_id": "LOAN0001",
        "customer_id": "CUST0001",
        "loan_type": "PERSONAL",
        "loan_amount": 200000,
        "annual_interest_rate": 12.0,
        "term_months": 36,
        "emi_amount": 6642.86,
        "outstanding_amount": 150000,
        "start_date": "2025-01-01",
        "status": "ACTIVE",
    }


def test_valid_loan_is_accepted():
    customers = build_customers()

    loans = pd.DataFrame(
        [build_valid_loan()]
    )

    valid, rejected = validate_loans(
        loans,
        customers,
    )

    assert len(valid) == 1
    assert len(rejected) == 0


def test_invalid_customer_reference_is_rejected():
    customers = build_customers()

    loan = build_valid_loan()
    loan["customer_id"] = "CUST9999"

    loans = pd.DataFrame([loan])

    valid, rejected = validate_loans(
        loans,
        customers,
    )

    assert len(valid) == 0
    assert len(rejected) == 1

    assert (
        "LOAN-002: invalid customer reference"
        in rejected.iloc[0]["rejection_reason"]
    )


def test_invalid_financial_values_are_rejected():
    customers = build_customers()

    loan = build_valid_loan()
    loan["loan_amount"] = -100
    loan["annual_interest_rate"] = 0
    loan["term_months"] = 0
    loan["emi_amount"] = -50
    loan["outstanding_amount"] = -10

    loans = pd.DataFrame([loan])

    valid, rejected = validate_loans(
        loans,
        customers,
    )

    assert len(valid) == 0
    assert len(rejected) == 1

    reason = rejected.iloc[0]["rejection_reason"]

    assert "LOAN-004" in reason
    assert "LOAN-005" in reason
    assert "LOAN-006" in reason
    assert "LOAN-007" in reason
    assert "LOAN-008" in reason


def test_invalid_loan_dates_are_rejected():
    customers = build_customers()

    before_join = build_valid_loan()
    before_join["loan_id"] = "LOAN0002"
    before_join["customer_id"] = "CUST0002"
    before_join["start_date"] = "2024-06-01"

    after_snapshot = build_valid_loan()
    after_snapshot["loan_id"] = "LOAN0003"
    after_snapshot["start_date"] = "2026-07-01"

    loans = pd.DataFrame(
        [
            before_join,
            after_snapshot,
        ]
    )

    valid, rejected = validate_loans(
        loans,
        customers,
    )

    assert len(valid) == 0
    assert len(rejected) == 2

    reasons = " ".join(
        rejected["rejection_reason"]
    )

    assert "LOAN-010" in reasons
    assert "LOAN-011" in reasons


def test_status_and_outstanding_balance_must_be_consistent():
    customers = build_customers()

    closed_with_balance = build_valid_loan()
    closed_with_balance["loan_id"] = "LOAN0002"
    closed_with_balance["status"] = "CLOSED"
    closed_with_balance["outstanding_amount"] = 10000

    active_without_balance = build_valid_loan()
    active_without_balance["loan_id"] = "LOAN0003"
    active_without_balance["status"] = "ACTIVE"
    active_without_balance["outstanding_amount"] = 0

    loans = pd.DataFrame(
        [
            closed_with_balance,
            active_without_balance,
        ]
    )

    valid, rejected = validate_loans(
        loans,
        customers,
    )

    assert len(valid) == 0
    assert len(rejected) == 2

    reasons = " ".join(
        rejected["rejection_reason"]
    )

    assert "LOAN-013" in reasons
    assert "LOAN-014" in reasons