import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Superstore Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CUSTOM CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
#MainMenu {visibility: hidden;}
footer     {visibility: hidden;}
header     {visibility: hidden;}
[data-testid="collapsedControl"] { display: none !important; }
[data-testid="stSidebar"]        { display: none !important; }
.stApp { background: #0f1117; }
.filter-title { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #5a6482; margin-bottom: 6px; }
[data-testid="stMultiSelect"] > div { background: #1e2538 !important; border-color: #2a3150 !important; border-radius: 8px !important; }
[data-testid="stMultiSelect"] span  { color: #c8ccd8 !important; }
.stMultiSelect label { color: #7c8db5 !important; font-size: 11px !important; text-transform: uppercase; letter-spacing: 0.06em; }
.kpi-card { background: linear-gradient(135deg, #1a2035 0%, #1e2640 100%); border: 1px solid #2a3150; border-radius: 12px; padding: 18px 20px; position: relative; overflow: hidden; }
.kpi-card::after { content: ''; position: absolute; top: 0; right: 0; width: 60px; height: 60px; border-radius: 0 12px 0 100%; opacity: 0.18; }
.kpi-card.blue::after  { background: #4f8ef7; }
.kpi-card.green::after { background: #2ec27e; }
.kpi-card.amber::after { background: #f7a83e; }
.kpi-card.pink::after  { background: #e05c8b; }
.kpi-icon  { font-size: 20px; margin-bottom: 8px; }
.kpi-label { font-size: 11px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.1em; color: #7c8db5; margin-bottom: 6px; }
.kpi-value { font-size: 28px; font-weight: 600; color: #e8ecf5; font-family: 'DM Mono', monospace; line-height: 1.1; }
.kpi-delta { font-size: 12px; margin-top: 4px; }
.kpi-delta.pos { color: #2ec27e; }
.kpi-delta.neg { color: #f87171; }
.section-header { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #7c8db5; padding-bottom: 8px; border-bottom: 1px solid #2a3150; margin-bottom: 4px; }
.dash-title    { font-size: 24px; font-weight: 600; color: #e8ecf5; letter-spacing: -0.02em; }
.dash-subtitle { font-size: 13px; color: #5a6482; margin-top: 2px; }
hr { border-color: #2a3150 !important; }
.stSlider label { color: #7c8db5 !important; font-size: 11px !important; text-transform: uppercase; letter-spacing: 0.06em; }
</style>
""", unsafe_allow_html=True)

# ─── PLOT LAYOUT HELPER (no margin in base — avoids **kwargs conflict) ────────
def plot_layout(title="", height=None, margin=None, extra=None):
    m = margin or dict(l=10, r=10, t=36, b=10)
    base = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color="#c8ccd8", size=12),
        margin=m,
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(255,255,255,0.05)", borderwidth=1, font=dict(size=11, color="#8a94b0")),
        xaxis=dict(gridcolor="#1e2538", linecolor="#2a3150", tickcolor="#2a3150", tickfont=dict(size=11, color="#7c8db5"), zeroline=False),
        yaxis=dict(gridcolor="#1e2538", linecolor="#2a3150", tickcolor="#2a3150", tickfont=dict(size=11, color="#7c8db5"), zeroline=False),
        colorway=["#4f8ef7","#2ec27e","#f7a83e","#e05c8b","#a78bfa","#34d399"],
    )
    if title:
        base["title"] = dict(text=title, font=dict(size=13, color="#8a94b0"))
    if height:
        base["height"] = height
    if extra:
        base.update(extra)
    return base

COLORS = {
    "blue":"#4f8ef7","green":"#2ec27e","amber":"#f7a83e","pink":"#e05c8b","purple":"#a78bfa","red":"#f87171",
    "cat":    {"Technology":"#4f8ef7","Furniture":"#f7a83e","Office Supplies":"#2ec27e"},
    "region": {"West":"#4f8ef7","East":"#2ec27e","Central":"#f7a83e","South":"#e05c8b"},
    "seg":    {"Consumer":"#a78bfa","Corporate":"#4f8ef7","Home Office":"#2ec27e"},
    "ship":   {"Standard Class":"#4f8ef7","Second Class":"#f7a83e","First Class":"#2ec27e","Same Day":"#e05c8b"},
}

# ─── LOAD DATA ───────────────────────────────────────────────────────────────
@st.cache_data
def load_data(file=None):
    if file is not None:
        df = pd.read_csv(file)
    else:
        candidates = [
            "SampleSuperstore.csv",
            "SampleSuperstore (1).csv",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "SampleSuperstore.csv"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "SampleSuperstore (1).csv"),
            os.path.join(os.getcwd(), "SampleSuperstore.csv"),
            os.path.join(os.getcwd(), "SampleSuperstore (1).csv"),
        ]
        df = None
        for path in candidates:
            if os.path.exists(path):
                df = pd.read_csv(path)
                break
        if df is None:
            return None
    df.columns  = df.columns.str.strip()
    df["Sales"]    = pd.to_numeric(df["Sales"],    errors="coerce")
    df["Profit"]   = pd.to_numeric(df["Profit"],   errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["Discount"] = pd.to_numeric(df["Discount"], errors="coerce")
    df["Margin"]   = (df["Profit"] / df["Sales"]) * 100
    return df

df = load_data()

if df is None:
    st.markdown("""
    <div style='text-align:center;padding:80px 20px'>
      <div style='font-size:52px;margin-bottom:16px'>📂</div>
      <div style='font-size:22px;font-weight:600;color:#e8ecf5;margin-bottom:8px'>Upload your dataset</div>
      <div style='font-size:14px;color:#7c8db5'>Upload <b>SampleSuperstore.csv</b> below to begin.</div>
    </div>""", unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload SampleSuperstore.csv", type=["csv"])
    if uploaded:
        df = load_data(file=uploaded)
        st.rerun()
    else:
        st.stop()

# ─── HEADER ──────────────────────────────────────────────────────────────────
col_title, col_reset = st.columns([5, 1])
with col_title:
    st.markdown(
        '<div class="dash-title">📊 Superstore Sales Analytics</div>'
        '<div class="dash-subtitle">Power BI-style dashboard • Sample Superstore Dataset</div>',
        unsafe_allow_html=True,
    )
with col_reset:
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    if st.button("↺ Reset Filters", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.markdown("---")

# ─── INLINE FILTER BAR ───────────────────────────────────────────────────────
st.markdown('<div class="filter-title">🔽 &nbsp;Dashboard Filters</div>', unsafe_allow_html=True)
f1, f2, f3, f4 = st.columns(4)

with f1:
    regions = st.multiselect("Region", options=sorted(df["Region"].unique()), default=sorted(df["Region"].unique()), key="regions")
with f2:
    segments = st.multiselect("Segment", options=sorted(df["Segment"].unique()), default=sorted(df["Segment"].unique()), key="segments")
with f3:
    categories = st.multiselect("Category", options=sorted(df["Category"].unique()), default=sorted(df["Category"].unique()), key="categories")
with f4:
    ship_modes = st.multiselect("Ship Mode", options=sorted(df["Ship Mode"].unique()), default=sorted(df["Ship Mode"].unique()), key="ship_modes")

st.markdown("---")

# ─── FILTER DATA ─────────────────────────────────────────────────────────────
mask = (
    df["Region"].isin(regions) &
    df["Segment"].isin(segments) &
    df["Category"].isin(categories) &
    df["Ship Mode"].isin(ship_modes)
)
dff = df[mask]

if dff.empty:
    st.warning("No data matches your filters. Please adjust your selections above.")
    st.stop()

# ─── KPI CARDS ───────────────────────────────────────────────────────────────
total_sales  = dff["Sales"].sum()
total_profit = dff["Profit"].sum()
total_orders = len(dff)
total_qty    = dff["Quantity"].sum()
avg_margin   = (total_profit / total_sales * 100) if total_sales else 0
avg_discount = dff["Discount"].mean() * 100
aov          = total_sales / max(total_orders, 1)

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f'<div class="kpi-card blue"><div class="kpi-icon">💰</div><div class="kpi-label">Total Sales</div><div class="kpi-value">${total_sales/1e6:.2f}M</div><div class="kpi-delta pos">▲ {total_orders:,} orders</div></div>', unsafe_allow_html=True)
with k2:
    dc = "pos" if total_profit > 0 else "neg"
    arrow = "▲" if total_profit > 0 else "▼"
    st.markdown(f'<div class="kpi-card green"><div class="kpi-icon">📈</div><div class="kpi-label">Total Profit</div><div class="kpi-value">${total_profit/1e3:.1f}K</div><div class="kpi-delta {dc}">{arrow} Margin {avg_margin:.1f}%</div></div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div class="kpi-card amber"><div class="kpi-icon">📦</div><div class="kpi-label">Units Sold</div><div class="kpi-value">{total_qty:,}</div><div class="kpi-delta pos">▲ Avg {total_qty/max(total_orders,1):.1f} / order</div></div>', unsafe_allow_html=True)
with k4:
    st.markdown(f'<div class="kpi-card pink"><div class="kpi-icon">🏷️</div><div class="kpi-label">Avg Discount</div><div class="kpi-value">{avg_discount:.1f}%</div><div class="kpi-delta neg">AOV ${aov:.0f}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── SECTION 1: Category Performance ─────────────────────────────────────────
st.markdown('<div class="section-header">Category Performance</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)

with c1:
    cat_s = dff.groupby("Category")["Sales"].sum().reset_index().sort_values("Sales", ascending=False)
    fig = go.Figure(go.Bar(
        x=cat_s["Category"], y=cat_s["Sales"],
        marker_color=[COLORS["cat"][c] for c in cat_s["Category"]], marker_line_width=0,
        text=[f"${v/1e3:.0f}K" for v in cat_s["Sales"]], textposition="outside", textfont=dict(size=12, color="#c8ccd8"),
    ))
    fig.update_layout(**plot_layout("Sales by Category"))
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    cat_p = dff.groupby("Category")["Profit"].sum().reset_index().sort_values("Profit", ascending=False)
    fig2 = go.Figure(go.Bar(
        x=cat_p["Category"], y=cat_p["Profit"],
        marker_color=[COLORS["green"] if v >= 0 else COLORS["red"] for v in cat_p["Profit"]], marker_line_width=0,
        text=[f"${v/1e3:.0f}K" for v in cat_p["Profit"]], textposition="outside", textfont=dict(size=12, color="#c8ccd8"),
    ))
    fig2.update_layout(**plot_layout("Profit by Category"))
    fig2.update_yaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(fig2, use_container_width=True)

# ─── SECTION 2: Distribution Donuts ──────────────────────────────────────────
st.markdown('<div class="section-header">Distribution Analysis</div>', unsafe_allow_html=True)

def donut(grp_df, color_map, title):
    fig = go.Figure(go.Pie(
        labels=grp_df.iloc[:,0], values=grp_df["Sales"], hole=0.58,
        marker_colors=[color_map.get(v,"#888") for v in grp_df.iloc[:,0]],
        textinfo="label+percent", textfont=dict(size=11, color="#c8ccd8"), insidetextorientation="radial",
    ))
    fig.update_layout(**plot_layout(title, height=240, extra={"showlegend":False}))
    return fig

d1, d2, d3 = st.columns(3)
with d1:
    st.plotly_chart(donut(dff.groupby("Region")["Sales"].sum().reset_index(),   COLORS["region"], "Sales by Region"),    use_container_width=True)
with d2:
    st.plotly_chart(donut(dff.groupby("Segment")["Sales"].sum().reset_index(),  COLORS["seg"],    "Sales by Segment"),   use_container_width=True)
with d3:
    st.plotly_chart(donut(dff.groupby("Ship Mode")["Sales"].sum().reset_index(),COLORS["ship"],   "Sales by Ship Mode"), use_container_width=True)

# ─── SECTION 3: Sub-Category ─────────────────────────────────────────────────
st.markdown('<div class="section-header">Sub-Category Deep Dive</div>', unsafe_allow_html=True)
s1, s2 = st.columns(2)

with s1:
    sub_s = dff.groupby("Sub-Category")["Sales"].sum().reset_index().sort_values("Sales")
    fig_ss = go.Figure(go.Bar(
        x=sub_s["Sales"], y=sub_s["Sub-Category"], orientation="h",
        marker_color=COLORS["blue"], marker_line_width=0,
        text=[f"${v/1e3:.0f}K" for v in sub_s["Sales"]], textposition="outside", textfont=dict(size=10, color="#c8ccd8"),
    ))
    fig_ss.update_layout(**plot_layout("Sales by Sub-Category", height=420, margin=dict(l=10,r=70,t=36,b=10)))
    fig_ss.update_xaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(fig_ss, use_container_width=True)

with s2:
    sub_p = dff.groupby("Sub-Category")["Profit"].sum().reset_index().sort_values("Profit")
    fig_sp = go.Figure(go.Bar(
        x=sub_p["Profit"], y=sub_p["Sub-Category"], orientation="h",
        marker_color=[COLORS["green"] if v >= 0 else COLORS["red"] for v in sub_p["Profit"]], marker_line_width=0,
        text=[f"${v/1e3:.0f}K" for v in sub_p["Profit"]], textposition="outside", textfont=dict(size=10, color="#c8ccd8"),
    ))
    fig_sp.update_layout(**plot_layout("Profit / Loss by Sub-Category", height=420, margin=dict(l=10,r=70,t=36,b=10)))
    fig_sp.update_xaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(fig_sp, use_container_width=True)

# ─── SECTION 4: Geographic & Discount ────────────────────────────────────────
st.markdown('<div class="section-header">Geographic & Discount Insights</div>', unsafe_allow_html=True)
g1, g2 = st.columns([1.1, 0.9])

with g1:
    top_n = st.slider("Top N States to show", min_value=5, max_value=20, value=10, key="top_states")
    state_d = (
        dff.groupby("State").agg(Sales=("Sales","sum"), Profit=("Profit","sum"))
        .reset_index().sort_values("Sales", ascending=False).head(top_n).sort_values("Sales")
    )
    fig_st = go.Figure()
    fig_st.add_trace(go.Bar(name="Sales",  x=state_d["Sales"],  y=state_d["State"], orientation="h", marker_color=COLORS["blue"],  marker_line_width=0))
    fig_st.add_trace(go.Bar(name="Profit", x=state_d["Profit"], y=state_d["State"], orientation="h", marker_color=COLORS["green"], marker_line_width=0))
    fig_st.update_layout(**plot_layout(f"Top {top_n} States — Sales vs Profit", height=top_n*36+80, margin=dict(l=10,r=20,t=36,b=10), extra={"barmode":"overlay"}))
    fig_st.update_xaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(fig_st, use_container_width=True)

with g2:
    sample = dff.sample(min(2000, len(dff)), random_state=42)
    fig_sc = go.Figure(go.Scatter(
        x=sample["Discount"], y=sample["Profit"], mode="markers",
        marker=dict(size=5, color=sample["Sales"], colorscale=[[0,"#1e2538"],[0.5,"#4f8ef7"],[1,"#2ec27e"]],
                    showscale=True, colorbar=dict(title=dict(text="Sales ($)",font=dict(color="#7c8db5",size=11)), tickfont=dict(color="#7c8db5",size=10), thickness=10, len=0.7),
                    opacity=0.7, line=dict(width=0)),
        hovertemplate="Discount: %{x:.0%}<br>Profit: $%{y:,.0f}<extra></extra>",
    ))
    fig_sc.add_hline(y=0, line_color="#e05c8b", line_dash="dot", line_width=1.5)
    fig_sc.update_layout(**plot_layout("Discount vs Profit", height=380))
    fig_sc.update_xaxes(tickformat=".0%", title_text="Discount Rate", title_font=dict(size=11,color="#7c8db5"))
    fig_sc.update_yaxes(tickprefix="$", title_text="Profit ($)",      title_font=dict(size=11,color="#7c8db5"))
    st.plotly_chart(fig_sc, use_container_width=True)

# ─── SECTION 5: Cross-Dimensional ────────────────────────────────────────────
st.markdown('<div class="section-header">Cross-Dimensional Analysis</div>', unsafe_allow_html=True)
h1, h2 = st.columns(2)

with h1:
    heat = dff.pivot_table(index="Category", columns="Region", values="Profit", aggfunc="sum").fillna(0)
    fig_hm = go.Figure(go.Heatmap(
        z=heat.values, x=heat.columns.tolist(), y=heat.index.tolist(),
        colorscale=[[0,"#f87171"],[0.5,"#1e2538"],[1,"#2ec27e"]],
        text=[[f"${v/1e3:.0f}K" for v in row] for row in heat.values],
        texttemplate="%{text}", textfont=dict(size=13,color="#e8ecf5"),
        showscale=True, colorbar=dict(tickfont=dict(color="#7c8db5",size=10),thickness=10),
    ))
    fig_hm.update_layout(**plot_layout("Profit Heatmap: Category × Region", height=260, margin=dict(l=10,r=70,t=36,b=10)))
    st.plotly_chart(fig_hm, use_container_width=True)

with h2:
    margin_sub = (
        dff.groupby("Sub-Category")
        .apply(lambda x: (x["Profit"].sum()/x["Sales"].sum())*100 if x["Sales"].sum() else 0)
        .reset_index(name="Margin").sort_values("Margin", ascending=False)
    )
    fig_mg = go.Figure(go.Bar(
        x=margin_sub["Sub-Category"], y=margin_sub["Margin"],
        marker_color=[COLORS["green"] if v >= 0 else COLORS["red"] for v in margin_sub["Margin"]], marker_line_width=0,
        text=[f"{v:.1f}%" for v in margin_sub["Margin"]], textposition="outside", textfont=dict(size=10,color="#c8ccd8"),
    ))
    fig_mg.add_hline(y=0, line_color="#e05c8b", line_dash="dot", line_width=1)
    fig_mg.update_layout(**plot_layout("Profit Margin % by Sub-Category", height=260))
    fig_mg.update_xaxes(tickangle=-40)
    fig_mg.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig_mg, use_container_width=True)

# ─── SECTION 6: Cities Table & Quantity Mix ───────────────────────────────────
st.markdown('<div class="section-header">Top Cities & Quantity Mix</div>', unsafe_allow_html=True)
t1, t2 = st.columns([1.2, 0.8])

with t1:
    city_df = (
        dff.groupby(["City","State"]).agg(Sales=("Sales","sum"),Profit=("Profit","sum"),Orders=("Sales","count"))
        .reset_index().sort_values("Sales",ascending=False).head(15)
    )
    city_df["Margin %"] = (city_df["Profit"]/city_df["Sales"]*100).round(1).map("{:.1f}%".format)
    city_df["Sales"]    = city_df["Sales"].map("${:,.0f}".format)
    city_df["Profit"]   = city_df["Profit"].map("${:,.0f}".format)
    st.markdown("**Top 15 Cities by Sales**")
    st.dataframe(city_df, use_container_width=True, hide_index=True, height=420)

with t2:
    qty = dff.groupby(["Segment","Category"])["Quantity"].sum().reset_index()
    fig_q = px.bar(qty, x="Segment", y="Quantity", color="Category", barmode="group",
                   color_discrete_map=COLORS["cat"], text_auto=True)
    fig_q.update_traces(textfont_size=10, textposition="outside", marker_line_width=0)
    fig_q.update_layout(**plot_layout("Quantity: Segment × Category", height=420,
        extra={"legend":dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1,font=dict(size=11,color="#8a94b0"),bgcolor="rgba(0,0,0,0)")}))
    fig_q.update_yaxes(title_text="")
    st.plotly_chart(fig_q, use_container_width=True)

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("<div style='text-align:center;color:#3a4060;font-size:12px;padding:8px 0'>Superstore Analytics • Built with Streamlit & Plotly</div>", unsafe_allow_html=True)
