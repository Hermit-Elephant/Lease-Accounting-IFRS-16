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
st.markdown("Lease Schedule • Escalation • Security Deposit • Journal Entries")
st.divider()

# =====================================================
# SIDEBAR INPUTS
# =====================================================

st.sidebar.header("Lease Inputs")

base_rent = st.sidebar.number_input("Base Lease Payment", min_value=0.0, value=100000.0)
discount_rate_input = st.sidebar.number_input("Discount Rate (%)", min_value=0.0, value=8.0)
lease_term = st.sidebar.number_input("Lease Term (Years)", min_value=1, value=8)

payment_timing = st.sidebar.selectbox(
    "Payment Timing",
    ["End of Period", "Beginning of Period"]
)

# =====================================================
# ESCALATION INPUTS
# =====================================================

st.sidebar.subheader("Rent Escalation")

escalation_rate = st.sidebar.number_input("Escalation (%)", min_value=0.0, value=5.0)
escalation_frequency = st.sidebar.selectbox(
    "Escalation Frequency",
    ["Every Year", "Every 2 Years", "Every 3 Years"]
)

escalation_start = st.sidebar.number_input(
    "Escalation Starts After (Years)",
    min_value=0,
    max_value=int(lease_term),
    value=1
)

# =====================================================
# SECURITY DEPOSIT
# =====================================================

st.sidebar.subheader("Security Deposit")

security_deposit = st.sidebar.number_input("Security Deposit Amount", min_value=0.0, value=0.0)
sd_discount_rate_input = st.sidebar.number_input("SD Discount Rate (%)", min_value=0.0, value=8.0)

generate = st.sidebar.button("Generate Lease Model")

# =====================================================
# MAIN LOGIC
# =====================================================

if generate:

    discount_rate = discount_rate_input / 100
    escalation_rate = escalation_rate / 100

    # Determine escalation interval
    if escalation_frequency == "Every Year":
        interval = 1
    elif escalation_frequency == "Every 2 Years":
        interval = 2
    else:
        interval = 3

    # =====================================================
    # BUILD ESCALATED RENT SCHEDULE
    # =====================================================

    rents = []
    current_rent = base_rent

    for year in range(1, int(lease_term) + 1):

        if year > escalation_start and (year - escalation_start - 1) % interval == 0:
            current_rent *= (1 + escalation_rate)

        rents.append(round(current_rent, 2))

    # =====================================================
    # CALCULATE PRESENT VALUE
    # =====================================================

    pv = 0

    for year in range(1, lease_term + 1):
        if payment_timing == "Beginning of Period":
            pv += rents[year - 1] / ((1 + discount_rate) ** (year - 1))
        else:
            pv += rents[year - 1] / ((1 + discount_rate) ** year)

    present_value = round(pv, 2)
    depreciation = round(present_value / lease_term, 2)

    # =====================================================
    # LEASE AMORTISATION
    # =====================================================

    opening_liability = present_value
    opening_rou = present_value

    lease_schedule = []
    journal_entries = []

    # Initial Recognition
    journal_entries.append({"Year": 0, "Account": "ROU Asset", "Debit": present_value, "Credit": 0})
    journal_entries.append({"Year": 0, "Account": "Lease Liability", "Debit": 0, "Credit": present_value})

    for year in range(1, lease_term + 1):

        rent = rents[year - 1]

        if payment_timing == "Beginning of Period":
            opening_liability -= rent
            interest = round(opening_liability * discount_rate, 2)
            closing_liability = round(opening_liability + interest, 2)
        else:
            interest = round(opening_liability * discount_rate, 2)
            closing_liability = round(opening_liability + interest - rent, 2)

        closing_rou = round(opening_rou - depreciation, 2)

        lease_schedule.append({
            "Year": year,
            "Opening Liability": opening_liability,
            "Rent Payment": rent,
            "Interest Expense": interest,
            "Closing Liability": closing_liability,
            "Opening ROU": opening_rou,
            "Depreciation": depreciation,
            "Closing ROU": closing_rou
        })

        journal_entries.extend([
            {"Year": year, "Account": "Interest Expense", "Debit": interest, "Credit": 0},
            {"Year": year, "Account": "Lease Liability", "Debit": rent, "Credit": 0},
            {"Year": year, "Account": "Bank", "Debit": 0, "Credit": rent},
            {"Year": year, "Account": "Depreciation Expense", "Debit": depreciation, "Credit": 0},
            {"Year": year, "Account": "Accumulated Depreciation - ROU", "Debit": 0, "Credit": depreciation}
        ])

        opening_liability = closing_liability
        opening_rou = closing_rou

    df_schedule = pd.DataFrame(lease_schedule)

    # =====================================================
    # SECURITY DEPOSIT
    # =====================================================

    sd_df = pd.DataFrame()

    if security_deposit > 0:

        sd_rate = sd_discount_rate_input / 100
        pv_sd = round(security_deposit / ((1 + sd_rate) ** lease_term), 2)
        sd_diff = security_deposit - pv_sd

        journal_entries.append({"Year": 0, "Account": "Security Deposit (Financial Asset)", "Debit": pv_sd, "Credit": 0})
        journal_entries.append({"Year": 0, "Account": "ROU Asset", "Debit": sd_diff, "Credit": 0})
        journal_entries.append({"Year": 0, "Account": "Bank", "Debit": 0, "Credit": security_deposit})

        opening_balance = pv_sd
        sd_schedule = []

        for year in range(1, lease_term + 1):
            interest_income = round(opening_balance * sd_rate, 2)
            closing_balance = round(opening_balance + interest_income, 2)

            sd_schedule.append({
                "Year": year,
                "Opening Balance": opening_balance,
                "Interest Accretion": interest_income,
                "Closing Balance": closing_balance
            })

            journal_entries.append({"Year": year, "Account": "Security Deposit", "Debit": interest_income, "Credit": 0})
            journal_entries.append({"Year": year, "Account": "Interest Income", "Debit": 0, "Credit": interest_income})

            opening_balance = closing_balance

        sd_df = pd.DataFrame(sd_schedule)

    df_journals = pd.DataFrame(journal_entries)

    # =====================================================
    # DISPLAY
    # =====================================================

    tab1, tab2, tab3 = st.tabs([
        "📊 Lease Schedule",
        "💰 Security Deposit",
        "📘 Journal Entries"
    ])

    with tab1:
        st.dataframe(df_schedule, use_container_width=True)

    with tab2:
        if not sd_df.empty:
            st.dataframe(sd_df, use_container_width=True)
        else:
            st.info("No Security Deposit Entered.")

    with tab3:
        st.dataframe(df_journals, use_container_width=True)

    # =====================================================
    # EXCEL EXPORT
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
