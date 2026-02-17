import pandas as pd

# ==========================
# USER INPUTS
# ==========================

lease_payment = float(input("Enter Annual Lease Payment: "))
discount_rate_input = float(input("Enter Discount Rate (%): "))
years = int(input("Enter Lease Term (Years): "))

discount_rate = discount_rate_input / 100

# ==========================
# PRESENT VALUE CALCULATION
# ==========================

if discount_rate == 0:
    present_value = lease_payment * years
else:
    present_value = lease_payment * (1 - (1 + discount_rate) ** (-years)) / discount_rate

present_value = round(present_value, 2)

print(f"\nPresent Value of Lease Liability: {present_value}")

# ==========================
# DEPRECIATION CALCULATION
# ==========================

annual_depreciation = round(present_value / years, 2)

# ==========================
# BUILD SCHEDULES
# ==========================

opening_balance = present_value
opening_rou = present_value

lease_schedule = []
journal_entries = []

# --------------------------
# INITIAL RECOGNITION
# --------------------------

journal_entries.append({
    "Year": 0,
    "Account": "Right of Use Asset",
    "Debit": present_value,
    "Credit": 0
})

journal_entries.append({
    "Year": 0,
    "Account": "Lease Liability",
    "Debit": 0,
    "Credit": present_value
})

# --------------------------
# YEARLY PROCESSING
# --------------------------

for year in range(1, years + 1):

    # Interest Calculation
    interest = round(opening_balance * discount_rate, 2)
    closing_balance = round(opening_balance + interest - lease_payment, 2)

    # ROU Depreciation
    depreciation = annual_depreciation
    closing_rou = round(opening_rou - depreciation, 2)

    # Lease Liability Schedule
    lease_schedule.append({
        "Year": year,
        "Opening Lease Liability": opening_balance,
        "Interest Expense": interest,
        "Lease Payment": lease_payment,
        "Closing Lease Liability": closing_balance,
        "Opening ROU Asset": opening_rou,
        "Depreciation": depreciation,
        "Closing ROU Asset": closing_rou
    })

    # --------------------------
    # JOURNAL ENTRIES
    # --------------------------

    # 1️⃣ Interest Entry
    journal_entries.append({
        "Year": year,
        "Account": "Interest Expense",
        "Debit": interest,
        "Credit": 0
    })

    journal_entries.append({
        "Year": year,
        "Account": "Lease Liability",
        "Debit": 0,
        "Credit": interest
    })

    # 2️⃣ Lease Payment Entry
    journal_entries.append({
        "Year": year,
        "Account": "Lease Liability",
        "Debit": lease_payment,
        "Credit": 0
    })

    journal_entries.append({
        "Year": year,
        "Account": "Bank",
        "Debit": 0,
        "Credit": lease_payment
    })

    # 3️⃣ Depreciation Entry
    journal_entries.append({
        "Year": year,
        "Account": "Depreciation Expense",
        "Debit": depreciation,
        "Credit": 0
    })

    journal_entries.append({
        "Year": year,
        "Account": "Accumulated Depreciation - ROU",
        "Debit": 0,
        "Credit": depreciation
    })

    # Update balances
    opening_balance = closing_balance
    opening_rou = closing_rou

# ==========================
# CREATE DATAFRAMES
# ==========================

df_schedule = pd.DataFrame(lease_schedule)
df_journals = pd.DataFrame(journal_entries)

inputs_df = pd.DataFrame({
    "Parameter": [
        "Annual Lease Payment",
        "Discount Rate (%)",
        "Lease Term (Years)",
        "Annual Depreciation"
    ],
    "Value": [
        lease_payment,
        discount_rate_input,
        years,
        annual_depreciation
    ]
})

# ==========================
# VALIDATION CHECK
# ==========================

total_debit = round(df_journals["Debit"].sum(), 2)
total_credit = round(df_journals["Credit"].sum(), 2)

print("\nTotal Debit:", total_debit)
print("Total Credit:", total_credit)

if total_debit == total_credit:
    print("Journal is balanced ✅")
else:
    print("Journal is NOT balanced ❌")

# ==========================
# EXPORT TO EXCEL
# ==========================

file_name = "lease_schedule.xlsx"

with pd.ExcelWriter(file_name, engine="openpyxl", mode="w") as writer:
    inputs_df.to_excel(writer, sheet_name="Lease Inputs", index=False)
    df_schedule.to_excel(writer, sheet_name="Lease Schedule", index=False)
    df_journals.to_excel(writer, sheet_name="Journal Entries", index=False)

print("\nExcel file created successfully with 3 sheets!")
print("Journal rows created:", len(df_journals))
