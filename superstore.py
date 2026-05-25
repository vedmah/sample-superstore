import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, date, timedelta

# ─── LIVE DATE ────────────────────────────────────────────────────────────────
TODAY        = datetime.now()
CURRENT_YEAR = TODAY.year
CURRENT_MON  = TODAY.month
DATA_THRU    = TODAY.strftime("%d %b %Y")   # e.g. "25 May 2026"

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=f"India Retail Analytics — Live {CURRENT_YEAR}",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}
#MainMenu{visibility:hidden;}footer{visibility:hidden;}header{visibility:hidden;}
[data-testid="collapsedControl"]{display:none!important;}
[data-testid="stSidebar"]{display:none!important;}
.stApp{background:#0a0e1a;}

.dash-header{background:linear-gradient(135deg,#0d1b3e 0%,#0f2b5b 50%,#1a1f3a 100%);
  border-bottom:1px solid #1e3a6e;padding:18px 24px 14px;border-radius:0 0 16px 16px;margin-bottom:18px;}
.dash-title{font-size:26px;font-weight:700;color:#e8ecf5;letter-spacing:-0.02em;display:flex;align-items:center;gap:10px;}
.dash-subtitle{font-size:13px;color:#5a7ab5;margin-top:3px;}

/* LIVE badge */
.live-badge{display:inline-flex;align-items:center;gap:5px;background:rgba(19,136,8,0.15);
  border:1px solid #138808;border-radius:20px;padding:3px 10px;font-size:11px;
  font-weight:600;color:#2ec27e;letter-spacing:0.05em;}
.live-dot{width:7px;height:7px;border-radius:50%;background:#2ec27e;
  animation:pulse 1.5s infinite;}
@keyframes pulse{0%,100%{opacity:1;}50%{opacity:0.3;}}

/* Last updated strip */
.last-updated{background:#0d1528;border:1px solid #1a3050;border-radius:8px;
  padding:6px 14px;font-size:12px;color:#4a6490;display:inline-flex;align-items:center;gap:8px;margin-bottom:14px;}

[data-testid="stMultiSelect"]>div{background:#111827!important;border:1px solid #1e3050!important;border-radius:8px!important;}
[data-testid="stMultiSelect"] span{color:#c8ccd8!important;}
.stMultiSelect label{color:#4a6490!important;font-size:10px!important;text-transform:uppercase;letter-spacing:0.07em;}
[data-testid="stSelectbox"]>div>div{background:#111827!important;border:1px solid #1e3050!important;border-radius:8px!important;color:#c8ccd8!important;}
.stSelectbox label{color:#4a6490!important;font-size:10px!important;text-transform:uppercase;letter-spacing:0.07em;}

.kpi-row{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:16px;}
.kpi{background:linear-gradient(135deg,#111827,#151f35);border:1px solid #1e3050;border-radius:12px;
     padding:16px 18px;position:relative;overflow:hidden;}
.kpi::before{content:'';position:absolute;top:0;left:0;width:3px;height:100%;border-radius:3px 0 0 3px;}
.kpi.saffron::before{background:#FF9933;}
.kpi.white::before{background:#e8ecf5;}
.kpi.green::before{background:#138808;}
.kpi.blue::before{background:#4f8ef7;}
.kpi.purple::before{background:#a78bfa;}
.kpi-icon{font-size:18px;margin-bottom:6px;}
.kpi-label{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.1em;color:#4a6490;margin-bottom:4px;}
.kpi-value{font-size:22px;font-weight:700;color:#e8ecf5;font-family:'DM Mono',monospace;line-height:1.1;}
.kpi-sub{font-size:11px;margin-top:4px;color:#5a7ab5;}
.kpi-sub.pos{color:#138808;}
.kpi-sub.neg{color:#e05c5c;}

/* YTD highlight card */
.ytd-card{background:linear-gradient(135deg,#0d2010,#0f2b10);border:1px solid #1a4020;
  border-radius:12px;padding:14px 18px;margin-bottom:14px;}
.ytd-title{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.1em;
  color:#2ec27e;margin-bottom:8px;display:flex;align-items:center;gap:6px;}
.ytd-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;}
.ytd-item{text-align:center;}
.ytd-val{font-size:18px;font-weight:700;color:#e8ecf5;font-family:'DM Mono',monospace;}
.ytd-lbl{font-size:10px;color:#4a7050;margin-top:2px;}

.filter-label{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.1em;color:#4a6490;margin-bottom:6px;}
.sec{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#4a6490;
     padding:8px 0;border-bottom:1px solid #1a2540;margin-bottom:2px;display:flex;align-items:center;gap:8px;}
hr{border-color:#1a2540!important;}
.stSlider label{color:#4a6490!important;font-size:10px!important;text-transform:uppercase;}
</style>
""", unsafe_allow_html=True)

# ─── PLOT LAYOUT HELPER ───────────────────────────────────────────────────────
def PL(title="", height=None, margin=None, extra=None):
    m = margin or dict(l=8, r=8, t=36, b=8)
    base = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color="#c8ccd8", size=11),
        margin=m,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10, color="#7c8db5")),
        xaxis=dict(gridcolor="#141e30", linecolor="#1e3050", tickcolor="#1e3050",
                   tickfont=dict(size=10, color="#5a7ab5"), zeroline=False),
        yaxis=dict(gridcolor="#141e30", linecolor="#1e3050", tickcolor="#1e3050",
                   tickfont=dict(size=10, color="#5a7ab5"), zeroline=False),
        colorway=["#FF9933","#138808","#4f8ef7","#a78bfa","#f7a83e","#e05c8b","#34d399"],
    )
    if title:
        base["title"] = dict(text=title, font=dict(size=12, color="#7c8db5"))
    if height:
        base["height"] = height
    if extra:
        base.update(extra)
    return base

C = {
    "saffron":"#FF9933","green":"#138808","blue":"#4f8ef7","navy":"#000080",
    "purple":"#a78bfa","amber":"#f7a83e","pink":"#e05c8b","teal":"#34d399","red":"#f87171",
    "cat":{
        "Electronics":"#4f8ef7","Furniture":"#f7a83e",
        "Office Supplies":"#138808","Clothing":"#FF9933","Home & Kitchen":"#a78bfa",
    },
    "region":{"North":"#FF9933","South":"#138808","East":"#4f8ef7","West":"#a78bfa","Central":"#f7a83e"},
    "seg":{"Consumer":"#4f8ef7","Corporate":"#FF9933","Small Business":"#138808","Government":"#a78bfa"},
    "ship":{"Standard Delivery":"#4f8ef7","Express Delivery":"#FF9933",
            "Same Day Delivery":"#f87171","Economy Delivery":"#138808"},
}

# ─── LOAD DATA ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)   # refresh cache every hour for "live" feel
def load_data(file=None):
    if file is not None:
        df = pd.read_csv(file)
    else:
        candidates = [
            "IndiaSuperstore.csv",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "IndiaSuperstore.csv"),
            os.path.join(os.getcwd(), "IndiaSuperstore.csv"),
        ]
        df = None
        for p in candidates:
            if os.path.exists(p):
                df = pd.read_csv(p)
                break
        if df is None:
            return None
    df.columns   = df.columns.str.strip()
    df["Sales"]      = pd.to_numeric(df["Sales"],    errors="coerce")
    df["Profit"]     = pd.to_numeric(df["Profit"],   errors="coerce")
    df["Quantity"]   = pd.to_numeric(df["Quantity"], errors="coerce")
    df["Discount"]   = pd.to_numeric(df["Discount"], errors="coerce")
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    # ── Derived time columns ──────────────────────────────────────────────────
    df["Year"]       = df["Order Date"].dt.year
    df["Month"]      = df["Order Date"].dt.month
    df["MonthName"]  = df["Order Date"].dt.strftime("%b")
    df["Quarter"]    = "Q" + df["Order Date"].dt.quarter.astype(str)
    df["YearMonth"]  = df["Order Date"].dt.to_period("M").astype(str)
    df["Week"]       = df["Order Date"].dt.isocalendar().week.astype(int)
    df["YearWeek"]   = df["Order Date"].dt.strftime("%Y-W%V")
    df["DayOfWeek"]  = df["Order Date"].dt.day_name()
    return df

df = load_data()

if df is None:
    st.markdown("""
    <div style='text-align:center;padding:80px 20px'>
      <div style='font-size:52px;margin-bottom:16px'>📂</div>
      <div style='font-size:22px;font-weight:600;color:#e8ecf5;margin-bottom:8px'>Upload IndiaSuperstore.csv</div>
      <div style='font-size:14px;color:#5a7ab5'>Upload the dataset file below to begin.</div>
    </div>""", unsafe_allow_html=True)
    up = st.file_uploader("Upload IndiaSuperstore.csv", type=["csv"])
    if up:
        df = load_data(file=up)
        st.rerun()
    else:
        st.stop()

# ─── LIVE HEADER ─────────────────────────────────────────────────────────────
latest_date  = df["Order Date"].max()
earliest_date = df["Order Date"].min()
days_since   = (TODAY - latest_date).days

st.markdown(f"""
<div class="dash-header">
  <div class="dash-title">
    🇮🇳 India Retail Analytics Dashboard
    <span class="live-badge"><span class="live-dot"></span>LIVE</span>
  </div>
  <div class="dash-subtitle">
    State-wise Sales Intelligence &nbsp;•&nbsp; 26 States &nbsp;•&nbsp; 156 Cities &nbsp;•&nbsp;
    Data: {earliest_date.strftime('%d %b %Y')} → <b style="color:#2ec27e">{latest_date.strftime('%d %b %Y')}</b>
    &nbsp;•&nbsp; Updated: {DATA_THRU}
  </div>
</div>""", unsafe_allow_html=True)

# ─── FILTER BAR ──────────────────────────────────────────────────────────────
st.markdown('<div class="filter-label">🔽 &nbsp;Dashboard Filters</div>', unsafe_allow_html=True)

col_r, col_s, col_st, col_cat, col_seg, col_ship, col_yr, col_btn = st.columns([1,1,1.2,1.2,1,1,0.8,0.7])

with col_r:
    sel_region = st.multiselect("Region", sorted(df["Region"].unique()), default=sorted(df["Region"].unique()), key="region")
with col_s:
    state_opts = sorted(df[df["Region"].isin(sel_region)]["State"].unique())
    sel_state  = st.multiselect("State", state_opts, default=state_opts, key="state")
with col_st:
    city_opts  = sorted(df[df["State"].isin(sel_state)]["City"].unique())
    sel_city   = st.multiselect("City", city_opts, default=city_opts, key="city")
with col_cat:
    sel_cat    = st.multiselect("Category", sorted(df["Category"].unique()), default=sorted(df["Category"].unique()), key="cat")
with col_seg:
    sel_seg    = st.multiselect("Segment", sorted(df["Segment"].unique()), default=sorted(df["Segment"].unique()), key="seg")
with col_ship:
    sel_ship   = st.multiselect("Ship Mode", sorted(df["Ship Mode"].unique()), default=sorted(df["Ship Mode"].unique()), key="ship")
with col_yr:
    all_years  = sorted(df["Year"].unique().tolist())
    sel_yr     = st.multiselect("Year", all_years, default=all_years, key="yr")
with col_btn:
    st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
    if st.button("↺ Reset", use_container_width=True):
        st.session_state.clear(); st.rerun()

st.markdown("---")

# ─── FILTER DATA ─────────────────────────────────────────────────────────────
dff = df[
    df["Region"].isin(sel_region) &
    df["State"].isin(sel_state)   &
    df["City"].isin(sel_city)     &
    df["Category"].isin(sel_cat)  &
    df["Segment"].isin(sel_seg)   &
    df["Ship Mode"].isin(sel_ship)&
    df["Year"].isin(sel_yr)
]

if dff.empty:
    st.warning("No data matches your filters. Please adjust selections.")
    st.stop()

# ─── YTD PANEL (current year only) ───────────────────────────────────────────
ytd = dff[dff["Year"] == CURRENT_YEAR]
prev_yr = dff[dff["Year"] == CURRENT_YEAR - 1]

if not ytd.empty:
    ytd_sales   = ytd["Sales"].sum()
    ytd_profit  = ytd["Profit"].sum()
    ytd_orders  = len(ytd)
    ytd_qty     = ytd["Quantity"].sum()

    # Compare same period last year (Jan 1 → today's month last year)
    prev_same = prev_yr[prev_yr["Month"] <= CURRENT_MON]
    prev_sales = prev_same["Sales"].sum()
    growth = ((ytd_sales - prev_sales) / prev_sales * 100) if prev_sales else 0
    arrow  = "▲" if growth >= 0 else "▼"
    g_col  = "#2ec27e" if growth >= 0 else "#f87171"

    st.markdown(f"""
    <div class="ytd-card">
      <div class="ytd-title">
        📅 &nbsp;{CURRENT_YEAR} Year-to-Date &nbsp;(Jan – {TODAY.strftime('%b %Y')})
        &nbsp;&nbsp;
        <span style="font-size:12px;color:{g_col}">{arrow} {abs(growth):.1f}% vs same period {CURRENT_YEAR-1}</span>
      </div>
      <div class="ytd-grid">
        <div class="ytd-item"><div class="ytd-val">₹{ytd_sales/1e5:.1f}L</div><div class="ytd-lbl">YTD Revenue</div></div>
        <div class="ytd-item"><div class="ytd-val">₹{ytd_profit/1e5:.1f}L</div><div class="ytd-lbl">YTD Profit</div></div>
        <div class="ytd-item"><div class="ytd-val">{ytd_orders:,}</div><div class="ytd-lbl">YTD Orders</div></div>
        <div class="ytd-item"><div class="ytd-val">{ytd_qty:,}</div><div class="ytd-lbl">YTD Units</div></div>
      </div>
    </div>""", unsafe_allow_html=True)

# ─── KPI CARDS (all-time filtered) ───────────────────────────────────────────
tot_sales  = dff["Sales"].sum()
tot_profit = dff["Profit"].sum()
tot_orders = len(dff)
tot_qty    = dff["Quantity"].sum()
avg_margin = (tot_profit / tot_sales * 100) if tot_sales else 0
avg_disc   = dff["Discount"].mean() * 100
aov        = tot_sales / max(tot_orders, 1)

def fmt_cr(v): return f"₹{v/1e7:.2f} Cr" if v >= 1e7 else f"₹{v/1e5:.1f}L"

st.markdown(f"""
<div class="kpi-row">
  <div class="kpi saffron">
    <div class="kpi-icon">💰</div>
    <div class="kpi-label">Total Revenue</div>
    <div class="kpi-value">{fmt_cr(tot_sales)}</div>
    <div class="kpi-sub pos">▲ {tot_orders:,} orders</div>
  </div>
  <div class="kpi green">
    <div class="kpi-icon">📈</div>
    <div class="kpi-label">Net Profit</div>
    <div class="kpi-value">{fmt_cr(tot_profit)}</div>
    <div class="kpi-sub {'pos' if tot_profit>0 else 'neg'}">{'▲' if tot_profit>0 else '▼'} Margin {avg_margin:.1f}%</div>
  </div>
  <div class="kpi blue">
    <div class="kpi-icon">📦</div>
    <div class="kpi-label">Units Sold</div>
    <div class="kpi-value">{tot_qty:,}</div>
    <div class="kpi-sub pos">▲ Avg {tot_qty/max(tot_orders,1):.1f}/order</div>
  </div>
  <div class="kpi purple">
    <div class="kpi-icon">🏷️</div>
    <div class="kpi-label">Avg Order Value</div>
    <div class="kpi-value">₹{aov:,.0f}</div>
    <div class="kpi-sub">Avg disc {avg_disc:.1f}%</div>
  </div>
  <div class="kpi white">
    <div class="kpi-icon">🏙️</div>
    <div class="kpi-label">Active Cities</div>
    <div class="kpi-value">{dff['City'].nunique()}</div>
    <div class="kpi-sub">{dff['State'].nunique()} states • {dff['Year'].nunique()} yrs</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — LIVE TREND: Monthly + Last 12 Months Rolling
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec">📅 &nbsp;Revenue Trend & Seasonality</div>', unsafe_allow_html=True)
tr1, tr2 = st.columns([1.6, 1])

with tr1:
    trend = dff.groupby("YearMonth").agg(Sales=("Sales","sum"), Profit=("Profit","sum")).reset_index().sort_values("YearMonth")
    fig_tr = go.Figure()
    fig_tr.add_trace(go.Scatter(
        x=trend["YearMonth"], y=trend["Sales"], name="Revenue",
        line=dict(color=C["saffron"], width=2.5),
        fill="tozeroy", fillcolor="rgba(255,153,51,0.08)",
        mode="lines+markers", marker=dict(size=4, color=C["saffron"])
    ))
    fig_tr.add_trace(go.Scatter(
        x=trend["YearMonth"], y=trend["Profit"], name="Profit",
        line=dict(color=C["green"], width=2),
        mode="lines+markers", marker=dict(size=4, color=C["green"])
    ))
    # vertical line for current month
    curr_ym = TODAY.strftime("%Y-%m")
    if curr_ym in trend["YearMonth"].values:
        fig_tr.add_vline(x=curr_ym, line_color="#4f8ef7", line_dash="dot", line_width=1.5,
                         annotation_text="Today", annotation_font_color="#4f8ef7", annotation_font_size=10)
    fig_tr.update_layout(**PL("Monthly Revenue & Profit Trend (2021 → Present)", height=290,
        extra={"legend":dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                             font=dict(size=10,color="#7c8db5"), bgcolor="rgba(0,0,0,0)")}))
    fig_tr.update_xaxes(tickangle=-45, nticks=30)
    fig_tr.update_yaxes(tickprefix="₹", tickformat=",.0f")
    st.plotly_chart(fig_tr, use_container_width=True)

with tr2:
    # Last 12 months rolling
    cutoff_12m = TODAY - timedelta(days=365)
    last12 = dff[dff["Order Date"] >= cutoff_12m].groupby("YearMonth").agg(Sales=("Sales","sum")).reset_index().sort_values("YearMonth")
    fig_12 = go.Figure(go.Bar(
        x=last12["YearMonth"], y=last12["Sales"],
        marker_color=C["blue"], marker_line_width=0,
        text=[f"₹{v/1e5:.0f}L" for v in last12["Sales"]],
        textposition="outside", textfont=dict(size=9, color="#c8ccd8"),
    ))
    fig_12.update_layout(**PL("Last 12 Months Rolling Revenue", height=290))
    fig_12.update_xaxes(tickangle=-45)
    fig_12.update_yaxes(tickprefix="₹", tickformat=",.0f")
    st.plotly_chart(fig_12, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — YoY Comparison (every year including current partial)
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec">📆 &nbsp;Year-over-Year Performance</div>', unsafe_allow_html=True)
y1, y2, y3 = st.columns(3)

with y1:
    yoy_cat = dff.groupby(["Year","Category"])["Sales"].sum().reset_index()
    fig_yoy = px.bar(yoy_cat, x="Year", y="Sales", color="Category",
                     barmode="group", color_discrete_map=C["cat"], text_auto=False)
    fig_yoy.update_traces(marker_line_width=0)
    fig_yoy.update_layout(**PL("YoY Revenue by Category", height=280,
        extra={"legend":dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                             font=dict(size=9,color="#7c8db5"), bgcolor="rgba(0,0,0,0)")}))
    fig_yoy.update_yaxes(tickprefix="₹", tickformat=",.0f")
    st.plotly_chart(fig_yoy, use_container_width=True)

with y2:
    yoy_sum = dff.groupby("Year").agg(Sales=("Sales","sum"), Profit=("Profit","sum"), Orders=("Sales","count")).reset_index()
    yoy_sum["Margin"] = (yoy_sum["Profit"] / yoy_sum["Sales"] * 100).round(1)
    fig_yoy2 = go.Figure()
    fig_yoy2.add_trace(go.Bar(name="Revenue", x=yoy_sum["Year"], y=yoy_sum["Sales"], marker_color=C["saffron"], marker_line_width=0))
    fig_yoy2.add_trace(go.Bar(name="Profit",  x=yoy_sum["Year"], y=yoy_sum["Profit"], marker_color=C["green"],  marker_line_width=0))
    # annotate current year as partial
    if CURRENT_YEAR in yoy_sum["Year"].values:
        fig_yoy2.add_annotation(x=CURRENT_YEAR, y=yoy_sum[yoy_sum["Year"]==CURRENT_YEAR]["Sales"].values[0],
            text=f"YTD {TODAY.strftime('%b')}", showarrow=False,
            font=dict(size=9, color="#4f8ef7"), yshift=14)
    fig_yoy2.update_layout(**PL("Annual Revenue vs Profit", height=280,
        extra={"barmode":"group",
               "legend":dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                             font=dict(size=10,color="#7c8db5"), bgcolor="rgba(0,0,0,0)")}))
    fig_yoy2.update_yaxes(tickprefix="₹", tickformat=",.0f")
    st.plotly_chart(fig_yoy2, use_container_width=True)

with y3:
    # Growth % YoY
    yoy_g = yoy_sum.copy().sort_values("Year")
    yoy_g["Growth%"] = yoy_g["Sales"].pct_change() * 100
    yoy_g = yoy_g.dropna()
    fig_g = go.Figure(go.Bar(
        x=yoy_g["Year"], y=yoy_g["Growth%"],
        marker_color=[C["green"] if v >= 0 else C["red"] for v in yoy_g["Growth%"]],
        marker_line_width=0,
        text=[f"{v:.1f}%" for v in yoy_g["Growth%"]], textposition="outside",
        textfont=dict(size=11, color="#c8ccd8"),
    ))
    fig_g.add_hline(y=0, line_color=C["pink"], line_dash="dot", line_width=1)
    fig_g.update_layout(**PL("Revenue Growth % YoY", height=280))
    fig_g.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig_g, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Seasonality (month pattern across all years)
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec">🗓️ &nbsp;Seasonality & Monthly Patterns</div>', unsafe_allow_html=True)
sea1, sea2 = st.columns(2)

with sea1:
    month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    seas = dff.groupby("MonthName")["Sales"].sum().reset_index()
    seas["sort"] = seas["MonthName"].apply(lambda x: month_order.index(x) if x in month_order else 99)
    seas = seas.sort_values("sort")
    # highlight current month
    bar_colors = []
    for m in seas["MonthName"]:
        if m == TODAY.strftime("%b"):
            bar_colors.append("#4f8ef7")   # current month = blue
        elif m in ["Oct","Nov","Dec"]:
            bar_colors.append(C["saffron"]) # festive = orange
        else:
            bar_colors.append("#2a3a5c")
    fig_seas = go.Figure(go.Bar(
        x=seas["MonthName"], y=seas["Sales"],
        marker_color=bar_colors, marker_line_width=0,
        text=[f"₹{v/1e5:.0f}L" for v in seas["Sales"]], textposition="outside",
        textfont=dict(size=9, color="#c8ccd8"),
    ))
    fig_seas.update_layout(**PL(f"Monthly Seasonality — 🔵 Current Month, 🟠 Festive Season", height=280))
    fig_seas.update_yaxes(tickprefix="₹", tickformat=",.0f")
    st.plotly_chart(fig_seas, use_container_width=True)

with sea2:
    dow = dff.groupby("DayOfWeek")["Sales"].sum().reset_index()
    day_order_map = {"Monday":0,"Tuesday":1,"Wednesday":2,"Thursday":3,"Friday":4,"Saturday":5,"Sunday":6}
    dow["sort"] = dow["DayOfWeek"].map(day_order_map)
    dow = dow.sort_values("sort")
    fig_dow = go.Figure(go.Bar(
        x=dow["DayOfWeek"], y=dow["Sales"],
        marker_color=[C["saffron"] if d in ["Saturday","Sunday"] else "#2a3a5c" for d in dow["DayOfWeek"]],
        marker_line_width=0,
        text=[f"₹{v/1e5:.0f}L" for v in dow["Sales"]], textposition="outside",
        textfont=dict(size=9, color="#c8ccd8"),
    ))
    fig_dow.update_layout(**PL("Sales by Day of Week — 🟠 Weekend", height=280))
    fig_dow.update_yaxes(tickprefix="₹", tickformat=",.0f")
    st.plotly_chart(fig_dow, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Category Performance
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec">🛍️ &nbsp;Category Performance</div>', unsafe_allow_html=True)
ca1, ca2, ca3 = st.columns(3)

with ca1:
    cat_s = dff.groupby("Category")["Sales"].sum().reset_index().sort_values("Sales",ascending=False)
    fig_cs = go.Figure(go.Bar(
        x=cat_s["Category"], y=cat_s["Sales"],
        marker_color=[C["cat"][c] for c in cat_s["Category"]], marker_line_width=0,
        text=[f"₹{v/1e5:.0f}L" for v in cat_s["Sales"]], textposition="outside",
        textfont=dict(size=10, color="#c8ccd8"),
    ))
    fig_cs.update_layout(**PL("Revenue by Category", height=260))
    fig_cs.update_xaxes(tickangle=-20)
    fig_cs.update_yaxes(tickprefix="₹", tickformat=",.0f")
    st.plotly_chart(fig_cs, use_container_width=True)

with ca2:
    cat_p = dff.groupby("Category")["Profit"].sum().reset_index().sort_values("Profit",ascending=False)
    fig_cp = go.Figure(go.Bar(
        x=cat_p["Category"], y=cat_p["Profit"],
        marker_color=[C["green"] if v>=0 else C["red"] for v in cat_p["Profit"]], marker_line_width=0,
        text=[f"₹{v/1e5:.0f}L" for v in cat_p["Profit"]], textposition="outside",
        textfont=dict(size=10, color="#c8ccd8"),
    ))
    fig_cp.update_layout(**PL("Profit by Category", height=260))
    fig_cp.update_xaxes(tickangle=-20)
    fig_cp.update_yaxes(tickprefix="₹", tickformat=",.0f")
    st.plotly_chart(fig_cp, use_container_width=True)

with ca3:
    cat_qty = dff.groupby("Category")["Quantity"].sum().reset_index()
    fig_pie = go.Figure(go.Pie(
        labels=cat_qty["Category"], values=cat_qty["Quantity"], hole=0.55,
        marker_colors=[C["cat"][c] for c in cat_qty["Category"]],
        textinfo="label+percent", textfont=dict(size=10, color="#c8ccd8"),
        insidetextorientation="radial",
    ))
    fig_pie.update_layout(**PL("Units Share by Category", height=260, extra={"showlegend":False}))
    st.plotly_chart(fig_pie, use_container_width=True)

# Sub-categories
st.markdown('<div class="sec">📊 &nbsp;Sub-Category Deep Dive</div>', unsafe_allow_html=True)
sb1, sb2 = st.columns(2)

with sb1:
    sub_s = dff.groupby(["Category","Sub-Category"])["Sales"].sum().reset_index().sort_values("Sales")
    fig_ss = go.Figure(go.Bar(
        x=sub_s["Sales"], y=sub_s["Sub-Category"], orientation="h",
        marker_color=[C["cat"][c] for c in sub_s["Category"]], marker_line_width=0,
        text=[f"₹{v/1e5:.0f}L" for v in sub_s["Sales"]], textposition="outside",
        textfont=dict(size=9, color="#c8ccd8"),
    ))
    fig_ss.update_layout(**PL("Revenue by Sub-Category", height=480, margin=dict(l=8,r=70,t=36,b=8)))
    fig_ss.update_xaxes(tickprefix="₹", tickformat=",.0f")
    st.plotly_chart(fig_ss, use_container_width=True)

with sb2:
    sub_p = dff.groupby("Sub-Category")["Profit"].sum().reset_index().sort_values("Profit")
    fig_sp = go.Figure(go.Bar(
        x=sub_p["Profit"], y=sub_p["Sub-Category"], orientation="h",
        marker_color=[C["green"] if v>=0 else C["red"] for v in sub_p["Profit"]], marker_line_width=0,
        text=[f"₹{v/1e5:.0f}L" for v in sub_p["Profit"]], textposition="outside",
        textfont=dict(size=9, color="#c8ccd8"),
    ))
    fig_sp.update_layout(**PL("Profit/Loss by Sub-Category", height=480, margin=dict(l=8,r=70,t=36,b=8)))
    fig_sp.update_xaxes(tickprefix="₹", tickformat=",.0f")
    st.plotly_chart(fig_sp, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — State-wise Geography
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec">🗺️ &nbsp;State-wise & Regional Analysis</div>', unsafe_allow_html=True)
g1, g2 = st.columns([1.4, 0.6])

with g1:
    top_n = st.slider("Top N States", 5, 26, 15, key="top_states")
    state_d = (
        dff.groupby(["State","Region"])
        .agg(Sales=("Sales","sum"), Profit=("Profit","sum"), Orders=("Sales","count"))
        .reset_index().sort_values("Sales",ascending=False).head(top_n).sort_values("Sales")
    )
    fig_st = go.Figure()
    fig_st.add_trace(go.Bar(name="Revenue", x=state_d["Sales"],  y=state_d["State"],
        orientation="h", marker_color=[C["region"][r] for r in state_d["Region"]], marker_line_width=0))
    fig_st.add_trace(go.Bar(name="Profit",  x=state_d["Profit"], y=state_d["State"],
        orientation="h", marker_color=C["green"], marker_line_width=0, opacity=0.75))
    fig_st.update_layout(**PL(f"Top {top_n} States — Revenue vs Profit",
        height=top_n*30+80, margin=dict(l=8,r=10,t=36,b=8),
        extra={"barmode":"overlay",
               "legend":dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                             font=dict(size=10,color="#7c8db5"), bgcolor="rgba(0,0,0,0)")}))
    fig_st.update_xaxes(tickprefix="₹", tickformat=",.0f")
    st.plotly_chart(fig_st, use_container_width=True)

with g2:
    reg = dff.groupby("Region")["Sales"].sum().reset_index()
    fig_r = go.Figure(go.Pie(
        labels=reg["Region"], values=reg["Sales"], hole=0.55,
        marker_colors=[C["region"][r] for r in reg["Region"]],
        textinfo="label+percent", textfont=dict(size=11, color="#c8ccd8"),
        insidetextorientation="radial",
    ))
    fig_r.update_layout(**PL("Revenue by Region", height=300, extra={"showlegend":False}))
    st.plotly_chart(fig_r, use_container_width=True)

    state_profit_heat = dff.pivot_table(index="State", columns="Year", values="Profit", aggfunc="sum").fillna(0)
    fig_sph = go.Figure(go.Heatmap(
        z=state_profit_heat.values,
        x=[str(c) for c in state_profit_heat.columns.tolist()],
        y=state_profit_heat.index.tolist(),
        colorscale=[[0,"#f87171"],[0.5,"#0a1628"],[1,"#138808"]],
        text=[[f"₹{v/1e5:.0f}L" for v in row] for row in state_profit_heat.values],
        texttemplate="%{text}", textfont=dict(size=7, color="#e8ecf5"),
        showscale=True, colorbar=dict(tickfont=dict(color="#5a7ab5",size=9),thickness=10),
    ))
    fig_sph.update_layout(**PL("State Profit by Year", height=320, margin=dict(l=8,r=60,t=36,b=8)))
    st.plotly_chart(fig_sph, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Heatmaps, Margin, Discount Scatter
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec">🔥 &nbsp;Cross-Dimensional Analysis</div>', unsafe_allow_html=True)
h1, h2 = st.columns(2)

with h1:
    heat = dff.pivot_table(index="Category", columns="Region", values="Sales", aggfunc="sum").fillna(0)
    fig_hm = go.Figure(go.Heatmap(
        z=heat.values, x=heat.columns.tolist(), y=heat.index.tolist(),
        colorscale=[[0,"#0a1628"],[0.4,"#0f3460"],[0.7,"#FF9933"],[1,"#138808"]],
        text=[[f"₹{v/1e5:.0f}L" for v in row] for row in heat.values],
        texttemplate="%{text}", textfont=dict(size=11, color="#e8ecf5"),
        showscale=True, colorbar=dict(tickfont=dict(color="#5a7ab5",size=9),thickness=10),
    ))
    fig_hm.update_layout(**PL("Revenue Heatmap: Category × Region", height=260, margin=dict(l=8,r=60,t=36,b=8)))
    st.plotly_chart(fig_hm, use_container_width=True)

with h2:
    seg_cat = dff.pivot_table(index="Segment", columns="Category", values="Sales", aggfunc="sum").fillna(0)
    fig_hm2 = go.Figure(go.Heatmap(
        z=seg_cat.values, x=seg_cat.columns.tolist(), y=seg_cat.index.tolist(),
        colorscale=[[0,"#0a1628"],[0.4,"#1a3a6e"],[0.7,"#4f8ef7"],[1,"#a78bfa"]],
        text=[[f"₹{v/1e5:.0f}L" for v in row] for row in seg_cat.values],
        texttemplate="%{text}", textfont=dict(size=11, color="#e8ecf5"),
        showscale=True, colorbar=dict(tickfont=dict(color="#5a7ab5",size=9),thickness=10),
    ))
    fig_hm2.update_layout(**PL("Revenue Heatmap: Segment × Category", height=260, margin=dict(l=8,r=60,t=36,b=8)))
    st.plotly_chart(fig_hm2, use_container_width=True)

m1, m2 = st.columns(2)
with m1:
    margin_sub = (
        dff.groupby("Sub-Category")
        .apply(lambda x: (x["Profit"].sum()/x["Sales"].sum())*100 if x["Sales"].sum() else 0)
        .reset_index(name="Margin").sort_values("Margin",ascending=False)
    )
    fig_mg = go.Figure(go.Bar(
        x=margin_sub["Sub-Category"], y=margin_sub["Margin"],
        marker_color=[C["green"] if v>=0 else C["red"] for v in margin_sub["Margin"]],
        marker_line_width=0,
        text=[f"{v:.1f}%" for v in margin_sub["Margin"]], textposition="outside",
        textfont=dict(size=9, color="#c8ccd8"),
    ))
    fig_mg.add_hline(y=0, line_color=C["pink"], line_dash="dot", line_width=1)
    fig_mg.update_layout(**PL("Profit Margin % by Sub-Category", height=270))
    fig_mg.update_xaxes(tickangle=-40)
    fig_mg.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig_mg, use_container_width=True)

with m2:
    samp = dff.sample(min(3000,len(dff)), random_state=42)
    fig_sc = go.Figure(go.Scatter(
        x=samp["Discount"], y=samp["Profit"], mode="markers",
        marker=dict(size=4, color=samp["Sales"],
                    colorscale=[[0,"#0a1628"],[0.5,"#FF9933"],[1,"#138808"]],
                    showscale=True,
                    colorbar=dict(title=dict(text="Sales (₹)",font=dict(color="#5a7ab5",size=9)),
                                  tickfont=dict(color="#5a7ab5",size=9),thickness=10,len=0.7),
                    opacity=0.65, line=dict(width=0)),
        hovertemplate="Discount: %{x:.0%}<br>Profit: ₹%{y:,.0f}<extra></extra>",
    ))
    fig_sc.add_hline(y=0, line_color=C["pink"], line_dash="dot", line_width=1.5)
    fig_sc.update_layout(**PL("Discount vs Profit Impact", height=270))
    fig_sc.update_xaxes(tickformat=".0%", title_text="Discount", title_font=dict(size=10,color="#5a7ab5"))
    fig_sc.update_yaxes(tickprefix="₹", title_text="Profit",    title_font=dict(size=10,color="#5a7ab5"))
    st.plotly_chart(fig_sc, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — Segment & Ship Mode
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec">👥 &nbsp;Segment & Shipping Analysis</div>', unsafe_allow_html=True)

def donut(grp, col, cmap, title, height=220):
    fig = go.Figure(go.Pie(
        labels=grp[col], values=grp["Sales"], hole=0.55,
        marker_colors=[cmap.get(v,"#888") for v in grp[col]],
        textinfo="label+percent", textfont=dict(size=10,color="#c8ccd8"),
        insidetextorientation="radial",
    ))
    fig.update_layout(**PL(title, height=height, extra={"showlegend":False}))
    return fig

d1, d2, d3, d4 = st.columns(4)
qcolors = {"Q1":C["blue"],"Q2":C["saffron"],"Q3":C["purple"],"Q4":C["green"]}
with d1:
    st.plotly_chart(donut(dff.groupby("Segment")["Sales"].sum().reset_index(),  "Segment",  C["seg"],   "Sales by Segment"),   use_container_width=True)
with d2:
    st.plotly_chart(donut(dff.groupby("Ship Mode")["Sales"].sum().reset_index(),"Ship Mode",C["ship"],  "Sales by Ship Mode"), use_container_width=True)
with d3:
    st.plotly_chart(donut(dff.groupby("Quarter")["Sales"].sum().reset_index(),  "Quarter",  qcolors,    "Sales by Quarter"),   use_container_width=True)
with d4:
    seg_p = dff.groupby("Segment")["Profit"].sum().reset_index().sort_values("Profit",ascending=False)
    fig_sp2 = go.Figure(go.Bar(
        x=seg_p["Segment"], y=seg_p["Profit"],
        marker_color=[C["seg"][s] for s in seg_p["Segment"]], marker_line_width=0,
        text=[f"₹{v/1e5:.0f}L" for v in seg_p["Profit"]], textposition="outside",
        textfont=dict(size=10, color="#c8ccd8"),
    ))
    fig_sp2.update_layout(**PL("Profit by Segment", height=220))
    fig_sp2.update_yaxes(tickprefix="₹", tickformat=",.0f")
    st.plotly_chart(fig_sp2, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — City & Product Tables
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec">🏙️ &nbsp;City & Product Intelligence</div>', unsafe_allow_html=True)
tb1, tb2 = st.columns(2)

with tb1:
    city_df = (
        dff.groupby(["City","State","Region"])
        .agg(Revenue=("Sales","sum"), Profit=("Profit","sum"),
             Orders=("Sales","count"), Qty=("Quantity","sum"))
        .reset_index().sort_values("Revenue",ascending=False).head(20)
    )
    city_df["Margin%"] = (city_df["Profit"]/city_df["Revenue"]*100).round(1).map("{:.1f}%".format)
    city_df["Revenue"] = city_df["Revenue"].map("₹{:,.0f}".format)
    city_df["Profit"]  = city_df["Profit"].map("₹{:,.0f}".format)
    st.markdown("**🏆 Top 20 Cities by Revenue**")
    st.dataframe(city_df, use_container_width=True, hide_index=True, height=460)

with tb2:
    prod_df = (
        dff.groupby(["Product Name","Category","Sub-Category"])
        .agg(Revenue=("Sales","sum"), Profit=("Profit","sum"),
             Orders=("Sales","count"), Qty=("Quantity","sum"))
        .reset_index().sort_values("Revenue",ascending=False).head(20)
    )
    prod_df["Margin%"] = (prod_df["Profit"]/prod_df["Revenue"]*100).round(1).map("{:.1f}%".format)
    prod_df["Revenue"] = prod_df["Revenue"].map("₹{:,.0f}".format)
    prod_df["Profit"]  = prod_df["Profit"].map("₹{:,.0f}".format)
    st.markdown("**🛒 Top 20 Products by Revenue**")
    st.dataframe(prod_df, use_container_width=True, hide_index=True, height=460)

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f"<div style='text-align:center;color:#1e3050;font-size:12px;padding:8px 0'>"
    f"🇮🇳 India Retail Analytics Dashboard &nbsp;•&nbsp; Data through {DATA_THRU} &nbsp;•&nbsp; "
    f"Streamlit + Plotly &nbsp;•&nbsp; Refreshes hourly</div>",
    unsafe_allow_html=True,
)
