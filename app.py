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
st.markdown("Lease Schedule • Security Deposit • Lock-in Analysis • Journal Entries")
st.divider()

# =====================================================
# SIDEBAR INPUTS
# =====================================================

st.sidebar.header("Lease Inputs")

lease_payment = st.sidebar.number_input("Lease Payment", min_value=0.0, value=50000.0)
discount_rate_input = st.sidebar.number_input("Discount Rate (%)", min_value=0.0, value=9.0)
lease_term = st.sidebar.number_input("Lease Term (Years)", min_value=1, value=5)

payment_frequency = st.sidebar.selectbox(
    "Payment Frequency",
    ["Annual", "Monthly"]
)

payment_timing = st.sidebar.selectbox(
    "Payment Timing",
    ["End of Period", "Beginning of Period"]
)

# =====================================================
# LOCK-IN INPUT
# =====================================================

st.sidebar.subheader("Lock-in Settings")

lock_in_years = st.sidebar.number_input(
    "Lock-in Period (Years)",
    min_value=0,
    max_value=int(lease_term),
    value=0
)

# =====================================================
# SECURITY DEPOSIT INPUTS
# =====================================================

st.sidebar.subheader("Security Deposit")

security_deposit = st.sidebar.number_input("Security Deposit Amount", min_value=0.0, value=0.0)
sd_discount_rate_input = st.sidebar.number_input("SD Discount Rate (%)", min_value=0.0, value=8.0)

generate = st.sidebar.button("Generate Lease Model")

# =====================================================
# MAIN CALCULATIONS
# =====================================================

if generate:

    # Frequency logic
    if payment_frequency == "Monthly":
        periods = lease_term * 12
        discount_rate = discount_rate_input / 100 / 12
    else:
        periods = lease_term
        discount_rate = discount_rate_input / 100

    # ============================
    # PRESENT VALUE CALCULATION
    # ============================

    if discount_rate == 0:
        present_value = lease_payment * periods
    else:
        pv_factor = (1 - (1 + discount_rate) ** (-periods)) / discount_rate

        # Annuity Due Adjustment
        if payment_timing == "Beginning of Period":
            pv_factor = pv_factor * (1 + discount_rate)

        present_value = lease_payment * pv_factor

    present_value = round(present_value, 2)
    depreciation = round(present_value / periods, 2)

    opening_liability = present_value
    opening_rou = present_value

    lease_schedule = []
    journal_entries = []

    # Initial Recognition
    journal_entries.append({"Period": 0, "Account": "Right of Use Asset", "Debit": present_value, "Credit": 0})
    journal_entries.append({"Period": 0, "Account": "Lease Liability", "Debit": 0, "Credit": present_value})

    # ============================
    # LEASE SCHEDULE
    # ============================

    for period in range(1, int(periods) + 1):

        if payment_timing == "Beginning of Period":
            # Payment first
            closing_liability = opening_liability - lease_payment
            interest = round(closing_liability * discount_rate, 2)
            closing_liability = round(closing_liability + interest, 2)
        else:
            # Interest first
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
        sd_difference = round(security_deposit - pv_sd, 2)

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

            opening_balance = closing_balance

        sd_df = pd.DataFrame(sd_schedule)

    # =====================================================
    # LOCK-IN ANALYSIS
    # =====================================================

    lock_df = pd.DataFrame()

    if lock_in_years > 0:

        locked_periods = lock_in_years * (12 if payment_frequency == "Monthly" else 1)
        locked_payments = lease_payment * locked_periods

        lock_df = pd.DataFrame({
            "Lock-in Years": [lock_in_years],
            "Total Lock-in Payments": [locked_payments],
            "Remaining Term After Lock-in": [lease_term - lock_in_years]
        })

    # =====================================================
    # TABS
    # =====================================================

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Lease Schedule",
        "💰 Security Deposit",
        "🔒 Lock-in Analysis",
        "📘 Journals Summary"
    ])

    with tab1:
        st.dataframe(df_schedule, use_container_width=True)

    with tab2:
        if not sd_df.empty:
            st.dataframe(sd_df, use_container_width=True)
        else:
            st.info("No Security Deposit entered.")

    with tab3:
        if not lock_df.empty:
            st.dataframe(lock_df, use_container_width=True)
        else:
            st.info("No Lock-in period defined.")

    with tab4:
        st.write("Initial Lease Liability:", present_value)
        st.write("Annual Depreciation:", depreciation)

    # =====================================================
    # EXCEL DOWNLOAD
    # =====================================================

    output = BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_schedule.to_excel(writer, sheet_name='Lease Schedule', index=False)
        if not sd_df.empty:
            sd_df.to_excel(writer, sheet_name='Security Deposit', index=False)
        if not lock_df.empty:
            lock_df.to_excel(writer, sheet_name='Lock-in', index=False)

    st.download_button(
        label="⬇ Download Excel File",
        data=output.getvalue(),
        file_name="IFRS16_Lease_Model.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
