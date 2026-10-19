import os
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PANDAS_METRICS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "customer_metrics.csv"
)

SPARK_METRICS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "customer_metrics_spark.csv"
)


DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "dbname": "financial_customer_intelligence",
    "user": "postgres",
}


METRIC_COLUMNS = [
    "account_count",
    "total_credit",
    "total_debit",
    "net_cash_flow",
    "spending_ratio",
    "transaction_count",
    "spending_variability",
]


FLOAT_METRICS = [
    "total_credit",
    "total_debit",
    "net_cash_flow",
    "spending_ratio",
    "spending_variability",
]


INTEGER_METRICS = [
    "account_count",
    "transaction_count",
]


ABSOLUTE_TOLERANCE = 0.001


def load_pandas_metrics():
    if not PANDAS_METRICS_PATH.exists():
        raise FileNotFoundError(
            "Pandas customer metrics file not found: "
            f"{PANDAS_METRICS_PATH}"
        )

    return pd.read_csv(
        PANDAS_METRICS_PATH
    )


def load_spark_metrics():
    if not SPARK_METRICS_PATH.exists():
        raise FileNotFoundError(
            "Spark customer metrics file not found: "
            f"{SPARK_METRICS_PATH}"
        )

    return pd.read_csv(
        SPARK_METRICS_PATH
    )


def load_sql_metrics():
    password = os.getenv(
        "DB_PASSWORD"
    )

    if not password:
        raise RuntimeError(
            "DB_PASSWORD environment variable is not set."
        )

    query = """
        SELECT
            customer_id,
            account_count,
            total_credit,
            total_debit,
            net_cash_flow,
            spending_ratio,
            transaction_count,
            spending_variability
        FROM customer_360
        ORDER BY customer_id;
    """

    with psycopg.connect(
        **DB_CONFIG,
        password=password,
    ) as connection:
        return pd.read_sql_query(
            query,
            connection,
        )


def prepare_metrics(
    dataframe,
    source_name,
):
    required_columns = {
        "customer_id",
        *METRIC_COLUMNS,
    }

    missing_columns = (
        required_columns
        - set(
            dataframe.columns
        )
    )

    if missing_columns:
        raise ValueError(
            f"{source_name} is missing columns: "
            f"{sorted(missing_columns)}"
        )

    prepared = dataframe[
        [
            "customer_id",
            *METRIC_COLUMNS,
        ]
    ].copy()

    if prepared[
        "customer_id"
    ].duplicated().any():
        raise ValueError(
            f"{source_name} contains duplicate "
            "customer_id values."
        )

    for column in METRIC_COLUMNS:
        prepared[column] = (
            pd.to_numeric(
                prepared[column],
                errors="coerce",
            )
        )

    return (
        prepared
        .sort_values(
            "customer_id"
        )
        .reset_index(
            drop=True
        )
    )


def validate_customer_ids(
    pandas_metrics,
    spark_metrics,
    sql_metrics,
):
    pandas_ids = set(
        pandas_metrics[
            "customer_id"
        ]
    )

    spark_ids = set(
        spark_metrics[
            "customer_id"
        ]
    )

    sql_ids = set(
        sql_metrics[
            "customer_id"
        ]
    )

    if not (
        pandas_ids
        == spark_ids
        == sql_ids
    ):
        raise AssertionError(
            "Customer IDs do not match "
            "across Pandas, Spark and SQL."
        )

    print(
        "Customer IDs match across all implementations."
    )


def compare_integer_metric(
    metric,
    left,
    right,
    left_name,
    right_name,
):
    left_values = (
        left[metric]
        .fillna(0)
        .astype(int)
        .to_numpy()
    )

    right_values = (
        right[metric]
        .fillna(0)
        .astype(int)
        .to_numpy()
    )

    matches = np.array_equal(
        left_values,
        right_values,
    )

    if not matches:
        mismatch_positions = np.where(
            left_values
            != right_values
        )[0]

        details = []

        for position in mismatch_positions:
            customer_id = left.iloc[
                position
            ]["customer_id"]

            details.append(
                f"{customer_id}: "
                f"{left_name}="
                f"{left_values[position]}, "
                f"{right_name}="
                f"{right_values[position]}"
            )

        raise AssertionError(
            f"{metric} mismatch between "
            f"{left_name} and {right_name}:\n"
            + "\n".join(details)
        )


def compare_float_metric(
    metric,
    left,
    right,
    left_name,
    right_name,
):
    left_values = (
        left[metric]
        .to_numpy(
            dtype=float
        )
    )

    right_values = (
        right[metric]
        .to_numpy(
            dtype=float
        )
    )

    matches = np.isclose(
        left_values,
        right_values,
        atol=ABSOLUTE_TOLERANCE,
        rtol=0,
        equal_nan=True,
    )

    if not matches.all():
        mismatch_positions = np.where(
            ~matches
        )[0]

        details = []

        for position in mismatch_positions:
            customer_id = left.iloc[
                position
            ]["customer_id"]

            details.append(
                f"{customer_id}: "
                f"{left_name}="
                f"{left_values[position]}, "
                f"{right_name}="
                f"{right_values[position]}"
            )

        raise AssertionError(
            f"{metric} mismatch between "
            f"{left_name} and {right_name}:\n"
            + "\n".join(details)
        )


def compare_sources(
    left,
    right,
    left_name,
    right_name,
):
    for metric in INTEGER_METRICS:
        compare_integer_metric(
            metric,
            left,
            right,
            left_name,
            right_name,
        )

    for metric in FLOAT_METRICS:
        compare_float_metric(
            metric,
            left,
            right,
            left_name,
            right_name,
        )

    print(
        f"{left_name} ↔ {right_name}: "
        "all metrics match."
    )


def main():
    pandas_metrics = prepare_metrics(
        load_pandas_metrics(),
        "Pandas",
    )

    spark_metrics = prepare_metrics(
        load_spark_metrics(),
        "Spark",
    )

    sql_metrics = prepare_metrics(
        load_sql_metrics(),
        "SQL",
    )

    print(
        "\nThree-way customer metrics reconciliation"
    )

    print(
        "-----------------------------------------"
    )

    print(
        f"Pandas rows: {len(pandas_metrics)}"
    )

    print(
        f"Spark rows:  {len(spark_metrics)}"
    )

    print(
        f"SQL rows:    {len(sql_metrics)}"
    )

    if not (
        len(pandas_metrics)
        == len(spark_metrics)
        == len(sql_metrics)
    ):
        raise AssertionError(
            "Row counts do not match across "
            "Pandas, Spark and SQL."
        )

    validate_customer_ids(
        pandas_metrics,
        spark_metrics,
        sql_metrics,
    )

    compare_sources(
        pandas_metrics,
        spark_metrics,
        "Pandas",
        "Spark",
    )

    compare_sources(
        pandas_metrics,
        sql_metrics,
        "Pandas",
        "SQL",
    )

    compare_sources(
        spark_metrics,
        sql_metrics,
        "Spark",
        "SQL",
    )

    print(
        "\nRECONCILIATION PASSED"
    )

    print(
        "Pandas, PySpark and PostgreSQL produce "
        "equivalent customer-level metrics."
    )


if __name__ == "__main__":
    main()