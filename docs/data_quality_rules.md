# Data Quality Rules

This document defines the initial validation rules applied to raw financial data before it is accepted for downstream processing and analysis.

## Customer Rules

| Rule ID | Column | Validation Rule |
|---|---|---|
| CUST-001 | customer_id | Must not be missing and must be unique |
| CUST-002 | age | Must be between 18 and 100 |
| CUST-003 | city | Must not be missing |
| CUST-004 | occupation | Must not be missing |
| CUST-005 | annual_income | Must be greater than 0 |
| CUST-006 | join_date | Must be a valid date |

## Account Rules

| Rule ID | Column | Validation Rule |
|---|---|---|
| ACC-001 | account_id | Must not be missing and must be unique |
| ACC-002 | customer_id | Must reference an existing customer |
| ACC-003 | account_type | Must be SAVINGS or CURRENT |
| ACC-004 | balance | Must not be negative |
| ACC-005 | open_date | Must be a valid date |
| ACC-006 | open_date | Must not be earlier than the customer's join date |
| ACC-007 | status | Must be ACTIVE or INACTIVE |

## Transaction Rules

| Rule ID | Column | Validation Rule |
|---|---|---|
| TXN-001 | transaction_id | Must not be missing and must be unique |
| TXN-002 | account_id | Must reference an existing account |
| TXN-003 | transaction_date | Must be a valid date |
| TXN-004 | transaction_date | Must not be earlier than the account open date |
| TXN-005 | transaction_type | Must be CREDIT or DEBIT |
| TXN-006 | category | Must not be missing |
| TXN-007 | amount | Must be greater than 0 |

## Validation Outcomes

Each raw record will have one of two outcomes:

- **Valid** - the record satisfies all applicable data quality rules and can continue to downstream processing.
- **Rejected** - the record violates one or more rules and is separated for investigation instead of silently entering the analytical dataset.

Rejected records should retain the reason for rejection so that data quality problems can be traced and understood.