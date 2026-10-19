CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    age INTEGER NOT NULL,
    city VARCHAR(100) NOT NULL,
    occupation VARCHAR(100) NOT NULL,
    annual_income NUMERIC(12, 2) NOT NULL,
    join_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    account_type VARCHAR(20) NOT NULL,
    balance NUMERIC(12, 2) NOT NULL,
    open_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,

    CONSTRAINT fk_accounts_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR(20) PRIMARY KEY,
    account_id VARCHAR(20) NOT NULL,
    transaction_date DATE NOT NULL,
    transaction_type VARCHAR(10) NOT NULL,
    category VARCHAR(50) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,

    CONSTRAINT fk_transactions_account
        FOREIGN KEY (account_id)
        REFERENCES accounts(account_id)
);

CREATE TABLE IF NOT EXISTS loans (
    loan_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    loan_type VARCHAR(50) NOT NULL,
    loan_amount NUMERIC(12, 2) NOT NULL,
    annual_interest_rate NUMERIC(5, 2) NOT NULL,
    term_months INTEGER NOT NULL,
    emi_amount NUMERIC(12, 2) NOT NULL,
    outstanding_amount NUMERIC(12, 2) NOT NULL,
    start_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,

    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
);