DROP VIEW IF EXISTS customer_segmentation;

CREATE VIEW customer_segmentation AS

WITH customer_features AS (

    SELECT
        customer_id,
        annual_income,
        total_credit,
        total_debit,
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
        END AS cash_flow_margin

    FROM customer_360
),

segmented_customers AS (

    SELECT
        *,

        CASE

            /*
            Strong cash-flow retention, controlled spending,
            and manageable debt.
            */
            WHEN cash_flow_margin >= 0.40
                 AND spending_ratio <= 0.60
                 AND debt_to_income_ratio < 0.30
            THEN 'FINANCIALLY_STRONG'

            /*
            Existing debt consumes a relatively high share
            of monthly income.
            */
            WHEN debt_to_income_ratio >= 0.30
            THEN 'DEBT_BURDENED'

            /*
            Customer spends a relatively large share
            of incoming funds.
            */
            WHEN spending_ratio >= 0.65
            THEN 'HIGH_SPENDER'

            /*
            Positive financial position without meeting
            the stronger profile above.
            */
            WHEN cash_flow_margin >= 0.30
                 AND debt_to_income_ratio < 0.30
            THEN 'STABLE'

            /*
                Remaining customers do not clearly match
                one of the defined behavioral profiles.
            */
            ELSE 'OTHER'

        END AS customer_segment

    FROM customer_features
)

SELECT
    customer_id,
    annual_income,
    total_credit,
    total_debit,
    net_cash_flow,
    cash_flow_margin,
    spending_ratio,
    spending_variability,
    active_loan_count,
    total_outstanding_amount,
    monthly_emi_obligation,
    debt_to_income_ratio,
    customer_segment

FROM segmented_customers;