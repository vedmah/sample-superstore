"""
India Superstore — Live Business Intelligence Dashboard
Flask + Chart.js + RAG (Claude API)
Auto-simulates new orders every few seconds like a trading feed
"""

import os, json, random, threading, time, datetime, math
from collections import deque
import pandas as pd
import numpy as np
from flask import Flask, jsonify, render_template_string, request

# ── Load dataset ────────────────────────────────────────────────────────────
CSV_PATH = os.path.join(os.path.dirname(__file__), "IndiaSuperstore.csv")
BASE_DF  = pd.read_csv(CSV_PATH, parse_dates=["Order Date", "Ship Date"])

# ── Live order feed (ring buffer – last 200 synthetic orders) ────────────────
LIVE_ORDERS   = deque(maxlen=200)
LIVE_LOCK     = threading.Lock()
LIVE_METRICS  = {
    "total_sales":   float(BASE_DF["Sales"].sum()),
    "total_profit":  float(BASE_DF["Profit"].sum()),
    "total_orders":  int(len(BASE_DF)),
    "total_qty":     int(BASE_DF["Quantity"].sum()),
    "last_sale":     0.0,
    "last_profit":   0.0,
    "ticker":        [],   # last 60 sale ticks for sparkline
    "profit_ticker": [],
}

PRODUCTS   = BASE_DF["Product Name"].unique().tolist()
CATEGORIES = BASE_DF["Category"].unique().tolist()
SUBCATS    = BASE_DF["Sub-Category"].unique().tolist()
SEGMENTS   = BASE_DF["Segment"].unique().tolist()
REGIONS    = BASE_DF["Region"].unique().tolist()
CITIES     = BASE_DF["City"].unique().tolist()

ORDER_COUNTER = {"n": int(BASE_DF["Order ID"].str.extract(r"(\d+)")[0].max()) + 1}

def make_order():
    cat   = random.choice(CATEGORIES)
    sub   = random.choice(BASE_DF[BASE_DF["Category"]==cat]["Sub-Category"].unique().tolist())
    prod  = random.choice(BASE_DF[BASE_DF["Sub-Category"]==sub]["Product Name"].unique().tolist())
    qty   = random.randint(1, 15)
    price = round(random.uniform(200, 15000), 2)
    disc  = round(random.choice([0, 0, 0, 0.1, 0.2, 0.3, 0.4, 0.5]), 2)
    sales = round(price * qty * (1 - disc), 2)
    margin= random.uniform(-0.2, 0.45)
    profit= round(sales * margin, 2)
    region= random.choice(REGIONS)
    city  = random.choice(CITIES)
    seg   = random.choice(SEGMENTS)
    oid   = f"IND-{ORDER_COUNTER['n']:05d}"
    ORDER_COUNTER["n"] += 1
    now   = datetime.datetime.now()
    return {
        "order_id":    oid,
        "timestamp":   now.isoformat(),
        "time_str":    now.strftime("%H:%M:%S"),
        "category":    cat,
        "sub_category":sub,
        "product":     prod[:45] + ("…" if len(prod) > 45 else ""),
        "quantity":    qty,
        "sales":       sales,
        "profit":      profit,
        "discount":    disc,
        "region":      region,
        "city":        city,
        "segment":     seg,
        "margin_pct":  round(margin * 100, 1),
    }

def order_generator():
    """Background thread — emits 1 new order every 2-4 seconds."""
    while True:
        order = make_order()
        with LIVE_LOCK:
            LIVE_ORDERS.appendleft(order)
            LIVE_METRICS["total_sales"]  += order["sales"]
            LIVE_METRICS["total_profit"] += order["profit"]
            LIVE_METRICS["total_orders"] += 1
            LIVE_METRICS["total_qty"]    += order["quantity"]
            LIVE_METRICS["last_sale"]     = order["sales"]
            LIVE_METRICS["last_profit"]   = order["profit"]
            ticks = LIVE_METRICS["ticker"]
            ticks.append(round(LIVE_METRICS["total_sales"] / 1e6, 4))
            if len(ticks) > 60: ticks.pop(0)
            pt = LIVE_METRICS["profit_ticker"]
            pt.append(round(LIVE_METRICS["total_profit"] / 1e6, 4))
            if len(pt) > 60: pt.pop(0)
        time.sleep(random.uniform(1.5, 3.5))

threading.Thread(target=order_generator, daemon=True).start()

# ── Pre-aggregate historical data for charts ─────────────────────────────────
def build_aggregates():
    df = BASE_DF.copy()
    df["Month"] = df["Order Date"].dt.to_period("M").astype(str)
    df["Year"]  = df["Order Date"].dt.year.astype(str)
    df["Week"]  = df["Order Date"].dt.to_period("W").astype(str)

    monthly = (df.groupby("Month")
                 .agg(Sales=("Sales","sum"), Profit=("Profit","sum"), Orders=("Order ID","count"))
                 .reset_index()
                 .tail(24))

    by_cat  = df.groupby("Category").agg(Sales=("Sales","sum"), Profit=("Profit","sum")).reset_index()
    by_sub  = df.groupby("Sub-Category").agg(Sales=("Sales","sum"), Profit=("Profit","sum")).reset_index().nlargest(10,"Sales")
    by_reg  = df.groupby("Region").agg(Sales=("Sales","sum"), Profit=("Profit","sum"), Orders=("Order ID","count")).reset_index()
    by_seg  = df.groupby("Segment").agg(Sales=("Sales","sum"), Profit=("Profit","sum")).reset_index()
    by_city = df.groupby("City").agg(Sales=("Sales","sum")).reset_index().nlargest(10,"Sales")
    by_ship = df.groupby("Ship Mode").agg(Orders=("Order ID","count")).reset_index()

    daily   = (df.groupby(df["Order Date"].dt.date)
                 .agg(Sales=("Sales","sum"), Profit=("Profit","sum"))
                 .reset_index()
                 .tail(90))
    daily.columns = ["Date","Sales","Profit"]
    daily["Date"] = daily["Date"].astype(str)

    # YoY
    yoy = df.groupby("Year").agg(Sales=("Sales","sum"), Profit=("Profit","sum"), Orders=("Order ID","count")).reset_index()

    return dict(
        monthly=monthly.to_dict("records"),
        by_cat =by_cat.to_dict("records"),
        by_sub =by_sub.to_dict("records"),
        by_reg =by_reg.to_dict("records"),
        by_seg =by_seg.to_dict("records"),
        by_city=by_city.to_dict("records"),
        by_ship=by_ship.to_dict("records"),
        daily  =daily.to_dict("records"),
        yoy    =yoy.to_dict("records"),
    )

AGG = build_aggregates()

# ── RAG helpers ──────────────────────────────────────────────────────────────
CONTEXT_SUMMARY = f"""
India Superstore Business Data Summary (RAG Context):
- Date Range: {BASE_DF['Order Date'].min().date()} to {BASE_DF['Order Date'].max().date()}
- Total Historical Orders: {len(BASE_DF):,}
- Total Historical Sales: ₹{BASE_DF['Sales'].sum()/1e6:.2f}M
- Total Historical Profit: ₹{BASE_DF['Profit'].sum()/1e6:.2f}M
- Overall Profit Margin: {BASE_DF['Profit'].sum()/BASE_DF['Sales'].sum()*100:.1f}%
- Categories: {', '.join(BASE_DF['Category'].unique())}
- Regions: {', '.join(BASE_DF['Region'].unique())}
- Segments: {', '.join(BASE_DF['Segment'].unique())}
- Top Category by Sales: {BASE_DF.groupby('Category')['Sales'].sum().idxmax()}
- Top Region by Sales: {BASE_DF.groupby('Region')['Sales'].sum().idxmax()}
- Most Profitable Segment: {BASE_DF.groupby('Segment')['Profit'].sum().idxmax()}
- Best Sub-Category: {BASE_DF.groupby('Sub-Category')['Sales'].sum().idxmax()}
- Avg Order Value: ₹{BASE_DF['Sales'].mean():.0f}
- Avg Discount: {BASE_DF['Discount'].mean()*100:.1f}%
- High Discount (>40%) hurts margin — {(BASE_DF['Discount']>0.4).sum()} orders at >40% discount
- Furniture has the lowest margin among categories.
"""

# ── Flask app ────────────────────────────────────────────────────────────────
app = Flask(__name__)

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>India Superstore — Live BI Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
:root{
  --bg:#0a0e1a;--surface:#111827;--card:#151f2e;--border:#1e2d45;
  --accent:#00d4ff;--green:#00ff88;--red:#ff4757;--yellow:#ffd700;
  --purple:#a855f7;--orange:#f97316;--text:#e2e8f0;--muted:#64748b;
  --font:'Inter',system-ui,sans-serif;
}
body{background:var(--bg);color:var(--text);font-family:var(--font);min-height:100vh;}

/* ── Header ── */
header{background:linear-gradient(135deg,#0d1b2a,#1a2744);
  border-bottom:1px solid var(--border);padding:12px 24px;
  display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;}
.logo{display:flex;align-items:center;gap:12px;}
.logo-icon{width:36px;height:36px;background:linear-gradient(135deg,var(--accent),var(--purple));
  border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:18px;}
.logo h1{font-size:18px;font-weight:700;letter-spacing:.5px;}
.logo span{font-size:11px;color:var(--muted);display:block;}
.live-badge{display:flex;align-items:center;gap:8px;background:rgba(0,255,136,.1);
  border:1px solid rgba(0,255,136,.3);border-radius:20px;padding:6px 14px;font-size:12px;color:var(--green);}
.pulse{width:8px;height:8px;border-radius:50%;background:var(--green);animation:pulse 1.2s infinite;}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1);}50%{opacity:.4;transform:scale(.8);}}
.header-right{display:flex;align-items:center;gap:16px;}
#clock{font-size:13px;color:var(--muted);font-family:monospace;}

/* ── Layout ── */
main{padding:20px 24px;max-width:1800px;margin:0 auto;}
.section-title{font-size:13px;font-weight:600;color:var(--muted);letter-spacing:1.2px;
  text-transform:uppercase;margin:24px 0 12px;padding-left:4px;border-left:3px solid var(--accent);}

/* ── KPI Ticker Bar ── */
.ticker-bar{background:var(--surface);border:1px solid var(--border);border-radius:10px;
  padding:14px 20px;margin-bottom:16px;overflow:hidden;position:relative;}
.ticker-scroll{display:flex;gap:32px;animation:tickerscroll 30s linear infinite;width:max-content;}
@keyframes tickerscroll{0%{transform:translateX(0);}100%{transform:translateX(-50%);}}
.ticker-item{display:flex;align-items:center;gap:8px;white-space:nowrap;font-size:13px;}
.ticker-label{color:var(--muted);}
.ticker-val{font-weight:700;font-family:monospace;}
.up{color:var(--green);}
.dn{color:var(--red);}

/* ── KPI Cards ── */
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin-bottom:16px;}
.kpi-card{background:var(--card);border:1px solid var(--border);border-radius:12px;
  padding:16px 20px;position:relative;overflow:hidden;transition:border-color .3s;}
.kpi-card:hover{border-color:var(--accent);}
.kpi-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--accent),var(--purple));}
.kpi-label{font-size:11px;color:var(--muted);font-weight:600;letter-spacing:.8px;text-transform:uppercase;}
.kpi-val{font-size:26px;font-weight:800;font-family:monospace;margin:6px 0 2px;
  background:linear-gradient(135deg,#fff,var(--accent));-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.kpi-sub{font-size:11px;display:flex;align-items:center;gap:4px;}
.kpi-change{font-size:20px;position:absolute;right:16px;top:16px;opacity:.15;}
.flash-green{animation:flashg .6s;}
.flash-red{animation:flashr .6s;}
@keyframes flashg{0%,100%{background:transparent;}50%{background:rgba(0,255,136,.12);}}
@keyframes flashr{0%,100%{background:transparent;}50%{background:rgba(255,71,87,.12);}}

/* ── Sparkline row ── */
.spark-row{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px;}
.spark-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:14px 18px;}
.spark-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;}
.spark-title{font-size:12px;color:var(--muted);}
.spark-cur{font-size:18px;font-weight:700;font-family:monospace;}

/* ── Chart grid ── */
.chart-grid-2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px;}
.chart-grid-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:16px;}
.chart-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:18px;position:relative;}
.chart-card h3{font-size:13px;font-weight:600;color:var(--text);margin-bottom:14px;display:flex;align-items:center;gap:8px;}
.chart-card h3 .dot{width:8px;height:8px;border-radius:50%;}
canvas{max-height:220px;}

/* ── Live Order Feed ── */
.order-feed{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:18px;}
.order-feed h3{font-size:13px;font-weight:600;margin-bottom:12px;display:flex;align-items:center;gap:8px;}
.order-table{width:100%;border-collapse:collapse;font-size:12px;}
.order-table th{color:var(--muted);text-align:left;padding:6px 10px;border-bottom:1px solid var(--border);
  font-weight:600;font-size:11px;letter-spacing:.6px;text-transform:uppercase;}
.order-table td{padding:7px 10px;border-bottom:1px solid rgba(30,45,69,.5);font-family:monospace;}
.order-table tr:first-child td{background:rgba(0,212,255,.04);}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:600;}
.badge-green{background:rgba(0,255,136,.15);color:var(--green);}
.badge-red{background:rgba(255,71,87,.15);color:var(--red);}
.badge-blue{background:rgba(0,212,255,.15);color:var(--accent);}

/* ── RAG Chat ── */
.rag-section{background:var(--card);border:1px solid var(--border);border-radius:12px;
  padding:20px;margin-bottom:24px;}
.rag-section h3{font-size:13px;font-weight:600;margin-bottom:14px;display:flex;align-items:center;gap:8px;}
.chat-window{height:240px;overflow-y:auto;background:var(--surface);border-radius:8px;
  padding:12px;margin-bottom:12px;border:1px solid var(--border);}
.msg{margin-bottom:12px;display:flex;flex-direction:column;gap:2px;}
.msg-user{align-items:flex-end;}
.msg-bubble{max-width:85%;padding:10px 14px;border-radius:10px;font-size:13px;line-height:1.5;}
.msg-user .msg-bubble{background:linear-gradient(135deg,#1e3a5f,#1a2d4a);color:var(--accent);}
.msg-ai .msg-bubble{background:rgba(30,45,69,.6);color:var(--text);border:1px solid var(--border);}
.msg-time{font-size:10px;color:var(--muted);}
.rag-input{display:flex;gap:10px;}
.rag-input input{flex:1;background:var(--surface);border:1px solid var(--border);border-radius:8px;
  padding:10px 14px;color:var(--text);font-size:13px;outline:none;}
.rag-input input:focus{border-color:var(--accent);}
.rag-input button{background:linear-gradient(135deg,var(--accent),var(--purple));border:none;
  border-radius:8px;padding:10px 20px;color:#fff;font-weight:600;cursor:pointer;font-size:13px;}
.suggestions{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px;}
.sug-btn{background:rgba(0,212,255,.08);border:1px solid rgba(0,212,255,.2);border-radius:20px;
  padding:4px 12px;font-size:11px;color:var(--accent);cursor:pointer;}
.sug-btn:hover{background:rgba(0,212,255,.18);}
.thinking{display:flex;align-items:center;gap:6px;color:var(--muted);font-size:12px;padding:10px 14px;}
.dot-anim span{animation:dotbounce 1.2s infinite;}
.dot-anim span:nth-child(2){animation-delay:.2s;}
.dot-anim span:nth-child(3){animation-delay:.4s;}
@keyframes dotbounce{0%,100%{opacity:.3;}50%{opacity:1;}}

/* ── Footer ── */
footer{text-align:center;padding:20px;color:var(--muted);font-size:11px;border-top:1px solid var(--border);}

@media(max-width:900px){
  .chart-grid-2,.chart-grid-3,.spark-row{grid-template-columns:1fr;}
  .kpi-grid{grid-template-columns:repeat(2,1fr);}
}
</style>
</head>
<body>

<header>
  <div class="logo">
    <div class="logo-icon">🛍</div>
    <div>
      <h1>India Superstore</h1>
      <span>Live Business Intelligence Dashboard</span>
    </div>
  </div>
  <div class="header-right">
    <div id="clock">--:--:--</div>
    <div class="live-badge"><div class="pulse"></div> LIVE FEED ACTIVE</div>
  </div>
</header>

<main>

<!-- Ticker -->
<div class="ticker-bar" style="margin-top:12px;">
  <div class="ticker-scroll" id="tickerScroll">
    <!-- duplicated for seamless loop -->
  </div>
</div>

<!-- KPI Cards -->
<div class="section-title">📊 Key Performance Indicators</div>
<div class="kpi-grid">
  <div class="kpi-card" id="kpiSales">
    <div class="kpi-change">💰</div>
    <div class="kpi-label">Total Revenue</div>
    <div class="kpi-val" id="valSales">—</div>
    <div class="kpi-sub"><span class="up" id="lastSale">—</span></div>
  </div>
  <div class="kpi-card" id="kpiProfit">
    <div class="kpi-change">📈</div>
    <div class="kpi-label">Total Profit</div>
    <div class="kpi-val" id="valProfit">—</div>
    <div class="kpi-sub"><span id="lastProfit">—</span></div>
  </div>
  <div class="kpi-card" id="kpiOrders">
    <div class="kpi-change">📦</div>
    <div class="kpi-label">Total Orders</div>
    <div class="kpi-val" id="valOrders">—</div>
    <div class="kpi-sub"><span class="up">↑ live updates</span></div>
  </div>
  <div class="kpi-card">
    <div class="kpi-change">🎯</div>
    <div class="kpi-label">Profit Margin</div>
    <div class="kpi-val" id="valMargin">—</div>
    <div class="kpi-sub"><span class="up">Net overall</span></div>
  </div>
  <div class="kpi-card">
    <div class="kpi-change">🛒</div>
    <div class="kpi-label">Avg Order Value</div>
    <div class="kpi-val" id="valAOV">—</div>
    <div class="kpi-sub"><span class="muted">per transaction</span></div>
  </div>
  <div class="kpi-card">
    <div class="kpi-change">📮</div>
    <div class="kpi-label">Total Units</div>
    <div class="kpi-val" id="valQty">—</div>
    <div class="kpi-sub"><span class="up">items sold</span></div>
  </div>
</div>

<!-- Sparklines -->
<div class="spark-row">
  <div class="spark-card">
    <div class="spark-header">
      <span class="spark-title">Revenue Pulse (₹M) — last 60 ticks</span>
      <span class="spark-cur up" id="sparkSalesCur">—</span>
    </div>
    <canvas id="sparkSales" height="60"></canvas>
  </div>
  <div class="spark-card">
    <div class="spark-header">
      <span class="spark-title">Profit Pulse (₹M) — last 60 ticks</span>
      <span class="spark-cur" id="sparkProfCur">—</span>
    </div>
    <canvas id="sparkProfit" height="60"></canvas>
  </div>
</div>

<!-- RAG Chat -->
<div class="section-title">🤖 AI Business Analyst (RAG)</div>
<div class="rag-section">
  <h3><span class="dot" style="background:var(--purple)"></span>Ask anything about your business data</h3>
  <div class="suggestions">
    <span class="sug-btn" onclick="askSug(this)">Which category drives most revenue?</span>
    <span class="sug-btn" onclick="askSug(this)">What's the profit margin trend?</span>
    <span class="sug-btn" onclick="askSug(this)">Which region is underperforming?</span>
    <span class="sug-btn" onclick="askSug(this)">Top growth opportunities?</span>
    <span class="sug-btn" onclick="askSug(this)">Impact of discounts on profit?</span>
    <span class="sug-btn" onclick="askSug(this)">Best performing segment?</span>
  </div>
  <div class="chat-window" id="chatWindow">
    <div class="msg msg-ai">
      <div class="msg-bubble">👋 Hi! I'm your AI Business Analyst. I have full context of your India Superstore data — 16,000+ orders, ₹493M+ in revenue. Ask me anything about trends, performance, or strategy!</div>
      <span class="msg-time">AI Analyst • ready</span>
    </div>
  </div>
  <div class="rag-input">
    <input id="ragInput" placeholder="e.g. Which sub-category has the best margin?" onkeydown="if(event.key==='Enter')sendRag()"/>
    <button onclick="sendRag()">Ask AI →</button>
  </div>
</div>

<!-- Charts Row 1 -->
<div class="section-title">📅 Revenue & Profit Trends</div>
<div class="chart-grid-2">
  <div class="chart-card">
    <h3><span class="dot" style="background:var(--accent)"></span>Monthly Revenue & Profit (₹)</h3>
    <canvas id="chartMonthly"></canvas>
  </div>
  <div class="chart-card">
    <h3><span class="dot" style="background:var(--green)"></span>Daily Sales — Last 90 Days</h3>
    <canvas id="chartDaily"></canvas>
  </div>
</div>

<!-- Charts Row 2 -->
<div class="section-title">🗂 Category & Segment Analysis</div>
<div class="chart-grid-3">
  <div class="chart-card">
    <h3><span class="dot" style="background:var(--yellow)"></span>Sales by Category</h3>
    <canvas id="chartCat"></canvas>
  </div>
  <div class="chart-card">
    <h3><span class="dot" style="background:var(--purple)"></span>Sales by Segment</h3>
    <canvas id="chartSeg"></canvas>
  </div>
  <div class="chart-card">
    <h3><span class="dot" style="background:var(--orange)"></span>Ship Mode Distribution</h3>
    <canvas id="chartShip"></canvas>
  </div>
</div>

<!-- Charts Row 3 -->
<div class="section-title">🗺 Regional & Sub-Category Performance</div>
<div class="chart-grid-2">
  <div class="chart-card">
    <h3><span class="dot" style="background:var(--red)"></span>Sales & Profit by Region</h3>
    <canvas id="chartReg"></canvas>
  </div>
  <div class="chart-card">
    <h3><span class="dot" style="background:var(--green)"></span>Top 10 Sub-Categories by Sales</h3>
    <canvas id="chartSub"></canvas>
  </div>
</div>

<!-- YoY -->
<div class="section-title">📆 Year-over-Year Growth</div>
<div class="chart-grid-2">
  <div class="chart-card">
    <h3><span class="dot" style="background:var(--accent)"></span>Annual Revenue</h3>
    <canvas id="chartYoY"></canvas>
  </div>
  <div class="chart-card">
    <h3><span class="dot" style="background:var(--purple)"></span>Annual Profit</h3>
    <canvas id="chartYoYProfit"></canvas>
  </div>
</div>

<!-- Top Cities -->
<div class="section-title">🏙 Top 10 Cities by Revenue</div>
<div class="chart-card" style="margin-bottom:16px;">
  <canvas id="chartCity" style="max-height:180px;"></canvas>
</div>

<!-- Live Order Feed -->
<div class="section-title">⚡ Live Order Feed</div>
<div class="order-feed">
  <h3><span class="dot" style="background:var(--green)"></span>Real-Time Incoming Orders</h3>
  <div style="overflow-x:auto;">
    <table class="order-table">
      <thead>
        <tr>
          <th>Time</th><th>Order ID</th><th>Category</th><th>Product</th>
          <th>Qty</th><th>Sales ₹</th><th>Profit ₹</th><th>Margin</th>
          <th>Region</th><th>Segment</th>
        </tr>
      </thead>
      <tbody id="orderBody"></tbody>
    </table>
  </div>
</div>

</main>
<footer>India Superstore Live BI Dashboard • Real-time data simulation • Powered by AI Analytics</footer>

<script>
// ── Chart.js defaults ────────────────────────────────────────────────────────
Chart.defaults.color = '#64748b';
Chart.defaults.borderColor = '#1e2d45';
Chart.defaults.font.family = 'Inter, system-ui, sans-serif';
Chart.defaults.font.size = 11;

const COLORS = ['#00d4ff','#00ff88','#a855f7','#f97316','#ffd700','#ff4757','#06b6d4','#34d399'];

function fmt(n,dec=0){
  if(n>=1e7) return '₹'+(n/1e7).toFixed(1)+'Cr';
  if(n>=1e5) return '₹'+(n/1e5).toFixed(1)+'L';
  return '₹'+n.toLocaleString('en-IN',{maximumFractionDigits:dec});
}
function fmtK(n){if(n>=1000)return (n/1000).toFixed(1)+'K';return n.toFixed(0);}

// ── Clock ────────────────────────────────────────────────────────────────────
setInterval(()=>{
  document.getElementById('clock').textContent=new Date().toLocaleTimeString('en-IN');
},1000);

// ── Ticker ────────────────────────────────────────────────────────────────────
function buildTicker(m){
  const items=[
    `💰 Revenue: ${fmt(m.total_sales)}`,
    `📈 Profit: ${fmt(m.total_profit)}`,
    `📦 Orders: ${m.total_orders.toLocaleString()}`,
    `🛒 Last Sale: ${fmt(m.last_sale)}`,
    `💵 Last Profit: ${m.last_profit>=0?'▲':'▼'} ${fmt(Math.abs(m.last_profit))}`,
    `🎯 Margin: ${(m.total_profit/m.total_sales*100).toFixed(1)}%`,
    `📮 Units: ${fmtK(m.total_qty)}`,
    `⚡ AOV: ${fmt(m.total_sales/m.total_orders)}`,
  ];
  const doubled=[...items,...items];
  const ts=document.getElementById('tickerScroll');
  ts.innerHTML=doubled.map(t=>`<span class="ticker-item"><span class="ticker-val up">${t}</span></span>`).join('');
}

// ── Sparklines ────────────────────────────────────────────────────────────────
let sparkSalesChart, sparkProfChart;
function initSparks(){
  const cfg=(color,label)=>({
    type:'line',
    data:{labels:[],datasets:[{data:[],borderColor:color,borderWidth:1.5,
      fill:true,backgroundColor:color+'22',pointRadius:0,tension:.4}]},
    options:{animation:false,plugins:{legend:{display:false}},
      scales:{x:{display:false},y:{display:false}},responsive:true,maintainAspectRatio:false}
  });
  sparkSalesChart=new Chart(document.getElementById('sparkSales'),cfg('#00d4ff','Revenue'));
  sparkProfChart =new Chart(document.getElementById('sparkProfit'),cfg('#00ff88','Profit'));
}
function updateSparks(m){
  const ticks=m.ticker, pt=m.profit_ticker;
  const labels=ticks.map((_,i)=>i);
  sparkSalesChart.data.labels=labels;
  sparkSalesChart.data.datasets[0].data=ticks;
  sparkSalesChart.update('none');
  sparkProfChart.data.labels=labels;
  sparkProfChart.data.datasets[0].data=pt;
  sparkProfChart.data.datasets[0].borderColor=pt[pt.length-1]>=0?'#00ff88':'#ff4757';
  sparkProfChart.data.datasets[0].backgroundColor=(pt[pt.length-1]>=0?'#00ff88':'#ff4757')+'22';
  sparkProfChart.update('none');
  document.getElementById('sparkSalesCur').textContent='₹'+(ticks[ticks.length-1]||0).toFixed(2)+'M';
  const pv=pt[pt.length-1]||0;
  const pc=document.getElementById('sparkProfCur');
  pc.textContent='₹'+pv.toFixed(2)+'M';
  pc.className='spark-cur '+(pv>=0?'up':'dn');
}

// ── KPI update ────────────────────────────────────────────────────────────────
let prevSales=0;
function updateKPIs(m){
  const s=m.total_sales, p=m.total_profit;
  document.getElementById('valSales').textContent=fmt(s);
  document.getElementById('valProfit').textContent=fmt(p);
  document.getElementById('valOrders').textContent=m.total_orders.toLocaleString();
  document.getElementById('valMargin').textContent=(p/s*100).toFixed(1)+'%';
  document.getElementById('valAOV').textContent=fmt(s/m.total_orders);
  document.getElementById('valQty').textContent=fmtK(m.total_qty);
  const ls=document.getElementById('lastSale');
  ls.textContent='Last: '+fmt(m.last_sale);
  ls.className=m.last_sale>0?'up':'dn';
  const lp=document.getElementById('lastProfit');
  lp.textContent=(m.last_profit>=0?'▲ ':'▼ ')+fmt(Math.abs(m.last_profit));
  lp.className=m.last_profit>=0?'up':'dn';
  // flash card
  const card=document.getElementById('kpiSales');
  const changed=s!==prevSales;
  if(changed){card.classList.add('flash-green');setTimeout(()=>card.classList.remove('flash-green'),600);}
  prevSales=s;
}

// ── Order feed ────────────────────────────────────────────────────────────────
let knownOrders=new Set();
function renderOrders(orders){
  const tbody=document.getElementById('orderBody');
  let html='';
  orders.slice(0,12).forEach(o=>{
    const isNew=!knownOrders.has(o.order_id);
    const pc=o.profit>=0?'badge-green':'badge-red';
    const mc=o.margin_pct>=0?'up':'dn';
    html+=`<tr style="${isNew?'animation:flashg .8s;':''}">
      <td>${o.time_str}</td>
      <td><span class="badge badge-blue">${o.order_id}</span></td>
      <td>${o.category}</td>
      <td style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${o.product}</td>
      <td>${o.quantity}</td>
      <td class="up">${fmt(o.sales)}</td>
      <td><span class="badge ${pc}">${o.profit>=0?'+':''}${fmt(o.profit)}</span></td>
      <td class="${mc}">${o.margin_pct}%</td>
      <td>${o.region}</td>
      <td>${o.segment}</td>
    </tr>`;
    knownOrders.add(o.order_id);
  });
  tbody.innerHTML=html;
}

// ── Static charts ─────────────────────────────────────────────────────────────
let chartsInited=false;
function initCharts(agg){
  // Monthly
  const mLabels=agg.monthly.map(r=>r.Month);
  new Chart('chartMonthly',{type:'bar',data:{
    labels:mLabels,
    datasets:[
      {label:'Sales',data:agg.monthly.map(r=>r.Sales),backgroundColor:'#00d4ff44',borderColor:'#00d4ff',borderWidth:1.5,yAxisID:'y'},
      {label:'Profit',data:agg.monthly.map(r=>r.Profit),type:'line',borderColor:'#00ff88',borderWidth:2,pointRadius:2,tension:.4,yAxisID:'y1',fill:false}
    ]
  },options:{responsive:true,maintainAspectRatio:true,
    scales:{y:{ticks:{callback:v=>fmt(v)}},y1:{position:'right',grid:{drawOnChartArea:false},ticks:{callback:v=>fmt(v)}}},
    plugins:{legend:{position:'top',labels:{boxWidth:10}}}}});

  // Daily
  new Chart('chartDaily',{type:'line',data:{
    labels:agg.daily.map(r=>r.Date.slice(5)),
    datasets:[
      {label:'Sales',data:agg.daily.map(r=>r.Sales),borderColor:'#a855f7',fill:true,backgroundColor:'#a855f722',pointRadius:0,tension:.4},
      {label:'Profit',data:agg.daily.map(r=>r.Profit),borderColor:'#00ff88',fill:false,pointRadius:0,tension:.4}
    ]
  },options:{responsive:true,maintainAspectRatio:true,
    scales:{x:{ticks:{maxTicksLimit:10}},y:{ticks:{callback:v=>fmt(v)}}},
    plugins:{legend:{position:'top',labels:{boxWidth:10}}}}});

  // Category donut
  new Chart('chartCat',{type:'doughnut',data:{
    labels:agg.by_cat.map(r=>r.Category),
    datasets:[{data:agg.by_cat.map(r=>r.Sales),backgroundColor:COLORS,borderWidth:2,borderColor:'#151f2e'}]
  },options:{responsive:true,plugins:{legend:{position:'bottom',labels:{boxWidth:10,padding:8}}}}});

  // Segment donut
  new Chart('chartSeg',{type:'doughnut',data:{
    labels:agg.by_seg.map(r=>r.Segment),
    datasets:[{data:agg.by_seg.map(r=>r.Sales),backgroundColor:COLORS.slice(2),borderWidth:2,borderColor:'#151f2e'}]
  },options:{responsive:true,plugins:{legend:{position:'bottom',labels:{boxWidth:10,padding:8}}}}});

  // Ship mode pie
  new Chart('chartShip',{type:'pie',data:{
    labels:agg.by_ship.map(r=>r['Ship Mode']),
    datasets:[{data:agg.by_ship.map(r=>r.Orders),backgroundColor:COLORS.slice(1),borderWidth:2,borderColor:'#151f2e'}]
  },options:{responsive:true,plugins:{legend:{position:'bottom',labels:{boxWidth:10,padding:8}}}}});

  // Region grouped bar
  new Chart('chartReg',{type:'bar',data:{
    labels:agg.by_reg.map(r=>r.Region),
    datasets:[
      {label:'Sales',data:agg.by_reg.map(r=>r.Sales),backgroundColor:'#00d4ff88'},
      {label:'Profit',data:agg.by_reg.map(r=>r.Profit),backgroundColor:'#00ff8888'}
    ]
  },options:{responsive:true,scales:{y:{ticks:{callback:v=>fmt(v)}}},
    plugins:{legend:{position:'top',labels:{boxWidth:10}}}}});

  // Sub-cat horizontal bar
  new Chart('chartSub',{type:'bar',data:{
    labels:agg.by_sub.map(r=>r['Sub-Category']),
    datasets:[
      {label:'Sales',data:agg.by_sub.map(r=>r.Sales),backgroundColor:'#f9731688'},
      {label:'Profit',data:agg.by_sub.map(r=>r.Profit),backgroundColor:'#a855f788'}
    ]
  },options:{indexAxis:'y',responsive:true,scales:{x:{ticks:{callback:v=>fmt(v)}}},
    plugins:{legend:{position:'top',labels:{boxWidth:10}}}}});

  // YoY Revenue
  new Chart('chartYoY',{type:'bar',data:{
    labels:agg.yoy.map(r=>r.Year),
    datasets:[{label:'Annual Revenue',data:agg.yoy.map(r=>r.Sales),
      backgroundColor:COLORS,borderRadius:6}]
  },options:{responsive:true,scales:{y:{ticks:{callback:v=>fmt(v)}}},
    plugins:{legend:{display:false}}}});

  // YoY Profit
  new Chart('chartYoYProfit',{type:'bar',data:{
    labels:agg.yoy.map(r=>r.Year),
    datasets:[{label:'Annual Profit',data:agg.yoy.map(r=>r.Profit),
      backgroundColor:agg.yoy.map(r=>r.Profit>=0?'#00ff8888':'#ff475788'),borderRadius:6}]
  },options:{responsive:true,scales:{y:{ticks:{callback:v=>fmt(v)}}},
    plugins:{legend:{display:false}}}});

  // Top Cities
  new Chart('chartCity',{type:'bar',data:{
    labels:agg.by_city.map(r=>r.City),
    datasets:[{label:'Sales',data:agg.by_city.map(r=>r.Sales),backgroundColor:'#00d4ff55',borderColor:'#00d4ff',borderWidth:1.5}]
  },options:{responsive:true,maintainAspectRatio:true,
    scales:{y:{ticks:{callback:v=>fmt(v)}}},plugins:{legend:{display:false}}}});

  chartsInited=true;
}

// ── Poll live data ────────────────────────────────────────────────────────────
async function pollLive(){
  try{
    const r=await fetch('/api/live');
    const d=await r.json();
    updateKPIs(d.metrics);
    updateSparks(d.metrics);
    buildTicker(d.metrics);
    renderOrders(d.orders);
    if(!chartsInited && d.agg) initCharts(d.agg);
  }catch(e){console.warn('poll err',e);}
}

// ── RAG chat ──────────────────────────────────────────────────────────────────
function askSug(el){document.getElementById('ragInput').value=el.textContent;sendRag();}
async function sendRag(){
  const inp=document.getElementById('ragInput');
  const q=inp.value.trim();
  if(!q)return;
  inp.value='';
  const cw=document.getElementById('chatWindow');
  const t=new Date().toLocaleTimeString('en-IN');
  cw.innerHTML+=`<div class="msg msg-user"><div class="msg-bubble">${q}</div><span class="msg-time">You • ${t}</span></div>`;
  cw.innerHTML+=`<div class="msg msg-ai" id="thinking"><div class="thinking">🤖 Analysing<span class="dot-anim"><span>.</span><span>.</span><span>.</span></span></div></div>`;
  cw.scrollTop=cw.scrollHeight;
  try{
    const r=await fetch('/api/rag',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({q})});
    const d=await r.json();
    document.getElementById('thinking').outerHTML=
      `<div class="msg msg-ai"><div class="msg-bubble">${d.answer.replace(/\n/g,'<br>')}</div><span class="msg-time">AI Analyst • ${new Date().toLocaleTimeString('en-IN')}</span></div>`;
    cw.scrollTop=cw.scrollHeight;
  }catch(e){
    document.getElementById('thinking').outerHTML=`<div class="msg msg-ai"><div class="msg-bubble">⚠️ Error contacting AI. Please try again.</div></div>`;
  }
}

// ── Boot ──────────────────────────────────────────────────────────────────────
initSparks();
pollLive();
setInterval(pollLive, 2500);
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/live")
def api_live():
    with LIVE_LOCK:
        orders = list(LIVE_ORDERS)
        metrics = dict(LIVE_METRICS)
    return jsonify({"metrics": metrics, "orders": orders, "agg": AGG})

@app.route("/api/rag", methods=["POST"])
def api_rag():
    """RAG endpoint — uses Anthropic Claude API with business context injected."""
    import urllib.request
    question = request.json.get("q", "")
    if not question:
        return jsonify({"answer": "Please ask a question."})

    with LIVE_LOCK:
        live_ctx = (
            f"\nCURRENT LIVE METRICS (as of now):\n"
            f"- Total Revenue: ₹{LIVE_METRICS['total_sales']/1e6:.2f}M\n"
            f"- Total Profit: ₹{LIVE_METRICS['total_profit']/1e6:.2f}M\n"
            f"- Total Orders: {LIVE_METRICS['total_orders']:,}\n"
            f"- Live Margin: {LIVE_METRICS['total_profit']/LIVE_METRICS['total_sales']*100:.1f}%\n"
        )

    prompt = f"""{CONTEXT_SUMMARY}{live_ctx}

User question: {question}

Answer concisely (3-5 sentences max) with specific numbers from the data. Be direct and actionable. Use ₹ for currency."""

    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 400,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            answer = data["content"][0]["text"]
    except Exception as e:
        answer = f"AI analysis unavailable: {str(e)[:80]}"
    return jsonify({"answer": answer})

if __name__ == "__main__":
    print("🚀 India Superstore Live Dashboard starting on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
