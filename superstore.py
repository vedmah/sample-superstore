import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
from pathlib import Path

st.set_page_config(
    page_title="India Executive Dashboard",
    layout="wide",
    page_icon="📊"
)

st.markdown("""
<style>
    .main { background: #f5f7fb; }
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    .hero {
        background: linear-gradient(90deg, #0f172a, #1d4ed8);
        color: white;
        padding: 18px 22px;
        border-radius: 18px;
        margin-bottom: 16px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.18);
    }
    .kpi {
        background: white;
        padding: 14px 14px;
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .small {
        color: #64748b;
        font-size: 12px;
    }
    section[data-testid="stSidebar"] {
        background: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h2 style="margin:0;">India Executive Sales Dashboard</h2>
    <p style="margin:6px 0 0 0;">Synthetic India view built from your dataset with state-level choropleth and executive KPIs</p>
</div>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(uploaded_file):
    df = pd.read_csv(uploaded_file)
    df.columns = [c.strip() for c in df.columns]
    return df

def detect_date_col(df):
    for c in df.columns:
        if "date" in c.lower():
            parsed = pd.to_datetime(df[c], errors="coerce")
            if parsed.notna().sum() > 0:
                return c
    return None

def build_india_mapping(us_states):
    india_states = [
        "Maharashtra","Karnataka","Tamil Nadu","Gujarat","Rajasthan","Uttar Pradesh","Bihar",
        "West Bengal","Madhya Pradesh","Kerala","Punjab","Haryana","Telangana","Andhra Pradesh",
        "Odisha","Assam","Jharkhand","Chhattisgarh","Delhi","Himachal Pradesh","Uttarakhand",
        "Goa","Tripura","Meghalaya","Manipur","Mizoram","Nagaland","Arunachal Pradesh","Sikkim"
    ]
    region_map = {
        "Maharashtra": "West", "Karnataka": "South", "Tamil Nadu": "South", "Gujarat": "West",
        "Rajasthan": "North", "Uttar Pradesh": "North", "Bihar": "East", "West Bengal": "East",
        "Madhya Pradesh": "Central", "Kerala": "South", "Punjab": "North", "Haryana": "North",
        "Telangana": "South", "Andhra Pradesh": "South", "Odisha": "East", "Assam": "North East",
        "Jharkhand": "East", "Chhattisgarh": "Central", "Delhi": "North", "Himachal Pradesh": "North",
        "Uttarakhand": "North", "Goa": "West", "Tripura": "North East", "Meghalaya": "North East",
        "Manipur": "North East", "Mizoram": "North East", "Nagaland": "North East",
        "Arunachal Pradesh": "North East", "Sikkim": "North East"
    }
    mapping = {}
    for i, s in enumerate(us_states):
        mapping[s] = india_states[i % len(india_states)]
    return mapping, region_map

def normalize_state_name(s):
    return str(s).strip()

uploaded = st.sidebar.file_uploader("Upload CSV", type=["csv"])
if uploaded is None:
    st.info("Upload SampleSuperstore.csv to continue.")
    st.stop()

df = load_data(uploaded)

state_col = next((c for c in df.columns if c.lower() == "state"), None)
sales_col = next((c for c in df.columns if c.lower() == "sales"), None)
profit_col = next((c for c in df.columns if c.lower() == "profit"), None)
qty_col = next((c for c in df.columns if c.lower() == "quantity"), None)
disc_col = next((c for c in df.columns if c.lower() == "discount"), None)
cat_col = next((c for c in df.columns if c.lower() == "category"), None)
subcat_col = next((c for c in df.columns if c.lower() in ["sub-category", "subcategory"]), None)
segment_col = next((c for c in df.columns if c.lower() == "segment"), None)
ship_col = next((c for c in df.columns if c.lower() == "ship mode"), None)
date_col = detect_date_col(df)

if any(c is None for c in [state_col, sales_col, profit_col, qty_col, disc_col]):
    st.error("Required columns not found: State, Sales, Profit, Quantity, Discount.")
    st.stop()

for c in [sales_col, profit_col, qty_col, disc_col]:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

if date_col:
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

us_states = sorted(df[state_col].dropna().astype(str).unique().tolist())
us_to_india, india_region_map = build_india_mapping(us_states)

df["India State"] = df[state_col].astype(str).map(us_to_india)
df["India Region"] = df["India State"].map(india_region_map)

if date_col:
    df["Month"] = df[date_col].dt.to_period("M").astype(str)

st.sidebar.header("Filters")
regions = sorted(df["India Region"].dropna().unique().tolist())
states = sorted(df["India State"].dropna().unique().tolist())
categories = sorted(df[cat_col].dropna().astype(str).unique().tolist()) if cat_col else []
segments = sorted(df[segment_col].dropna().astype(str).unique().tolist()) if segment_col else []
ship_modes = sorted(df[ship_col].dropna().astype(str).unique().tolist()) if ship_col else []

sel_regions = st.sidebar.multiselect("India Region", regions, default=regions)
sel_states = st.sidebar.multiselect("India State", states, default=states)
sel_categories = st.sidebar.multiselect("Category", categories, default=categories) if categories else []
sel_segments = st.sidebar.multiselect("Segment", segments, default=segments) if segments else []
sel_ship = st.sidebar.multiselect("Ship Mode", ship_modes, default=ship_modes) if ship_col else []

f = df[df["India Region"].isin(sel_regions) & df["India State"].isin(sel_states)]
if cat_col and sel_categories:
    f = f[f[cat_col].astype(str).isin(sel_categories)]
if segment_col and sel_segments:
    f = f[f[segment_col].astype(str).isin(sel_segments)]
if ship_col and sel_ship:
    f = f[f[ship_col].astype(str).isin(sel_ship)]

geo_path = Path("india_states.geojson")
geojson_data = None
if geo_path.exists():
    with open(geo_path, "r", encoding="utf-8") as fp:
        geojson_data = json.load(fp)
else:
    st.warning("india_states.geojson not found. The choropleth will be replaced by a bar chart unless you add the geojson file.")

state_summary = f.groupby(["India State", "India Region"], as_index=False).agg(
    Sales=(sales_col, "sum"),
    Profit=(profit_col, "sum"),
    Quantity=(qty_col, "sum"),
    AvgDiscount=(disc_col, "mean")
)
state_summary["Profit Margin %"] = np.where(state_summary["Sales"] != 0, state_summary["Profit"] / state_summary["Sales"] * 100, 0)

total_sales = f[sales_col].sum()
total_profit = f[profit_col].sum()
total_qty = f[qty_col].sum()
avg_discount = f[disc_col].mean()
profit_margin = (total_profit / total_sales * 100) if total_sales else 0
order_count = len(f)

k1, k2, k3, k4, k5, k6 = st.columns(6)
vals = [
    ("Total Sales", f"{total_sales:,.2f}"),
    ("Total Profit", f"{total_profit:,.2f}"),
    ("Profit Margin %", f"{profit_margin:,.2f}%"),
    ("Orders", f"{order_count:,}"),
    ("Quantity", f"{total_qty:,.0f}"),
    ("Avg Discount", f"{avg_discount:,.2f}%"),
]
for col, (label, val) in zip([k1, k2, k3, k4, k5, k6], vals):
    with col:
        st.markdown('<div class="kpi">', unsafe_allow_html=True)
        st.metric(label, val)
        st.markdown('</div>', unsafe_allow_html=True)

c1, c2 = st.columns([1.25, 1])

with c1:
    if geojson_data is not None:
        geo_df = state_summary.copy()
        fig = px.choropleth(
            geo_df,
            geojson=geojson_data,
            locations="India State",
            featureidkey="properties.ST_NM",
            color="Sales",
            color_continuous_scale="Blues",
            scope="asia",
            title="India State-wise Sales Map"
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(height=560, template="plotly_white", margin=dict(l=0, r=0, t=50, b=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        top_map = state_summary.sort_values("Sales", ascending=False).head(15)
        fig = px.bar(top_map, x="Sales", y="India State", orientation="h", color="Sales", color_continuous_scale="Blues", title="Top States by Sales")
        fig.update_layout(height=560, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

with c2:
    region_agg = f.groupby("India Region", as_index=False).agg(Sales=(sales_col, "sum"), Profit=(profit_col, "sum"), Quantity=(qty_col, "sum"))
    fig = px.bar(region_agg, x="India Region", y="Sales", color="Profit", color_continuous_scale="RdYlGn", title="Sales by India Region")
    fig.update_layout(height=260, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

    if date_col and "Month" in f.columns and not f.empty:
        ts = f.groupby("Month", as_index=False).agg(Sales=(sales_col, "sum"), Profit=(profit_col, "sum"))
        ts["MonthSort"] = pd.to_datetime(ts["Month"] + "-01")
        ts = ts.sort_values("MonthSort")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=ts["Month"], y=ts["Sales"], mode="lines+markers", name="Sales", line=dict(color="#2563eb", width=3)))
        fig.add_trace(go.Scatter(x=ts["Month"], y=ts["Profit"], mode="lines+markers", name="Profit", line=dict(color="#16a34a", width=3)))
        fig.update_layout(height=260, title="Monthly Trend", template="plotly_white", legend_title_text="")
        st.plotly_chart(fig, use_container_width=True)

c3, c4 = st.columns(2)

with c3:
    if cat_col:
        cat = f.groupby(cat_col, as_index=False).agg(Sales=(sales_col, "sum"), Profit=(profit_col, "sum")).sort_values("Sales", ascending=False)
        fig = px.bar(cat, x=cat_col, y="Sales", color="Profit", color_continuous_scale="Viridis", title="Category Performance")
        fig.update_layout(height=420, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

with c4:
    if subcat_col:
        sub = f.groupby(subcat_col, as_index=False).agg(Sales=(sales_col, "sum"), Profit=(profit_col, "sum")).sort_values("Profit", ascending=False)
        fig = px.bar(sub.head(10), x=subcat_col, y="Profit", color="Profit", color_continuous_scale="Plasma", title="Top Sub-Categories by Profit")
        fig.update_layout(height=420, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

c5, c6 = st.columns(2)

with c5:
    if segment_col:
        seg = f.groupby(segment_col, as_index=False).agg(Sales=(sales_col, "sum"))
        fig = px.pie(seg, values="Sales", names=segment_col, hole=0.5, title="Sales Share by Segment")
        fig.update_layout(height=420, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

with c6:
    if ship_col:
        ship = f.groupby(ship_col, as_index=False).agg(Orders=(ship_col, "size"), Profit=(profit_col, "sum")).sort_values("Orders", ascending=False)
        fig = px.bar(ship, x=ship_col, y="Orders", color="Profit", color_continuous_scale="Cividis", title="Orders by Ship Mode")
        fig.update_layout(height=420, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

c7, c8 = st.columns(2)

with c7:
    top_states = state_summary.sort_values("Sales", ascending=False).head(10)
    fig = px.bar(top_states, x="Sales", y="India State", orientation="h", color="Profit", color_continuous_scale="Tealgrn", title="Top 10 Indian States by Sales")
    fig.update_layout(height=420, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

with c8:
    sc = px.scatter(
        f,
        x=disc_col,
        y=profit_col,
        color="India Region",
        size=sales_col,
        hover_data=["India State", cat_col] if cat_col else ["India State"],
        title="Discount vs Profit",
        template="plotly_white"
    )
    sc.update_layout(height=420)
    st.plotly_chart(sc, use_container_width=True)

st.subheader("State-level Executive Table")
st.dataframe(
    state_summary.sort_values("Sales", ascending=False),
    use_container_width=True,
    hide_index=True
)

st.download_button(
    "Download filtered data as CSV",
    data=f.to_csv(index=False).encode("utf-8"),
    file_name="india_executive_dashboard_data.csv",
    mime="text/csv"
)
