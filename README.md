# S&P 500 Stock Screener & Analyst Rating Classifier

![Python](https://img.shields.io/badge/Python-3.11-blue) ![yfinance](https://img.shields.io/badge/Data-yfinance-green) ![XGBoost](https://img.shields.io/badge/Model-XGBoost-orange) ![Status](https://img.shields.io/badge/Status-Complete-brightgreen)

An end-to-end financial data project that pulls live S&P 500 stock data from Yahoo Finance, processes it with Python/Pandas, builds an XGBoost analyst rating classifier, and generates a fully interactive browser-based sector dashboard — no paid API required.

---

## Business questions

> 1. Which S&P 500 sectors offer the best combination of valuation, income, and analyst conviction?
> 2. Can financial ratios alone predict whether analysts rate a stock Buy or Hold?

---

## Project structure

```
sp500-stock-screener/
├── sp500_screener.py       — data pipeline + dashboard generator
├── sp500_model.py          — XGBoost analyst rating classifier
├── sp500_tickers.txt       — full S&P 500 ticker list (504 stocks)
├── sp500_data.csv          — processed output (504 stocks, 20 features)
├── sp500_predictions.csv   — model predictions with buy probability
├── sp500_dashboard.html    — interactive browser dashboard
├── feature_importance.png  — XGBoost feature importance chart
├── shap_summary.png        — SHAP feature importance chart
└── README.md
```

---

## Part 1 — Stock screener & sector dashboard

### How to run

```bash
git clone https://github.com/jumma786/sp500-stock-screener
cd sp500-stock-screener
pip install yfinance pandas
python sp500_screener.py
start sp500_dashboard.html
```

Fetches 504 stocks one at a time (~40 minutes). Outputs `sp500_data.csv` and `sp500_dashboard.html`.

### Dashboard features

- **Sector heatmap** — 11 sectors with live stock count, % analyst buy, and avg P/E. Click any sector to filter
- **Bar charts** — avg P/E and avg dividend yield ranked by sector
- **Stock screener** — filter by sector, analyst rating, P/E band, dividend yield, profit margin
- **Sortable table** — 504 stocks with price, 1D change, P/E, dividend yield, profit margin, market cap, analyst rating

### Sector findings

| Sector | Stocks | Avg P/E | Avg Div % | Buy % |
|---|---|---|---|---|
| Technology | 9 | 31.7 | 1.5 | 89% |
| Financial Services | 9 | 21.1 | 1.6 | 78% |
| Healthcare | 9 | 36.6 | 2.4 | 89% |
| Consumer Cyclical | 5 | 93.3 | 1.5 | 100% |
| Industrials | 6 | 44.3 | 1.2 | 100% |
| Energy | 2 | 28.6 | 3.3 | 100% |

- Energy has 100% analyst buy consensus with the highest dividend yield
- Consumer Cyclical carries a 93x avg P/E driven by TSLA and AMZN growth premiums
- Financial Services is the most attractively valued at 21x P/E

---

## Part 2 — XGBoost analyst rating classifier

### Objective

Binary classification: predict whether a stock is rated **Buy** or **Hold** using 10 financial ratio features.

### Features

| Feature | Description |
|---|---|
| `pe_ratio` | Price / earnings |
| `price_to_book` | Price / book value |
| `div_yield_pct` | Dividend yield % |
| `earnings_growth` | YoY earnings growth |
| `debt_to_equity` | Leverage ratio |
| `roe_pct` | Return on equity |
| `profit_margin` | Net profit margin |
| `revenue_bn` | Annual revenue (£bn) |
| `beta` | Market sensitivity |
| `52w_position` | Price position in 52-week range (0–100%) |

### How to run

```bash
pip install xgboost shap scikit-learn matplotlib
python sp500_model.py
```

### Results

| Metric | Value |
|---|---|
| CV Accuracy | 69.3% |
| CV ROC-AUC | 0.697 |
| CV F1 (Buy) | 0.788 |
| Overfitting gap | 0.058 |
| Buy precision | 0.92 |
| Hold precision | 0.45 |
| Majority baseline | 78.8% |

### Feature importance (top 5)

1. `pe_ratio` — 16.3% — valuation is the strongest signal
2. `price_to_book` — 14.6% — asset valuation second
3. `div_yield_pct` — 14.0% — income profile third
4. `earnings_growth` — 12.0%
5. `debt_to_equity` — 11.9%

### Honest findings

The model does not beat the majority class baseline on accuracy (69.3% vs 78.8%). However, ROC-AUC of 0.697 confirms genuine discriminative ability beyond random chance (0.5).

**This is a meaningful finding:** financial ratios alone are not sufficient to predict analyst ratings. Analyst consensus reflects qualitative factors — management quality, earnings call tone, industry outlook, ESG positioning — that balance sheet ratios do not capture.

The overfitting gap of 0.058 confirms the model generalises well with the regularisation applied (`max_depth=2`, `subsample=0.8`, `reg_alpha=0.1`).

### Limitations

1. Point-in-time snapshot — no time series history
2. Analyst ratings are opinions, not return outcomes
3. 79% Buy base rate creates a high accuracy floor
4. 453 usable rows is small for a robust classifier
5. No qualitative features (management, ESG, sector outlook)

---

## Tech stack

| Layer | Tool |
|---|---|
| Data source | Yahoo Finance via `yfinance` |
| Data processing | Python, Pandas |
| ML model | XGBoost, Scikit-learn |
| Explainability | SHAP |
| Dashboard | Vanilla HTML/CSS/JavaScript |
| Environment | Anaconda Python 3.11 |

---

## About

Built by **Jumma Mohammad Teli** — Data Analyst & ML Engineer at UBS London.

Part of a broader financial analytics portfolio spanning Power BI dashboards, SQL analysis, XGBoost modelling, and MLOps pipelines.

[LinkedIn](https://linkedin.com/in/jumma-mohammad) · [GitHub](https://github.com/jumma786)
