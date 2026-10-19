import numpy as np
import os
from pathlib import Path

import pandas as pd
import psycopg


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PANDAS_METRICS_PATH = (
    PROJECT_ROOT / "data" / "processed" / "customer_metrics.csv"
)

SQL_QUERY_PATH = (
    PROJECT_ROOT / "sql" / "customer_transaction_summary.sql"
)


def load_pandas_metrics():
    return pd.read_csv(PANDAS_METRICS_PATH)


def load_sql_query():
    return SQL_QUERY_PATH.read_text(encoding="utf-8")

def get_database_connection():
    password = os.environ.get("DB_PASSWORD")

    if not password:
        raise ValueError("DB_PASSWORD environment variable is not set.")

    return psycopg.connect(
        host="127.0.0.1",
        port=5432,
        dbname="financial_customer_intelligence",
        user="postgres",
        password=password,
    )

def load_sql_metrics(connection, sql_query):
    with connection.cursor() as cursor:
        cursor.execute(sql_query)

        columns = [
            column.name
            for column in cursor.description
        ]

        rows = cursor.fetchall()

    return pd.DataFrame(rows, columns=columns)


def validate_customer_ids(pandas_metrics, sql_metrics):
    pandas_ids = set(pandas_metrics["customer_id"])
    sql_ids = set(sql_metrics["customer_id"])

    missing_in_sql = pandas_ids - sql_ids
    missing_in_pandas = sql_ids - pandas_ids

    if missing_in_sql or missing_in_pandas:
        raise ValueError(
            "Customer ID mismatch. "
            f"Missing in SQL: {sorted(missing_in_sql)}. "
            f"Missing in Pandas: {sorted(missing_in_pandas)}."
        )

    print("Customer IDs match.")

def compare_numeric_metrics(pandas_metrics, sql_metrics):
    metrics = [
        "account_count",
        "total_credit",
        "total_debit",
        "net_cash_flow",
        "spending_ratio",
        "spending_variability",
        "transaction_count",
    ]

    merged = pandas_metrics[
        ["customer_id"] + metrics
    ].merge(
        sql_metrics[["customer_id"] + metrics],
        on="customer_id",
        suffixes=("_pandas", "_sql"),
    )

    mismatches = []

    for metric in metrics:
        pandas_values = merged[f"{metric}_pandas"].astype(float)
        sql_values = merged[f"{metric}_sql"].astype(float)

        matches = np.isclose(
            pandas_values,
            sql_values,
            rtol=0,
            atol=0.001,
        )

        if not matches.all():
            mismatches.append(metric)

    if mismatches:
        raise ValueError(
            f"Metric mismatch found for: {', '.join(mismatches)}"
        )

    print("Customer numeric metrics match.")

if __name__ == "__main__":
    pandas_metrics = load_pandas_metrics()
    sql_query = load_sql_query()

    with get_database_connection() as connection:
        sql_metrics = load_sql_metrics(connection, sql_query)

    print(f"Pandas metric rows: {len(pandas_metrics)}")
    print(f"SQL metric rows: {len(sql_metrics)}")

    validate_customer_ids(pandas_metrics, sql_metrics)
    compare_numeric_metrics(pandas_metrics, sql_metrics)