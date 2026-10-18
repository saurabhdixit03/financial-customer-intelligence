import pandas as pd

from src.validate_transactions import validate_transactions


def create_accounts():
    return pd.DataFrame(
        [
            {
                "account_id": "ACC00001",
                "open_date": "2024-01-15",
            },
            {
                "account_id": "ACC00002",
                "open_date": "2024-06-01",
            },
        ]
    )


def test_valid_transaction_is_accepted():
    accounts = create_accounts()

    transactions = pd.DataFrame(
        [
            {
                "transaction_id": "TXN0000001",
                "account_id": "ACC00001",
                "transaction_date": "2024-01-20",
                "transaction_type": "DEBIT",
                "category": "GROCERIES",
                "amount": 2500,
            }
        ]
    )

    valid, rejected = validate_transactions(
        transactions,
        accounts,
    )

    assert len(valid) == 1
    assert len(rejected) == 0


def test_transaction_with_unknown_account_is_rejected():
    accounts = create_accounts()

    transactions = pd.DataFrame(
        [
            {
                "transaction_id": "TXN0000002",
                "account_id": "ACC99999",
                "transaction_date": "2024-07-01",
                "transaction_type": "DEBIT",
                "category": "SHOPPING",
                "amount": 3000,
            }
        ]
    )

    valid, rejected = validate_transactions(
        transactions,
        accounts,
    )

    assert len(valid) == 0
    assert len(rejected) == 1

    rejection_reason = rejected.iloc[0]["rejection_reason"]

    assert "TXN-002: invalid account reference" in rejection_reason


def test_transaction_before_account_opened_is_rejected():
    accounts = create_accounts()

    transactions = pd.DataFrame(
        [
            {
                "transaction_id": "TXN0000003",
                "account_id": "ACC00002",
                "transaction_date": "2024-05-15",
                "transaction_type": "DEBIT",
                "category": "UTILITIES",
                "amount": 1500,
            }
        ]
    )

    valid, rejected = validate_transactions(
        transactions,
        accounts,
    )

    assert len(valid) == 0
    assert len(rejected) == 1

    rejection_reason = rejected.iloc[0]["rejection_reason"]

    assert (
        "TXN-004: transaction occurred before account opened"
        in rejection_reason
    )


def test_transaction_with_invalid_amount_is_rejected():
    accounts = create_accounts()

    transactions = pd.DataFrame(
        [
            {
                "transaction_id": "TXN0000004",
                "account_id": "ACC00001",
                "transaction_date": "2024-02-01",
                "transaction_type": "DEBIT",
                "category": "GROCERIES",
                "amount": -500,
            }
        ]
    )

    valid, rejected = validate_transactions(
        transactions,
        accounts,
    )

    assert len(valid) == 0
    assert len(rejected) == 1

    rejection_reason = rejected.iloc[0]["rejection_reason"]

    assert "TXN-007: invalid amount" in rejection_reason