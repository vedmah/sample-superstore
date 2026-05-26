"""
India Superstore — Live Business Intelligence Dashboard
Streamlit Cloud compatible — reads CSV from same repo folder
"""

import os, random, time, datetime
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="India Superstore Live Dashboard",
    page_icon="🛍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Dark trading terminal theme */
.stApp { background: #0a0e1a; color: #e2e8f0; }
section[data-testid="stSidebar"] { background: #111827; }

/* Hide Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }

/* KPI Cards */
.kpi-card {
  background: linear-gradient(135deg, #151f2e, #1a2744);
  border: 1px solid #1e2d45;
  border-radius: 14px;
  padding: 20px 22px;
  position: relative;
  overflow: hidden;
  margin-bottom: 4px;
}
.kpi-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: linear-gradient(90deg, #00d4ff, #a855f7);
}
.kpi-label { font-size: 11px; color: #64748b; font-weight: 700;
  letter-spacing: 1px; text-transform: uppercase; margin-bottom: 6px; }
.kpi-value { font-family: 'JetBrains Mono', monospace;
  font-size: 28px; font-weight: 800; color: #ffffff; line-height: 1.1; }
.kpi-sub { font-size: 12px; margin-top: 6px; }
.kpi-up { color: #00ff88; }
.kpi-dn { color: #ff4757; }
.kpi-icon { font-size: 28px; position: absolute; right: 18px;
  top: 18px; opacity: 0.18; }

/* Live badge */
.live-header {
  background: linear-gradient(135deg, #0d1b2a, #1a2744);
  border: 1px solid #1e2d45;
  border-radius: 14px;
  padding: 18px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

/* Section titles */
.section-title {
  font-size: 12px; font-weight: 700; color: #64748b;
  letter-spacing: 1.5px; text-transform: uppercase;
  border-left: 3px solid #00d4ff;
  padding-left: 10px;
  margin: 22px 0 12px;
}

/* Order table */
.order-row-new { background: rgba(0,212,255,0.06); }
.badge-profit { background: rgba(0,255,136,.15); color: #00ff88;
  border-radius: 8px; padding: 2px 9px; font-size: 11px; font-weight: 700; }
.badge-loss { background: rgba(255,71,87,.15); color: #ff4757;
  border-radius: 8px; padding: 2px 9px; font-size: 11px; font-weight: 700; }

/* Ticker */
.ticker-wrap {
  background: #111827;
  border: 1px solid #1e2d45;
  border-radius: 10px;
  padding: 10px 18px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: #00ff88;
  overflow: hidden;
  white-space: nowrap;
  margin-bottom: 16px;
}
</style>
""", unsafe_allow_html=True)

# ── Load data — Streamlit Cloud safe path ─────────────────────────────────────
@st.cache_data
def load_data():
    # Works both locally and on Streamlit Cloud (CSV in same repo folder)
    base = os.path.dirname(os.path.abspath(__file__))
    paths = [
        os.path.join(base, "IndiaSuperstore.csv"),
        os.path.join(base, "data", "IndiaSuperstore.csv"),
        "IndiaSuperstore.csv",
    ]
    for p in paths:
        if os.path.exists(p):
            df = pd.read_csv(p, parse_dates=["Order Date", "Ship Date"])
            return df
    st.error("❌ CSV not found. Please place **IndiaSuperstore.csv** in the same folder as superstore.py in your GitHub repo.")
    st.stop()

df = load_data()

# ── Precompute aggregations ───────────────────────────────────────────────────
@st.cache_data
def precompute(df):
    df = df.copy()
    df["Month"]  = df["Order Date"].dt.to_period("M").astype(str)
    df["Year"]   = df["Order Date"].dt.year
    df["Day"]    = df["Order Date"].dt.date

    monthly = (df.groupby("Month")
                 .agg(Sales=("Sales","sum"), Profit=("Profit","sum"), Orders=("Order ID","count"))
                 .reset_index().tail(30))

    daily   = (df.groupby("Day")
                 .agg(Sales=("Sales","sum"), Profit=("Profit","sum"))
                 .reset_index().tail(90))
    daily.columns = ["Date","Sales","Profit"]

    yoy     = df.groupby("Year").agg(Sales=("Sales","sum"), Profit=("Profit","sum"),
                                      Orders=("Order ID","count")).reset_index()
    by_cat  = df.groupby("Category").agg(Sales=("Sales","sum"), Profit=("Profit","sum")).reset_index()
    by_sub  = df.groupby("Sub-Category").agg(Sales=("Sales","sum"), Profit=("Profit","sum")).reset_index().nlargest(10,"Sales")
    by_reg  = df.groupby("Region").agg(Sales=("Sales","sum"), Profit=("Profit","sum"), Orders=("Order ID","count")).reset_index()
    by_seg  = df.groupby("Segment").agg(Sales=("Sales","sum"), Profit=("Profit","sum")).reset_index()
    by_city = df.groupby("City").agg(Sales=("Sales","sum")).reset_index().nlargest(10,"Sales")
    by_ship = df.groupby("Ship Mode").agg(Orders=("Order ID","count")).reset_index()
    by_disc = df.copy()
    by_disc["Disc Band"] = pd.cut(df["Discount"],[-.01,.05,.15,.25,.4,1.01],
                                   labels=["No disc","0–5%","5–15%","15–40%",">40%"])
    disc_margin = by_disc.groupby("Disc Band",observed=False).agg(
        Margin=("Profit","sum"), Sales=("Sales","sum")).reset_index()
    disc_margin["Margin%"] = (disc_margin["Margin"]/disc_margin["Sales"]*100).round(1)

    return dict(monthly=monthly, daily=daily, yoy=yoy, by_cat=by_cat, by_sub=by_sub,
                by_reg=by_reg, by_seg=by_seg, by_city=by_city, by_ship=by_ship, disc_margin=disc_margin)

agg = precompute(df)

# ── Synthetic live order generator ───────────────────────────────────────────
CATS   = df["Category"].unique().tolist()
REGS   = df["Region"].unique().tolist()
SEGS   = df["Segment"].unique().tolist()
CITIES = df["City"].unique().tolist()

def make_order(n):
    cat   = random.choice(CATS)
    sub   = random.choice(df[df["Category"]==cat]["Sub-Category"].unique().tolist())
    prod  = random.choice(df[df["Sub-Category"]==sub]["Product Name"].unique().tolist())
    qty   = random.randint(1, 15)
    price = round(random.uniform(200, 18000), 2)
    disc  = random.choice([0,0,0,0,0.1,0.2,0.3,0.4,0.5])
    sales = round(price * qty * (1 - disc), 2)
    margin= random.uniform(-0.15, 0.45)
    profit= round(sales * margin, 2)
    return {
        "order_id":  f"IND-{n:05d}",
        "time":      datetime.datetime.now().strftime("%H:%M:%S"),
        "category":  cat,
        "sub":       sub,
        "product":   prod[:42] + "…" if len(prod)>42 else prod,
        "qty":       qty,
        "sales":     sales,
        "profit":    profit,
        "discount":  disc,
        "region":    random.choice(REGS),
        "city":      random.choice(CITIES),
        "segment":   random.choice(SEGS),
        "margin_pct":round(margin*100,1),
    }

# ── Session state — live order accumulator ────────────────────────────────────
if "live_orders"  not in st.session_state: st.session_state.live_orders  = []
if "order_ctr"    not in st.session_state: st.session_state.order_ctr    = int(df["Order ID"].str.extract(r"(\d+)")[0].max()) + 1
if "extra_sales"  not in st.session_state: st.session_state.extra_sales  = 0.0
if "extra_profit" not in st.session_state: st.session_state.extra_profit = 0.0
if "extra_orders" not in st.session_state: st.session_state.extra_orders = 0
if "extra_qty"    not in st.session_state: st.session_state.extra_qty    = 0

# Generate 1–3 new orders per refresh cycle
for _ in range(random.randint(1, 3)):
    o = make_order(st.session_state.order_ctr)
    st.session_state.live_orders.insert(0, o)
    st.session_state.order_ctr    += 1
    st.session_state.extra_sales  += o["sales"]
    st.session_state.extra_profit += o["profit"]
    st.session_state.extra_orders += 1
    st.session_state.extra_qty    += o["qty"]

if len(st.session_state.live_orders) > 200:
    st.session_state.live_orders = st.session_state.live_orders[:200]

# ── Live cumulative metrics ───────────────────────────────────────────────────
total_sales  = float(df["Sales"].sum())  + st.session_state.extra_sales
total_profit = float(df["Profit"].sum()) + st.session_state.extra_profit
total_orders = len(df) + st.session_state.extra_orders
total_qty    = int(df["Quantity"].sum()) + st.session_state.extra_qty
margin_pct   = total_profit / total_sales * 100
aov          = total_sales / total_orders

last = st.session_state.live_orders[0] if st.session_state.live_orders else None

def fmt(v):
    if v >= 1e7:  return f"₹{v/1e7:.2f} Cr"
    if v >= 1e5:  return f"₹{v/1e5:.1f} L"
    if v >= 1000: return f"₹{v/1000:.1f} K"
    return f"₹{v:.0f}"

def fmtN(v):
    if v >= 1e6: return f"{v/1e6:.2f}M"
    if v >= 1e3: return f"{v/1e3:.1f}K"
    return str(int(v))

# ── PLOTLY THEME ──────────────────────────────────────────────────────────────
PLOT_BG   = "#111827"
PAPER_BG  = "#111827"
GRID_CLR  = "#1e2d45"
TEXT_CLR  = "#94a3b8"
COLORS    = ["#00d4ff","#00ff88","#a855f7","#f97316","#ffd700","#ff4757","#06b6d4","#34d399","#fb923c","#818cf8"]

def themed(fig, height=280):
    fig.update_layout(
        height=height,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(color=TEXT_CLR, family="Inter"),
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
        xaxis=dict(gridcolor=GRID_CLR, linecolor=GRID_CLR, zerolinecolor=GRID_CLR),
        yaxis=dict(gridcolor=GRID_CLR, linecolor=GRID_CLR, zerolinecolor=GRID_CLR),
    )
    return fig

# ══════════════════════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════════════════════
now_str = datetime.datetime.now().strftime("%d %b %Y  %H:%M:%S")

st.markdown(f"""
<div class="live-header">
  <div style="display:flex;align-items:center;gap:14px;">
    <div style="width:42px;height:42px;background:linear-gradient(135deg,#00d4ff,#a855f7);
      border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:22px;">🛍</div>
    <div>
      <div style="font-size:20px;font-weight:800;color:#fff;">India Superstore</div>
      <div style="font-size:12px;color:#64748b;">Live Business Intelligence Dashboard</div>
    </div>
  </div>
  <div style="display:flex;align-items:center;gap:20px;">
    <div style="font-family:monospace;color:#64748b;font-size:13px;">{now_str}</div>
    <div style="background:rgba(0,255,136,.12);border:1px solid rgba(0,255,136,.3);
      border-radius:20px;padding:7px 16px;font-size:12px;color:#00ff88;display:flex;align-items:center;gap:8px;">
      <span style="width:8px;height:8px;border-radius:50%;background:#00ff88;display:inline-block;
        animation:pulse 1s infinite;"></span> LIVE FEED ACTIVE
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Ticker bar ────────────────────────────────────────────────────────────────
last_sale_str = fmt(last["sales"]) if last else "—"
last_prof_str = (("▲ " if last["profit"]>=0 else "▼ ") + fmt(abs(last["profit"]))) if last else "—"
ticker_text = (
    f"💰 Revenue: {fmt(total_sales)}   |   "
    f"📈 Profit: {fmt(total_profit)}   |   "
    f"📦 Orders: {fmtN(total_orders)}   |   "
    f"🎯 Margin: {margin_pct:.1f}%   |   "
    f"🛒 AOV: {fmt(aov)}   |   "
    f"📮 Units: {fmtN(total_qty)}   |   "
    f"⚡ Last Sale: {last_sale_str}   |   "
    f"💵 Last Profit: {last_prof_str}   |   "
    f"🔄 Live Orders: +{st.session_state.extra_orders}"
)
st.markdown(f'<div class="ticker-wrap">{"   ·   ".join([ticker_text]*3)}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  KPI CARDS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">📊 KEY PERFORMANCE INDICATORS</div>', unsafe_allow_html=True)

k1,k2,k3,k4,k5,k6 = st.columns(6)

def kpi_card(col, label, value, sub, sub_cls, icon):
    col.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-icon">{icon}</div>
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      <div class="kpi-sub {sub_cls}">{sub}</div>
    </div>""", unsafe_allow_html=True)

kpi_card(k1, "Total Revenue",   fmt(total_sales),  f"Last: {last_sale_str}", "kpi-up", "💰")
kpi_card(k2, "Total Profit",    fmt(total_profit), f"{'▲' if total_profit>0 else '▼'} overall", "kpi-up" if total_profit>0 else "kpi-dn", "📈")
kpi_card(k3, "Total Orders",    fmtN(total_orders),f"+{st.session_state.extra_orders} live", "kpi-up", "📦")
kpi_card(k4, "Profit Margin",   f"{margin_pct:.1f}%", "net margin", "kpi-up" if margin_pct>0 else "kpi-dn", "🎯")
kpi_card(k5, "Avg Order Value", fmt(aov),           "per transaction", "kpi-up", "🛒")
kpi_card(k6, "Units Sold",      fmtN(total_qty),    "total quantity", "kpi-up", "📮")

# ══════════════════════════════════════════════════════════════════════════════
#  RAG / AI ANALYST
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">🤖 AI BUSINESS ANALYST (RAG)</div>', unsafe_allow_html=True)

CONTEXT = f"""India Superstore Business Data Context:
- Date Range: {df['Order Date'].min().date()} to {df['Order Date'].max().date()}
- Total Historical Orders: {len(df):,}
- Total Revenue: ₹{df['Sales'].sum()/1e6:.2f}M  |  Total Profit: ₹{df['Profit'].sum()/1e6:.2f}M
- Overall Margin: {df['Profit'].sum()/df['Sales'].sum()*100:.1f}%
- Categories: {', '.join(df['Category'].unique())}  |  Regions: {', '.join(df['Region'].unique())}
- Segments: {', '.join(df['Segment'].unique())}
- Top Category by Sales: {df.groupby('Category')['Sales'].sum().idxmax()}
- Top Region by Sales: {df.groupby('Region')['Sales'].sum().idxmax()}
- Best Sub-Category: {df.groupby('Sub-Category')['Sales'].sum().idxmax()}
- Avg Discount: {df['Discount'].mean()*100:.1f}%  |  High-discount (>40%) orders: {(df['Discount']>0.4).sum()}
- Most Profitable Segment: {df.groupby('Segment')['Profit'].sum().idxmax()}
LIVE NOW: Revenue=₹{total_sales/1e6:.2f}M, Profit=₹{total_profit/1e6:.2f}M, Orders={total_orders:,}, Margin={margin_pct:.1f}%
"""

with st.expander("💬 Ask your AI Business Analyst", expanded=True):
    suggestions = [
        "Which category drives most revenue?",
        "What's hurting profit margin?",
        "Which region is underperforming?",
        "Impact of discounts on profit?",
        "Top 3 growth opportunities?",
        "Best performing customer segment?",
    ]
    scols = st.columns(len(suggestions))
    chosen_sug = None
    for i, sug in enumerate(suggestions):
        if scols[i].button(sug, key=f"sug_{i}", use_container_width=True):
            chosen_sug = sug

    question = st.text_input("Ask anything about your business data:", placeholder="e.g. Which sub-category has the best margin?", key="rag_q")
    if chosen_sug:
        question = chosen_sug

    if question:
        import urllib.request, json as jsonlib
        prompt = f"{CONTEXT}\n\nQuestion: {question}\n\nAnswer concisely in 3–5 sentences with specific numbers. Use ₹ for currency. Be actionable."
        payload = jsonlib.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 500,
            "messages": [{"role":"user","content": prompt}]
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={"Content-Type":"application/json","anthropic-version":"2023-06-01"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = jsonlib.loads(resp.read())
                answer = data["content"][0]["text"]
        except Exception as e:
            answer = f"⚠️ AI unavailable: {e}"
        st.markdown(f"""
        <div style="background:#151f2e;border:1px solid #1e2d45;border-radius:12px;
          padding:16px 20px;margin-top:12px;font-size:14px;line-height:1.7;color:#e2e8f0;">
          🤖 <strong style="color:#00d4ff;">AI Analyst:</strong><br>{answer}
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  TREND CHARTS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">📅 REVENUE & PROFIT TRENDS</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)

with c1:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    m = agg["monthly"]
    fig.add_trace(go.Bar(x=m["Month"], y=m["Sales"], name="Sales",
                          marker_color="#00d4ff55", marker_line_color="#00d4ff", marker_line_width=1), secondary_y=False)
    fig.add_trace(go.Scatter(x=m["Month"], y=m["Profit"], name="Profit",
                              line=dict(color="#00ff88", width=2), mode="lines+markers",
                              marker=dict(size=4)), secondary_y=True)
    fig.update_layout(title="Monthly Revenue & Profit", height=290,
                      paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
                      font=dict(color=TEXT_CLR), margin=dict(l=10,r=10,t=36,b=10),
                      legend=dict(bgcolor="rgba(0,0,0,0)"))
    fig.update_xaxes(gridcolor=GRID_CLR, tickangle=-45, nticks=10)
    fig.update_yaxes(gridcolor=GRID_CLR)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    d = agg["daily"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d["Date"].astype(str), y=d["Sales"], fill="tozeroy",
                              fillcolor="#a855f722", line=dict(color="#a855f7",width=1.5), name="Sales"))
    fig.add_trace(go.Scatter(x=d["Date"].astype(str), y=d["Profit"],
                              line=dict(color="#00ff88",width=1.5), name="Profit"))
    themed(fig, 290).update_layout(title="Daily Sales — Last 90 Days")
    fig.update_xaxes(nticks=10, tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

# YoY
st.markdown('<div class="section-title">📆 YEAR-OVER-YEAR GROWTH</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)
y = agg["yoy"]

with c1:
    fig = go.Figure(go.Bar(x=y["Year"].astype(str), y=y["Sales"],
                            marker_color=COLORS[:len(y)], text=y["Sales"].apply(fmt),
                            textposition="outside"))
    themed(fig).update_layout(title="Annual Revenue", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    colors_p = ["#00ff8888" if v>=0 else "#ff475788" for v in y["Profit"]]
    fig = go.Figure(go.Bar(x=y["Year"].astype(str), y=y["Profit"],
                            marker_color=colors_p, text=y["Profit"].apply(fmt),
                            textposition="outside"))
    themed(fig).update_layout(title="Annual Profit", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
#  CATEGORY / SEGMENT / REGION
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">🗂 CATEGORY, SEGMENT & REGION ANALYSIS</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)

with c1:
    fig = go.Figure(go.Pie(labels=agg["by_cat"]["Category"], values=agg["by_cat"]["Sales"],
                            hole=.42, marker_colors=COLORS))
    themed(fig).update_layout(title="Sales by Category",
                               legend=dict(orientation="h", y=-0.12, font=dict(size=10)))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    fig = go.Figure(go.Pie(labels=agg["by_seg"]["Segment"], values=agg["by_seg"]["Sales"],
                            hole=.42, marker_colors=COLORS[2:]))
    themed(fig).update_layout(title="Sales by Segment",
                               legend=dict(orientation="h", y=-0.12, font=dict(size=10)))
    st.plotly_chart(fig, use_container_width=True)

with c3:
    fig = go.Figure(go.Pie(labels=agg["by_ship"]["Ship Mode"], values=agg["by_ship"]["Orders"],
                            hole=.42, marker_colors=COLORS[1:]))
    themed(fig).update_layout(title="Ship Mode Distribution",
                               legend=dict(orientation="h", y=-0.12, font=dict(size=10)))
    st.plotly_chart(fig, use_container_width=True)

# Region
c1, c2 = st.columns(2)
r = agg["by_reg"]

with c1:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=r["Region"], y=r["Sales"], name="Sales", marker_color="#00d4ff77"))
    fig.add_trace(go.Bar(x=r["Region"], y=r["Profit"], name="Profit", marker_color="#00ff8877"))
    themed(fig).update_layout(title="Sales & Profit by Region", barmode="group")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    sub = agg["by_sub"]
    fig = go.Figure()
    fig.add_trace(go.Bar(y=sub["Sub-Category"], x=sub["Sales"], name="Sales",
                          orientation="h", marker_color="#f9731677"))
    fig.add_trace(go.Bar(y=sub["Sub-Category"], x=sub["Profit"], name="Profit",
                          orientation="h", marker_color="#a855f777"))
    themed(fig).update_layout(title="Top 10 Sub-Categories", barmode="group")
    st.plotly_chart(fig, use_container_width=True)

# Cities + Discount impact
c1, c2 = st.columns(2)

with c1:
    city = agg["by_city"]
    fig = go.Figure(go.Bar(x=city["City"], y=city["Sales"],
                            marker_color=COLORS, text=city["Sales"].apply(fmt), textposition="outside"))
    themed(fig).update_layout(title="Top 10 Cities by Revenue", showlegend=False)
    fig.update_xaxes(tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    dm = agg["disc_margin"]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=dm["Disc Band"].astype(str), y=dm["Sales"], name="Sales",
                          marker_color="#00d4ff55"), secondary_y=False)
    fig.add_trace(go.Scatter(x=dm["Disc Band"].astype(str), y=dm["Margin%"], name="Margin %",
                              line=dict(color="#ff4757", width=2.5),
                              marker=dict(size=7)), secondary_y=True)
    fig.update_layout(title="Discount Band vs Margin %", height=280,
                      paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
                      font=dict(color=TEXT_CLR), margin=dict(l=10,r=10,t=36,b=10),
                      legend=dict(bgcolor="rgba(0,0,0,0)"))
    fig.update_xaxes(gridcolor=GRID_CLR)
    fig.update_yaxes(gridcolor=GRID_CLR)
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
#  LIVE ORDER FEED
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">⚡ LIVE ORDER FEED</div>', unsafe_allow_html=True)

orders = st.session_state.live_orders[:15]
if orders:
    rows = []
    for o in orders:
        p_cls = "🟢" if o["profit"] >= 0 else "🔴"
        rows.append({
            "Time":       o["time"],
            "Order ID":   o["order_id"],
            "Category":   o["category"],
            "Sub-Cat":    o["sub"],
            "Product":    o["product"],
            "Qty":        o["qty"],
            "Sales ₹":   fmt(o["sales"]),
            "Profit":     f"{p_cls} {fmt(abs(o['profit']))}",
            "Margin":     f"{o['margin_pct']}%",
            "Region":     o["region"],
            "Segment":    o["segment"],
        })
    feed_df = pd.DataFrame(rows)
    st.dataframe(feed_df, use_container_width=True, height=400,
                 column_config={
                     "Sales ₹": st.column_config.TextColumn("Sales ₹"),
                     "Profit":  st.column_config.TextColumn("Profit"),
                 })
else:
    st.info("Waiting for live orders...")

# ══════════════════════════════════════════════════════════════════════════════
#  AUTO REFRESH — trading-style every 3 seconds
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
col_r, col_s = st.columns([3,1])
with col_r:
    st.markdown(f"<div style='color:#64748b;font-size:11px;'>📡 Last updated: {now_str} · Auto-refreshing every 3s · {st.session_state.extra_orders} live orders generated</div>",
                unsafe_allow_html=True)
with col_s:
    if st.button("⏸ Pause / Resume", use_container_width=True):
        st.session_state["paused"] = not st.session_state.get("paused", False)

if not st.session_state.get("paused", False):
    time.sleep(3)
    st.rerun()
