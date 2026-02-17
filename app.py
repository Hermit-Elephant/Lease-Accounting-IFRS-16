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
st.markdown("Automated Lease Schedule • Security Deposit • Journal Entries • Financial Impact")
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

# =====================================================
# SECURITY DEPOSIT INPUTS
# =====================================================

st.sidebar.subheader("Security Deposit")

security_deposit = st.sidebar.number_input(
    "Security Deposit Amount",
    min_value=0.0,
    value=0.0
)

sd_discount_rate_input = st.sidebar.number_input(
    "SD Discount Rate (%)",
    min_value=0.0,
    value=8.0
)

generate = st.sidebar.button("Generate Lease Model")

# =====================================================
# CALCULATIONS
# =====================================================

if generate:

    # -------------------------------------------------
    # LEASE CALCULATIONS
    # -------------------------------------------------

    if payment_frequency == "Monthly":
        periods = lease_term * 12
        discount_rate = discount_rate_input / 100 / 12
    else:
        periods = lease_term
        discount_rate = discount_rate_input / 100

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

    # Initial Lease Recognition
    journal_entries.append({"Period": 0, "Account": "Right of Use Asset", "Debit": present_value, "Credit": 0})
    journal_entries.append({"Period": 0, "Account": "Lease Liability", "Debit": 0, "Credit": present_value})

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

        # Lease Journals
        journal_entries.extend([
            {"Period": period, "Account": "Interest Expense", "Debit": interest, "Credit": 0},
            {"Period": period, "Account": "Lease Liability", "Debit": 0, "Credit": interest},
            {"Period": period, "Account": "Lease Liability", "Debit": lease_payment, "Credit": 0},
            {"Period": period, "Account": "Bank", "Debit": 0, "Credit": lease_payment},
            {"Period": period, "Account": "Depreciation Expense", "Debit": depreciation, "Credit": 0},
            {"Period": period, "Account": "Accumulated Depreciation - ROU", "Debit": 0, "Credit": depreciation}
        ])

        opening_liability = closing_liability
        opening_rou = closing_rou

    df_schedule = pd.DataFrame(lease_schedule)

    # -------------------------------------------------
    # SECURITY DEPOSIT CALCULATIONS
    # -------------------------------------------------

    sd_df = pd.DataFrame()
    sd_journals = pd.DataFrame()

    if security_deposit > 0:

        sd_rate = sd_discount_rate_input / 100

        pv_sd = round(security_deposit / ((1 + sd_rate) ** lease_term), 2)
        sd_difference = round(security_deposit - pv_sd, 2)

        # Initial Recognition (IFRS Treatment)
        journal_entries.append({"Period": 0, "Account": "Security Deposit (Financial Asset)", "Debit": pv_sd, "Credit": 0})
        journal_entries.append({"Period": 0, "Account": "Right of Use Asset", "Debit": sd_difference, "Credit": 0})
        journal_entries.append({"Period": 0, "Account": "Bank", "Debit": 0, "Credit": security_deposit})

        opening_balance = pv_sd
        sd_schedule = []

        for year in range(1, int(lease_term) + 1):
            interest_income = round(opening_balance * sd_rate, 2)
            closing_balance = round(opening_balance + interest_income, 2)

            sd_schedule.append({
                "Year": year,
                "Opening Balance": opening_balance,
                "Interest Accretion": interest_income,
                "Closing Balance": closing_balance
            })

            journal_entries.append({"Period": year, "Account": "Security Deposit", "Debit": interest_income, "Credit": 0})
            journal_entries.append({"Period": year, "Account": "Interest Income", "Debit": 0, "Credit": interest_income})

            opening_balance = closing_balance

        sd_df = pd.DataFrame(sd_schedule)

    df_journals = pd.DataFrame(journal_entries)

    # =====================================================
    # DISPLAY SECTION
    # =====================================================

    st.subheader("Lease Schedule")
    st.dataframe(df_schedule, use_container_width=True)

    if not sd_df.empty:
        st.subheader("Security Deposit Amortisation Schedule")
        st.dataframe(sd_df, use_container_width=True)

    st.subheader("Journal Entries")
    st.dataframe(df_journals, use_container_width=True)

    # =====================================================
    # EXCEL DOWNLOAD
    # =====================================================

    output = BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_schedule.to_excel(writer, sheet_name='Lease Schedule', index=False)
        df_journals.to_excel(writer, sheet_name='Journal Entries', index=False)
        if not sd_df.empty:
            sd_df.to_excel(writer, sheet_name='Security Deposit', index=False)

    st.download_button(
        label="⬇ Download Excel File",
        data=output.getvalue(),
        file_name="IFRS16_Lease_Model.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
