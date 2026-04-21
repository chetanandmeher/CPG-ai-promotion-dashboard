import pandas as pd
from data_loader import load_data

df = load_data("../data/retail_data.csv")

if df is None:
    print("❌ Data not loaded. Check file path.")
    exit()

df.columns = df.columns.str.strip().str.replace(" ", "_")

print(df.columns)