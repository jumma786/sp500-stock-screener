# S&P 500 Stock Screener & Sector Dashboard

![Python](https://img.shields.io/badge/Python-3.11-blue) ![yfinance](https://img.shields.io/badge/yfinance-free-green) ![HTML](https://img.shields.io/badge/Dashboard-HTML%2FJS-orange) ![Status](https://img.shields.io/badge/Status-Complete-brightgreen)

An end-to-end financial data project that pulls live S&P 500 stock data from Yahoo Finance, processes it with Python/Pandas, and generates a fully interactive browser-based sector dashboard — no paid API required.

---

## Business question

> Which S&P 500 sectors offer the best combination of valuation (P/E), income (dividend yield), and analyst conviction (buy %) — and which individual stocks stand out within each sector?

---

## Dashboard features

- **Sector heatmap** — 10 sectors with live stock count, % analyst buy, and avg P/E. Click any sector to filter the screener instantly
- **Bar charts** — avg P/E and avg dividend yield ranked by sector side by side
- **Stock screener** — filter by sector, analyst rating, P/E band, and dividend yield threshold
- **Sortable table** — 50 stocks with price, 1-day change, P/E, dividend yield, profit margin, market cap, and analyst rating
- **Fully self-contained** — single HTML file, no server needed, opens in any browser

---

## Key findings

| Sector | Stocks | Avg P/E | Avg Div % | Buy % |
|---|---|---|---|---|
| Technology | 9 | 31.7 | 1.5 | 89% |
| Financial Services | 9 | 21.1 | 1.6 | 78% |
| Healthcare | 9 | 36.6 | 2.4 | 89% |
| Consumer Cyclical | 5 | 93.3 | 1.5 | 100% |
| Industrials | 6 | 44.3 | 1.2 | 100% |
| Energy | 2 | 28.6 | 3.3 | 100% |

- **Energy** has the highest analyst buy consensus (100%) with the most attractive dividend yield
- **Consumer Cyclical** carries the highest avg P/E (93.3x) driven by TSLA and AMZN growth premiums
- **Financial Services** is the most attractively valued sector at P/E 21.1x with strong buy consensus

---

## Tech stack

| Layer | Tool |
|---|---|
| Data source | Yahoo Finance via `yfinance` |
| Data processing | Python, Pandas |
| Dashboard | Vanilla HTML/CSS/JavaScript |
| Environment | Anaconda (Python 3.11) |

---

## How to run

```bash
# 1. Clone the repo
git clone https://github.com/jumma786/sp500-stock-screener
cd sp500-stock-screener

# 2. Install dependencies
pip install yfinance pandas

# 3. Run the screener
python sp500_screener.py

# 4. Open the dashboard
start sp500_dashboard.html   # Windows
open sp500_dashboard.html    # Mac/Linux
```

Fetches 50 stocks one at a time (~2–3 minutes). Outputs `sp500_data.csv` and `sp500_dashboard.html`.

---

## Project structure

```
sp500-stock-screener/
├── sp500_screener.py       — data pipeline + dashboard generator
├── sp500_data.csv          — processed output (50 stocks, 15 fields)
├── sp500_dashboard.html    — interactive browser dashboard
└── README.md
```

---

## About

Built by **Jumma Mohammad Teli** — Data Analyst & ML Engineer at UBS London.

Part of a broader financial analytics portfolio spanning Power BI dashboards, SQL analysis, XGBoost modelling, and MLOps pipelines.

[LinkedIn](https://linkedin.com/in/jumma-mohammad) · [GitHub](https://github.com/jumma786)
