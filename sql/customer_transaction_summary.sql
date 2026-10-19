WITH transaction_summary AS (
    SELECT
        c.customer_id,
        c.city,
        c.occupation,
        COUNT(DISTINCT a.account_id) AS account_count,

        SUM(
            CASE
                WHEN t.transaction_type = 'CREDIT'
                THEN t.amount
                ELSE 0
            END
        ) AS total_credit,

        SUM(
            CASE
                WHEN t.transaction_type = 'DEBIT'
                THEN t.amount
                ELSE 0
            END
        ) AS total_debit,

        COUNT(t.transaction_id) AS transaction_count

    FROM customers c

    LEFT JOIN accounts a
        ON c.customer_id = a.customer_id

    LEFT JOIN transactions t
        ON a.account_id = t.account_id

    GROUP BY
        c.customer_id,
        c.city,
        c.occupation
),

monthly_spending AS (
    SELECT
        c.customer_id,
        DATE_TRUNC('month', t.transaction_date)::DATE AS month,
        SUM(t.amount) AS monthly_debit

    FROM customers c

    JOIN accounts a
        ON c.customer_id = a.customer_id

    JOIN transactions t
        ON a.account_id = t.account_id

    WHERE t.transaction_type = 'DEBIT'

    GROUP BY
        c.customer_id,
        DATE_TRUNC('month', t.transaction_date)::DATE
),

spending_variability_summary AS (
    SELECT
        customer_id,
        AVG(monthly_debit) AS average_monthly_spending,
        STDDEV_SAMP(monthly_debit) AS monthly_spending_std,
        STDDEV_SAMP(monthly_debit) / AVG(monthly_debit)
            AS spending_variability

    FROM monthly_spending

    GROUP BY customer_id
)

SELECT
    ts.customer_id,
    ts.city,
    ts.occupation,
    ts.account_count,
    ts.total_credit,
    ts.total_debit,
    ts.total_credit - ts.total_debit AS net_cash_flow,

    CASE
        WHEN ts.total_credit > 0
        THEN ts.total_debit / ts.total_credit
        ELSE 0
    END AS spending_ratio,

    sv.spending_variability,
    ts.transaction_count

FROM transaction_summary ts

LEFT JOIN spending_variability_summary sv
    ON ts.customer_id = sv.customer_id

ORDER BY ts.customer_id;