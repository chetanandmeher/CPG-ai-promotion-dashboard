import pandas as pd
from data_loader import load_data

# Load data
df = load_data("../data/retail_data.csv")

if df is None:
    print("❌ Data not loaded")
    exit()

# 🔹 Step 1: Clean column names
df.columns = df.columns.str.strip().str.replace(" ", "_")

# 🔹 Step 2: Discount Percentage (convert to %)
df["discount_pct"] = (df["Markdown_1"] / df["Original_Price"]) * 100

# 🔹 Step 3: Discounted Price (IMPORTANT FIX)
df["discounted_price"] = df["Original_Price"] - df["Markdown_1"]

# 🔹 Step 4: Revenue Before Promotion
df["revenue_before"] = df["Original_Price"] * df["Historical_Sales"]

# 🔹 Step 5: Revenue After Promotion (correct logic)
df["revenue_after"] = df["discounted_price"] * df["Sales_After_M1"]

# 🔹 Step 6: Promotion Lift (CORE KPI)
df["promotion_lift"] = (
    (df["Sales_After_M1"] - df["Historical_Sales"]) 
    / df["Historical_Sales"]
) * 100

# 🔹 Step 7: Revenue Change (NEW – VERY STRONG FEATURE)
df["revenue_change_pct"] = (
    (df["revenue_after"] - df["revenue_before"]) 
    / df["revenue_before"]
) * 100

# Preview important columns
print(df[[
    "Original_Price",
    "Markdown_1",
    "discount_pct",
    "discounted_price",
    "Historical_Sales",
    "Sales_After_M1",
    "promotion_lift",
    "revenue_before",
    "revenue_after",
    "revenue_change_pct"
]].head())