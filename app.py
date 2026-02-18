import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="IFRS 16 Lease Automation",
    page_icon="📘",
    layout="wide"
)

# =====================================================
# DARK MODE TOGGLE
# =====================================================

dark_mode = st.sidebar.toggle("🌙 Enable Dark Mode")

if dark_mode:
    st.markdown("""
        <style>
        .stApp {
            background-color: #0E1117;
            color: white;
        }
        section[data-testid="stSidebar"] {
            background-color: #161B22;
        }
        div[data-testid="stDataFrame"] {
            background-color: #1E2228;
        }
        .stButton>button {
            background-color: #262730;
            color: white;
        }
        .stDownloadButton>button {
            background-color: #262730;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .stApp {
            background-color: white;
            color: black;
        }
        section[data-testid="stSidebar"] {
            background-color: #F0F2F6;
        }
        </style>
    """, unsafe_allow_html=True)

# =====================================================
# TITLE
# =====================================================

st.title("📘 IFRS 16 Lease Accounting Tool")
st.markdown("Lease Schedule • Escalation • Analytics Dashboard")
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

st.sidebar.subheader("Rent Escalation")

escalation_rate_input = st.sidebar.number_input("Escalation (%)", min_value=0.0, value=5.0)
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

generate = st.sidebar.button("Generate Lease Model")

# =====================================================
# MAIN LOGIC
# =====================================================

if generate:

    discount_rate = discount_rate_input / 100
    escalation_rate = escalation_rate_input / 100

    interval = {"Every Year": 1, "Every 2 Years": 2, "Every 3 Years": 3}[escalation_frequency]

    rents = []
    current_rent = base_rent

    for year in range(1, int(lease_term) + 1):
        if year > escalation_start and (year - escalation_start - 1) % interval == 0:
            current_rent *= (1 + escalation_rate)
        rents.append(round(current_rent, 2))

    pv = 0
    for year in range(1, lease_term + 1):
        if payment_timing == "Beginning of Period":
            pv += rents[year - 1] / ((1 + discount_rate) ** (year - 1))
        else:
            pv += rents[year - 1] / ((1 + discount_rate) ** year)

    present_value = round(pv, 2)
    depreciation = round(present_value / lease_term, 2)

    opening_liability = present_value
    lease_schedule = []

    for year in range(1, lease_term + 1):

        rent = rents[year - 1]

        if payment_timing == "Beginning of Period":
            opening_liability -= rent
            interest = round(opening_liability * discount_rate, 2)
            closing_liability = round(opening_liability + interest, 2)
        else:
            interest = round(opening_liability * discount_rate, 2)
            closing_liability = round(opening_liability + interest - rent, 2)

        lease_schedule.append({
            "Year": year,
            "Interest Expense": interest,
            "Depreciation": depreciation,
            "Closing Liability": closing_liability
        })

        opening_liability = closing_liability

    df_schedule = pd.DataFrame(lease_schedule)

    # =====================================================
    # TABS
    # =====================================================

    tab1, tab2, tab3 = st.tabs(["📊 Schedule", "📈 Analytics", "⬇ Export"])

    with tab1:
        st.dataframe(df_schedule, use_container_width=True)

    with tab2:

        st.subheader("Interest vs Depreciation Trend")

        fig, ax = plt.subplots()

        if dark_mode:
            fig.patch.set_facecolor("#0E1117")
            ax.set_facecolor("#0E1117")
            ax.tick_params(colors="white")
            ax.xaxis.label.set_color("white")
            ax.yaxis.label.set_color("white")
            ax.title.set_color("white")

        ax.plot(df_schedule["Year"], df_schedule["Interest Expense"], marker='o')
        ax.plot(df_schedule["Year"], df_schedule["Depreciation"], marker='o')

        ax.set_xlabel("Year")
        ax.set_ylabel("Amount")
        ax.set_title("Interest vs Depreciation")

        ax.legend(["Interest Expense", "Depreciation"])
        ax.grid(alpha=0.3)

        st.pyplot(fig)

    with tab3:

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_schedule.to_excel(writer, sheet_name='Lease Schedule', index=False)

        st.download_button(
            label="⬇ Download Excel File",
            data=output.getvalue(),
            file_name="IFRS16_Lease_Model.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
