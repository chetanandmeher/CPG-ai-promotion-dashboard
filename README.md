# 📊 CPG AI-Powered Promotion Dashboard

An intelligent **Streamlit** dashboard that uses **AI-driven multi-signal optimization** to recommend the best markdown (discount) strategy for CPG retail products. Powered by **Groq LLM (LLaMA 3.3 70B)** for real-time business insights.

🔗 **Live App →** [cpg-ai-promotion-dashboard.streamlit.app](https://cpg-ai-promotion-dashboard-hmcthprktlakktc4xsejzx.streamlit.app/)

---

## ✨ Key Features

| Feature | Description |
|---|---|
| **Multi-Signal Discount Optimizer** | Scores each discount bucket on 4 signals — Promotion Lift, Incremental Revenue, Lift Efficiency & Revenue Stability — with dynamic weight adjustments based on context (seasonality, return rate, customer ratings). |
| **AI Recommendation Engine** | Generates actionable pricing strategies using Groq's LLaMA 3.3 70B model, including business actions, KPIs to monitor, and risk cautions. |
| **Interactive Visualizations** | Dual-axis Lift vs Revenue chart, Category bar charts, Category × Season heatmap, and box-plot distribution — each paired with AI-generated insights. |
| **Dynamic Filtering** | Filter by product **Category** and **Season** with automatic fallback when no data matches. |
| **Context-Aware Scoring** | Weights shift automatically — e.g., high seasonality boosts lift weight; high return rates boost stability weight. |

---

## 🖼️ Dashboard Overview

The dashboard includes:

- **KPI Cards** — Avg Lift, Best Lift, Avg Discount, Discount↔Lift Correlation
- **🤖 AI Discount Recommendation** — Full strategy with scoring weights and context signals
- **📈 Lift vs Revenue vs Score** — Dual-axis chart with optimal point annotation
- **📊 Avg Lift by Category** — Bar chart with AI insight
- **🌡️ Lift Heatmap: Category × Season** — Heatmap with AI insight
- **📦 Lift Distribution by Category** — Box plot with AI insight
- **📋 Data Preview** — Filtered tabular view

---

## 🗂️ Project Structure

```
tiger_analytics_project/
├── .gitignore
├── README.md
└── CPG/
    ├── app.py                  # Main Streamlit dashboard (entry point)
    ├── requirements.txt        # Python dependencies
    ├── .env                    # API keys (not committed)
    ├── data/
    │   └── retail_data.csv     # Retail promotion dataset
    └── src/
        ├── ai_agent.py         # Multi-signal optimizer + Groq AI summaries
        ├── data_loader.py      # CSV data loading utility
        ├── data_cleaning.py    # Column cleaning helpers
        ├── feature_engineering.py  # Discount %, promotion lift, revenue calcs
        ├── analysis.py         # Standalone analysis scripts
        └── data_understanding.py   # EDA utilities
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- A [Groq API key](https://console.groq.com/) (free tier available)

### Installation

```bash
# Clone the repository
git clone https://github.com/chetanandmeher/CPG-ai-promotion-dashboard.git
cd CPG-ai-promotion-dashboard/CPG

# Create a virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the `CPG/` directory:

```env
GROQ_API_KEY=your_groq_api_key_here
```

For Streamlit Cloud deployment, add the key in `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "your_groq_api_key_here"
```

### Run the App

```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`.

---

## 🧠 How the Optimizer Works

The **Multi-Signal Optimal Discount Predictor** scores each discount bucket (0–1%, 1–2%, … 9–10%) using four normalized signals:

| Signal | Base Weight | What It Measures |
|---|---|---|
| Promotion Lift | 0.35 | Demand stimulation — how much sales increase |
| Incremental Revenue | 0.30 | Revenue gain vs the lowest-discount baseline |
| Lift Efficiency | 0.20 | Lift per percentage point of discount given |
| Revenue Stability | 0.15 | Penalizes sharp revenue drops at high discounts |

**Dynamic weight adjustments:**

- 📈 High seasonality factor (>1.5) → boost Lift weight (+0.10)
- 🔄 High return rate (>3%) → boost Stability weight (+0.10)
- ⭐ High customer ratings (≥4.5) → boost Revenue weight (+0.05)

The bucket with the highest composite score is recommended as the optimal discount range.

---

## 🛠️ Tech Stack

- **Frontend:** [Streamlit](https://streamlit.io/) — Interactive Python dashboards
- **Charts:** [Plotly](https://plotly.com/python/) — Interactive graphs (Graph Objects + Express)
- **AI/LLM:** [Groq](https://groq.com/) — LLaMA 3.3 70B Versatile for real-time insights
- **Data:** [Pandas](https://pandas.pydata.org/) — Data manipulation and analysis
- **Environment:** [python-dotenv](https://pypi.org/project/python-dotenv/) — Secure API key management

---

## 📦 Dependencies

```
streamlit==1.32.0
pandas==2.0.3
plotly==5.18.0
groq
python-dotenv
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 👤 Author

**Chetan & Meher**

- GitHub: [@chetanandmeher](https://github.com/chetanandmeher)

---

<p align="center">
  Built with ❤️ using Streamlit & Groq AI
</p>
