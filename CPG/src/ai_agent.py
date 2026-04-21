import os
from groq import Groq
from dotenv import load_dotenv
from data_loader import load_data

# Load env
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Load data
df = load_data("../data/retail_data.csv")

if df is None:
    exit()

# Clean columns
df.columns = df.columns.str.strip().str.replace(" ", "_")

# Features
df["discount_pct"] = (df["Markdown_1"] / df["Original_Price"]) * 100
df["promotion_lift"] = (
    (df["Sales_After_M1"] - df["Historical_Sales"]) 
    / df["Historical_Sales"]
) * 100

# 🔥 Extract insights
avg_lift = round(df["promotion_lift"].mean(), 2)
best = df.loc[df["promotion_lift"].idxmax()]
best_discount = round(best["discount_pct"], 2)
best_lift = round(best["promotion_lift"], 2)
corr = round(df["discount_pct"].corr(df["promotion_lift"]), 2)

# 🔥 Create prompt (VERY IMPORTANT)
prompt = f"""
You are a senior business analyst working in a retail analytics company.

Analyze the following data:

- Average promotion lift: {avg_lift}%
- Best discount: {best_discount}%
- Best lift: {best_lift}%
- Correlation between discount and lift: {corr}

IMPORTANT:
Do NOT explain definitions.
Do NOT give textbook answers.

ONLY:
1. Give business insights from this data
2. Explain what low/high correlation means
3. Suggest pricing strategy

Be concise and professional.
"""
# Call Groq
response = client.chat.completions.create(
    messages=[{"role": "user", "content": prompt}],
    model="llama-3.3-70b-versatile"
)

print("\nAI ANALYSIS:\n")
print(response.choices[0].message.content)

def get_ai_summary(context, data):
    prompt = f"""
    You are a business analyst.

    Context: {context}

    Data:
    {data}

    IMPORTANT:
    - DO NOT give general definitions
    - ONLY analyze this specific graph
    - Give 3 short insights
    """

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile"
    )

    return response.choices[0].message.content
    prompt = f"""
    You are a business analyst.

    Data:
    - Avg Lift: {avg_lift}%
    - Best Discount: {best_discount}%
    - Correlation: {corr}

    Give 3 short business insights.
    No definitions.
    """

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile"
    )

    return response.choices[0].message.content