import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ==============================================================================
# 🔥 CORE: MULTI-SIGNAL OPTIMAL DISCOUNT PREDICTOR
# ==============================================================================

def predict_optimal_discount(bucket_df, category=None, season=None,
                              avg_ratings=None, avg_return_rate=None,
                              seasonality_factor=None):
    """
    Predicts the best discount range using a multi-signal scoring model.

    Signals:
      1. Promotion Lift         (weight 0.35) — demand stimulation
      2. Incremental Revenue    (weight 0.30) — revenue gain vs baseline
      3. Lift-to-Discount Ratio (weight 0.20) — efficiency per % discount given
      4. Revenue Stability      (weight 0.15) — penalises sharp revenue drops

    Context modifiers:
      - High seasonality  → boost lift weight (drive volume)
      - High return rate  → boost stability weight (avoid over-discounting)
      - High ratings      → trust revenue signal more
    """
    df = bucket_df.copy()

    # Always sort ascending by numeric bucket start FIRST (e.g. "3-4%" → 3)
    df["_sort_key"] = df["discount_bucket"].astype(str).str.extract(r"^(\d+)").astype(int)
    df = df.sort_values("_sort_key").reset_index(drop=True)

    # Numeric midpoint of each bucket for efficiency calc
    df["disc_mid"] = df["_sort_key"] + 0.5

    baseline_rev = df["revenue_after"].iloc[0]  # now always the lowest bucket
    max_rev      = df["revenue_after"].max()

    df["incremental_revenue"] = df["revenue_after"] - baseline_rev
    df["inc_rev_clipped"]     = df["incremental_revenue"].clip(lower=0)
    df["lift_efficiency"]     = df["promotion_lift"] / df["disc_mid"]
    df["rev_stability"]       = (df["revenue_after"] / max_rev).clip(upper=1.0)

    def norm(s):
        rng = s.max() - s.min()
        return (s - s.min()) / rng if rng > 0 else s * 0

    df["lift_norm"]       = norm(df["promotion_lift"])
    df["inc_rev_norm"]    = norm(df["inc_rev_clipped"])
    df["efficiency_norm"] = norm(df["lift_efficiency"])
    df["stability_norm"]  = norm(df["rev_stability"])

    # Base weights
    w_lift       = 0.35
    w_inc_rev    = 0.30
    w_efficiency = 0.20
    w_stability  = 0.15

    # Dynamic adjustments
    if seasonality_factor and seasonality_factor > 1.5:
        w_lift       += 0.10
        w_inc_rev    -= 0.05
        w_efficiency -= 0.05

    if avg_return_rate and avg_return_rate > 3.0:
        w_stability  += 0.10
        w_lift       -= 0.10

    if avg_ratings and avg_ratings >= 4.5:
        w_inc_rev    += 0.05
        w_efficiency -= 0.05

    df["score"] = (
        w_lift       * df["lift_norm"] +
        w_inc_rev    * df["inc_rev_norm"] +
        w_efficiency * df["efficiency_norm"] +
        w_stability  * df["stability_norm"]
    )

    optimal_row = df.loc[df["score"].idxmax()]

    weights = {
        "w_lift": w_lift, "w_inc_rev": w_inc_rev,
        "w_efficiency": w_efficiency, "w_stability": w_stability
    }

    df = df.drop(columns=["_sort_key"], errors="ignore")

    return df, optimal_row, weights


# ==============================================================================
# 🤖 PER-CHART AI SUMMARY
# ==============================================================================

def get_ai_summary(context, data):
    prompt = f"""
You are a senior pricing strategist at a CPG retail analytics firm.

Chart context: {context}

Data:
{data}

Rules:
- Give exactly 3 bullet insights (start each with •)
- Reference specific numbers from the data — never invent figures
- Think in terms of margins, demand elasticity, and sell-through risk
- No textbook definitions. No generic statements.
- Max 20 words per bullet.
"""
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile"
    )
    return response.choices[0].message.content


# ==============================================================================
# 🤖 OPTIMAL DISCOUNT RECOMMENDATION
# ==============================================================================

def get_discount_recommendation(optimal_row, weights, bucket_df,
                                 category=None, season=None,
                                 avg_ratings=None, avg_return_rate=None,
                                 seasonality_factor=None):
    context_parts = []
    if category:           context_parts.append(f"Category: {category}")
    if season:             context_parts.append(f"Season: {season}")
    if avg_ratings:        context_parts.append(f"Avg Rating: {avg_ratings:.1f}/5")
    if avg_return_rate:    context_parts.append(f"Return Rate: {avg_return_rate:.1f}%")
    if seasonality_factor: context_parts.append(f"Seasonality: {seasonality_factor:.2f}")
    context_str = " | ".join(context_parts) if context_parts else "All categories, all seasons"

    bucket_summary = bucket_df[
        ["discount_bucket", "promotion_lift", "revenue_after", "score"]
    ].to_string(index=False)

    prompt = f"""
You are a markdown optimization expert in the CPG industry.

Business context: {context_str}

Scoring weights applied:
- Lift: {weights['w_lift']:.2f} | Incremental Revenue: {weights['w_inc_rev']:.2f}
- Efficiency: {weights['w_efficiency']:.2f} | Stability: {weights['w_stability']:.2f}

Full bucket analysis:
{bucket_summary}

OPTIMAL DISCOUNT IDENTIFIED: {optimal_row['discount_bucket']}
- Promotion Lift: {optimal_row['promotion_lift']:.2f}%
- Revenue: {optimal_row['revenue_after']:.2f}
- Composite Score: {optimal_row['score']:.3f}

Respond in this EXACT format:

RECOMMENDED DISCOUNT: [range]

WHY THIS WORKS:
• [Reason 1 — cite actual numbers]
• [Reason 2 — explain the lift vs margin trade-off]
• [Reason 3 — context or risk factor]

BUSINESS ACTION:
• [What the pricing team should do this week]
• [KPI to monitor and threshold to watch]
• [Contingency if results underperform]

CAUTION:
• [One condition where this recommendation breaks down]

Rules: specific numbers only, no generic advice, max 20 words per bullet.
"""
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile"
    )
    return response.choices[0].message.content


# ==============================================================================
# 🔥 STANDALONE — run ai_agent.py directly to test
# ==============================================================================

if __name__ == "__main__":
    import pandas as pd
    from data_loader import load_data

    df = load_data("../data/retail_data.csv")
    if df is None:
        exit()

    df.columns = df.columns.str.strip().str.replace(" ", "_")
    df["discount_pct"]     = (df["Markdown_1"] / df["Original_Price"]) * 100
    df["promotion_lift"]   = ((df["Sales_After_M1"] - df["Historical_Sales"]) / df["Historical_Sales"]) * 100
    df["discounted_price"] = df["Original_Price"] - df["Markdown_1"]
    df["revenue_after"]    = df["discounted_price"] * df["Sales_After_M1"]

    bins = list(range(0, 11))
    df["discount_bucket"] = pd.cut(
        df["discount_pct"], bins=bins,
        labels=[f"{i}-{i+1}%" for i in bins[:-1]]
    )

    bucket_df = df.groupby("discount_bucket").agg({
        "promotion_lift": "mean",
        "revenue_after":  "mean"
    }).reset_index()

    scored_df, optimal_row, weights = predict_optimal_discount(
        bucket_df,
        avg_ratings=df["Customer_Ratings"].mean(),
        avg_return_rate=df["Return_Rate"].mean(),
        seasonality_factor=df["Seasonality_Factor"].mean()
    )

    print("\n📊 SCORED BUCKET TABLE:\n")
    print(scored_df[["discount_bucket", "promotion_lift", "revenue_after",
                      "lift_efficiency", "score"]].to_string(index=False))

    print("\n" + "=" * 60)
    print(get_discount_recommendation(
        optimal_row, weights, scored_df,
        avg_ratings=df["Customer_Ratings"].mean(),
        avg_return_rate=df["Return_Rate"].mean(),
        seasonality_factor=df["Seasonality_Factor"].mean()
    ))