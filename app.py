import os
from pathlib import Path

import pandas as pd
import psycopg
import streamlit as st

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "dbname": "financial_customer_intelligence",
    "user": "postgres",
}

PROJECT_ROOT = Path(__file__).resolve().parent
SNAPSHOT_DIR = PROJECT_ROOT / "exports" / "dashboard"

DATA_SOURCE = os.getenv(
    "DASHBOARD_DATA_SOURCE",
    "snapshot",
).strip().lower()

VALID_DATA_SOURCES = {
    "postgres",
    "snapshot",
}

if DATA_SOURCE not in VALID_DATA_SOURCES:
    raise RuntimeError(
        "DASHBOARD_DATA_SOURCE must be either "
        "'postgres' or 'snapshot'."
    )


st.set_page_config(
    page_title="Financial Customer Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------
# Database
# ---------------------------------------------------------

def get_password():
    password = os.getenv("DB_PASSWORD")

    if not password:
        raise RuntimeError(
            "DB_PASSWORD environment variable is not set."
        )

    return password


@st.cache_data(ttl=60)
def load_customer_360():
    if DATA_SOURCE == "snapshot":
        return pd.read_csv(
            SNAPSHOT_DIR / "customer_360.csv"
        )

    with psycopg.connect(
        **DB_CONFIG,
        password=get_password(),
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
    if DATA_SOURCE == "snapshot":
        return pd.read_csv(
            SNAPSHOT_DIR / "loan_readiness.csv"
        )

    with psycopg.connect(
        **DB_CONFIG,
        password=get_password(),
    ) as connection:
        return pd.read_sql_query(
            """
            SELECT *
            FROM loan_readiness
            ORDER BY customer_id;
            """,
            connection,
        )


@st.cache_data(ttl=60)
def load_customer_segmentation():
    if DATA_SOURCE == "snapshot":
        return pd.read_csv(
            SNAPSHOT_DIR / "customer_segmentation.csv"
        )

    with psycopg.connect(
        **DB_CONFIG,
        password=get_password(),
    ) as connection:
        return pd.read_sql_query(
            """
            SELECT *
            FROM customer_segmentation
            ORDER BY customer_id;
            """,
            connection,
        )

# ---------------------------------------------------------
# Formatting
# ---------------------------------------------------------

def format_currency(value):
    if pd.isna(value):
        return "N/A"

    return f"₹{float(value):,.0f}"


def format_percentage(value):
    if pd.isna(value):
        return "N/A"

    return f"{float(value) * 100:.1f}%"


def readiness_icon(level):
    return {
        "HIGH": "🟢",
        "MODERATE": "🟡",
        "LOW": "🔴",
    }.get(level, "⚪")


def segment_description(segment):
    descriptions = {
        "FINANCIALLY_STRONG": (
            "Strong cash-flow retention, controlled spending "
            "and manageable debt."
        ),
        "DEBT_BURDENED": (
            "Existing monthly debt obligations consume a "
            "relatively high share of monthly income."
        ),
        "HIGH_SPENDER": (
            "A relatively high proportion of incoming funds "
            "is used for spending."
        ),
        "STABLE": (
            "Positive cash-flow position with manageable debt, "
            "without meeting the stronger profile."
        ),
        "OTHER": (
            "Does not clearly match one of the defined "
            "behavioral profiles."
        ),
    }

    return descriptions.get(
        segment,
        "No description available.",
    )


# ---------------------------------------------------------
# Load analytical views
# ---------------------------------------------------------

try:
    customer_360 = load_customer_360()
    readiness = load_loan_readiness()
    segmentation = load_customer_segmentation()

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


# ---------------------------------------------------------
# Numeric conversion
# ---------------------------------------------------------

customer_numeric_columns = [
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

for column in customer_numeric_columns:
    if column in customer_360.columns:
        customer_360[column] = pd.to_numeric(
            customer_360[column],
            errors="coerce",
        )


readiness_numeric_columns = [
    "cash_flow_margin",
]

for column in readiness_numeric_columns:
    if column in readiness.columns:
        readiness[column] = pd.to_numeric(
            readiness[column],
            errors="coerce",
        )


segmentation_numeric_columns = [
    "cash_flow_margin",
]

for column in segmentation_numeric_columns:
    if column in segmentation.columns:
        segmentation[column] = pd.to_numeric(
            segmentation[column],
            errors="coerce",
        )


# ---------------------------------------------------------
# Build unified analytical dataset
# ---------------------------------------------------------

readiness_features = readiness[
    [
        "customer_id",
        "cash_flow_margin",
        "healthy_cash_flow_flag",
        "stable_spending_flag",
        "manageable_debt_flag",
        "readiness_score",
        "readiness_level",
    ]
].rename(
    columns={
        "cash_flow_margin": "readiness_cash_flow_margin",
    }
)


segment_features = segmentation[
    [
        "customer_id",
        "customer_segment",
    ]
]


analytics = (
    customer_360
    .merge(
        readiness_features,
        on="customer_id",
        how="left",
    )
    .merge(
        segment_features,
        on="customer_id",
        how="left",
    )
)


# ---------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------

st.sidebar.title(
    "Financial Intelligence"
)

st.sidebar.caption(
    "Explore customer behavior, debt exposure, "
    "segmentation and explainable loan readiness."
)

st.sidebar.divider()


selected_cities = st.sidebar.multiselect(
    "City",
    sorted(
        analytics["city"]
        .dropna()
        .unique()
    ),
)


selected_occupations = st.sidebar.multiselect(
    "Occupation",
    sorted(
        analytics["occupation"]
        .dropna()
        .unique()
    ),
)


segment_options = [
    "FINANCIALLY_STRONG",
    "HIGH_SPENDER",
    "DEBT_BURDENED",
    "STABLE",
    "OTHER",
]

selected_segments = st.sidebar.multiselect(
    "Customer Segment",
    segment_options,
)


selected_readiness = st.sidebar.multiselect(
    "Readiness Level",
    [
        "HIGH",
        "MODERATE",
        "LOW",
    ],
)


# ---------------------------------------------------------
# Apply filters
# ---------------------------------------------------------

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


if selected_segments:
    filtered = filtered[
        filtered["customer_segment"].isin(
            selected_segments
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

st.title(
    "Financial Customer Intelligence"
)

st.markdown(
    """
    **Customer 360 • Behavioral Segmentation •
    Financial Health • Explainable Loan Readiness**
    """
)

st.caption(
    "An end-to-end data pipeline transforming raw financial records "
    "into validated customer-level intelligence."
)


# ---------------------------------------------------------
# Tabs
# ---------------------------------------------------------

(
    overview_tab,
    customer_tab,
    segmentation_tab,
    readiness_tab,
    data_tab,
) = st.tabs(
    [
        "📊 Overview",
        "👤 Customer Explorer",
        "🧩 Segmentation",
        "💳 Loan Readiness",
        "🗃️ Data Explorer",
    ]
)


# =========================================================
# OVERVIEW
# =========================================================

with overview_tab:

    st.subheader(
        "Portfolio Overview"
    )

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
            filtered[
                "readiness_level"
            ]
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
            "Customer Segments"
        )

        segment_distribution = (
            filtered[
                "customer_segment"
            ]
            .value_counts()
        )

        st.bar_chart(
            segment_distribution,
            horizontal=True,
        )


    st.divider()


    chart3, chart4 = st.columns(2)


    with chart3:

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


    with chart4:

        st.subheader(
            "Financial Indicators"
        )

        indicator1, indicator2 = st.columns(2)

        indicator1.metric(
            "Avg Spending Ratio",
            format_percentage(
                filtered[
                    "spending_ratio"
                ].mean()
            ),
        )

        indicator2.metric(
            "Avg Cash-Flow Margin",
            format_percentage(
                filtered[
                    "readiness_cash_flow_margin"
                ].mean()
            ),
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
        .set_index(
            "customer_id"
        )
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
            "#### Customer Intelligence"
        )


        intelligence1, intelligence2 = st.columns(2)


        with intelligence1:

            st.markdown(
                "**Behavioral Segment**"
            )

            st.markdown(
                f"### {customer['customer_segment']}"
            )

            st.write(
                segment_description(
                    customer[
                        "customer_segment"
                    ]
                )
            )


        with intelligence2:

            st.markdown(
                "**Loan Readiness**"
            )

            level = customer[
                "readiness_level"
            ]

            st.markdown(
                f"### "
                f"{readiness_icon(level)} "
                f"{level}"
            )

            st.write(
                f"Readiness score: "
                f"**{int(customer['readiness_score'])}/3**"
            )


        st.divider()


        st.markdown(
            "#### Financial Behavior"
        )


        behavior1, behavior2, behavior3 = st.columns(3)


        behavior1.metric(
            "Cash-Flow Margin",
            format_percentage(
                customer[
                    "readiness_cash_flow_margin"
                ]
            ),
        )


        behavior2.metric(
            "Spending Ratio",
            format_percentage(
                customer[
                    "spending_ratio"
                ]
            ),
        )


        behavior3.metric(
            "Spending Variability",
            format_percentage(
                customer[
                    "spending_variability"
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


        st.markdown(
            "#### Readiness Explanation"
        )


        strengths = []
        concerns = []


        if (
            customer[
                "healthy_cash_flow_flag"
            ]
            == 1
        ):
            strengths.append(
                "Healthy cash-flow margin"
            )

        else:
            concerns.append(
                "Cash-flow margin below 30%"
            )


        if (
            customer[
                "stable_spending_flag"
            ]
            == 1
        ):
            strengths.append(
                "Stable monthly spending"
            )

        else:
            concerns.append(
                "Higher monthly spending variability"
            )


        if (
            customer[
                "manageable_debt_flag"
            ]
            == 1
        ):
            strengths.append(
                "Manageable existing debt burden"
            )

        else:
            concerns.append(
                "Debt-to-income ratio at or above 30%"
            )


        explanation1, explanation2 = st.columns(2)


        with explanation1:

            st.markdown(
                "**Positive Signals**"
            )

            if strengths:

                for strength in strengths:
                    st.success(
                        f"✓ {strength}"
                    )

            else:

                st.write(
                    "No positive signals."
                )


        with explanation2:

            st.markdown(
                "**Signals Requiring Attention**"
            )

            if concerns:

                for concern in concerns:
                    st.warning(
                        concern
                    )

            else:

                st.success(
                    "No readiness concerns under "
                    "the current project rules."
                )


# =========================================================
# SEGMENTATION
# =========================================================

with segmentation_tab:

    st.subheader(
        "Behavioral Customer Segmentation"
    )


    st.write(
        "Customers are grouped using transparent financial "
        "behavior rules derived from Customer 360 metrics."
    )


    st.caption(
        "Segmentation describes customer behavior. "
        "It does not represent credit approval or risk classification."
    )


    st.divider()


    segment_distribution = (
        filtered[
            "customer_segment"
        ]
        .value_counts()
    )


    st.subheader(
        "Segment Distribution"
    )


    st.bar_chart(
        segment_distribution,
        horizontal=True,
    )


    st.divider()


    st.subheader(
        "Segment Definitions"
    )


    segment1, segment2 = st.columns(2)


    with segment1:

        st.markdown(
            "#### FINANCIALLY_STRONG"
        )

        st.write(
            "Cash-flow margin ≥ 40%, spending ratio ≤ 60%, "
            "and DTI < 30%."
        )


        st.markdown(
            "#### HIGH_SPENDER"
        )

        st.write(
            "Spending ratio ≥ 65%, provided the customer "
            "has not already been classified as debt burdened."
        )


    with segment2:

        st.markdown(
            "#### DEBT_BURDENED"
        )

        st.write(
            "Debt-to-income ratio ≥ 30%. "
            "This rule takes priority over high spending."
        )


        st.markdown(
            "#### STABLE"
        )

        st.write(
            "Cash-flow margin ≥ 30% with DTI < 30%, "
            "without satisfying the financially strong profile."
        )


    st.markdown(
        "#### OTHER"
    )

    st.write(
        "Fallback for customers who do not clearly match "
        "one of the defined behavioral profiles."
    )


    st.divider()


    st.subheader(
        "Customer Segments"
    )


    segment_table = filtered[
        [
            "customer_id",
            "readiness_cash_flow_margin",
            "spending_ratio",
            "debt_to_income_ratio",
            "customer_segment",
        ]
    ].copy()


    segment_table[
        "readiness_cash_flow_margin"
    ] = segment_table[
        "readiness_cash_flow_margin"
    ].map(
        format_percentage
    )


    segment_table[
        "spending_ratio"
    ] = segment_table[
        "spending_ratio"
    ].map(
        format_percentage
    )


    segment_table[
        "debt_to_income_ratio"
    ] = segment_table[
        "debt_to_income_ratio"
    ].map(
        format_percentage
    )


    segment_table = segment_table.rename(
        columns={
            "customer_id": "Customer",
            "readiness_cash_flow_margin": "Cash-Flow Margin",
            "spending_ratio": "Spending Ratio",
            "debt_to_income_ratio": "DTI",
            "customer_segment": "Segment",
        }
    )


    st.dataframe(
        segment_table,
        width="stretch",
        hide_index=True,
    )


# =========================================================
# LOAN READINESS
# =========================================================

with readiness_tab:

    st.subheader(
        "Explainable Loan Readiness"
    )


    st.info(
        "Readiness is calculated using transparent rules based on "
        "cash-flow margin, spending stability, and debt-to-income ratio. "
        "The result is an analytical score rather than a predictive "
        "credit-approval model."
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
            "readiness_cash_flow_margin",
            "spending_variability",
            "debt_to_income_ratio",
            "readiness_score",
            "readiness_level",
        ]
    ].copy()


    readiness_table[
        "readiness_cash_flow_margin"
    ] = readiness_table[
        "readiness_cash_flow_margin"
    ].map(
        format_percentage
    )


    readiness_table[
        "spending_variability"
    ] = readiness_table[
        "spending_variability"
    ].map(
        format_percentage
    )


    readiness_table[
        "debt_to_income_ratio"
    ] = readiness_table[
        "debt_to_income_ratio"
    ].map(
        format_percentage
    )


    readiness_table = readiness_table.rename(
        columns={
            "customer_id": "Customer",
            "readiness_cash_flow_margin": "Cash-Flow Margin",
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
        "The analytical dataset combines customer profile, "
        "account activity, transaction behavior, debt exposure, "
        "segmentation and readiness."
    )


    st.dataframe(
        filtered,
        width="stretch",
        hide_index=True,
    )


    st.divider()


    st.markdown(
        "#### Analytical Pipeline"
    )


    st.code(
        """
Synthetic CSV Data
        ↓
Python Generation
        ↓
Validation & Data Quality
        ↓
Processed / Rejected Layers
        ↓
PostgreSQL
        ↓
SQL Analytical Transformations
        ↓
Customer 360
        ├── Behavioral Segmentation
        └── Explainable Loan Readiness
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
    "Python • PostgreSQL • Pandas • PySpark • Streamlit"
)
