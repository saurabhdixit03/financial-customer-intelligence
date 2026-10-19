import os

import pandas as pd
import psycopg
import streamlit as st


DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "dbname": "financial_customer_intelligence",
    "user": "postgres",
}


st.set_page_config(
    page_title="Financial Customer Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------
# Database
# ---------------------------------------------------------

@st.cache_data(ttl=60)
def load_customer_360():
    password = os.getenv("DB_PASSWORD")

    if not password:
        raise RuntimeError(
            "DB_PASSWORD environment variable is not set."
        )

    with psycopg.connect(
        **DB_CONFIG,
        password=password,
    ) as connection:
        return pd.read_sql_query(
            """
            SELECT *
            FROM customer_360
            ORDER BY customer_id;
            """,
            connection,
        )


@st.cache_data(ttl=60)
def load_loan_readiness():
    password = os.getenv("DB_PASSWORD")

    if not password:
        raise RuntimeError(
            "DB_PASSWORD environment variable is not set."
        )

    with psycopg.connect(
        **DB_CONFIG,
        password=password,
    ) as connection:
        return pd.read_sql_query(
            """
            SELECT *
            FROM loan_readiness
            ORDER BY customer_id;
            """,
            connection,
        )


# ---------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------

def format_currency(value):
    if pd.isna(value):
        return "N/A"

    return f"₹{float(value):,.0f}"


def format_percentage(value):
    if pd.isna(value):
        return "N/A"

    return f"{float(value) * 100:.1f}%"


def readiness_reason(customer):
    strengths = []
    concerns = []

    if customer["healthy_cash_flow_flag"] == 1:
        strengths.append(
            "Healthy cash-flow margin"
        )
    else:
        concerns.append(
            "Cash-flow margin is below the 30% project threshold"
        )

    if customer["stable_spending_flag"] == 1:
        strengths.append(
            "Monthly spending is relatively stable"
        )
    else:
        concerns.append(
            "Monthly spending shows higher variability"
        )

    if customer["manageable_debt_flag"] == 1:
        strengths.append(
            "Existing debt burden is manageable"
        )
    else:
        concerns.append(
            "Debt-to-income ratio is at or above the 30% project threshold"
        )

    return strengths, concerns


def readiness_icon(level):
    if level == "HIGH":
        return "🟢"

    if level == "MODERATE":
        return "🟡"

    return "🔴"


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------

try:
    customer_360 = load_customer_360()
    readiness = load_loan_readiness()

except Exception as error:
    st.error(
        "Unable to load analytical data from PostgreSQL."
    )

    st.code(str(error))

    st.info(
        "Make sure PostgreSQL is running and the "
        "DB_PASSWORD environment variable is set."
    )

    st.stop()


# Convert PostgreSQL Decimal columns used by charts
# into normal floating-point values.

numeric_columns = [
    "annual_income",
    "total_credit",
    "total_debit",
    "net_cash_flow",
    "spending_ratio",
    "spending_variability",
    "total_outstanding_amount",
    "monthly_emi_obligation",
    "debt_to_income_ratio",
]

for column in numeric_columns:
    if column in customer_360.columns:
        customer_360[column] = pd.to_numeric(
            customer_360[column],
            errors="coerce",
        )

readiness_numeric_columns = [
    "annual_income",
    "net_cash_flow",
    "spending_ratio",
    "spending_variability",
    "total_outstanding_amount",
    "monthly_emi_obligation",
    "debt_to_income_ratio",
    "cash_flow_margin",
]

for column in readiness_numeric_columns:
    if column in readiness.columns:
        readiness[column] = pd.to_numeric(
            readiness[column],
            errors="coerce",
        )


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

st.sidebar.title("Financial Intelligence")

st.sidebar.caption(
    "Explore customer behavior, debt exposure "
    "and explainable loan readiness."
)

st.sidebar.divider()

selected_cities = st.sidebar.multiselect(
    "City",
    sorted(customer_360["city"].dropna().unique()),
)

selected_occupations = st.sidebar.multiselect(
    "Occupation",
    sorted(
        customer_360[
            "occupation"
        ].dropna().unique()
    ),
)

selected_readiness = st.sidebar.multiselect(
    "Readiness Level",
    ["HIGH", "MODERATE", "LOW"],
)

st.sidebar.divider()

st.sidebar.caption(
    "Synthetic educational dataset. "
    "Not intended for real lending decisions."
)


# ---------------------------------------------------------
# Combine analytical views for filtering
# ---------------------------------------------------------

readiness_for_merge = readiness[
    [
        "customer_id",
        "cash_flow_margin",
        "healthy_cash_flow_flag",
        "stable_spending_flag",
        "manageable_debt_flag",
        "readiness_score",
        "readiness_level",
    ]
]

analytics = customer_360.merge(
    readiness_for_merge,
    on="customer_id",
    how="left",
)


filtered = analytics.copy()

if selected_cities:
    filtered = filtered[
        filtered["city"].isin(
            selected_cities
        )
    ]

if selected_occupations:
    filtered = filtered[
        filtered["occupation"].isin(
            selected_occupations
        )
    ]

if selected_readiness:
    filtered = filtered[
        filtered["readiness_level"].isin(
            selected_readiness
        )
    ]


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.title("Financial Customer Intelligence")

st.markdown(
    """
    **Customer 360 • Financial Behavior • Debt Exposure •
    Explainable Loan Readiness**
    """
)

st.caption(
    "A data engineering and analytics project that transforms "
    "raw synthetic financial data into validated, customer-level "
    "decision-support insights."
)


# ---------------------------------------------------------
# Tabs
# ---------------------------------------------------------

overview_tab, customer_tab, readiness_tab, data_tab = st.tabs(
    [
        "📊 Overview",
        "👤 Customer Explorer",
        "💳 Loan Readiness",
        "🗃️ Data Explorer",
    ]
)


# =========================================================
# OVERVIEW
# =========================================================

with overview_tab:

    st.subheader("Portfolio Overview")

    total_customers = len(filtered)

    customers_with_loans = (
        filtered["active_loan_count"] > 0
    ).sum()

    total_outstanding = filtered[
        "total_outstanding_amount"
    ].sum()

    average_dti = filtered[
        "debt_to_income_ratio"
    ].mean()

    metric1, metric2, metric3, metric4 = st.columns(4)

    metric1.metric(
        "Customers",
        total_customers,
    )

    metric2.metric(
        "Customers With Active Loans",
        int(customers_with_loans),
    )

    metric3.metric(
        "Outstanding Balance",
        format_currency(
            total_outstanding
        ),
    )

    metric4.metric(
        "Average DTI",
        format_percentage(
            average_dti
        ),
    )

    st.divider()

    chart1, chart2 = st.columns(2)

    with chart1:

        st.subheader(
            "Loan Readiness Distribution"
        )

        readiness_distribution = (
            filtered["readiness_level"]
            .value_counts()
            .reindex(
                [
                    "HIGH",
                    "MODERATE",
                    "LOW",
                ],
                fill_value=0,
            )
        )

        st.bar_chart(
            readiness_distribution,
            horizontal=True,
        )

    with chart2:

        st.subheader(
            "Customers by City"
        )

        city_distribution = (
            filtered["city"]
            .value_counts()
        )

        st.bar_chart(
            city_distribution
        )

    st.divider()

    st.subheader(
        "Outstanding Loan Exposure"
    )

    loan_exposure = (
        filtered[
            filtered[
                "active_loan_count"
            ] > 0
        ][
            [
                "customer_id",
                "total_outstanding_amount",
            ]
        ]
        .sort_values(
            "total_outstanding_amount",
            ascending=False,
        )
        .set_index("customer_id")
    )

    if loan_exposure.empty:
        st.info(
            "No customers with active loans "
            "match the selected filters."
        )
    else:
        st.bar_chart(
            loan_exposure
        )

    st.divider()

    st.subheader(
        "Portfolio Financial Indicators"
    )

    indicator1, indicator2, indicator3 = st.columns(3)

    indicator1.metric(
        "Average Spending Ratio",
        format_percentage(
            filtered[
                "spending_ratio"
            ].mean()
        ),
    )

    indicator2.metric(
        "Average Spending Variability",
        format_percentage(
            filtered[
                "spending_variability"
            ].mean()
        ),
    )

    indicator3.metric(
        "Average Cash-Flow Margin",
        format_percentage(
            filtered[
                "cash_flow_margin"
            ].mean()
        ),
    )


# =========================================================
# CUSTOMER EXPLORER
# =========================================================

with customer_tab:

    st.subheader(
        "Customer 360 Explorer"
    )

    if filtered.empty:

        st.warning(
            "No customers match the current filters."
        )

    else:

        selected_customer_id = st.selectbox(
            "Select Customer",
            filtered[
                "customer_id"
            ].tolist(),
        )

        customer = filtered[
            filtered["customer_id"]
            == selected_customer_id
        ].iloc[0]

        st.markdown(
            f"### {selected_customer_id}"
        )

        st.caption(
            f"{customer['occupation']} • "
            f"{customer['city']} • "
            f"Customer since "
            f"{customer['join_date']}"
        )

        profile1, profile2, profile3, profile4 = st.columns(4)

        profile1.metric(
            "Annual Income",
            format_currency(
                customer[
                    "annual_income"
                ]
            ),
        )

        profile2.metric(
            "Net Cash Flow",
            format_currency(
                customer[
                    "net_cash_flow"
                ]
            ),
        )

        profile3.metric(
            "Accounts",
            int(
                customer[
                    "account_count"
                ]
            ),
        )

        profile4.metric(
            "Active Loans",
            int(
                customer[
                    "active_loan_count"
                ]
            ),
        )

        st.divider()

        st.markdown(
            "#### Financial Behavior"
        )

        behavior1, behavior2, behavior3 = st.columns(3)

        behavior1.metric(
            "Spending Ratio",
            format_percentage(
                customer[
                    "spending_ratio"
                ]
            ),
        )

        behavior2.metric(
            "Spending Variability",
            format_percentage(
                customer[
                    "spending_variability"
                ]
            ),
        )

        behavior3.metric(
            "Transaction Count",
            int(
                customer[
                    "transaction_count"
                ]
            ),
        )

        st.markdown(
            "#### Debt Position"
        )

        debt1, debt2, debt3 = st.columns(3)

        debt1.metric(
            "Outstanding Balance",
            format_currency(
                customer[
                    "total_outstanding_amount"
                ]
            ),
        )

        debt2.metric(
            "Monthly EMI",
            format_currency(
                customer[
                    "monthly_emi_obligation"
                ]
            ),
        )

        debt3.metric(
            "Debt-to-Income Ratio",
            format_percentage(
                customer[
                    "debt_to_income_ratio"
                ]
            ),
        )

        st.divider()

        level = customer[
            "readiness_level"
        ]

        st.markdown(
            "#### Loan Readiness"
        )

        st.markdown(
            f"### {readiness_icon(level)} "
            f"{level}"
        )

        st.write(
            f"Readiness score: "
            f"**{int(customer['readiness_score'])}/3**"
        )

        strength_list = []
        concern_list = []

        if (
            customer[
                "healthy_cash_flow_flag"
            ]
            == 1
        ):
            strength_list.append(
                "Healthy cash-flow margin"
            )
        else:
            concern_list.append(
                "Cash-flow margin below 30%"
            )

        if (
            customer[
                "stable_spending_flag"
            ]
            == 1
        ):
            strength_list.append(
                "Stable monthly spending"
            )
        else:
            concern_list.append(
                "Higher monthly spending variability"
            )

        if (
            customer[
                "manageable_debt_flag"
            ]
            == 1
        ):
            strength_list.append(
                "Manageable existing debt burden"
            )
        else:
            concern_list.append(
                "Debt-to-income ratio at or above 30%"
            )

        explanation_left, explanation_right = st.columns(2)

        with explanation_left:

            st.markdown(
                "**Positive Signals**"
            )

            if strength_list:
                for strength in strength_list:
                    st.success(
                        f"✓ {strength}"
                    )
            else:
                st.write(
                    "No positive signals."
                )

        with explanation_right:

            st.markdown(
                "**Signals Requiring Attention**"
            )

            if concern_list:
                for concern in concern_list:
                    st.warning(
                        concern
                    )
            else:
                st.success(
                    "No readiness concerns "
                    "under the current project rules."
                )


# =========================================================
# LOAN READINESS
# =========================================================

with readiness_tab:

    st.subheader(
        "Explainable Loan Readiness"
    )

    st.info(
        "This assessment uses transparent project rules rather "
        "than a black-box model. It is an educational indicator, "
        "not a lending or credit-approval system."
    )

    rule1, rule2, rule3 = st.columns(3)

    rule1.metric(
        "Cash-Flow Rule",
        "≥ 30%",
        help=(
            "Net cash flow divided by total credit."
        ),
    )

    rule2.metric(
        "Stability Rule",
        "< 30%",
        help=(
            "Coefficient of variation of monthly spending."
        ),
    )

    rule3.metric(
        "Debt Rule",
        "< 30%",
        help=(
            "Monthly EMI obligations divided by monthly income."
        ),
    )

    st.caption(
        "3/3 signals = HIGH • "
        "2/3 = MODERATE • "
        "0–1/3 = LOW"
    )

    st.divider()

    readiness_table = filtered[
        [
            "customer_id",
            "cash_flow_margin",
            "spending_variability",
            "debt_to_income_ratio",
            "readiness_score",
            "readiness_level",
        ]
    ].copy()

    readiness_table[
        "cash_flow_margin"
    ] = readiness_table[
        "cash_flow_margin"
    ].map(format_percentage)

    readiness_table[
        "spending_variability"
    ] = readiness_table[
        "spending_variability"
    ].map(format_percentage)

    readiness_table[
        "debt_to_income_ratio"
    ] = readiness_table[
        "debt_to_income_ratio"
    ].map(format_percentage)

    readiness_table = readiness_table.rename(
        columns={
            "customer_id": "Customer",
            "cash_flow_margin": "Cash-Flow Margin",
            "spending_variability": "Spending Variability",
            "debt_to_income_ratio": "DTI",
            "readiness_score": "Score",
            "readiness_level": "Readiness",
        }
    )

    st.dataframe(
        readiness_table,
        width="stretch",
        hide_index=True,
    )


# =========================================================
# DATA EXPLORER
# =========================================================

with data_tab:

    st.subheader(
        "Customer 360 Analytical Dataset"
    )

    st.caption(
        "Grain: one row per customer. "
        "This view combines customer profile, account activity, "
        "transaction behavior and loan exposure."
    )

    st.dataframe(
        filtered,
        width="stretch",
        hide_index=True,
    )

    st.divider()

    st.markdown(
        "#### Pipeline"
    )

    st.code(
        """
Synthetic CSV data
        ↓
Python ingestion & validation
        ↓
Raw / Processed / Rejected layers
        ↓
PostgreSQL
        ↓
SQL analytical transformations
        ↓
Customer 360
        ↓
Explainable Loan Readiness
        ↓
Streamlit Dashboard
        """,
        language=None,
    )


# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------

st.divider()

st.caption(
    "Financial Customer Intelligence • "
    "Synthetic educational data • "
    "Not intended for real lending decisions"
)