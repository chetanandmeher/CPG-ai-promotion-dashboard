import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
from src.data_loader import load_data
from src.ai_agent import (
    get_ai_summary,
    predict_optimal_discount,
    get_discount_recommendation,
)

# ======================
# PAGE CONFIG
# ======================
st.set_page_config(page_title="Promotion Analyzer", layout="wide")
st.title("📊 AI-Powered Promotion Dashboard")

# ======================
# LOAD DATA
# ======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_DIR, "data", "retail_data.csv")
@st.cache_data
def get_data(path):
    return load_data(path)

df = get_data(file_path)

if df is None:
    st.error("❌ Data not loaded")
    st.stop()

# ======================
# CLEAN DATA
# ======================
df.columns = df.columns.str.strip().str.replace(" ", "_")

# ======================
# FEATURE ENGINEERING
# ======================
df["discount_pct"]     = (df["Markdown_1"] / df["Original_Price"]) * 100
df["promotion_lift"]   = (
    (df["Sales_After_M1"] - df["Historical_Sales"]) / df["Historical_Sales"]
) * 100
df["discounted_price"] = df["Original_Price"] - df["Markdown_1"]
df["revenue_after"]    = df["discounted_price"] * df["Sales_After_M1"]

# ======================
# SIDEBAR FILTERS
# ======================
st.sidebar.header("🔍 Filters")

category = st.sidebar.selectbox(
    "Select Category",
    ["All"] + sorted(df["Category"].unique().tolist())
)

season = st.sidebar.selectbox(
    "Select Season",
    ["All"] + sorted(df["Season"].unique().tolist())
)

df_filtered = df.copy()
if category != "All":
    df_filtered = df_filtered[df_filtered["Category"] == category].copy()
if season != "All":
    df_filtered = df_filtered[df_filtered["Season"] == season].copy()

if df_filtered.empty:
    st.warning("⚠️ No data for this filter combination. Showing all data.")
    df_filtered = df.copy()

# Always reset index so groupby / iloc work correctly on filtered data
df_filtered = df_filtered.reset_index(drop=True)

# ======================
# CONTEXT SIGNALS (for dynamic weighting)
# ======================
avg_ratings        = df_filtered["Customer_Ratings"].mean()
avg_return_rate    = df_filtered["Return_Rate"].mean()
seasonality_factor = df_filtered["Seasonality_Factor"].mean()

# ======================
# KPI SECTION
# ======================
avg_lift     = df_filtered["promotion_lift"].mean()
best_lift    = df_filtered["promotion_lift"].max()
avg_discount = df_filtered["discount_pct"].mean()
corr         = df_filtered["discount_pct"].corr(df_filtered["promotion_lift"])

col1, col2, col3, col4 = st.columns(4)
col1.metric("Avg Lift",           f"{avg_lift:.2f}%")
col2.metric("Best Lift",          f"{best_lift:.2f}%")
col3.metric("Avg Discount",       f"{avg_discount:.2f}%")
col4.metric("Discount↔Lift Corr", f"{corr:.3f}")

# ======================
# DISCOUNT BUCKETS
# ======================
bins = list(range(0, 11))
df_filtered["discount_bucket"] = pd.cut(
    df_filtered["discount_pct"],
    bins=bins,
    labels=[f"{i}-{i+1}%" for i in bins[:-1]]
)

bucket_df = df_filtered.groupby("discount_bucket", observed=True).agg(
    promotion_lift=("promotion_lift", "mean"),
    revenue_after=("revenue_after",  "mean")
).reset_index()

bucket_df = bucket_df.dropna(subset=["promotion_lift", "revenue_after"])

# Sort ascending by numeric bucket start so the function receives ordered data
bucket_df["_sort_key"] = bucket_df["discount_bucket"].astype(str).str.extract(r"^(\d+)").astype(int)
bucket_df = bucket_df.sort_values("_sort_key").drop(columns="_sort_key").reset_index(drop=True)

# ======================
# 🔥 MULTI-SIGNAL OPTIMIZATION
# ======================
scored_df, optimal_row, weights = predict_optimal_discount(
    bucket_df,
    category=category if category != "All" else None,
    season=season if season != "All" else None,
    avg_ratings=avg_ratings,
    avg_return_rate=avg_return_rate,
    seasonality_factor=seasonality_factor,
)

optimal_discount = optimal_row["discount_bucket"]
optimal_lift     = optimal_row["promotion_lift"]
optimal_revenue  = optimal_row["revenue_after"]
optimal_score    = optimal_row["score"]

# ======================
# 🔥 AI RECOMMENDATION BANNER
# ======================
st.divider()
st.subheader("🤖 AI Discount Recommendation")

with st.spinner("Generating AI-powered pricing strategy…"):
    recommendation = get_discount_recommendation(
        optimal_row, weights, scored_df,
        category=category if category != "All" else None,
        season=season if season != "All" else None,
        avg_ratings=avg_ratings,
        avg_return_rate=avg_return_rate,
        seasonality_factor=seasonality_factor,
    )

col_rec, col_meta = st.columns([2, 1])

with col_rec:
    st.info(recommendation)

with col_meta:
    st.markdown("**Scoring Weights Applied**")
    weights_df = pd.DataFrame({
        "Signal":  ["Promotion Lift", "Incremental Revenue", "Lift Efficiency", "Revenue Stability"],
        "Weight":  [weights["w_lift"], weights["w_inc_rev"], weights["w_efficiency"], weights["w_stability"]],
    })
    st.dataframe(weights_df, hide_index=True, use_container_width=True)

    st.markdown("**Context Used**")
    st.markdown(f"- Avg Customer Rating: **{avg_ratings:.2f}**")
    st.markdown(f"- Avg Return Rate: **{avg_return_rate:.2f}%**")
    st.markdown(f"- Seasonality Factor: **{seasonality_factor:.2f}**")

st.divider()

# ======================
# GRAPH 1: LIFT + REVENUE (DUAL AXIS) with optimal point
# ======================
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=[optimal_discount],
    y=[optimal_lift],
    mode="markers+text",
    marker=dict(size=14, color="red", symbol="star"),
    text=[f"★ Best ({optimal_discount})"],
    textposition="top center",
    name="Optimal Discount",
))

fig.add_annotation(
    x=optimal_discount,
    y=optimal_lift,
    text=f"Score: {optimal_score:.3f}",
    showarrow=True,
    arrowhead=2,
    bgcolor="rgba(255,80,80,0.15)",
    bordercolor="red",
)

fig.add_trace(go.Scatter(
    x=scored_df["discount_bucket"],
    y=scored_df["promotion_lift"],
    mode="lines+markers",
    name="Promotion Lift (%)",
    line=dict(color="#636EFA", width=2),
))

fig.add_trace(go.Scatter(
    x=scored_df["discount_bucket"],
    y=scored_df["revenue_after"],
    mode="lines+markers",
    name="Revenue (Profit Proxy)",
    yaxis="y2",
    line=dict(color="#00CC96", width=2),
))

fig.add_trace(go.Bar(
    x=scored_df["discount_bucket"],
    y=scored_df["score"],
    name="Composite Score",
    yaxis="y3",
    marker_color="rgba(255,165,0,0.25)",
))

fig.update_layout(
    title="Discount Range vs Lift, Revenue & Composite Score",
    xaxis=dict(
        title="Discount Range (%)",
        categoryorder="array",
        categoryarray=scored_df["discount_bucket"].tolist(),  # lock x-axis to sorted order
    ),
    yaxis=dict(title="Promotion Lift (%)"),
    yaxis2=dict(title="Revenue", overlaying="y", side="right"),
    yaxis3=dict(title="Score", overlaying="y", side="right",
                anchor="free", position=1.0, showgrid=False),
    hovermode="x unified",
    legend=dict(orientation="h", y=-0.2),
)

col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("📈 Lift vs Revenue vs Score")
    st.plotly_chart(fig, use_container_width=True)
with col2:
    st.subheader("🤖 Insight")
    summary = get_ai_summary(
        context="Discount range vs Promotion Lift and Revenue — markdown optimization",
        data=scored_df[["discount_bucket", "promotion_lift", "revenue_after", "score"]].to_string(),
    )
    st.info(summary)

# ======================
# GRAPH 2: CATEGORY LIFT BAR
# ======================
cat_df = df_filtered.groupby("Category")["promotion_lift"].mean().reset_index()
fig2 = px.bar(
    cat_df, x="Category", y="promotion_lift",
    color="Category", text_auto=".1f",
    labels={"promotion_lift": "Avg Lift (%)"},
)
fig2.update_traces(textposition="outside")

col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("📊 Avg Lift by Category")
    st.plotly_chart(fig2, use_container_width=True)
with col2:
    st.subheader("🤖 Insight")
    summary = get_ai_summary(
        context="Average promotion lift by product category",
        data=cat_df.to_string(),
    )
    st.info(summary)

# ======================
# GRAPH 3: SEASON x CATEGORY HEATMAP  (NEW)
# ======================
pivot = df_filtered.groupby(["Category", "Season"])["promotion_lift"].mean().unstack()
fig_heat = px.imshow(
    pivot,
    text_auto=".1f",
    color_continuous_scale="RdYlGn",
    title="Avg Promotion Lift (%) — Category × Season",
    labels=dict(color="Lift %"),
)

col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("🌡️ Lift Heatmap: Category × Season")
    st.plotly_chart(fig_heat, use_container_width=True)
with col2:
    st.subheader("🤖 Insight")
    summary = get_ai_summary(
        context="Promotion lift heatmap broken down by category and season",
        data=pivot.round(2).to_string(),
    )
    st.info(summary)

# ======================
# GRAPH 4: BOX PLOT DISTRIBUTION
# ======================
fig3 = px.box(
    df_filtered, x="Category", y="promotion_lift",
    color="Category", points="outliers",
    labels={"promotion_lift": "Promotion Lift (%)"},
)

col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("📦 Lift Distribution by Category")
    st.plotly_chart(fig3, use_container_width=True)
with col2:
    st.subheader("🤖 Insight")
    summary = get_ai_summary(
        context="Distribution of promotion lift across product categories",
        data=df_filtered[["Category", "promotion_lift"]].head(200).to_string(),
    )
    st.info(summary)

# ======================
# DATA TABLE
# ======================
st.subheader("📋 Data Preview")
display_cols = [
    "Category", "Season", "Brand", "Product_Name",
    "Original_Price", "discount_pct", "promotion_lift",
    "revenue_after", "Customer_Ratings", "Return_Rate",
]
st.dataframe(df_filtered[display_cols].head(100), use_container_width=True)