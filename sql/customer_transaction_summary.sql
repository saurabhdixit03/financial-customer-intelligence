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
)



SELECT
    customer_id,
    city,
    occupation,
    account_count,
    total_credit,
    total_debit,
    total_credit - total_debit AS net_cash_flow,

CASE
    WHEN total_credit > 0
    THEN total_debit / total_credit
    ELSE 0
END AS spending_ratio,

transaction_count

FROM transaction_summary

ORDER BY customer_id;