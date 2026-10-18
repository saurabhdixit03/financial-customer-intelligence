import pandas as pd

from src.validate_accounts import validate_accounts


def create_customers():
    return pd.DataFrame(
        [
            {
                "customer_id": "CUST0001",
                "join_date": "2024-01-15",
            },
            {
                "customer_id": "CUST0002",
                "join_date": "2024-06-01",
            },
        ]
    )


def test_valid_account_is_accepted():
    customers = create_customers()

    accounts = pd.DataFrame(
        [
            {
                "account_id": "ACC00001",
                "customer_id": "CUST0001",
                "account_type": "SAVINGS",
                "balance": 50000,
                "open_date": "2024-01-20",
                "status": "ACTIVE",
            }
        ]
    )

    valid, rejected = validate_accounts(accounts, customers)

    assert len(valid) == 1
    assert len(rejected) == 0


def test_account_with_unknown_customer_is_rejected():
    customers = create_customers()

    accounts = pd.DataFrame(
        [
            {
                "account_id": "ACC00002",
                "customer_id": "CUST9999",
                "account_type": "SAVINGS",
                "balance": 30000,
                "open_date": "2024-07-01",
                "status": "ACTIVE",
            }
        ]
    )

    valid, rejected = validate_accounts(accounts, customers)

    assert len(valid) == 0
    assert len(rejected) == 1

    rejection_reason = rejected.iloc[0]["rejection_reason"]

    assert "ACC-002: invalid customer reference" in rejection_reason


def test_account_opened_before_customer_joined_is_rejected():
    customers = create_customers()

    accounts = pd.DataFrame(
        [
            {
                "account_id": "ACC00003",
                "customer_id": "CUST0002",
                "account_type": "CURRENT",
                "balance": 75000,
                "open_date": "2024-05-15",
                "status": "ACTIVE",
            }
        ]
    )

    valid, rejected = validate_accounts(accounts, customers)

    assert len(valid) == 0
    assert len(rejected) == 1

    rejection_reason = rejected.iloc[0]["rejection_reason"]

    assert (
        "ACC-006: account opened before customer joined"
        in rejection_reason
    )