import pandas as pd

from src.validate_customers import validate_customers


def test_valid_customers_are_accepted():
    customers = pd.DataFrame(
        [
            {
                "customer_id": "CUST0001",
                "age": 30,
                "city": "Pune",
                "occupation": "Software Engineer",
                "annual_income": 800000,
                "join_date": "2024-01-15",
            }
        ]
    )

    valid, rejected = validate_customers(customers)

    assert len(valid) == 1
    assert len(rejected) == 0


def test_invalid_customer_is_rejected():
    customers = pd.DataFrame(
        [
            {
                "customer_id": "CUST0001",
                "age": 15,
                "city": "Pune",
                "occupation": "Student",
                "annual_income": -50000,
                "join_date": "not-a-date",
            }
        ]
    )

    valid, rejected = validate_customers(customers)

    assert len(valid) == 0
    assert len(rejected) == 1

    rejection_reason = rejected.iloc[0]["rejection_reason"]

    assert "CUST-002: invalid age" in rejection_reason
    assert "CUST-005: invalid annual_income" in rejection_reason
    assert "CUST-006: invalid join_date" in rejection_reason