import pandas as pd
from data_loader import load_data

df = load_data("../data/SYNTHETIC_Markdown_Dataset.csv")

# 1. Basic info
print("\n--- INFO ---")
print(df.info())

# 2. Column names
print("\n--- COLUMNS ---")
print(df.columns)

# 3. Summary stats
print("\n--- SUMMARY ---")
print(df.describe())