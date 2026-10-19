import os
from pathlib import Path

import pandas as pd
import psycopg


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "exports" / "dashboard"

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "dbname": "financial_customer_intelligence",
    "user": "postgres",
}

EXPORTS = {
    "customer_360": "customer_360.csv",
    "customer_segmentation": "customer_segmentation.csv",
    "loan_readiness": "loan_readiness.csv",
}


def get_password():
    password = os.getenv("DB_PASSWORD")

    if not password:
        raise RuntimeError(
            "DB_PASSWORD environment variable is not set."
        )

    return password


def export_dashboard_data():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with psycopg.connect(
        **DB_CONFIG,
        password=get_password(),
    ) as connection:
        for source_name, file_name in EXPORTS.items():
            query = f"""
                SELECT *
                FROM {source_name}
                ORDER BY customer_id;
            """

            dataframe = pd.read_sql_query(
                query,
                connection,
            )

            output_path = OUTPUT_DIR / file_name

            dataframe.to_csv(
                output_path,
                index=False,
            )

            print(
                f"Exported {source_name}: "
                f"{len(dataframe)} rows -> "
                f"{output_path.relative_to(PROJECT_ROOT)}"
            )


def main():
    print("Exporting dashboard data from PostgreSQL...")
    export_dashboard_data()
    print("Dashboard data export completed successfully.")


if __name__ == "__main__":
    main()