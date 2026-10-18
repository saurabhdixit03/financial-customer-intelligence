# Data Model

## 1. Customer

Stores basic information about each customer.

| Column | Description |
|---|---|
| customer_id | Unique identifier for the customer |
| age | Customer age |
| city | Customer's city |
| occupation | Customer's occupation |
| annual_income | Estimated annual income |
| join_date | Date the customer joined the institution |

## 2. Account

Stores financial accounts belonging to customers.

| Column | Description |
|---|---|
| account_id | Unique identifier for the account |
| customer_id | Customer who owns the account |
| account_type | Type of account |
| balance | Current account balance |
| open_date | Date the account was opened |
| status | Current account status |

## 3. Transaction

Stores financial activity occurring on accounts.

| Column | Description |
|---|---|
| transaction_id | Unique identifier for the transaction |
| account_id | Account associated with the transaction |
| transaction_date | Date of the transaction |
| transaction_type | CREDIT or DEBIT |
| category | Business category of the transaction |
| amount | Transaction amount |

## 4. Loan

Stores existing borrowing information for customers.

| Column | Description |
|---|---|
| loan_id | Unique identifier for the loan |
| customer_id | Customer associated with the loan |
| loan_type | Type of loan |
| loan_amount | Original borrowed amount |
| emi_amount | Monthly EMI amount |
| outstanding_amount | Remaining loan balance |
| start_date | Date the loan started |
| status | Current loan status |

## Relationships

- One customer can have multiple accounts.
- One account can have multiple transactions.
- One customer can have multiple loans.