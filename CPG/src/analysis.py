import pandas as pd
from data_loader import load_data

df = load_data("../data/retail_data.csv")

if df is None:
    exit()

# Clean columns
df.columns = df.columns.str.strip().str.replace(" ", "_")

# Features (reuse)
df["discount_pct"] = (df["Markdown_1"] / df["Original_Price"]) * 100
df["promotion_lift"] = (
    (df["Sales_After_M1"] - df["Historical_Sales"]) 
    / df["Historical_Sales"]
) * 100

# 🔥 1. Average lift
print("Average Promotion Lift:", df["promotion_lift"].mean())

# 🔥 2. Best discount case
best = df.loc[df["promotion_lift"].idxmax()]
print("\nBest Discount vs Lift:")
print(best[["discount_pct", "promotion_lift"]])

# 🔥 3. Correlation
corr = df["discount_pct"].corr(df["promotion_lift"])
print("\nCorrelation:", corr)