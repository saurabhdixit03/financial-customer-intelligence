import csv
import random
from datetime import date, timedelta
from pathlib import Path

RANDOM_SEED = 42

NUMBER_OF_CUSTOMERS = 20

CITIES = [
    "Pune",
    "Mumbai",
    "Bengaluru",
    "Hyderabad",
    "Chennai",
]

OCCUPATIONS = [
    "Software Engineer",
    "Teacher",
    "Accountant",
    "Sales Executive",
    "Business Owner",
    "Operations Executive",
]


def generate_join_date():
    start_date = date(2020, 1, 1)
    end_date = date(2025, 12, 31)

    total_days = (end_date - start_date).days
    random_days = random.randint(0, total_days)

    return start_date + timedelta(days=random_days)


def generate_customers():
    customers = []

    for customer_number in range(1, NUMBER_OF_CUSTOMERS + 1):
        customer = {
            "customer_id": f"CUST{customer_number:04d}",
            "age": random.randint(21, 60),
            "city": random.choice(CITIES),
            "occupation": random.choice(OCCUPATIONS),
            "annual_income": random.randrange(300000, 2500001, 50000),
            "join_date": generate_join_date().isoformat(),
        }

        customers.append(customer)

    return customers


def save_customers(customers):
    output_path = Path("data/raw/customers.csv")

    fieldnames = [
        "customer_id",
        "age",
        "city",
        "occupation",
        "annual_income",
        "join_date",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(customers)


def main():
    random.seed(RANDOM_SEED)
    customers = generate_customers()
    save_customers(customers)

    print(f"Generated {len(customers)} customers.")
    print("Saved to data/raw/customers.csv")


if __name__ == "__main__":
    main()