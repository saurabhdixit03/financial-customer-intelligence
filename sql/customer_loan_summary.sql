WITH loan_summary AS (
    SELECT
        customer_id,

        COUNT(*) FILTER (
            WHERE status = 'ACTIVE'
        ) AS active_loan_count,

        COALESCE(
            SUM(loan_amount) FILTER (
                WHERE status = 'ACTIVE'
            ),
            0
        ) AS total_loan_amount,

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
    c.annual_income,

    COALESCE(
        ls.active_loan_count,
        0
    ) AS active_loan_count,

    COALESCE(
        ls.total_loan_amount,
        0
    ) AS total_loan_amount,

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

LEFT JOIN loan_summary ls
    ON c.customer_id = ls.customer_id

ORDER BY c.customer_id;