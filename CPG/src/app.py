import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
from data_loader import load_data
from ai_agent import get_ai_summary

# ======================
# PAGE CONFIG
# ======================
st.set_page_config(page_title="Promotion Analyzer", layout="wide")
st.title("📊 AI-Powered Promotion Dashboard")

# ======================
# LOAD DATA
# ======================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
file_path = os.path.join(BASE_DIR, "data", "retail_data.csv")

df = load_data(file_path)

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
df["discount_pct"] = (df["Markdown_1"] / df["Original_Price"]) * 100

df["promotion_lift"] = (
    (df["Sales_After_M1"] - df["Historical_Sales"])
    / df["Historical_Sales"]
) * 100

# 🔥 PROFIT (REVENUE PROXY)
df["discounted_price"] = df["Original_Price"] - df["Markdown_1"]
df["revenue_after"] = df["discounted_price"] * df["Sales_After_M1"]

# ======================
# SIDEBAR FILTER
# ======================
st.sidebar.header("🔍 Filters")

category = st.sidebar.selectbox(
    "Select Category",
    ["All"] + list(df["Category"].unique())
)

if category != "All":
    df = df[df["Category"] == category]

# ======================
# KPI SECTION
# ======================
avg_lift = df["promotion_lift"].mean()
best_lift = df["promotion_lift"].max()
avg_discount = df["discount_pct"].mean()

best_row = df.loc[df["promotion_lift"].idxmax()]
best_discount = best_row["discount_pct"]
corr = df["discount_pct"].corr(df["promotion_lift"])

col1, col2, col3 = st.columns(3)

col1.metric("Avg Lift", f"{avg_lift:.2f}%")
col2.metric("Best Lift", f"{best_lift:.2f}%")
col3.metric("Avg Discount", f"{avg_discount:.2f}%")

# ======================
# 🔥 DISCOUNT BUCKET (FIXED CLEAN LABELS)
# ======================
bins = list(range(0, 11))

df["discount_bucket"] = pd.cut(
    df["discount_pct"],
    bins=bins,
    labels=[f"{i}-{i+1}%" for i in bins[:-1]]
)

# ======================
# AGGREGATE DATA
# ======================
bucket_df = df.groupby("discount_bucket").agg({
    "promotion_lift": "mean",
    "revenue_after": "mean"
}).reset_index()

# ======================
# 🔥 SMART OPTIMIZATION LOGIC
# ======================

# Normalize values
bucket_df["lift_norm"] = bucket_df["promotion_lift"] / bucket_df["promotion_lift"].max()
bucket_df["revenue_norm"] = bucket_df["revenue_after"] / bucket_df["revenue_after"].max()

# Combined score (balanced decision)
bucket_df["score"] = 0.5 * bucket_df["lift_norm"] + 0.5 * bucket_df["revenue_norm"]

# Find optimal point
optimal_row = bucket_df.loc[bucket_df["score"].idxmax()]

optimal_discount = optimal_row["discount_bucket"]
optimal_lift = optimal_row["promotion_lift"]
optimal_revenue = optimal_row["revenue_after"]


# ======================
# 🔥 GRAPH 1: LIFT + PROFIT (BEST GRAPH)
# ======================
fig = go.Figure()


# ======================
# 🔥 HIGHLIGHT OPTIMAL POINT
# ======================

fig.add_trace(go.Scatter(
    x=[optimal_discount],
    y=[optimal_lift],
    mode="markers+text",
    marker=dict(size=14, color="red"),
    text=["Best"],
    textposition="top center",
    name="Optimal Point"
))

fig.add_annotation(
    x=optimal_discount,
    y=optimal_lift,
    text=f"Best: {optimal_discount}",
    showarrow=True,
    arrowhead=2
)

# Lift line
fig.add_trace(go.Scatter(
    x=bucket_df["discount_bucket"],
    y=bucket_df["promotion_lift"],
    mode='lines+markers',
    name='Promotion Lift (%)'
))

# Profit line
fig.add_trace(go.Scatter(
    x=bucket_df["discount_bucket"],
    y=bucket_df["revenue_after"],
    mode='lines+markers',
    name='Revenue (Profit Proxy)',
    yaxis="y2"
))

# Layout
fig.update_layout(
    title="Discount vs Lift & Profit",
    xaxis_title="Discount Range (%)",
    yaxis=dict(title="Promotion Lift (%)"),
    yaxis2=dict(
        title="Revenue",
        overlaying='y',
        side='right'
    ),

    # 👇 ADD THIS (VERY IMPORTANT)
    hovermode="x unified"
)

# SIDE-BY-SIDE LAYOUT
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("📈 Lift vs Profit Analysis")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.success(f"""
    🎯 Optimal Discount: {optimal_discount}
    📈 Lift: {optimal_lift:.2f}%
    💰 Revenue: {optimal_revenue:.2f}
    """)

    st.subheader("🤖 Insight")
    summary = get_ai_summary(
        context="Distribution of Promotion Lift across categories",
        data=df[["Category", "promotion_lift"]].head(100).to_string()
    )
    st.info(summary)

# ======================
# 🔥 CATEGORY GRAPH
# ======================
cat_df = df.groupby("Category")["promotion_lift"].mean().reset_index()

fig2 = px.bar(cat_df, x="Category", y="promotion_lift", color="Category")

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("📊 Avg Lift by Category")
    st.plotly_chart(fig2, use_container_width=True)

with col2:
    st.subheader("🤖 Insight")

    summary = get_ai_summary(
        context="Discount vs Lift and Revenue graph",
        data=bucket_df.to_string()
    )

    st.info(summary)

# ======================
# 🔥 DISTRIBUTION
# ======================
fig3 = px.box(df, x="Category", y="promotion_lift", color="Category")

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("📦 Lift Distribution")
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    st.subheader("🤖 Insight")
    summary = get_ai_summary(
        context="Category vs Promotion Lift",
        data=cat_df.to_string()
    )    
    st.info(summary)

# ======================
# DATA TABLE
# ======================
st.subheader("📋 Data Preview")
st.dataframe(df.head(100))