import csv
import os
from pathlib import Path

import psycopg
from psycopg import sql


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SQL_DIR = PROJECT_ROOT / "sql"


DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "dbname": "financial_customer_intelligence",
    "user": "postgres",
}


TABLE_LOAD_ORDER = [
    (
        "customers",
        PROCESSED_DIR / "customers.csv",
    ),
    (
        "accounts",
        PROCESSED_DIR / "accounts.csv",
    ),
    (
        "transactions",
        PROCESSED_DIR / "transactions.csv",
    ),
    (
        "loans",
        PROCESSED_DIR / "loans.csv",
    ),
]


ANALYTICAL_SQL_FILES = [
    "customer_transaction_summary.sql",
    "customer_loan_summary.sql",
    "customer_360.sql",
    "customer_segmentation.sql",
    "loan_readiness.sql",
]


def get_connection():
    password = os.getenv("DB_PASSWORD")

    if not password:
        raise RuntimeError(
            "DB_PASSWORD environment variable is not set."
        )

    return psycopg.connect(
        **DB_CONFIG,
        password=password,
    )


def execute_sql_file(
    connection,
    sql_path,
):
    if not sql_path.exists():
        raise FileNotFoundError(
            f"SQL file not found: {sql_path}"
        )

    sql_text = sql_path.read_text(
        encoding="utf-8"
    )

    with connection.cursor() as cursor:
        cursor.execute(sql_text)


def create_tables(connection):
    print("Creating PostgreSQL tables...")

    execute_sql_file(
        connection,
        SQL_DIR / "create_tables.sql",
    )

    connection.commit()

    print("PostgreSQL tables ready.")


def clear_tables(connection):
    print(
        "Clearing existing warehouse data..."
    )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            TRUNCATE TABLE
                transactions,
                loans,
                accounts,
                customers
            RESTART IDENTITY
            CASCADE;
            """
        )

    connection.commit()

    print("Existing warehouse data cleared.")


def load_csv(
    connection,
    table_name,
    csv_path,
):
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Processed file not found: {csv_path}"
        )

    with csv_path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        reader = csv.reader(file)

        try:
            columns = next(reader)
        except StopIteration:
            raise ValueError(
                f"CSV file is empty: {csv_path}"
            )

    if not columns:
        raise ValueError(
            f"CSV has no header: {csv_path}"
        )

    copy_statement = sql.SQL(
        "COPY {} ({}) FROM STDIN "
        "WITH (FORMAT CSV, HEADER TRUE)"
    ).format(
        sql.Identifier(table_name),
        sql.SQL(", ").join(
            sql.Identifier(column)
            for column in columns
        ),
    )

    with connection.cursor() as cursor:
        with csv_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            with cursor.copy(
                copy_statement
            ) as copy:
                while data := file.read(
                    1024 * 1024
                ):
                    copy.write(data)

    connection.commit()

    with connection.cursor() as cursor:
        query = sql.SQL(
            "SELECT COUNT(*) FROM {}"
        ).format(
            sql.Identifier(table_name)
        )

        cursor.execute(query)

        row_count = cursor.fetchone()[0]

    print(
        f"Loaded {table_name}: "
        f"{row_count} rows"
    )

    return row_count


def load_processed_data(connection):
    print(
        "\nLoading validated processed data..."
    )

    counts = {}

    for (
        table_name,
        csv_path,
    ) in TABLE_LOAD_ORDER:
        counts[table_name] = load_csv(
            connection,
            table_name,
            csv_path,
        )

    return counts


def build_analytical_layer(connection):
    print(
        "\nBuilding analytical SQL layer..."
    )

    for filename in ANALYTICAL_SQL_FILES:
        print(
            f"Executing {filename}..."
        )

        execute_sql_file(
            connection,
            SQL_DIR / filename,
        )

        connection.commit()

    print(
        "Analytical SQL layer ready."
    )


def verify_database(connection):
    checks = {
        "customers": 20,
        "accounts": 27,
        "transactions": 1707,
        "loans": 17,
    }

    print(
        "\nDatabase verification:"
    )

    with connection.cursor() as cursor:
        for table_name, expected in checks.items():
            query = sql.SQL(
                "SELECT COUNT(*) FROM {}"
            ).format(
                sql.Identifier(table_name)
            )

            cursor.execute(query)

            actual = cursor.fetchone()[0]

            print(
                f"{table_name}: "
                f"{actual} rows"
            )

            if actual != expected:
                raise AssertionError(
                    f"{table_name}: expected "
                    f"{expected} rows, found "
                    f"{actual}."
                )

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM customer_360;
            """
        )

        customer_360_count = (
            cursor.fetchone()[0]
        )

        print(
            "customer_360: "
            f"{customer_360_count} rows"
        )

        if customer_360_count != 20:
            raise AssertionError(
                "customer_360 should contain "
                "20 customers."
            )

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM loan_readiness;
            """
        )

        readiness_count = (
            cursor.fetchone()[0]
        )

        print(
            "loan_readiness: "
            f"{readiness_count} rows"
        )

        if readiness_count != 20:
            raise AssertionError(
                "loan_readiness should contain "
                "20 customers."
            )

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM customer_segmentation;
            """
        )

        segmentation_count = (
            cursor.fetchone()[0]
        )

        print(
            "customer_segmentation: "
            f"{segmentation_count} rows"
        )

        if segmentation_count != 20:
            raise AssertionError(
                "customer_segmentation should "
                "contain 20 customers."
            )

    print(
        "Database verification passed."
    )


def main():
    print(
        "\nPostgreSQL Warehouse Load"
    )
    print(
        "========================="
    )

    with get_connection() as connection:
        create_tables(connection)

        clear_tables(connection)

        load_processed_data(connection)

        build_analytical_layer(connection)

        verify_database(connection)

    print(
        "\nPostgreSQL load completed successfully."
    )


if __name__ == "__main__":
    main()