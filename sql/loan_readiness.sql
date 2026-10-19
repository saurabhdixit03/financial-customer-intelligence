DROP VIEW IF EXISTS loan_readiness;

CREATE VIEW loan_readiness AS

WITH readiness_signals AS (
    SELECT
        customer_id,
        annual_income,
        net_cash_flow,
        spending_ratio,
        spending_variability,
        active_loan_count,
        total_outstanding_amount,
        monthly_emi_obligation,
        debt_to_income_ratio,

        CASE
            WHEN total_credit > 0
            THEN net_cash_flow / total_credit
            ELSE NULL
        END AS cash_flow_margin,

        CASE
            WHEN total_credit > 0
                 AND net_cash_flow / total_credit >= 0.30
            THEN 1
            ELSE 0
        END AS healthy_cash_flow_flag,

        CASE
            WHEN spending_variability IS NOT NULL
                 AND spending_variability < 0.30
            THEN 1
            ELSE 0
        END AS stable_spending_flag,

        CASE
            WHEN debt_to_income_ratio < 0.30
            THEN 1
            ELSE 0
        END AS manageable_debt_flag

    FROM customer_360
),

scored_customers AS (
    SELECT
        *,

        (
            healthy_cash_flow_flag
            + stable_spending_flag
            + manageable_debt_flag
        ) AS readiness_score

    FROM readiness_signals
)

SELECT
    *,

    CASE
        WHEN readiness_score = 3
        THEN 'HIGH'

        WHEN readiness_score = 2
        THEN 'MODERATE'

        ELSE 'LOW'
    END AS readiness_level

FROM scored_customers;