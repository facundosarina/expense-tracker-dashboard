"""
app.py

Streamlit dashboard for the expense tracker. Run with:

    streamlit run app.py

Data lives in data/expenses.csv (date, description, amount, category).
New transactions -- whether added one at a time or imported from a CSV --
are auto-categorized by categorizer.py, and the suggested category can
always be overridden by hand before saving.
"""

from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import streamlit as st

from categorizer import CATEGORY_RULES, DEFAULT_CATEGORY, categorize

DATA_PATH = "data/expenses.csv"
CATEGORIES = list(CATEGORY_RULES.keys()) + [DEFAULT_CATEGORY]

st.set_page_config(page_title="Expense Tracker", page_icon="💸", layout="wide")


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame(columns=["date", "description", "amount", "category"])
    df = pd.read_csv(path, parse_dates=["date"])
    return df


def save_data(df: pd.DataFrame) -> None:
    df.to_csv(DATA_PATH, index=False)
    st.cache_data.clear()


def money(value: float) -> str:
    return f"${value:,.2f}"


# --- Load ---------------------------------------------------------------
df = load_data(DATA_PATH)

st.title("💸 Expense Tracker")
st.caption(
    "Personal spending dashboard with automatic category detection. "
    "All figures on this page are sample/fictional data."
)

# --- Sidebar: filters -----------------------------------------------------
st.sidebar.header("Filters")

if not df.empty:
    min_date, max_date = df["date"].min().date(), df["date"].max().date()
    date_range = st.sidebar.date_input(
        "Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date
    )
    selected_categories = st.sidebar.multiselect(
        "Categories", options=sorted(df["category"].unique()), default=None
    )
else:
    date_range = None
    selected_categories = []

filtered = df.copy()
if date_range and len(date_range) == 2:
    start, end = date_range
    filtered = filtered[
        (filtered["date"].dt.date >= start) & (filtered["date"].dt.date <= end)
    ]
if selected_categories:
    filtered = filtered[filtered["category"].isin(selected_categories)]

# --- KPI row --------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
total_spent = filtered["amount"].sum() if not filtered.empty else 0
txn_count = len(filtered)
avg_txn = filtered["amount"].mean() if not filtered.empty else 0
top_category = (
    filtered.groupby("category")["amount"].sum().idxmax() if not filtered.empty else "—"
)

col1.metric("Total spent", money(total_spent))
col2.metric("Transactions", f"{txn_count}")
col3.metric("Avg. per transaction", money(avg_txn) if txn_count else "—")
col4.metric("Top category", top_category)

st.divider()

# --- Charts ----------------------------------------------------------------
chart_col1, chart_col2 = st.columns([1, 2])

with chart_col1:
    st.subheader("By category")
    if not filtered.empty:
        by_cat = filtered.groupby("category")["amount"].sum().reset_index()
        fig_pie = px.pie(by_cat, names="category", values="amount", hole=0.45)
        fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No data for the selected filters.")

with chart_col2:
    st.subheader("Monthly trend")
    if not filtered.empty:
        monthly = filtered.copy()
        monthly["month"] = monthly["date"].dt.to_period("M").astype(str)
        by_month = monthly.groupby(["month", "category"])["amount"].sum().reset_index()
        fig_bar = px.bar(by_month, x="month", y="amount", color="category")
        fig_bar.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No data for the selected filters.")

st.divider()

# --- Add a transaction ------------------------------------------------------
with st.expander("➕ Add a transaction"):
    with st.form("add_transaction", clear_on_submit=True):
        new_date = st.date_input("Date")
        new_description = st.text_input("Description", placeholder="e.g. COTO SUPERMERCADO")
        new_amount = st.number_input("Amount", min_value=0.0, step=100.0, format="%.2f")

        suggested = categorize(new_description) if new_description else DEFAULT_CATEGORY
        new_category = st.selectbox(
            "Category (auto-suggested, override if needed)",
            options=CATEGORIES,
            index=CATEGORIES.index(suggested),
        )

        submitted = st.form_submit_button("Save transaction")
        if submitted and new_description:
            new_row = pd.DataFrame(
                [{"date": new_date, "description": new_description,
                  "amount": new_amount, "category": new_category}]
            )
            updated = pd.concat([df, new_row], ignore_index=True)
            save_data(updated)
            st.success(f"Saved · auto-categorized as **{new_category}**")
            st.rerun()

# --- Bulk import -------------------------------------------------------------
with st.expander("📤 Import transactions from CSV"):
    st.caption(
        "Expected columns: date, description, amount. "
        "Category is filled in automatically for every row."
    )
    uploaded = st.file_uploader("Upload CSV", type="csv")
    if uploaded is not None:
        try:
            new_df = pd.read_csv(uploaded, parse_dates=["date"])
            new_df["category"] = new_df["description"].apply(categorize)
            st.write("Preview (auto-categorized):")
            st.dataframe(new_df, use_container_width=True)
            if st.button("Confirm import"):
                updated = pd.concat([df, new_df], ignore_index=True)
                save_data(updated)
                st.success(f"Imported {len(new_df)} transactions.")
                st.rerun()
        except Exception as e:
            st.error(f"Couldn't read that file: {e}")

st.divider()

# --- Table -------------------------------------------------------------------
st.subheader("Transactions")
st.dataframe(
    filtered.sort_values("date", ascending=False),
    use_container_width=True,
    hide_index=True,
    column_config={
        "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
        "amount": st.column_config.NumberColumn("Amount", format="%.2f"),
    },
)
