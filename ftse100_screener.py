"""
S&P 500 Stock Screener & Sector Dashboard
==========================================
Free FMP plan compatible — fetches one ticker at a time.

Usage:
  conda activate mlops
  python sp500_screener.py --4oVpkbP9Z86VfhYGzUiGwBLZ6hSzoyHu
"""

import argparse
import os
import sys
import time
import requests
import pandas as pd
from datetime import datetime

BASE_URL = "https://financialmodelingprep.com/api/v3"

TICKERS = [
    "AAPL","MSFT","AMZN","NVDA","GOOGL","META","TSLA","JPM","UNH","XOM",
    "JNJ","V","PG","MA","HD","CVX","MRK","ABBV","PEP","KO",
    "AVGO","COST","WMT","BAC","TMO","MCD","ACN","LIN","ABT","CRM",
    "DHR","NEE","TXN","PM","UNP","RTX","HON","BMY","AMGN","LOW",
    "QCOM","IBM","GE","CAT","BA","GS","MS","BLK","SPGI","WFC"
]

SECTOR_FALLBACK = {
    "AAPL":"Technology","MSFT":"Technology","AMZN":"Consumer Discretionary",
    "NVDA":"Technology","GOOGL":"Communication Services","META":"Communication Services",
    "TSLA":"Consumer Discretionary","JPM":"Financials","UNH":"Health Care",
    "XOM":"Energy","JNJ":"Health Care","V":"Financials","PG":"Consumer Staples",
    "MA":"Financials","HD":"Consumer Discretionary","CVX":"Energy",
    "MRK":"Health Care","ABBV":"Health Care","PEP":"Consumer Staples",
    "KO":"Consumer Staples","AVGO":"Technology","COST":"Consumer Staples",
    "WMT":"Consumer Staples","BAC":"Financials","TMO":"Health Care",
    "MCD":"Consumer Discretionary","ACN":"Technology","LIN":"Materials",
    "ABT":"Health Care","CRM":"Technology","DHR":"Health Care","NEE":"Utilities",
    "TXN":"Technology","PM":"Consumer Staples","UNP":"Industrials",
    "RTX":"Industrials","HON":"Industrials","BMY":"Health Care","AMGN":"Health Care",
    "LOW":"Consumer Discretionary","QCOM":"Technology","IBM":"Technology",
    "GE":"Industrials","CAT":"Industrials","BA":"Industrials",
    "GS":"Financials","MS":"Financials","BLK":"Financials","SPGI":"Financials","WFC":"Financials"
}


def get(endpoint, key):
    url = f"{BASE_URL}/{endpoint}?apikey={key}"
    resp = requests.get(url, timeout=15)
    if resp.status_code == 429:
        print("  Rate limited — waiting 10s...")
        time.sleep(10)
        resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data[0] if isinstance(data, list) and data else data


def build_dataframe(key):
    rows = []
    total = len(TICKERS)
    for i, sym in enumerate(TICKERS, 1):
        print(f"  [{i}/{total}] {sym}", end="\r")
        try:
            q = get(f"quote/{sym}", key)
            if not q or isinstance(q, dict) and "Error" in str(q):
                continue

            try:
                prof = get(f"profile/{sym}", key)
            except Exception:
                prof = {}

            try:
                rat = get(f"rating/{sym}", key)
            except Exception:
                rat = {}

            price    = q.get("price") or 0
            last_div = (prof.get("lastDiv") or 0)
            div_yield = round(last_div / price * 100, 2) if price > 0 and last_div else 0

            rec = rat.get("ratingRecommendation", "")
            if not rec:
                score = rat.get("rating", 0) or 0
                rec = "Buy" if score >= 4 else "Hold" if score >= 3 else "Sell" if score > 0 else "N/A"

            rows.append({
                "ticker":         sym,
                "name":           (prof.get("companyName") or q.get("name") or sym)
                                  .replace(" Inc.","").replace(" Inc","")
                                  .replace(" Corp.","").replace(" Corp",""),
                "sector":         prof.get("sector") or SECTOR_FALLBACK.get(sym, "Other"),
                "price_usd":      round(price, 2),
                "change_pct":     round(q.get("changesPercentage") or 0, 2),
                "pe_ratio":       round(q.get("pe"), 1) if q.get("pe") and q.get("pe") > 0 else None,
                "div_yield_pct":  div_yield,
                "mkt_cap_usd":    q.get("marketCap") or prof.get("mktCap") or 0,
                "52w_high":       q.get("yearHigh"),
                "52w_low":        q.get("yearLow"),
                "analyst_rating": rec,
                "beta":           round(prof.get("beta"), 2) if prof.get("beta") else None,
            })
            time.sleep(0.25)  # stay within free tier rate limit

        except Exception as e:
            print(f"\n  Warning: {sym} failed — {e}")
            continue

    print(f"\nFetched {len(rows)} stocks successfully.")
    return pd.DataFrame(rows)


def sector_summary(df):
    grp = df.groupby("sector").agg(
        count=("ticker","count"),
        avg_pe=("pe_ratio","mean"),
        avg_div=("div_yield_pct","mean"),
        pct_buy=("analyst_rating", lambda x: round((x=="Buy").sum()/len(x)*100, 1)),
        total_mktcap=("mkt_cap_usd","sum")
    ).reset_index()
    grp["avg_pe"] = grp["avg_pe"].round(1)
    grp["avg_div"] = grp["avg_div"].round(2)
    grp["total_mktcap_bn"] = (grp["total_mktcap"] / 1e9).round(1)
    return grp.sort_values("count", ascending=False)


def build_html(df, summary, timestamp):
    stocks_json  = df[["ticker","name","sector","price_usd","change_pct","pe_ratio",
                        "div_yield_pct","mkt_cap_usd","analyst_rating","52w_high","52w_low","beta"]].to_json(orient="records")
    summary_json = summary.to_json(orient="records")
    avg_pe  = round(df["pe_ratio"].dropna().mean(), 1)
    buy_pct = round((df["analyst_rating"]=="Buy").sum() / len(df) * 100)
    avg_div = round(df["div_yield_pct"].mean(), 1)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>S&P 500 Screener — Jumma Mohammad Teli</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f8f8f6;color:#1a1a1a;font-size:14px}}
.hdr{{background:#fff;border-bottom:1px solid #e8e8e4;padding:1.25rem 2rem;display:flex;justify-content:space-between;align-items:center}}
.hdr h1{{font-size:18px;font-weight:600}}.hdr p{{font-size:12px;color:#888;margin-top:2px}}.hdr .ts{{font-size:12px;color:#888}}
.wrap{{padding:1.5rem 2rem}}
.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:1.5rem}}
.metric{{background:#fff;border:1px solid #e8e8e4;border-radius:8px;padding:1rem}}
.metric .lbl{{font-size:11px;color:#888;margin-bottom:4px;text-transform:uppercase;letter-spacing:.04em}}
.metric .val{{font-size:24px;font-weight:600}}.metric .sub{{font-size:11px;color:#aaa;margin-top:2px}}
.sec-lbl{{font-size:11px;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:.05em;margin-bottom:10px}}
.sgrid{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:1.5rem}}
.sc{{border-radius:8px;padding:10px 12px;cursor:pointer;border:2px solid transparent;transition:border-color .15s}}
.sc:hover,.sc.active{{border-color:#185FA5}}
.sc .sn{{font-size:12px;font-weight:600;margin-bottom:2px}}.sc .ss{{font-size:11px}}
.filters{{display:flex;gap:10px;margin-bottom:1rem;flex-wrap:wrap}}
.filters select,.filters input{{font-size:13px;padding:6px 10px;border:1px solid #ddd;border-radius:6px;background:#fff;height:34px}}
.filters input{{width:200px}}
.tw{{border:1px solid #e8e8e4;border-radius:8px;overflow:hidden;background:#fff;margin-bottom:1.5rem}}
table{{width:100%;border-collapse:collapse;table-layout:fixed}}
thead{{background:#f8f8f6}}
th{{font-size:11px;font-weight:600;color:#888;padding:10px 12px;text-align:left;border-bottom:1px solid #e8e8e4;cursor:pointer;white-space:nowrap;text-transform:uppercase}}
th:hover{{color:#1a1a1a}}
td{{font-size:13px;padding:10px 12px;border-bottom:1px solid #f0f0ec;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
tr:last-child td{{border-bottom:none}}tr:hover td{{background:#fafaf8}}
.badge{{display:inline-block;font-size:11px;font-weight:600;padding:2px 8px;border-radius:99px}}
.buy{{background:#e6f4d7;color:#2d6a04}}.hold{{background:#fef3c7;color:#92400e}}
.sell{{background:#fee2e2;color:#991b1b}}.na{{background:#f3f4f6;color:#6b7280}}
.pos{{color:#2d6a04}}.neg{{color:#dc2626}}
.empty{{padding:2rem;text-align:center;color:#888}}
.crow{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:1.5rem}}
.cbox{{background:#fff;border:1px solid #e8e8e4;border-radius:8px;padding:1rem 1.25rem}}
.ctitle{{font-size:12px;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:.04em;margin-bottom:12px}}
.brow{{display:flex;align-items:center;gap:8px;margin-bottom:8px}}
.bname{{font-size:11px;color:#888;width:130px;flex-shrink:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.btrack{{flex:1;background:#f3f4f6;border-radius:99px;height:8px;overflow:hidden}}
.bfill{{height:100%;border-radius:99px}}
.bval{{font-size:11px;color:#1a1a1a;width:42px;text-align:right;flex-shrink:0}}
footer{{text-align:center;padding:2rem;font-size:11px;color:#aaa}}
</style>
</head>
<body>
<div class="hdr">
  <div><h1>S&P 500 Stock Screener &amp; Sector Dashboard</h1>
  <p>Financial Modeling Prep · Live data · Jumma Mohammad Teli</p></div>
  <div class="ts">Updated: {timestamp}</div>
</div>
<div class="wrap">
  <div class="metrics">
    <div class="metric"><div class="lbl">Stocks</div><div class="val">{len(df)}</div><div class="sub">S&P 500 sample</div></div>
    <div class="metric"><div class="lbl">Avg P/E</div><div class="val">{avg_pe}</div><div class="sub">Price / earnings</div></div>
    <div class="metric"><div class="lbl">Buy consensus</div><div class="val">{buy_pct}%</div><div class="sub">Analyst buy rating</div></div>
    <div class="metric"><div class="lbl">Avg div yield</div><div class="val">{avg_div}%</div><div class="sub">Dividend yield</div></div>
  </div>
  <div class="sec-lbl">Sectors — click to filter</div>
  <div class="sgrid" id="sgrid"></div>
  <div class="crow">
    <div class="cbox"><div class="ctitle">Avg P/E by sector</div><div id="pe-chart"></div></div>
    <div class="cbox"><div class="ctitle">Avg dividend yield (%)</div><div id="div-chart"></div></div>
  </div>
  <div class="sec-lbl" style="margin-bottom:.75rem">Stock screener</div>
  <div class="filters">
    <input type="text" id="search" placeholder="Search ticker or company..." oninput="applyFilters()"/>
    <select id="f-sec" onchange="applyFilters()"><option value="">All sectors</option></select>
    <select id="f-rat" onchange="applyFilters()"><option value="">All ratings</option><option value="Buy">Buy</option><option value="Hold">Hold</option><option value="Sell">Sell</option></select>
    <select id="f-pe" onchange="applyFilters()"><option value="">Any P/E</option><option value="under15">P/E &lt; 15</option><option value="15to25">P/E 15-25</option><option value="over25">P/E &gt; 25</option></select>
    <select id="f-div" onchange="applyFilters()"><option value="">Any yield</option><option value="over3">Yield &gt; 3%</option><option value="over5">Yield &gt; 5%</option></select>
  </div>
  <div class="tw"><table>
    <thead><tr>
      <th style="width:70px" onclick="sortBy('ticker')">Ticker</th>
      <th style="width:155px" onclick="sortBy('name')">Company</th>
      <th style="width:135px" onclick="sortBy('sector')">Sector</th>
      <th style="width:80px" onclick="sortBy('price_usd')">Price ($)</th>
      <th style="width:75px" onclick="sortBy('change_pct')">1D %</th>
      <th style="width:60px" onclick="sortBy('pe_ratio')">P/E</th>
      <th style="width:70px" onclick="sortBy('div_yield_pct')">Div %</th>
      <th style="width:95px" onclick="sortBy('mkt_cap_usd')">Mkt cap</th>
      <th style="width:65px" onclick="sortBy('analyst_rating')">Rating</th>
    </tr></thead>
    <tbody id="tbody"></tbody>
  </table></div>
</div>
<footer>S&P 500 Stock Screener · Data: Financial Modeling Prep · Jumma Mohammad Teli · {timestamp}</footer>
<script>
const ALL={stocks_json};
const SUM={summary_json};
const SC={{"Financials":{{bg:"#E6F1FB",n:"#0C447C",s:"#185FA5"}},"Energy":{{bg:"#FAEEDA",n:"#633806",s:"#854F0B"}},"Health Care":{{bg:"#EAF3DE",n:"#27500A",s:"#3B6D11"}},"Consumer Staples":{{bg:"#EEEDFE",n:"#3C3489",s:"#534AB7"}},"Industrials":{{bg:"#E1F5EE",n:"#085041",s:"#0F6E56"}},"Materials":{{bg:"#FAECE7",n:"#712B13",s:"#993C1D"}},"Utilities":{{bg:"#FBEAF0",n:"#72243E",s:"#993556"}},"Technology":{{bg:"#F1EFE8",n:"#444441",s:"#5F5E5A"}},"Consumer Discretionary":{{bg:"#EAF3DE",n:"#173404",s:"#639922"}},"Real Estate":{{bg:"#FCEBEB",n:"#791F1F",s:"#A32D2D"}},"Communication Services":{{bg:"#E6F1FB",n:"#042C53",s:"#378ADD"}}}};
let fil=[...ALL],sc='',sd=1,col='ticker',asc='';
function init(){{
  const s=document.getElementById('f-sec');
  [...new Set(ALL.map(x=>x.sector))].sort().forEach(v=>{{const o=document.createElement('option');o.value=o.text=v;s.appendChild(o);}});
  buildSec();renderTable();
}}
function buildSec(){{
  const g=document.getElementById('sgrid');g.innerHTML='';
  SUM.forEach(s=>{{
    const c=SC[s.sector]||{{bg:'#f3f4f6',n:'#444',s:'#666'}};
    const d=document.createElement('div');
    d.className='sc'+(asc===s.sector?' active':'');d.style.background=c.bg;
    d.innerHTML=`<div class="sn" style="color:${{c.n}}">${{s.sector}}</div><div class="ss" style="color:${{c.s}}">${{s.count}} stocks · ${{s.pct_buy}}% buy · P/E ${{s.avg_pe||'N/A'}}</div>`;
    d.onclick=()=>{{asc=asc===s.sector?'':s.sector;document.getElementById('f-sec').value=asc;buildSec();applyFilters();}};
    g.appendChild(d);
  }});
  buildCharts();
}}
function buildCharts(){{
  const s1=[...SUM].sort((a,b)=>(b.avg_pe||0)-(a.avg_pe||0)),mp=Math.max(...s1.map(s=>s.avg_pe||0))||1;
  document.getElementById('pe-chart').innerHTML=s1.map(s=>{{const c=(SC[s.sector]||{{s:'#888'}}).s,p=s.avg_pe?(s.avg_pe/mp*100).toFixed(1):0;return`<div class="brow"><div class="bname">${{s.sector}}</div><div class="btrack"><div class="bfill" style="width:${{p}}%;background:${{c}}"></div></div><div class="bval">${{s.avg_pe||'—'}}</div></div>`;}}).join('');
  const s2=[...SUM].sort((a,b)=>b.avg_div-a.avg_div),md=Math.max(...s2.map(s=>s.avg_div))||1;
  document.getElementById('div-chart').innerHTML=s2.map(s=>{{const c=(SC[s.sector]||{{s:'#888'}}).s,p=(s.avg_div/md*100).toFixed(1);return`<div class="brow"><div class="bname">${{s.sector}}</div><div class="btrack"><div class="bfill" style="width:${{p}}%;background:${{c}}"></div></div><div class="bval">${{s.avg_div}}%</div></div>`;}}).join('');
}}
function applyFilters(){{
  const q=document.getElementById('search').value.toLowerCase(),sec=document.getElementById('f-sec').value,rat=document.getElementById('f-rat').value,peF=document.getElementById('f-pe').value,divF=document.getElementById('f-div').value;
  if(sec!==asc){{asc=sec;buildSec();}}
  fil=ALL.filter(s=>{{
    if(q&&!s.ticker.toLowerCase().includes(q)&&!s.name.toLowerCase().includes(q))return false;
    if(sec&&s.sector!==sec)return false;
    if(rat&&s.analyst_rating!==rat)return false;
    if(peF==='under15'&&(!s.pe_ratio||s.pe_ratio>=15))return false;
    if(peF==='15to25'&&(!s.pe_ratio||s.pe_ratio<15||s.pe_ratio>25))return false;
    if(peF==='over25'&&(!s.pe_ratio||s.pe_ratio<=25))return false;
    if(divF==='over3'&&s.div_yield_pct<3)return false;
    if(divF==='over5'&&s.div_yield_pct<5)return false;
    return true;
  }});renderTable();
}}
function sortBy(c){{if(col===c)sd*=-1;else{{col=c;sd=1;}}renderTable();}}
function fmtCap(v){{if(!v)return'—';if(v>=1e12)return'$'+(v/1e12).toFixed(2)+'T';if(v>=1e9)return'$'+(v/1e9).toFixed(1)+'B';return'—';}}
function renderTable(){{
  const src=[...fil].sort((a,b)=>{{let va=a[col],vb=b[col];if(va==null)return 1;if(vb==null)return-1;if(typeof va==='string')return va.localeCompare(vb)*sd;return(va-vb)*sd;}});
  if(!src.length){{document.getElementById('tbody').innerHTML='<tr><td colspan="9" class="empty">No stocks match filters</td></tr>';return;}}
  document.getElementById('tbody').innerHTML=src.map(s=>{{
    const chg=s.change_pct>=0?`<span class="pos">+${{s.change_pct.toFixed(2)}}%</span>`:`<span class="neg">${{s.change_pct.toFixed(2)}}%</span>`;
    const pe=s.pe_ratio?s.pe_ratio.toFixed(1):'<span style="color:#ccc">—</span>';
    const bc=s.analyst_rating==='Buy'?'buy':s.analyst_rating==='Sell'?'sell':s.analyst_rating==='N/A'?'na':'hold';
    return`<tr><td><strong>${{s.ticker}}</strong></td><td title="${{s.name}}">${{s.name}}</td><td style="color:#888;font-size:11px">${{s.sector}}</td><td>$${{s.price_usd?s.price_usd.toFixed(2):'—'}}</td><td>${{chg}}</td><td>${{pe}}</td><td>${{s.div_yield_pct?s.div_yield_pct.toFixed(1)+'%':'—'}}</td><td>${{fmtCap(s.mkt_cap_usd)}}</td><td><span class="badge ${{bc}}">${{s.analyst_rating}}</span></td></tr>`;
  }}).join('');
}}
init();
</script>
</body></html>"""


def main():
    parser = argparse.ArgumentParser(description="S&P 500 Stock Screener via FMP API")
    parser.add_argument("--key", required=True, help="Your FMP API key")
    parser.add_argument("--out", default=".", help="Output directory")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    timestamp = datetime.now().strftime("%d %b %Y %H:%M")

    print(f"\nS&P 500 Stock Screener")
    print(f"{'='*40}")
    print(f"Fetching {len(TICKERS)} stocks from FMP (one at a time)...\n")

    df = build_dataframe(args.key)
    if df.empty:
        print("No data fetched. Check your API key.")
        sys.exit(1)

    summary = sector_summary(df)

    csv_path  = os.path.join(args.out, "sp500_data.csv")
    html_path = os.path.join(args.out, "sp500_dashboard.html")

    df.to_csv(csv_path, index=False)
    print(f"Saved: {csv_path}")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(build_html(df, summary, timestamp))
    print(f"Saved: {html_path}")

    print(f"\n{'='*40}")
    print(f"Done. {len(df)} stocks loaded.\n")
    print(summary[["sector","count","avg_pe","avg_div","pct_buy","total_mktcap_bn"]].to_string(index=False))
    print(f"\nOpen sp500_dashboard.html in your browser.")

if __name__ == "__main__":
    main()