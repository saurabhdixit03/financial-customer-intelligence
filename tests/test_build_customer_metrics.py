import pytest
import pandas as pd

from src.build_customer_metrics import build_customer_metrics


def test_customer_transaction_metrics_are_calculated():
    customers = pd.DataFrame(
        [
            {
                "customer_id": "CUST0001",
                "age": 30,
                "city": "Pune",
                "occupation": "Software Engineer",
                "annual_income": 600000,
                "join_date": "2024-01-01",
            }
        ]
    )

    accounts = pd.DataFrame(
        [
            {
                "account_id": "ACC00001",
                "customer_id": "CUST0001",
            }
        ]
    )

    transactions = pd.DataFrame(
        [
            {
                "transaction_id": "TXN001",
                "account_id": "ACC00001",
                "transaction_type": "CREDIT",
                "amount": 50000,
            },
            {
                "transaction_id": "TXN002",
                "account_id": "ACC00001",
                "transaction_type": "DEBIT",
                "amount": 12000,
            },
            {
                "transaction_id": "TXN003",
                "account_id": "ACC00001",
                "transaction_type": "DEBIT",
                "amount": 8000,
            },
        ]
    )

    result = build_customer_metrics(
        customers,
        accounts,
        transactions,
    )

    customer = result.iloc[0]

    assert customer["total_credit"] == 50000
    assert customer["total_debit"] == 20000
    assert customer["net_cash_flow"] == 30000
    assert customer["spending_ratio"] == 0.4
    assert customer["transaction_count"] == 3



def test_customer_without_transactions_is_preserved():
    customers = pd.DataFrame(
        [
            {
                "customer_id": "CUST0001",
                "age": 30,
                "city": "Pune",
                "occupation": "Software Engineer",
                "annual_income": 600000,
                "join_date": "2024-01-01",
            },
            {
                "customer_id": "CUST0002",
                "age": 40,
                "city": "Mumbai",
                "occupation": "Teacher",
                "annual_income": 500000,
                "join_date": "2024-02-01",
            },
        ]
    )

    accounts = pd.DataFrame(
        [
            {
                "account_id": "ACC00001",
                "customer_id": "CUST0001",
            }
        ]
    )

    transactions = pd.DataFrame(
        [
            {
                "transaction_id": "TXN001",
                "account_id": "ACC00001",
                "transaction_type": "CREDIT",
                "amount": 50000,
            }
        ]
    )

    result = build_customer_metrics(
        customers,
        accounts,
        transactions,
    )

    assert len(result) == 2

    customer = result[
        result["customer_id"] == "CUST0002"
    ].iloc[0]

    assert customer["total_credit"] == 0
    assert customer["total_debit"] == 0
    assert customer["net_cash_flow"] == 0
    assert customer["spending_ratio"] == 0
    assert customer["transaction_count"] == 0


def test_unmatched_transaction_account_raises_error():
    customers = pd.DataFrame(
        [
            {
                "customer_id": "CUST0001",
                "age": 30,
                "city": "Pune",
                "occupation": "Software Engineer",
                "annual_income": 600000,
                "join_date": "2024-01-01",
            }
        ]
    )

    accounts = pd.DataFrame(
        [
            {
                "account_id": "ACC00001",
                "customer_id": "CUST0001",
            }
        ]
    )

    transactions = pd.DataFrame(
        [
            {
                "transaction_id": "TXN001",
                "account_id": "ACC99999",
                "transaction_type": "DEBIT",
                "amount": 1000,
            }
        ]
    )

    with pytest.raises(
        ValueError,
        match="Transaction count changed during account join",
    ):
        build_customer_metrics(
            customers,
            accounts,
            transactions,
        )