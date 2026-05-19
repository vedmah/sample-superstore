import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Superstore Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CUSTOM CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Hide default Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Main background */
.stApp {
    background: #0f1117;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #161b27;
    border-right: 1px solid #2a2f3e;
}
[data-testid="stSidebar"] * {
    color: #c8ccd8 !important;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label,
[data-testid="stSidebar"] h2, h3 {
    color: #7c8db5 !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* KPI Cards */
.kpi-card {
    background: linear-gradient(135deg, #1a2035 0%, #1e2640 100%);
    border: 1px solid #2a3150;
    border-radius: 12px;
    padding: 18px 20px;
    text-align: left;
    position: relative;
    overflow: hidden;
}
.kpi-card::after {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 60px; height: 60px;
    border-radius: 0 12px 0 100%;
    opacity: 0.15;
}
.kpi-card.blue::after  { background: #4f8ef7; }
.kpi-card.green::after { background: #2ec27e; }
.kpi-card.amber::after { background: #f7a83e; }
.kpi-card.pink::after  { background: #e05c8b; }

.kpi-label {
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #7c8db5;
    margin-bottom: 6px;
}
.kpi-value {
    font-size: 28px;
    font-weight: 600;
    color: #e8ecf5;
    font-family: 'DM Mono', monospace;
    line-height: 1.1;
}
.kpi-delta {
    font-size: 12px;
    margin-top: 4px;
}
.kpi-delta.pos { color: #2ec27e; }
.kpi-delta.neg { color: #e05c5c; }
.kpi-icon {
    font-size: 20px;
    margin-bottom: 8px;
}

/* Section headers */
.section-header {
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #7c8db5;
    margin-bottom: 4px;
    padding-bottom: 8px;
    border-bottom: 1px solid #2a3150;
}

/* Dashboard title */
.dash-title {
    font-size: 26px;
    font-weight: 600;
    color: #e8ecf5;
    letter-spacing: -0.02em;
}
.dash-subtitle {
    font-size: 13px;
    color: #5a6482;
    margin-top: 2px;
}

/* Divider */
hr {
    border-color: #2a3150 !important;
}
</style>
""", unsafe_allow_html=True)

# ─── PLOTLY DARK TEMPLATE ────────────────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans", color="#c8ccd8", size=12),
    margin=dict(l=10, r=10, t=30, b=10),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor="rgba(255,255,255,0.05)",
        borderwidth=1,
        font=dict(size=11, color="#8a94b0"),
    ),
    xaxis=dict(
        gridcolor="#1e2538",
        linecolor="#2a3150",
        tickcolor="#2a3150",
        tickfont=dict(size=11, color="#7c8db5"),
        zeroline=False,
    ),
    yaxis=dict(
        gridcolor="#1e2538",
        linecolor="#2a3150",
        tickcolor="#2a3150",
        tickfont=dict(size=11, color="#7c8db5"),
        zeroline=False,
    ),
    colorway=["#4f8ef7", "#2ec27e", "#f7a83e", "#e05c8b", "#a78bfa", "#34d399", "#fb923c"],
)

COLORS = {
    "blue":   "#4f8ef7",
    "green":  "#2ec27e",
    "amber":  "#f7a83e",
    "pink":   "#e05c8b",
    "purple": "#a78bfa",
    "teal":   "#34d399",
    "red":    "#f87171",
    "cat":    {"Technology": "#4f8ef7", "Furniture": "#f7a83e", "Office Supplies": "#2ec27e"},
    "region": {"West": "#4f8ef7", "East": "#2ec27e", "Central": "#f7a83e", "South": "#e05c8b"},
    "seg":    {"Consumer": "#a78bfa", "Corporate": "#4f8ef7", "Home Office": "#2ec27e"},
    "ship":   {
        "Standard Class": "#4f8ef7",
        "Second Class":   "#f7a83e",
        "First Class":    "#2ec27e",
        "Same Day":       "#e05c8b",
    },
}

# ─── LOAD DATA ───────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "SampleSuperstore.csv")
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    df["Sales"]    = pd.to_numeric(df["Sales"],    errors="coerce")
    df["Profit"]   = pd.to_numeric(df["Profit"],   errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["Discount"] = pd.to_numeric(df["Discount"], errors="coerce")
    df["Margin"]   = (df["Profit"] / df["Sales"]) * 100
    return df

df = load_data()

# ─── SIDEBAR FILTERS ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Superstore")
    st.markdown("---")
    st.markdown("### Filters")

    regions = st.multiselect(
        "Region",
        options=sorted(df["Region"].unique()),
        default=sorted(df["Region"].unique()),
    )
    segments = st.multiselect(
        "Segment",
        options=sorted(df["Segment"].unique()),
        default=sorted(df["Segment"].unique()),
    )
    categories = st.multiselect(
        "Category",
        options=sorted(df["Category"].unique()),
        default=sorted(df["Category"].unique()),
    )
    ship_modes = st.multiselect(
        "Ship Mode",
        options=sorted(df["Ship Mode"].unique()),
        default=sorted(df["Ship Mode"].unique()),
    )

    st.markdown("---")
    st.markdown("### About")
    st.markdown(
        "<span style='font-size:12px;color:#5a6482'>"
        "Sample Superstore dataset • US retail orders • 9,994 records"
        "</span>",
        unsafe_allow_html=True,
    )

# ─── FILTER DATA ─────────────────────────────────────────────────────────────
mask = (
    df["Region"].isin(regions) &
    df["Segment"].isin(segments) &
    df["Category"].isin(categories) &
    df["Ship Mode"].isin(ship_modes)
)
dff = df[mask]

# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="dash-title">📊 Superstore Sales Analytics</div>'
    '<div class="dash-subtitle">Interactive Power BI-style dashboard • Sample Superstore Dataset</div>',
    unsafe_allow_html=True,
)
st.markdown("---")

# ─── KPI CARDS ───────────────────────────────────────────────────────────────
total_sales   = dff["Sales"].sum()
total_profit  = dff["Profit"].sum()
total_orders  = len(dff)
total_qty     = dff["Quantity"].sum()
avg_margin    = (total_profit / total_sales * 100) if total_sales else 0
avg_discount  = dff["Discount"].mean() * 100

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
    <div class="kpi-card blue">
      <div class="kpi-icon">💰</div>
      <div class="kpi-label">Total Sales</div>
      <div class="kpi-value">${total_sales/1e6:.2f}M</div>
      <div class="kpi-delta pos">▲ {total_orders:,} orders</div>
    </div>""", unsafe_allow_html=True)

with k2:
    delta_cls = "pos" if total_profit > 0 else "neg"
    st.markdown(f"""
    <div class="kpi-card green">
      <div class="kpi-icon">📈</div>
      <div class="kpi-label">Total Profit</div>
      <div class="kpi-value">${total_profit/1e3:.1f}K</div>
      <div class="kpi-delta {delta_cls}">{'▲' if total_profit>0 else '▼'} Margin {avg_margin:.1f}%</div>
    </div>""", unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-card amber">
      <div class="kpi-icon">📦</div>
      <div class="kpi-label">Units Sold</div>
      <div class="kpi-value">{total_qty:,}</div>
      <div class="kpi-delta pos">▲ Avg {total_qty/max(total_orders,1):.1f} / order</div>
    </div>""", unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-card pink">
      <div class="kpi-icon">🏷️</div>
      <div class="kpi-label">Avg Discount</div>
      <div class="kpi-value">{avg_discount:.1f}%</div>
      <div class="kpi-delta neg">AOV ${total_sales/max(total_orders,1):.0f}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── ROW 1: Sales by Category  |  Profit by Category ────────────────────────
st.markdown('<div class="section-header">Category Performance</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)

with c1:
    cat_sales = (
        dff.groupby("Category")["Sales"]
        .sum().reset_index()
        .sort_values("Sales", ascending=False)
    )
    fig = go.Figure(go.Bar(
        x=cat_sales["Category"],
        y=cat_sales["Sales"],
        marker_color=[COLORS["cat"][c] for c in cat_sales["Category"]],
        marker_line_width=0,
        text=[f"${v/1e3:.0f}K" for v in cat_sales["Sales"]],
        textposition="outside",
        textfont=dict(size=12, color="#c8ccd8"),
    ))
    fig.update_layout(**PLOT_LAYOUT, title="Sales by Category", title_font=dict(size=13, color="#8a94b0"))
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    cat_profit = (
        dff.groupby("Category")["Profit"]
        .sum().reset_index()
        .sort_values("Profit", ascending=False)
    )
    colors_profit = [COLORS["green"] if v >= 0 else COLORS["red"] for v in cat_profit["Profit"]]
    fig2 = go.Figure(go.Bar(
        x=cat_profit["Category"],
        y=cat_profit["Profit"],
        marker_color=colors_profit,
        marker_line_width=0,
        text=[f"${v/1e3:.0f}K" for v in cat_profit["Profit"]],
        textposition="outside",
        textfont=dict(size=12, color="#c8ccd8"),
    ))
    fig2.update_layout(**PLOT_LAYOUT, title="Profit by Category", title_font=dict(size=13, color="#8a94b0"))
    fig2.update_yaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(fig2, use_container_width=True)

# ─── ROW 2: Region & Segment & Ship Mode ─────────────────────────────────────
st.markdown('<div class="section-header">Distribution Analysis</div>', unsafe_allow_html=True)
r1, r2, r3 = st.columns(3)

with r1:
    reg = dff.groupby("Region")["Sales"].sum().reset_index()
    fig_r = go.Figure(go.Pie(
        labels=reg["Region"],
        values=reg["Sales"],
        hole=0.58,
        marker_colors=[COLORS["region"].get(r, "#888") for r in reg["Region"]],
        textinfo="label+percent",
        textfont=dict(size=11, color="#c8ccd8"),
        insidetextorientation="radial",
    ))
    fig_r.update_layout(**PLOT_LAYOUT, title="Sales by Region", title_font=dict(size=13, color="#8a94b0"))
    fig_r.update_layout(showlegend=False, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_r, use_container_width=True)

with r2:
    seg = dff.groupby("Segment")["Sales"].sum().reset_index()
    fig_s = go.Figure(go.Pie(
        labels=seg["Segment"],
        values=seg["Sales"],
        hole=0.58,
        marker_colors=[COLORS["seg"].get(s, "#888") for s in seg["Segment"]],
        textinfo="label+percent",
        textfont=dict(size=11, color="#c8ccd8"),
        insidetextorientation="radial",
    ))
    fig_s.update_layout(**PLOT_LAYOUT, title="Sales by Segment", title_font=dict(size=13, color="#8a94b0"))
    fig_s.update_layout(showlegend=False, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_s, use_container_width=True)

with r3:
    ship = dff.groupby("Ship Mode")["Sales"].sum().reset_index()
    fig_sh = go.Figure(go.Pie(
        labels=ship["Ship Mode"],
        values=ship["Sales"],
        hole=0.58,
        marker_colors=[COLORS["ship"].get(m, "#888") for m in ship["Ship Mode"]],
        textinfo="label+percent",
        textfont=dict(size=11, color="#c8ccd8"),
        insidetextorientation="radial",
    ))
    fig_sh.update_layout(**PLOT_LAYOUT, title="Sales by Ship Mode", title_font=dict(size=13, color="#8a94b0"))
    fig_sh.update_layout(showlegend=False, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_sh, use_container_width=True)

# ─── ROW 3: Sub-category Sales | Sub-category Profit ─────────────────────────
st.markdown('<div class="section-header">Sub-Category Deep Dive</div>', unsafe_allow_html=True)
s1, s2 = st.columns(2)

with s1:
    sub_sales = (
        dff.groupby("Sub-Category")["Sales"]
        .sum().reset_index()
        .sort_values("Sales", ascending=True)
    )
    fig_sub = go.Figure(go.Bar(
        x=sub_sales["Sales"],
        y=sub_sales["Sub-Category"],
        orientation="h",
        marker_color=COLORS["blue"],
        marker_line_width=0,
        text=[f"${v/1e3:.0f}K" for v in sub_sales["Sales"]],
        textposition="outside",
        textfont=dict(size=10, color="#c8ccd8"),
    ))
    fig_sub.update_layout(
        **PLOT_LAYOUT,
        title="Sales by Sub-Category",
        title_font=dict(size=13, color="#8a94b0"),
        height=420,
        margin=dict(l=10, r=60, t=40, b=10),
    )
    fig_sub.update_xaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(fig_sub, use_container_width=True)

with s2:
    sub_profit = (
        dff.groupby("Sub-Category")["Profit"]
        .sum().reset_index()
        .sort_values("Profit", ascending=True)
    )
    colors_sub = [COLORS["green"] if v >= 0 else COLORS["red"] for v in sub_profit["Profit"]]
    fig_sub2 = go.Figure(go.Bar(
        x=sub_profit["Profit"],
        y=sub_profit["Sub-Category"],
        orientation="h",
        marker_color=colors_sub,
        marker_line_width=0,
        text=[f"${v/1e3:.0f}K" for v in sub_profit["Profit"]],
        textposition="outside",
        textfont=dict(size=10, color="#c8ccd8"),
    ))
    fig_sub2.update_layout(
        **PLOT_LAYOUT,
        title="Profit / Loss by Sub-Category",
        title_font=dict(size=13, color="#8a94b0"),
        height=420,
        margin=dict(l=10, r=60, t=40, b=10),
    )
    fig_sub2.update_xaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(fig_sub2, use_container_width=True)

# ─── ROW 4: Top States | Discount vs Profit scatter ──────────────────────────
st.markdown('<div class="section-header">Geographic & Discount Insights</div>', unsafe_allow_html=True)
g1, g2 = st.columns([1.1, 0.9])

with g1:
    top_n = st.slider("Top N States", min_value=5, max_value=20, value=10, key="top_states")
    state_data = (
        dff.groupby("State")
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
        .reset_index()
        .sort_values("Sales", ascending=False)
        .head(top_n)
        .sort_values("Sales", ascending=True)
    )
    fig_state = go.Figure()
    fig_state.add_trace(go.Bar(
        name="Sales",
        x=state_data["Sales"],
        y=state_data["State"],
        orientation="h",
        marker_color=COLORS["blue"],
        marker_line_width=0,
    ))
    fig_state.add_trace(go.Bar(
        name="Profit",
        x=state_data["Profit"],
        y=state_data["State"],
        orientation="h",
        marker_color=COLORS["green"],
        marker_line_width=0,
    ))
    fig_state.update_layout(
        **PLOT_LAYOUT,
        barmode="overlay",
        title=f"Top {top_n} States — Sales vs Profit",
        title_font=dict(size=13, color="#8a94b0"),
        height=top_n * 34 + 80,
        margin=dict(l=10, r=20, t=40, b=10),
    )
    fig_state.update_xaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(fig_state, use_container_width=True)

with g2:
    sample = dff.sample(min(2000, len(dff)), random_state=42)
    fig_scatter = go.Figure(go.Scatter(
        x=sample["Discount"],
        y=sample["Profit"],
        mode="markers",
        marker=dict(
            size=5,
            color=sample["Sales"],
            colorscale=[[0, "#1e2538"], [0.5, "#4f8ef7"], [1, "#2ec27e"]],
            showscale=True,
            colorbar=dict(
                title=dict(text="Sales ($)", font=dict(color="#7c8db5", size=11)),
                tickfont=dict(color="#7c8db5", size=10),
                thickness=10,
                len=0.7,
            ),
            opacity=0.7,
            line=dict(width=0),
        ),
        hovertemplate="Discount: %{x:.0%}<br>Profit: $%{y:,.0f}<extra></extra>",
    ))
    fig_scatter.add_hline(y=0, line_color="#e05c8b", line_dash="dot", line_width=1.5)
    fig_scatter.update_layout(
        **PLOT_LAYOUT,
        title="Discount vs Profit (bubble = sales)",
        title_font=dict(size=13, color="#8a94b0"),
        height=360,
    )
    fig_scatter.update_xaxes(tickformat=".0%", title_text="Discount Rate", title_font=dict(size=11, color="#7c8db5"))
    fig_scatter.update_yaxes(tickprefix="$", tickformat=",.0f", title_text="Profit ($)", title_font=dict(size=11, color="#7c8db5"))
    st.plotly_chart(fig_scatter, use_container_width=True)

# ─── ROW 5: Region × Category heatmap | Profit Margin by Sub-Cat ─────────────
st.markdown('<div class="section-header">Cross-Dimensional Analysis</div>', unsafe_allow_html=True)
h1, h2 = st.columns(2)

with h1:
    heat = dff.pivot_table(
        index="Category", columns="Region", values="Profit", aggfunc="sum"
    ).fillna(0)
    fig_heat = go.Figure(go.Heatmap(
        z=heat.values,
        x=heat.columns.tolist(),
        y=heat.index.tolist(),
        colorscale=[[0, "#f87171"], [0.5, "#1e2538"], [1, "#2ec27e"]],
        text=[[f"${v/1e3:.0f}K" for v in row] for row in heat.values],
        texttemplate="%{text}",
        textfont=dict(size=13, color="#e8ecf5"),
        showscale=True,
        colorbar=dict(
            tickfont=dict(color="#7c8db5", size=10),
            thickness=10,
        ),
    ))
    fig_heat.update_layout(
        **PLOT_LAYOUT,
        title="Profit Heatmap: Category × Region",
        title_font=dict(size=13, color="#8a94b0"),
        height=250,
        margin=dict(l=10, r=60, t=40, b=10),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

with h2:
    margin_sub = (
        dff.groupby("Sub-Category")
        .apply(lambda x: (x["Profit"].sum() / x["Sales"].sum()) * 100)
        .reset_index(name="Margin")
        .sort_values("Margin", ascending=False)
    )
    bar_colors = [COLORS["green"] if v >= 0 else COLORS["red"] for v in margin_sub["Margin"]]
    fig_margin = go.Figure(go.Bar(
        x=margin_sub["Sub-Category"],
        y=margin_sub["Margin"],
        marker_color=bar_colors,
        marker_line_width=0,
        text=[f"{v:.1f}%" for v in margin_sub["Margin"]],
        textposition="outside",
        textfont=dict(size=10, color="#c8ccd8"),
    ))
    fig_margin.add_hline(y=0, line_color="#e05c8b", line_dash="dot", line_width=1)
    fig_margin.update_layout(
        **PLOT_LAYOUT,
        title="Profit Margin % by Sub-Category",
        title_font=dict(size=13, color="#8a94b0"),
        height=260,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    fig_margin.update_xaxes(tickangle=-40)
    fig_margin.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig_margin, use_container_width=True)

# ─── ROW 6: City Table | Quantity by Segment × Category ──────────────────────
st.markdown('<div class="section-header">Top Cities & Quantity Mix</div>', unsafe_allow_html=True)
t1, t2 = st.columns([1.2, 0.8])

with t1:
    city_df = (
        dff.groupby(["City", "State"])
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"), Orders=("Sales", "count"))
        .reset_index()
        .sort_values("Sales", ascending=False)
        .head(15)
    )
    city_df["Margin %"] = (city_df["Profit"] / city_df["Sales"] * 100).round(1)
    city_df["Sales"]    = city_df["Sales"].map("${:,.0f}".format)
    city_df["Profit"]   = city_df["Profit"].map("${:,.0f}".format)
    city_df["Margin %"] = city_df["Margin %"].map("{:.1f}%".format)

    st.markdown("**Top 15 Cities by Sales**")
    st.dataframe(
        city_df.rename(columns={"City": "City", "State": "State"}),
        use_container_width=True,
        hide_index=True,
        height=420,
    )

with t2:
    qty_seg_cat = (
        dff.groupby(["Segment", "Category"])["Quantity"]
        .sum().reset_index()
    )
    fig_qty = px.bar(
        qty_seg_cat,
        x="Segment",
        y="Quantity",
        color="Category",
        barmode="group",
        color_discrete_map=COLORS["cat"],
        text_auto=True,
    )
    fig_qty.update_traces(textfont_size=10, textposition="outside", marker_line_width=0)
    fig_qty.update_layout(
        **PLOT_LAYOUT,
        title="Quantity: Segment × Category",
        title_font=dict(size=13, color="#8a94b0"),
        height=420,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font=dict(size=11, color="#8a94b0"),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    fig_qty.update_yaxes(title_text="")
    st.plotly_chart(fig_qty, use_container_width=True)

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#3a4060; font-size:12px; padding: 8px 0'>"
    "Superstore Analytics Dashboard • Built with Streamlit & Plotly"
    "</div>",
    unsafe_allow_html=True,
)
