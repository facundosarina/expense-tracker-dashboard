"""
app.py

Streamlit dashboard for the expense tracker. Run with:

    streamlit run app.py

The sample data in data/expenses.csv is read once and then lives in the
visitor's own session: adding, importing or resetting changes only what that
visitor sees, and nothing is ever written back to disk. That keeps the public
demo safe to try -- one person's test transaction cannot alter what the next
person loads.
"""

from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import streamlit as st

from categorizer import CATEGORY_RULES, DEFAULT_CATEGORY, categorize

DATA_PATH = "data/expenses.csv"
CATEGORIES = list(CATEGORY_RULES.keys()) + [DEFAULT_CATEGORY]
CURRENCY = "ARS"
COLUMNS = ["date", "description", "amount", "category"]

st.set_page_config(page_title="Expense Tracker", page_icon="💸", layout="wide")


@st.cache_data
def load_sample(path: str) -> pd.DataFrame:
    """Read the bundled sample file. Cached because it never changes."""
    if not os.path.exists(path):
        return pd.DataFrame(columns=COLUMNS)
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], format="mixed")
    return df


def session_data() -> pd.DataFrame:
    """The visitor's own copy of the data, seeded from the sample file."""
    if "df" not in st.session_state:
        st.session_state["df"] = load_sample(DATA_PATH).copy()
    return st.session_state["df"]


def set_session_data(df: pd.DataFrame) -> None:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], format="mixed")
    st.session_state["df"] = df[COLUMNS].reset_index(drop=True)


def money(value: float) -> str:
    """Amount with its symbol. The currency code lives in the label, so the
    KPI tiles stay narrow enough to show the whole number."""
    return f"${value:,.2f}"


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    return out.to_csv(index=False).encode("utf-8-sig")


# --- Load ---------------------------------------------------------------
df = session_data()

st.title("💸 Expense Tracker")
st.caption(
    f"Personal spending dashboard with automatic category detection. "
    f"Amounts are in {CURRENCY}. The data below is fictional sample data, and "
    "anything you add stays in your own browser session — nothing is saved on "
    "the server and nobody else sees your changes."
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

st.sidebar.header("Your session")
st.sidebar.download_button(
    "Download this data (CSV)",
    to_csv_bytes(df),
    file_name="expenses.csv",
    mime="text/csv",
)
if st.sidebar.button("Reset to sample data"):
    st.session_state["df"] = load_sample(DATA_PATH).copy()
    st.rerun()

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

col1.metric(f"Total spent ({CURRENCY})", money(total_spent))
col2.metric("Transactions", f"{txn_count}")
col3.metric(f"Avg. per transaction ({CURRENCY})", money(avg_txn) if txn_count else "—")
col4.metric("Top category", top_category)

st.divider()

# --- Add a transaction ------------------------------------------------------
# Deliberately NOT inside st.form: a form only sends its values on submit, so
# the suggested category could not update while the description is typed --
# which is the whole point of the feature.
st.subheader("➕ Add a transaction")

add_left, add_right = st.columns([2, 1])
with add_left:
    new_description = st.text_input(
        "Description", placeholder="e.g. COTO SUPERMERCADO", key="new_description"
    )
with add_right:
    new_amount = st.number_input("Amount", min_value=0.0, step=100.0, format="%.2f")

suggested = categorize(new_description) if new_description else DEFAULT_CATEGORY
if new_description:
    if suggested == DEFAULT_CATEGORY:
        st.caption("No rule matched this description — pick a category yourself.")
    else:
        st.caption(f"Suggested category: **{suggested}** (override it below if it's wrong)")

opt_left, opt_right = st.columns([2, 1])
with opt_left:
    new_category = st.selectbox(
        "Category", options=CATEGORIES, index=CATEGORIES.index(suggested)
    )
with opt_right:
    new_date = st.date_input("Date")

if st.button("Save transaction", type="primary"):
    if not new_description.strip():
        st.warning("Add a description first.")
    elif new_amount <= 0:
        st.warning("The amount has to be greater than zero.")
    else:
        new_row = pd.DataFrame(
            [{"date": pd.Timestamp(new_date), "description": new_description.strip(),
              "amount": new_amount, "category": new_category}]
        )
        set_session_data(pd.concat([df, new_row], ignore_index=True))
        st.success(f"Saved · categorized as **{new_category}**")
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
            new_df = pd.read_csv(uploaded)
            missing = [c for c in ["date", "description", "amount"] if c not in new_df.columns]
            if missing:
                st.error(
                    "That file is missing the column(s): "
                    + ", ".join(missing)
                    + ". Expected date, description and amount."
                )
            else:
                new_df["date"] = pd.to_datetime(new_df["date"], format="mixed", errors="coerce")
                new_df["amount"] = pd.to_numeric(new_df["amount"], errors="coerce")
                bad_rows = int(new_df["date"].isna().sum() + new_df["amount"].isna().sum())
                new_df = new_df.dropna(subset=["date", "amount"])
                new_df["description"] = new_df["description"].fillna("").astype(str)
                new_df["category"] = new_df["description"].apply(categorize)
                new_df = new_df[COLUMNS]

                if bad_rows:
                    st.warning(
                        f"{bad_rows} row(s) had an unreadable date or amount and were left out."
                    )
                if new_df.empty:
                    st.error("No usable rows in that file.")
                else:
                    st.write("Preview (auto-categorized):")
                    st.dataframe(new_df)
                    if st.button("Confirm import"):
                        set_session_data(pd.concat([df, new_df], ignore_index=True))
                        st.success(f"Imported {len(new_df)} transactions.")
                        st.rerun()
        except Exception as error:
            st.error(
                f"Couldn't read that file: {error}. "
                "It should be a CSV with the columns date, description and amount."
            )

st.divider()

# --- Table -------------------------------------------------------------------
st.subheader("Transactions")
st.dataframe(
    filtered.sort_values("date", ascending=False),
    hide_index=True,
    column_config={
        "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
        "amount": st.column_config.NumberColumn(f"Amount ({CURRENCY})", format="%.2f"),
    },
)

st.divider()

# --- Charts ----------------------------------------------------------------
chart_col1, chart_col2 = st.columns([1, 2])

with chart_col1:
    st.subheader("By category")
    if not filtered.empty:
        by_cat = (
            filtered.groupby("category")["amount"].sum()
            .sort_values(ascending=True).reset_index()
        )
        fig_bar_cat = px.bar(by_cat, x="amount", y="category", orientation="h")
        fig_bar_cat.update_traces(
            marker_color="#17868F",
            marker_line_width=0,
            hovertemplate="%{y}: " + CURRENCY + " $%{x:,.0f}<extra></extra>",
        )
        fig_bar_cat.update_layout(
            height=60 + 34 * len(by_cat),
            margin=dict(t=10, b=10, l=10, r=30),
            xaxis_title=None,
            yaxis_title=None,
            showlegend=False,
            bargap=0.35,
        )
        fig_bar_cat.update_xaxes(showgrid=False, showticklabels=False, zeroline=False)
        fig_bar_cat.update_yaxes(showgrid=False)
        st.plotly_chart(fig_bar_cat)
    else:
        st.info("No data for the selected filters.")

with chart_col2:
    st.subheader("Monthly trend")
    if not filtered.empty:
        monthly = filtered.copy()
        monthly["month"] = monthly["date"].dt.to_period("M").astype(str)
        by_month = monthly.groupby("month")["amount"].sum().reset_index()
        fig_bar = px.bar(by_month, x="month", y="amount")
        fig_bar.update_traces(
            marker_color="#17868F",
            marker_line_width=0,
            hovertemplate="%{x}: " + CURRENCY + " $%{y:,.0f}<extra></extra>",
        )
        fig_bar.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis_title=None,
            yaxis_title=None,
            showlegend=False,
            bargap=0.3,
        )
        fig_bar.update_yaxes(showgrid=False, showticklabels=False)
        st.plotly_chart(fig_bar)
    else:
        st.info("No data for the selected filters.")
