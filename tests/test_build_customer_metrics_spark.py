import math

import pytest
from pyspark.sql import SparkSession

from src.build_customer_metrics_spark import (
    build_customer_metrics,
)


@pytest.fixture(scope="module")
def spark():
    session = (
        SparkSession.builder
        .master("local[1]")
        .appName("FCI-Spark-Tests")
        .config("spark.sql.shuffle.partitions", "1")
        .getOrCreate()
    )

    session.sparkContext.setLogLevel("ERROR")

    yield session

    session.stop()


def make_customers(spark, rows_sql):
    return spark.sql(
        f"""
        SELECT
            customer_id,
            age,
            city,
            occupation,
            annual_income,
            CAST(join_date AS DATE) AS join_date
        FROM VALUES
            {rows_sql}
        AS customers(
            customer_id,
            age,
            city,
            occupation,
            annual_income,
            join_date
        )
        """
    )


def make_accounts(spark, rows_sql):
    return spark.sql(
        f"""
        SELECT
            account_id,
            customer_id,
            account_type,
            balance,
            CAST(open_date AS DATE) AS open_date,
            status
        FROM VALUES
            {rows_sql}
        AS accounts(
            account_id,
            customer_id,
            account_type,
            balance,
            open_date,
            status
        )
        """
    )


def make_transactions(spark, rows_sql):
    return spark.sql(
        f"""
        SELECT
            transaction_id,
            account_id,
            CAST(transaction_date AS DATE)
                AS transaction_date,
            transaction_type,
            category,
            amount
        FROM VALUES
            {rows_sql}
        AS transactions(
            transaction_id,
            account_id,
            transaction_date,
            transaction_type,
            category,
            amount
        )
        """
    )


def make_empty_transactions(spark):
    return spark.sql(
        """
        SELECT
            CAST(NULL AS STRING) AS transaction_id,
            CAST(NULL AS STRING) AS account_id,
            CAST(NULL AS DATE) AS transaction_date,
            CAST(NULL AS STRING) AS transaction_type,
            CAST(NULL AS STRING) AS category,
            CAST(NULL AS DOUBLE) AS amount
        WHERE FALSE
        """
    )


def test_customer_metrics_calculation(spark):
    customers = make_customers(
        spark,
        """
        ('CUST_TEST_1', 30, 'Pune', 'Engineer',
         600000.0, '2025-01-01')
        """,
    )

    accounts = make_accounts(
        spark,
        """
        ('ACC_TEST_1', 'CUST_TEST_1', 'SAVINGS',
         10000.0, '2025-01-01', 'ACTIVE')
        """,
    )

    transactions = make_transactions(
        spark,
        """
        ('TXN_TEST_1', 'ACC_TEST_1', '2026-01-01',
         'CREDIT', 'INCOME', 10000.0),

        ('TXN_TEST_2', 'ACC_TEST_1', '2026-01-05',
         'DEBIT', 'FOOD', 3000.0),

        ('TXN_TEST_3', 'ACC_TEST_1', '2026-01-10',
         'DEBIT', 'UTILITIES', 2000.0)
        """,
    )

    result = (
        build_customer_metrics(
            customers,
            accounts,
            transactions,
        )
        .collect()[0]
    )

    assert result["customer_id"] == "CUST_TEST_1"
    assert result["account_count"] == 1

    assert result["total_credit"] == pytest.approx(
        10000.0
    )

    assert result["total_debit"] == pytest.approx(
        5000.0
    )

    assert result["net_cash_flow"] == pytest.approx(
        5000.0
    )

    assert result["spending_ratio"] == pytest.approx(
        0.5
    )

    assert result["transaction_count"] == 3

    # Only one month of debit activity exists,
    # so sample standard deviation is undefined.
    assert result["spending_variability"] is None


def test_customer_with_multiple_accounts(spark):
    customers = make_customers(
        spark,
        """
        ('CUST_TEST_2', 35, 'Mumbai', 'Analyst',
         900000.0, '2025-01-01')
        """,
    )

    accounts = make_accounts(
        spark,
        """
        ('ACC_TEST_2A', 'CUST_TEST_2', 'SAVINGS',
         20000.0, '2025-01-01', 'ACTIVE'),

        ('ACC_TEST_2B', 'CUST_TEST_2', 'CURRENT',
         30000.0, '2025-02-01', 'ACTIVE')
        """,
    )

    transactions = make_transactions(
        spark,
        """
        ('TXN_TEST_4', 'ACC_TEST_2A', '2026-01-01',
         'CREDIT', 'INCOME', 15000.0),

        ('TXN_TEST_5', 'ACC_TEST_2B', '2026-01-10',
         'DEBIT', 'OTHER', 4000.0)
        """,
    )

    result = (
        build_customer_metrics(
            customers,
            accounts,
            transactions,
        )
        .collect()[0]
    )

    assert result["account_count"] == 2

    assert result["total_credit"] == pytest.approx(
        15000.0
    )

    assert result["total_debit"] == pytest.approx(
        4000.0
    )

    assert result["net_cash_flow"] == pytest.approx(
        11000.0
    )

    assert result["transaction_count"] == 2


def test_customer_without_transactions_is_preserved(
    spark,
):
    customers = make_customers(
        spark,
        """
        ('CUST_TEST_3', 40, 'Pune', 'Teacher',
         500000.0, '2025-01-01')
        """,
    )

    accounts = make_accounts(
        spark,
        """
        ('ACC_TEST_3', 'CUST_TEST_3', 'SAVINGS',
         5000.0, '2025-01-01', 'ACTIVE')
        """,
    )

    transactions = make_empty_transactions(
        spark
    )

    result = (
        build_customer_metrics(
            customers,
            accounts,
            transactions,
        )
        .collect()[0]
    )

    assert result["customer_id"] == "CUST_TEST_3"
    assert result["account_count"] == 1

    assert result["total_credit"] == pytest.approx(
        0.0
    )

    assert result["total_debit"] == pytest.approx(
        0.0
    )

    assert result["net_cash_flow"] == pytest.approx(
        0.0
    )

    assert result["transaction_count"] == 0

    assert result["spending_ratio"] is None
    assert result["spending_variability"] is None


def test_spending_variability_uses_monthly_debit_totals(
    spark,
):
    customers = make_customers(
        spark,
        """
        ('CUST_TEST_4', 28, 'Pune', 'Developer',
         800000.0, '2025-01-01')
        """,
    )

    accounts = make_accounts(
        spark,
        """
        ('ACC_TEST_4', 'CUST_TEST_4', 'SAVINGS',
         15000.0, '2025-01-01', 'ACTIVE')
        """,
    )

    transactions = make_transactions(
        spark,
        """
        ('TXN_TEST_6', 'ACC_TEST_4', '2026-01-05',
         'DEBIT', 'FOOD', 100.0),

        ('TXN_TEST_7', 'ACC_TEST_4', '2026-01-20',
         'DEBIT', 'OTHER', 100.0),

        ('TXN_TEST_8', 'ACC_TEST_4', '2026-02-10',
         'DEBIT', 'FOOD', 400.0)
        """,
    )

    result = (
        build_customer_metrics(
            customers,
            accounts,
            transactions,
        )
        .collect()[0]
    )

    # Monthly debit totals:
    # January  = 200
    # February = 400
    #
    # Mean = 300
    # Sample standard deviation = sqrt(20000)
    # Variability = stddev / mean.

    expected_variability = (
        math.sqrt(20000)
        / 300
    )

    assert result[
        "spending_variability"
    ] == pytest.approx(
        expected_variability
    )