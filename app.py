import streamlit as st
import pandas as pd
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
st.markdown("Lease Schedule • Security Deposit • Journal Entries")
st.divider()

# =====================================================
# SIDEBAR INPUTS
# =====================================================

st.sidebar.header("Lease Inputs")

lease_payment = st.sidebar.number_input("Lease Payment", min_value=0.0, value=50000.0)
discount_rate_input = st.sidebar.number_input("Discount Rate (%)", min_value=0.0, value=9.0)
lease_term = st.sidebar.number_input("Lease Term (Years)", min_value=1, value=8)

payment_frequen_
