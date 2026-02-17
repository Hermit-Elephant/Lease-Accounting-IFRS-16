import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="IFRS 16 Lease Automation",
    page_icon="📘",
    layout="wide"
)

st.title("📘 IFRS 16 Lease Accounting Tool")
st.markdown("Automated Lease Schedule • Journal Entries • Financial Impact")

st.divider()

# =====================================================
# SIDEBAR INPUTS
# =====================================================

st.sidebar.header("Lease Inputs")

lease_payment = st.sidebar.number_input(
    "Lease Payment",
    min_value=0.0,
    value=50000.0
)

discount_rate_input = st.sidebar.number_input(
    "Discount Rate (%)",
    min_value=0.0,
    value=9.0
)

lease_term = st.sidebar.number_input(
    "Lease Term (Years)",
    min_value=1,
    value=5
)

payment_frequency = st.sidebar.selectbox(
    "Payment Frequency",
    ["Annual", "Monthly"]
)

generate = st.sidebar.button("Generate Lease Model")

# =====================================================
# CALCULATIONS
# =====================================================

if generate:

    if payment_frequency == "Monthly":
        periods = lease_term * 12
        discount_rate = discount_rate_input / 100 / 12
    else:
        periods = lease_term
        discount_rate = discount_rate_input / 100

    # Present Value Calculation
    if discount_rate == 0:
        present_value = lease_payment * periods
    else:
        present_value = lease_payment * (1 - (1 + discount_rate) ** (-periods)) / discount_rate

    present_value = round(present_value, 2)
    depreciation = round(present_value / periods, 2)

    opening_liability = present_value
    opening_rou = present_value

    lease_schedule = []
    journal_entries = []

    # Initial Recognition Entry
    journal_entries.append({
        "Period": 0,
        "Account": "Right of Use Asset",
        "Debit": present_value,
        "Credit": 0
    })

    journal_entries.append({
        "Period": 0,
        "Account": "Lease Liability",
        "Debit": 0,
        "Credit": present_value
    })

    # Loop
    for period in range(1, int(periods) + 1):

        interest = round(opening_liability * discount_rate, 2)
        closing_liability = round(opening_liability + interest - lease_payment, 2)

        closing_rou = round(opening_rou - depreciation, 2)

        lease_schedule.append({
            "Period": period,
            "Opening Lease Liability": opening_liability,
            "Interest Expense": interest,
            "Lease Payment": lease_payment,
            "Closing Lease Liability": closing_liability,
            "Opening ROU Asset": opening_rou,
            "Depreciation": depreciation,
            "Closing ROU Asset": closing_rou
        })

        # Interest Entry
        journal_entries.append({
            "Period": period,
            "Account": "Interest Expense",
            "Debit": interest,
            "Credit": 0
        })

        journal_entries.append({
            "Period": period,
            "Account": "Lease Liability",
            "Debit": 0,
            "Credit": interest
        })

        # Payment Entry
        journal_entries.append({
            "Period": period,
            "Account": "Lease Liability",
            "Debit": lease_payment,
            "Credit": 0
        })

        journal_entries.append({
            "Period": period,
            "Account": "Bank",
            "Debit": 0,
            "Credit": lease_payment
        })

        # Depreciation Entry
        journal_entries.append({
            "Period": period,
            "Account": "Depreciation Expense",
            "Debit": depreciation,
            "Credit": 0
        })

        journal_entries.append({
            "Period": period,
            "Account": "Accumulated Depreciation - ROU",
            "Debit": 0,
            "Credit": depreciation
        })

        opening_liability = closing_liability
        opening_rou = closing_rou

    df_schedule = pd.DataFrame(lease_schedule)
    df_journals = pd.DataFrame(journal_entries)

    # =====================================================
    # KPI SECTION
    # =====================================================

    col1, col2, col3 = st.columns(3)

    col1.metric("Present Value of Lease", f"₹ {present_value:,.2f}")
    col2.metric("Periodic Depreciation", f"₹ {depreciation:,.2f}")
    col3.metric("Total Payments", f"₹ {lease_payment * periods:,.2f}")

    st.divider()

    # =====================================================
    # TABLE DISPLAY
    # =====================================================

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Lease Schedule")
        st.dataframe(df_schedule, use_container_width=True)

    with col2:
        st.subheader("Journal Entries")
        st.dataframe(df_journals, use_container_width=True)

    st.divider()

    # =====================================================
    # CHARTS
    # =====================================================

    st.subheader("Lease Liability Trend")
    st.line_chart(df_schedule.set_index("Period")["Closing Lease Liability"])

    st.subheader("ROU Asset Trend")
    st.line_chart(df_schedule.set_index("Period")["Closing ROU Asset"])

    st.divider()

    # =====================================================
    # FINANCIAL IMPACT
    # =====================================================

    st.subheader("Financial Impact (IFRS 16 vs Old Lease Accounting)")

    total_interest = df_schedule["Interest Expense"].sum()
    total_depreciation = df_schedule["Depreciation"].sum()

    col1, col2 = st.columns(2)

    col1.metric("Total Interest Expense", f"₹ {total_interest:,.2f}")
    col2.metric("Total Depreciation Expense", f"₹ {total_depreciation:,.2f}")

    st.divider()

    # =====================================================
    # EXCEL DOWNLOAD
    # =====================================================

    output = BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_schedule.to_excel(writer, sheet_name='Lease Schedule', index=False)
        df_journals.to_excel(writer, sheet_name='Journal Entries', index=False)

    st.download_button(
        label="⬇ Download Excel File",
        data=output.getvalue(),
        file_name="IFRS16_Lease_Model.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
