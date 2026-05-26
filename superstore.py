"""
India Superstore — Live Business Intelligence Dashboard
Streamlit Cloud compatible — CSV loaded from repo OR uploaded by user
"""
import os, io, random, time, datetime, pathlib
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

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:#0a0e1a;color:#e2e8f0;}
#MainMenu,footer,header{visibility:hidden;}
section[data-testid="stSidebar"]{background:#111827;}

.kpi-card{background:linear-gradient(135deg,#151f2e,#1a2744);border:1px solid #1e2d45;
  border-radius:14px;padding:20px 22px;position:relative;overflow:hidden;margin-bottom:4px;}
.kpi-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,#00d4ff,#a855f7);}
.kpi-label{font-size:11px;color:#64748b;font-weight:700;letter-spacing:1px;
  text-transform:uppercase;margin-bottom:6px;}
.kpi-value{font-family:'JetBrains Mono',monospace;font-size:26px;font-weight:800;
  color:#ffffff;line-height:1.1;}
.kpi-sub{font-size:12px;margin-top:6px;}
.kpi-up{color:#00ff88;} .kpi-dn{color:#ff4757;}
.kpi-icon{font-size:28px;position:absolute;right:18px;top:18px;opacity:.18;}

.live-header{background:linear-gradient(135deg,#0d1b2a,#1a2744);border:1px solid #1e2d45;
  border-radius:14px;padding:18px 28px;margin-bottom:20px;}
.section-title{font-size:12px;font-weight:700;color:#64748b;letter-spacing:1.5px;
  text-transform:uppercase;border-left:3px solid #00d4ff;padding-left:10px;margin:22px 0 12px;}
.ticker-wrap{background:#111827;border:1px solid #1e2d45;border-radius:10px;
  padding:10px 18px;font-family:'JetBrains Mono',monospace;font-size:12px;
  color:#00ff88;overflow:hidden;white-space:nowrap;margin-bottom:16px;}

/* Upload page */
.upload-box{background:linear-gradient(135deg,#151f2e,#1a2744);border:2px dashed #1e2d45;
  border-radius:16px;padding:48px;text-align:center;margin:40px auto;max-width:600px;}
.upload-title{font-size:24px;font-weight:800;color:#fff;margin-bottom:8px;}
.upload-sub{font-size:14px;color:#64748b;margin-bottom:24px;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  DATA LOADING — 3-layer fallback (never crashes)
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def parse_csv(raw_bytes: bytes) -> pd.DataFrame:
    """Parse CSV bytes and return DataFrame — cached so it only runs once."""
    df = pd.read_csv(io.BytesIO(raw_bytes), parse_dates=["Order Date", "Ship Date"])
    return df

def find_csv_in_repo() -> bytes | None:
    """
    Look for IndiaSuperstore.csv next to this script.
    On Streamlit Cloud: __file__ = /mount/src/<repo>/superstore.py
    CSV must be committed as:  /mount/src/<repo>/IndiaSuperstore.csv
    """
    here = pathlib.Path(__file__).parent.resolve()
    candidates = [
        here / "IndiaSuperstore.csv",
        here / "data" / "IndiaSuperstore.csv",
        here / "dataset" / "IndiaSuperstore.csv",
        pathlib.Path("IndiaSuperstore.csv"),          # cwd fallback
    ]
    for p in candidates:
        if p.exists() and p.stat().st_size > 0:
            return p.read_bytes()
    return None

# ── Try repo first ────────────────────────────────────────────────────────────
csv_bytes = find_csv_in_repo()

if csv_bytes is not None:
    # ✅ CSV found in repo — load silently
    df = parse_csv(csv_bytes)

else:
    # ── CSV NOT in repo — show uploader ──────────────────────────────────────
    st.markdown("""
    <div class="live-header" style="text-align:center;">
      <div style="font-size:36px;margin-bottom:8px;">🛍</div>
      <div style="font-size:22px;font-weight:800;color:#fff;">India Superstore Live Dashboard</div>
      <div style="color:#64748b;margin-top:4px;">Business Intelligence · RAG Analytics · Live Feed</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="upload-box">
      <div class="upload-title">📂 Upload Your Dataset</div>
      <div class="upload-sub">
        The CSV was not found in the repo.<br>
        Upload <strong>IndiaSuperstore.csv</strong> below to launch the dashboard.<br><br>
        <span style="color:#00d4ff;font-size:12px;">
        💡 To avoid this step: commit IndiaSuperstore.csv to your GitHub repo root.
        </span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Upload IndiaSuperstore.csv",
        type=["csv"],
        help="Upload the India Superstore CSV dataset",
    )

    if uploaded is None:
        st.info("⏳ Waiting for CSV upload to start the dashboard…")
        st.stop()

    csv_bytes = uploaded.read()
    if len(csv_bytes) == 0:
        st.error("❌ Uploaded file is empty. Please upload a valid CSV.")
        st.stop()

    df = parse_csv(csv_bytes)
    st.success(f"✅ Loaded {len(df):,} rows. Launching dashboard…")
    time.sleep(1)
    st.rerun()

# ── Validate columns ──────────────────────────────────────────────────────────
REQUIRED = {"Order ID","Order Date","Ship Date","Sales","Profit","Quantity",
            "Category","Sub-Category","Region","Segment","City","Ship Mode","Product Name"}
missing = REQUIRED - set(df.columns)
if missing:
    st.error(f"❌ CSV is missing columns: {missing}. Please upload the correct file.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
#  PRECOMPUTE AGGREGATIONS
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def precompute(_df):
    d = _df.copy()
    d["Month"] = d["Order Date"].dt.to_period("M").astype(str)
    d["Year"]  = d["Order Date"].dt.year
    d["Day"]   = d["Order Date"].dt.date

    monthly = (d.groupby("Month")
                .agg(Sales=("Sales","sum"), Profit=("Profit","sum"), Orders=("Order ID","count"))
                .reset_index().tail(30))
    daily   = (d.groupby("Day")
                .agg(Sales=("Sales","sum"), Profit=("Profit","sum"))
                .reset_index().tail(90))
    daily.columns = ["Date","Sales","Profit"]
    yoy     = d.groupby("Year").agg(Sales=("Sales","sum"), Profit=("Profit","sum"),
                                     Orders=("Order ID","count")).reset_index()
    by_cat  = d.groupby("Category").agg(Sales=("Sales","sum"), Profit=("Profit","sum")).reset_index()
    by_sub  = d.groupby("Sub-Category").agg(Sales=("Sales","sum"), Profit=("Profit","sum")).reset_index().nlargest(10,"Sales")
    by_reg  = d.groupby("Region").agg(Sales=("Sales","sum"), Profit=("Profit","sum"), Orders=("Order ID","count")).reset_index()
    by_seg  = d.groupby("Segment").agg(Sales=("Sales","sum"), Profit=("Profit","sum")).reset_index()
    by_city = d.groupby("City").agg(Sales=("Sales","sum")).reset_index().nlargest(10,"Sales")
    by_ship = d.groupby("Ship Mode").agg(Orders=("Order ID","count")).reset_index()

    bd = d.copy()
    bd["Disc Band"] = pd.cut(d["Discount"],[-.01,.05,.15,.25,.40,1.01],
                              labels=["No disc","1-5%","6-15%","16-40%",">40%"])
    disc_m = bd.groupby("Disc Band", observed=False).agg(
        Margin=("Profit","sum"), Sales=("Sales","sum")).reset_index()
    disc_m["Margin%"] = (disc_m["Margin"] / disc_m["Sales"].replace(0,1) * 100).round(1)

    return dict(monthly=monthly, daily=daily, yoy=yoy, by_cat=by_cat,
                by_sub=by_sub, by_reg=by_reg, by_seg=by_seg,
                by_city=by_city, by_ship=by_ship, disc_m=disc_m)

agg = precompute(df)

# ══════════════════════════════════════════════════════════════════════════════
#  LIVE ORDER SIMULATION
# ══════════════════════════════════════════════════════════════════════════════
CATS   = df["Category"].unique().tolist()
REGS   = df["Region"].unique().tolist()
SEGS   = df["Segment"].unique().tolist()
CITIES = df["City"].unique().tolist()

_max_id = df["Order ID"].str.extract(r"(\d+)")[0].dropna().astype(int).max()

def make_order(n):
    cat    = random.choice(CATS)
    sub_opts = df[df["Category"]==cat]["Sub-Category"].unique().tolist()
    sub    = random.choice(sub_opts)
    prod_opts = df[df["Sub-Category"]==sub]["Product Name"].unique().tolist()
    prod   = random.choice(prod_opts)
    qty    = random.randint(1,15)
    price  = round(random.uniform(200,18000),2)
    disc   = random.choice([0,0,0,0,0.1,0.2,0.3,0.4,0.5])
    sales  = round(price * qty * (1-disc), 2)
    margin = random.uniform(-0.15, 0.45)
    profit = round(sales * margin, 2)
    return dict(
        order_id=f"IND-{n:05d}",
        time=datetime.datetime.now().strftime("%H:%M:%S"),
        category=cat, sub=sub,
        product=prod[:44]+"…" if len(prod)>44 else prod,
        qty=qty, sales=sales, profit=profit,
        discount=disc, region=random.choice(REGS),
        city=random.choice(CITIES), segment=random.choice(SEGS),
        margin_pct=round(margin*100,1),
    )

# ── Session state ─────────────────────────────────────────────────────────────
ss = st.session_state
if "live_orders"  not in ss: ss.live_orders  = []
if "order_ctr"    not in ss: ss.order_ctr    = int(_max_id) + 1
if "extra_sales"  not in ss: ss.extra_sales  = 0.0
if "extra_profit" not in ss: ss.extra_profit = 0.0
if "extra_orders" not in ss: ss.extra_orders = 0
if "extra_qty"    not in ss: ss.extra_qty    = 0
if "paused"       not in ss: ss.paused       = False

if not ss.paused:
    for _ in range(random.randint(1,3)):
        o = make_order(ss.order_ctr)
        ss.live_orders.insert(0, o)
        ss.order_ctr    += 1
        ss.extra_sales  += o["sales"]
        ss.extra_profit += o["profit"]
        ss.extra_orders += 1
        ss.extra_qty    += o["qty"]
    ss.live_orders = ss.live_orders[:200]

# ── Live metrics ──────────────────────────────────────────────────────────────
total_sales  = float(df["Sales"].sum())  + ss.extra_sales
total_profit = float(df["Profit"].sum()) + ss.extra_profit
total_orders = len(df) + ss.extra_orders
total_qty    = int(df["Quantity"].sum()) + ss.extra_qty
margin_pct   = total_profit / total_sales * 100
aov          = total_sales / total_orders
last         = ss.live_orders[0] if ss.live_orders else None

def fmt(v):
    if v >= 1e7: return f"₹{v/1e7:.2f} Cr"
    if v >= 1e5: return f"₹{v/1e5:.1f} L"
    if v >= 1e3: return f"₹{v/1e3:.1f} K"
    return f"₹{v:.0f}"

def fmtN(v):
    if v >= 1e6: return f"{v/1e6:.2f}M"
    if v >= 1e3: return f"{v/1e3:.1f}K"
    return str(int(v))

# ── Plotly theme helpers ──────────────────────────────────────────────────────
PBG   = "#111827"; GRID  = "#1e2d45"; TXT   = "#94a3b8"
CLR   = ["#00d4ff","#00ff88","#a855f7","#f97316","#ffd700","#ff4757","#06b6d4","#34d399","#fb923c","#818cf8"]

def T(fig, h=280, title=""):
    fig.update_layout(
        height=h, title=dict(text=title, font=dict(size=13, color="#e2e8f0"), x=0),
        paper_bgcolor=PBG, plot_bgcolor=PBG,
        font=dict(color=TXT, family="Inter"),
        margin=dict(l=10,r=10,t=38,b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
        xaxis=dict(gridcolor=GRID,linecolor=GRID,zerolinecolor=GRID),
        yaxis=dict(gridcolor=GRID,linecolor=GRID,zerolinecolor=GRID),
    )
    return fig

# ══════════════════════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════════════════════
now_str = datetime.datetime.now().strftime("%d %b %Y  %H:%M:%S")
status  = "⏸ PAUSED" if ss.paused else "● LIVE FEED ACTIVE"
s_color = "#ffd700" if ss.paused else "#00ff88"

st.markdown(f"""
<div class="live-header" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
  <div style="display:flex;align-items:center;gap:14px;">
    <div style="width:44px;height:44px;background:linear-gradient(135deg,#00d4ff,#a855f7);
      border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:24px;">🛍</div>
    <div>
      <div style="font-size:20px;font-weight:800;color:#fff;">India Superstore</div>
      <div style="font-size:12px;color:#64748b;">Live Business Intelligence · {len(df):,} historical orders</div>
    </div>
  </div>
  <div style="display:flex;align-items:center;gap:18px;flex-wrap:wrap;">
    <div style="font-family:monospace;color:#64748b;font-size:13px;">{now_str}</div>
    <div style="background:rgba(0,212,255,.08);border:1px solid rgba(0,212,255,.2);
      border-radius:20px;padding:6px 16px;font-size:12px;color:{s_color};">{status}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Ticker ────────────────────────────────────────────────────────────────────
last_s = fmt(last["sales"])   if last else "—"
last_p = (("▲ " if last["profit"]>=0 else "▼ ")+fmt(abs(last["profit"]))) if last else "—"
t = (f"💰 Revenue: {fmt(total_sales)}   ·   📈 Profit: {fmt(total_profit)}   ·   "
     f"📦 Orders: {fmtN(total_orders)}   ·   🎯 Margin: {margin_pct:.1f}%   ·   "
     f"🛒 AOV: {fmt(aov)}   ·   📮 Units: {fmtN(total_qty)}   ·   "
     f"⚡ Last Sale: {last_s}   ·   💵 Last Profit: {last_p}   ·   "
     f"🔄 Live Orders: +{ss.extra_orders}")
st.markdown(f'<div class="ticker-wrap">{t}{"   ·   "+t}{"   ·   "+t}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  KPI CARDS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">📊 KEY PERFORMANCE INDICATORS</div>', unsafe_allow_html=True)

def kpi(col, label, value, sub, cls, icon):
    col.markdown(f"""<div class="kpi-card">
      <div class="kpi-icon">{icon}</div>
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      <div class="kpi-sub {cls}">{sub}</div>
    </div>""", unsafe_allow_html=True)

k = st.columns(6)
kpi(k[0],"Total Revenue",   fmt(total_sales),        f"Last: {last_s}",                "kpi-up","💰")
kpi(k[1],"Total Profit",    fmt(total_profit),        f"{'▲' if total_profit>0 else '▼'} overall","kpi-up" if total_profit>0 else "kpi-dn","📈")
kpi(k[2],"Total Orders",    fmtN(total_orders),       f"+{ss.extra_orders} live",       "kpi-up","📦")
kpi(k[3],"Profit Margin",   f"{margin_pct:.1f}%",     "net margin",                    "kpi-up" if margin_pct>0 else "kpi-dn","🎯")
kpi(k[4],"Avg Order Value", fmt(aov),                 "per transaction",               "kpi-up","🛒")
kpi(k[5],"Units Sold",      fmtN(total_qty),          "total quantity",                "kpi-up","📮")

# ══════════════════════════════════════════════════════════════════════════════
#  RAG AI ANALYST
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">🤖 AI BUSINESS ANALYST (RAG)</div>', unsafe_allow_html=True)

CTX = f"""India Superstore Data Context:
- Date Range: {df['Order Date'].min().date()} to {df['Order Date'].max().date()}
- Historical Orders: {len(df):,}  |  Revenue: ₹{df['Sales'].sum()/1e6:.2f}M  |  Profit: ₹{df['Profit'].sum()/1e6:.2f}M
- Overall Margin: {df['Profit'].sum()/df['Sales'].sum()*100:.1f}%  |  Avg Discount: {df['Discount'].mean()*100:.1f}%
- Categories: {', '.join(df['Category'].unique())}
- Regions: {', '.join(df['Region'].unique())}  |  Segments: {', '.join(df['Segment'].unique())}
- Top Category: {df.groupby('Category')['Sales'].sum().idxmax()}
- Top Region: {df.groupby('Region')['Sales'].sum().idxmax()}
- Best Sub-Cat: {df.groupby('Sub-Category')['Sales'].sum().idxmax()}
- Most Profitable Segment: {df.groupby('Segment')['Profit'].sum().idxmax()}
- High-discount (>40%) orders: {(df['Discount']>0.4).sum()}
LIVE NOW: Revenue=₹{total_sales/1e6:.2f}M, Profit=₹{total_profit/1e6:.2f}M, Orders={total_orders:,}, Margin={margin_pct:.1f}%"""

with st.expander("💬 Ask your AI Business Analyst", expanded=True):
    SUGS = ["Which category drives most revenue?","What's hurting profit margin?",
            "Which region is underperforming?","Impact of discounts on profit?",
            "Top 3 growth opportunities?","Best performing customer segment?"]
    sc = st.columns(len(SUGS))
    chosen = None
    for i,s in enumerate(SUGS):
        if sc[i].button(s, key=f"sug{i}", use_container_width=True):
            chosen = s

    q = st.text_input("Ask anything:", placeholder="e.g. Which sub-category has the best margin?", key="ragq")
    if chosen: q = chosen

    if q:
        import urllib.request, json as jl
        prompt = f"{CTX}\n\nQuestion: {q}\n\nAnswer in 3–5 sentences with specific ₹ numbers. Be direct and actionable."
        payload = jl.dumps({"model":"claude-sonnet-4-20250514","max_tokens":500,
                             "messages":[{"role":"user","content":prompt}]}).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=payload,
              headers={"Content-Type":"application/json","anthropic-version":"2023-06-01"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                ans = jl.loads(r.read())["content"][0]["text"]
        except Exception as e:
            ans = f"⚠️ AI unavailable ({e})"
        st.markdown(f"""<div style="background:#151f2e;border:1px solid #1e2d45;border-radius:12px;
          padding:16px 20px;margin-top:12px;font-size:14px;line-height:1.7;color:#e2e8f0;">
          🤖 <strong style="color:#00d4ff;">AI Analyst:</strong><br>{ans}</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  CHARTS — ROW 1: Trends
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">📅 REVENUE & PROFIT TRENDS</div>', unsafe_allow_html=True)
c1,c2 = st.columns(2)

with c1:
    m = agg["monthly"]
    fig = make_subplots(specs=[[{"secondary_y":True}]])
    fig.add_trace(go.Bar(x=m["Month"],y=m["Sales"],name="Sales",
                          marker_color="#00d4ff44",marker_line_color="#00d4ff",marker_line_width=1),secondary_y=False)
    fig.add_trace(go.Scatter(x=m["Month"],y=m["Profit"],name="Profit",
                              line=dict(color="#00ff88",width=2),mode="lines+markers",marker=dict(size=3)),secondary_y=True)
    fig.update_layout(height=290,title=dict(text="Monthly Revenue & Profit",font=dict(size=13,color="#e2e8f0")),
                      paper_bgcolor=PBG,plot_bgcolor=PBG,font=dict(color=TXT),
                      margin=dict(l=10,r=10,t=38,b=10),legend=dict(bgcolor="rgba(0,0,0,0)"))
    fig.update_xaxes(gridcolor=GRID,tickangle=-45,nticks=10)
    fig.update_yaxes(gridcolor=GRID)
    st.plotly_chart(fig,use_container_width=True)

with c2:
    d = agg["daily"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d["Date"].astype(str),y=d["Sales"],fill="tozeroy",
                              fillcolor="#a855f718",line=dict(color="#a855f7",width=1.5),name="Sales"))
    fig.add_trace(go.Scatter(x=d["Date"].astype(str),y=d["Profit"],
                              line=dict(color="#00ff88",width=1.5),name="Profit"))
    T(fig,290,"Daily Sales — Last 90 Days").update_xaxes(nticks=10,tickangle=-45)
    st.plotly_chart(fig,use_container_width=True)

# ── YoY ───────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📆 YEAR-OVER-YEAR GROWTH</div>', unsafe_allow_html=True)
c1,c2 = st.columns(2)
y = agg["yoy"]

with c1:
    fig = go.Figure(go.Bar(x=y["Year"].astype(str),y=y["Sales"],
                            marker_color=CLR[:len(y)],text=y["Sales"].apply(fmt),textposition="outside",
                            textfont=dict(size=10)))
    T(fig,260,"Annual Revenue").update_layout(showlegend=False)
    st.plotly_chart(fig,use_container_width=True)

with c2:
    cp = ["#00ff8877" if v>=0 else "#ff475777" for v in y["Profit"]]
    fig = go.Figure(go.Bar(x=y["Year"].astype(str),y=y["Profit"],
                            marker_color=cp,text=y["Profit"].apply(fmt),textposition="outside",
                            textfont=dict(size=10)))
    T(fig,260,"Annual Profit").update_layout(showlegend=False)
    st.plotly_chart(fig,use_container_width=True)

# ── Category / Segment / Ship ─────────────────────────────────────────────────
st.markdown('<div class="section-title">🗂 CATEGORY, SEGMENT & SHIPPING</div>', unsafe_allow_html=True)
c1,c2,c3 = st.columns(3)

with c1:
    fig = go.Figure(go.Pie(labels=agg["by_cat"]["Category"],values=agg["by_cat"]["Sales"],
                            hole=.42,marker_colors=CLR))
    T(fig,280,"Sales by Category").update_layout(legend=dict(orientation="h",y=-0.15,font=dict(size=10)))
    st.plotly_chart(fig,use_container_width=True)

with c2:
    fig = go.Figure(go.Pie(labels=agg["by_seg"]["Segment"],values=agg["by_seg"]["Sales"],
                            hole=.42,marker_colors=CLR[2:]))
    T(fig,280,"Sales by Segment").update_layout(legend=dict(orientation="h",y=-0.15,font=dict(size=10)))
    st.plotly_chart(fig,use_container_width=True)

with c3:
    fig = go.Figure(go.Pie(labels=agg["by_ship"]["Ship Mode"],values=agg["by_ship"]["Orders"],
                            hole=.42,marker_colors=CLR[1:]))
    T(fig,280,"Ship Mode Distribution").update_layout(legend=dict(orientation="h",y=-0.15,font=dict(size=10)))
    st.plotly_chart(fig,use_container_width=True)

# ── Region / Sub-cat ──────────────────────────────────────────────────────────
st.markdown('<div class="section-title">🗺 REGIONAL & SUB-CATEGORY PERFORMANCE</div>', unsafe_allow_html=True)
c1,c2 = st.columns(2)
r = agg["by_reg"]

with c1:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=r["Region"],y=r["Sales"],name="Sales",marker_color="#00d4ff66"))
    fig.add_trace(go.Bar(x=r["Region"],y=r["Profit"],name="Profit",marker_color="#00ff8866"))
    T(fig,280,"Sales & Profit by Region").update_layout(barmode="group")
    st.plotly_chart(fig,use_container_width=True)

with c2:
    sub = agg["by_sub"]
    fig = go.Figure()
    fig.add_trace(go.Bar(y=sub["Sub-Category"],x=sub["Sales"],name="Sales",orientation="h",marker_color="#f9731666"))
    fig.add_trace(go.Bar(y=sub["Sub-Category"],x=sub["Profit"],name="Profit",orientation="h",marker_color="#a855f766"))
    T(fig,280,"Top 10 Sub-Categories").update_layout(barmode="group")
    st.plotly_chart(fig,use_container_width=True)

# ── Cities / Discount ─────────────────────────────────────────────────────────
st.markdown('<div class="section-title">🏙 CITIES & DISCOUNT IMPACT</div>', unsafe_allow_html=True)
c1,c2 = st.columns(2)

with c1:
    city = agg["by_city"]
    fig  = go.Figure(go.Bar(x=city["City"],y=city["Sales"],marker_color=CLR,
                             text=city["Sales"].apply(fmt),textposition="outside",textfont=dict(size=10)))
    T(fig,280,"Top 10 Cities by Revenue").update_layout(showlegend=False)
    fig.update_xaxes(tickangle=-35)
    st.plotly_chart(fig,use_container_width=True)

with c2:
    dm  = agg["disc_m"]
    fig = make_subplots(specs=[[{"secondary_y":True}]])
    fig.add_trace(go.Bar(x=dm["Disc Band"].astype(str),y=dm["Sales"],name="Sales",
                          marker_color="#00d4ff44"),secondary_y=False)
    fig.add_trace(go.Scatter(x=dm["Disc Band"].astype(str),y=dm["Margin%"],name="Margin %",
                              line=dict(color="#ff4757",width=2.5),marker=dict(size=8)),secondary_y=True)
    fig.update_layout(height=280,title=dict(text="Discount Band vs Profit Margin",font=dict(size=13,color="#e2e8f0")),
                      paper_bgcolor=PBG,plot_bgcolor=PBG,font=dict(color=TXT),
                      margin=dict(l=10,r=10,t=38,b=10),legend=dict(bgcolor="rgba(0,0,0,0)"))
    fig.update_xaxes(gridcolor=GRID); fig.update_yaxes(gridcolor=GRID)
    st.plotly_chart(fig,use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
#  LIVE ORDER FEED
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">⚡ LIVE ORDER FEED</div>', unsafe_allow_html=True)

if ss.live_orders:
    rows = []
    for o in ss.live_orders[:15]:
        rows.append({
            "Time":     o["time"],
            "Order ID": o["order_id"],
            "Category": o["category"],
            "Sub-Cat":  o["sub"],
            "Product":  o["product"],
            "Qty":      o["qty"],
            "Sales ₹":  fmt(o["sales"]),
            "Profit":   ("🟢 " if o["profit"]>=0 else "🔴 ")+fmt(abs(o["profit"])),
            "Margin":   f"{o['margin_pct']}%",
            "Region":   o["region"],
            "Segment":  o["segment"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, height=420)
else:
    st.info("⏳ Live orders will appear here…")

# ══════════════════════════════════════════════════════════════════════════════
#  CONTROLS & AUTO-REFRESH
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
c1,c2,c3 = st.columns([4,1,1])
c1.markdown(f"<div style='color:#64748b;font-size:11px;padding-top:8px;'>"
            f"📡 Updated: {now_str} · +{ss.extra_orders} live orders · "
            f"{'⏸ Paused' if ss.paused else '▶ Auto-refreshing every 3s'}</div>",
            unsafe_allow_html=True)

if c2.button("⏸ Pause" if not ss.paused else "▶ Resume", use_container_width=True):
    ss.paused = not ss.paused
    st.rerun()

if c3.button("🔄 Refresh Now", use_container_width=True):
    st.rerun()

# Auto-refresh every 3 seconds when not paused
if not ss.paused:
    time.sleep(3)
    st.rerun()
