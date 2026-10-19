import math
import random
from datetime import timedelta
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CUSTOMERS_PATH = PROJECT_ROOT / "data" / "raw" / "customers.csv"
LOANS_PATH = PROJECT_ROOT / "data" / "raw" / "loans.csv"

RANDOM_SEED = 42
AS_OF_DATE = pd.Timestamp("2026-06-30")

LOAN_HOLDER_PROBABILITY = 0.60
MULTIPLE_LOAN_PROBABILITY = 0.25

LOAN_TYPES = [
    "PERSONAL",
    "HOME",
    "AUTO",
    "EDUCATION",
]

LOAN_CONFIG = {
    "PERSONAL": {
        "amount_range": (50000, 500000),
        "term_months": (12, 60),
        "annual_interest_rate": (10.0, 18.0),
    },
    "HOME": {
        "amount_range": (500000, 5000000),
        "term_months": (120, 240),
        "annual_interest_rate": (7.0, 10.0),
    },
    "AUTO": {
        "amount_range": (200000, 1500000),
        "term_months": (36, 84),
        "annual_interest_rate": (8.0, 12.0),
    },
    "EDUCATION": {
        "amount_range": (100000, 1000000),
        "term_months": (36, 120),
        "annual_interest_rate": (8.0, 13.0),
    },
}


def load_customers():
    return pd.read_csv(
        CUSTOMERS_PATH,
        parse_dates=["join_date"],
    )


def select_loan_holders(customers):
    loan_holders = []

    for _, customer in customers.iterrows():
        if random.random() < LOAN_HOLDER_PROBABILITY:
            loan_holders.append(customer["customer_id"])

    return loan_holders


def assign_loan_counts(loan_holders):
    loan_counts = {}

    for customer_id in loan_holders:
        loan_counts[customer_id] = (
            2 if random.random() < MULTIPLE_LOAN_PROBABILITY else 1
        )

    return loan_counts


def generate_loan_start_date(join_date):
    days_available = (AS_OF_DATE - join_date).days

    if days_available <= 0:
        return join_date

    random_days = random.randint(0, days_available)

    return join_date + timedelta(days=random_days)


def calculate_emi(
    principal,
    annual_interest_rate,
    term_months,
):
    monthly_rate = annual_interest_rate / (12 * 100)

    emi = (
        principal
        * monthly_rate
        * math.pow(1 + monthly_rate, term_months)
        / (math.pow(1 + monthly_rate, term_months) - 1)
    )

    return round(emi, 2)


def generate_loan_amount(loan_type, annual_income):
    config = LOAN_CONFIG[loan_type]

    minimum_amount, maximum_amount = config["amount_range"]

    income_based_limit = annual_income * 2.5

    effective_maximum = min(
        maximum_amount,
        income_based_limit,
    )

    if effective_maximum < minimum_amount:
        effective_maximum = minimum_amount

    amount = random.randint(
        int(minimum_amount),
        int(effective_maximum),
    )

    return round(amount / 1000) * 1000


def calculate_elapsed_months(start_date, as_of_date):
    months = (
        (as_of_date.year - start_date.year) * 12
        + (as_of_date.month - start_date.month)
    )

    if as_of_date.day < start_date.day:
        months -= 1

    return max(0, months)


def calculate_outstanding_amount(
    principal,
    annual_interest_rate,
    term_months,
    elapsed_months,
):
    if elapsed_months >= term_months:
        return 0.0

    monthly_rate = annual_interest_rate / (12 * 100)

    remaining_balance = (
        principal
        * (
            math.pow(1 + monthly_rate, term_months)
            - math.pow(1 + monthly_rate, elapsed_months)
        )
        / (
            math.pow(1 + monthly_rate, term_months)
            - 1
        )
    )

    return round(remaining_balance, 2)


def generate_loan_record(customer, loan_id):
    loan_type = random.choice(LOAN_TYPES)
    config = LOAN_CONFIG[loan_type]

    loan_amount = generate_loan_amount(
        loan_type,
        customer["annual_income"],
    )

    term_months = random.randint(
        config["term_months"][0],
        config["term_months"][1],
    )

    annual_interest_rate = round(
        random.uniform(
            config["annual_interest_rate"][0],
            config["annual_interest_rate"][1],
        ),
        2,
    )

    emi_amount = calculate_emi(
        loan_amount,
        annual_interest_rate,
        term_months,
    )

    start_date = generate_loan_start_date(
        customer["join_date"]
    )

    elapsed_months = calculate_elapsed_months(
        start_date,
        AS_OF_DATE,
    )

    outstanding_amount = calculate_outstanding_amount(
        principal=loan_amount,
        annual_interest_rate=annual_interest_rate,
        term_months=term_months,
        elapsed_months=elapsed_months,
    )

    status = (
        "CLOSED"
        if outstanding_amount == 0
        else "ACTIVE"
    )

    return {
        "loan_id": loan_id,
        "customer_id": customer["customer_id"],
        "loan_type": loan_type,
        "loan_amount": loan_amount,
        "annual_interest_rate": annual_interest_rate,
        "term_months": term_months,
        "emi_amount": emi_amount,
        "outstanding_amount": outstanding_amount,
        "start_date": start_date.date(),
        "status": status,
    }


def generate_loans(customers, loan_counts):
    loans = []
    loan_number = 1

    for _, customer in customers.iterrows():
        customer_id = customer["customer_id"]

        number_of_loans = loan_counts.get(
            customer_id,
            0,
        )

        for _ in range(number_of_loans):
            loan_id = f"LOAN{loan_number:04d}"

            loan = generate_loan_record(
                customer,
                loan_id,
            )

            loans.append(loan)
            loan_number += 1

    return pd.DataFrame(loans)


if __name__ == "__main__":
    random.seed(RANDOM_SEED)

    customers = load_customers()

    loan_holders = select_loan_holders(customers)
    loan_counts = assign_loan_counts(loan_holders)

    loans = generate_loans(
        customers,
        loan_counts,
    )

    loans.to_csv(
        LOANS_PATH,
        index=False,
    )

    print(f"Generated {len(loans)} loans.")
    print(f"Saved to: {LOANS_PATH}")