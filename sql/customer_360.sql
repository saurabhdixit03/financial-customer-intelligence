CREATE OR REPLACE VIEW customer_360 AS

WITH transaction_summary AS (
    SELECT
        c.customer_id,

        COUNT(DISTINCT a.account_id) AS account_count,

        COALESCE(
            SUM(
                CASE
                    WHEN t.transaction_type = 'CREDIT'
                    THEN t.amount
                    ELSE 0
                END
            ),
            0
        ) AS total_credit,

        COALESCE(
            SUM(
                CASE
                    WHEN t.transaction_type = 'DEBIT'
                    THEN t.amount
                    ELSE 0
                END
            ),
            0
        ) AS total_debit,

        COUNT(t.transaction_id) AS transaction_count

    FROM customers c

    LEFT JOIN accounts a
        ON c.customer_id = a.customer_id

    LEFT JOIN transactions t
        ON a.account_id = t.account_id

    GROUP BY c.customer_id
),

monthly_spending AS (
    SELECT
        a.customer_id,
        DATE_TRUNC(
            'month',
            t.transaction_date
        ) AS spending_month,
        SUM(t.amount) AS monthly_debit

    FROM accounts a

    INNER JOIN transactions t
        ON a.account_id = t.account_id

    WHERE t.transaction_type = 'DEBIT'

    GROUP BY
        a.customer_id,
        DATE_TRUNC(
            'month',
            t.transaction_date
        )
),

spending_variability_summary AS (
    SELECT
        customer_id,

        CASE
            WHEN AVG(monthly_debit) > 0
            THEN
                STDDEV_SAMP(monthly_debit)
                / AVG(monthly_debit)
            ELSE NULL
        END AS spending_variability

    FROM monthly_spending

    GROUP BY customer_id
),

loan_summary AS (
    SELECT
        customer_id,

        COUNT(*) FILTER (
            WHERE status = 'ACTIVE'
        ) AS active_loan_count,

        COALESCE(
            SUM(outstanding_amount) FILTER (
                WHERE status = 'ACTIVE'
            ),
            0
        ) AS total_outstanding_amount,

        COALESCE(
            SUM(emi_amount) FILTER (
                WHERE status = 'ACTIVE'
            ),
            0
        ) AS monthly_emi_obligation

    FROM loans

    GROUP BY customer_id
)

SELECT
    c.customer_id,
    c.age,
    c.city,
    c.occupation,
    c.annual_income,
    c.join_date,

    ts.account_count,
    ts.total_credit,
    ts.total_debit,

    ts.total_credit
        - ts.total_debit
        AS net_cash_flow,

    CASE
        WHEN ts.total_credit > 0
        THEN ts.total_debit / ts.total_credit
        ELSE 0
    END AS spending_ratio,

    svs.spending_variability,

    ts.transaction_count,

    COALESCE(
        ls.active_loan_count,
        0
    ) AS active_loan_count,

    COALESCE(
        ls.total_outstanding_amount,
        0
    ) AS total_outstanding_amount,

    COALESCE(
        ls.monthly_emi_obligation,
        0
    ) AS monthly_emi_obligation,

    CASE
        WHEN c.annual_income > 0
        THEN
            COALESCE(
                ls.monthly_emi_obligation,
                0
            ) / (c.annual_income / 12)
        ELSE 0
    END AS debt_to_income_ratio

FROM customers c

LEFT JOIN transaction_summary ts
    ON c.customer_id = ts.customer_id

LEFT JOIN spending_variability_summary svs
    ON c.customer_id = svs.customer_id

LEFT JOIN loan_summary ls
    ON c.customer_id = ls.customer_id

ORDER BY c.customer_id;