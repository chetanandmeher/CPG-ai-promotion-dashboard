import pandas as pd

def load_data(path):
    try:
        df = pd.read_csv(path)
        print("✅ Data loaded successfully")
        return df
    except Exception as e:
        print("❌ Error loading data:", e)
        return None


if __name__ == "__main__":
    df = load_data("../data/SYNTHETIC_Markdown_Dataset.csv")
    print(df.head())