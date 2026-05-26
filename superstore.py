# ============================================================
# 🇮🇳 INDIA LIVE BUSINESS ANALYTICS DASHBOARD
# Enterprise Professional Live Dashboard
# Streamlit + Plotly + Faker
# ============================================================

# RUN:
# streamlit run app.py

# INSTALL:
# pip install -r requirements.txt

# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from faker import Faker
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import random

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="India Live Retail Dashboard",
    layout="wide",
    page_icon="📈"
)

# ============================================================
# LIGHT PROFESSIONAL CSS
# ============================================================

st.markdown("""
<style>

.stApp {
    background-color: #f4f7fb;
    color: #1e293b;
}

.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}

h1, h2, h3, h4, h5 {
    color: #0f172a !important;
    font-family: 'Segoe UI', sans-serif;
    font-weight: 700;
}

[data-testid="stMetric"] {
    background: white;
    border: 1px solid #e2e8f0;
    padding: 22px;
    border-radius: 18px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.06);
}

[data-testid="stMetricLabel"] {
    color: #64748b !important;
}

[data-testid="stMetricValue"] {
    color: #0f172a !important;
}

section[data-testid="stSidebar"] {
    background: white;
    border-right: 1px solid #e2e8f0;
}

.js-plotly-plot {
    background: white !important;
    border-radius: 18px;
    padding: 10px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.05);
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# INDIA STATES & CITIES
# ============================================================

india_locations = {

    "Andhra Pradesh": [
        "Visakhapatnam", "Vijayawada", "Guntur",
        "Nellore", "Kurnool", "Tirupati"
    ],

    "Arunachal Pradesh": [
        "Itanagar", "Tawang", "Ziro"
    ],

    "Assam": [
        "Guwahati", "Dibrugarh", "Silchar",
        "Jorhat", "Tezpur"
    ],

    "Bihar": [
        "Patna", "Gaya", "Muzaffarpur",
        "Bhagalpur", "Darbhanga"
    ],

    "Chhattisgarh": [
        "Raipur", "Bilaspur", "Durg",
        "Korba", "Bhilai"
    ],

    "Goa": [
        "Panaji", "Margao", "Vasco da Gama"
    ],

    "Gujarat": [
        "Ahmedabad", "Surat", "Vadodara",
        "Rajkot", "Gandhinagar"
    ],

    "Haryana": [
        "Gurugram", "Faridabad", "Panipat",
        "Ambala", "Karnal"
    ],

    "Karnataka": [
        "Bengaluru", "Mysuru", "Hubli",
        "Mangalore"
    ],

    "Kerala": [
        "Kochi", "Thiruvananthapuram",
        "Kozhikode", "Thrissur"
    ],

    "Madhya Pradesh": [
        "Bhopal", "Indore", "Gwalior",
        "Jabalpur"
    ],

    "Maharashtra": [
        "Mumbai", "Pune", "Nagpur",
        "Nashik", "Thane"
    ],

    "Odisha": [
        "Bhubaneswar", "Cuttack",
        "Rourkela", "Puri"
    ],

    "Punjab": [
        "Ludhiana", "Amritsar",
        "Jalandhar", "Patiala"
    ],

    "Rajasthan": [
        "Jaipur", "Jodhpur",
        "Udaipur", "Kota"
    ],

    "Tamil Nadu": [
        "Chennai", "Coimbatore",
        "Madurai", "Salem"
    ],

    "Telangana": [
        "Hyderabad", "Warangal",
        "Karimnagar"
    ],

    "Uttar Pradesh": [
        "Lucknow", "Kanpur",
        "Noida", "Agra", "Varanasi"
    ],

    "West Bengal": [
        "Kolkata", "Howrah",
        "Siliguri", "Durgapur"
    ],

    "Delhi": [
        "New Delhi", "Dwarka",
        "Rohini"
    ]
}

# ============================================================
# DATA
# ============================================================

fake = Faker()

regions = ["North", "South", "East", "West", "Central"]

categories = [
    "Electronics",
    "Furniture",
    "Clothing",
    "Home & Kitchen",
    "Office Supplies"
]

sub_categories = {
    "Electronics": ["Laptops", "Mobiles", "TV", "Accessories"],
    "Furniture": ["Chairs", "Tables", "Beds", "Sofas"],
    "Clothing": ["Men Wear", "Women Wear", "Footwear"],
    "Home & Kitchen": ["Cookware", "Storage", "Decor"],
    "Office Supplies": ["Printers", "Paper", "Binders"]
}

segments = [
    "Consumer",
    "Corporate",
    "Government",
    "Small Business"
]

ship_modes = [
    "Express",
    "Standard",
    "Economy",
    "Same Day"
]

# ============================================================
# LIVE DATA GENERATOR
# ============================================================

@st.cache_data(ttl=5)
def generate_live_data(rows=1500):

    data = []

    for _ in range(rows):

        state = random.choice(list(india_locations.keys()))
        city = random.choice(india_locations[state])

        category = random.choice(categories)

        revenue = random.randint(5000, 200000)

        discount = random.choice([0, 5, 10, 15, 20, 25, 30])

        profit = revenue * random.uniform(0.05, 0.35)

        quantity = random.randint(1, 15)

        order_date = datetime.now() - timedelta(
            days=random.randint(0, 365)
        )

        data.append({

            "Region": random.choice(regions),

            "State": state,

            "City": city,

            "Category": category,

            "Sub_Category": random.choice(
                sub_categories[category]
            ),

            "Segment": random.choice(segments),

            "Ship_Mode": random.choice(ship_modes),

            "Revenue": revenue,

            "Profit": profit,

            "Quantity": quantity,

            "Discount": discount,

            "Order_Date": order_date

        })

    return pd.DataFrame(data)

df = generate_live_data()

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("📊 Dashboard Filters")

selected_states = st.sidebar.multiselect(
    "Select States",
    df["State"].unique(),
    default=df["State"].unique()
)

selected_category = st.sidebar.multiselect(
    "Select Category",
    df["Category"].unique(),
    default=df["Category"].unique()
)

selected_segment = st.sidebar.multiselect(
    "Select Segment",
    df["Segment"].unique(),
    default=df["Segment"].unique()
)

filtered_df = df[
    (df["State"].isin(selected_states)) &
    (df["Category"].isin(selected_category)) &
    (df["Segment"].isin(selected_segment))
]

# ============================================================
# HEADER
# ============================================================

st.title("🇮🇳 India Live Retail Analytics Dashboard")

st.markdown("""
Professional Real-Time Business Intelligence Dashboard  
Live Operational Analytics • Enterprise Insights • Market Scenario
""")

st.markdown("---")

# ============================================================
# KPI CARDS
# ============================================================

total_revenue = filtered_df["Revenue"].sum()
total_profit = filtered_df["Profit"].sum()
total_orders = len(filtered_df)
avg_order = filtered_df["Revenue"].mean()

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "💰 Total Revenue",
        f"₹ {total_revenue:,.0f}",
        "+12%"
    )

with c2:
    st.metric(
        "📈 Net Profit",
        f"₹ {total_profit:,.0f}",
        "+8%"
    )

with c3:
    st.metric(
        "📦 Total Orders",
        f"{total_orders:,}",
        "+15%"
    )

with c4:
    st.metric(
        "🛒 Avg Order Value",
        f"₹ {avg_order:,.0f}",
        "+6%"
    )

st.markdown("---")

# ============================================================
# MONTHLY TREND
# ============================================================

trend_df = filtered_df.copy()

trend_df["Month"] = trend_df["Order_Date"].dt.strftime("%b")

monthly = trend_df.groupby("Month")[[
    "Revenue", "Profit"
]].sum().reset_index()

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=monthly["Month"],
    y=monthly["Revenue"],
    mode='lines+markers',
    name='Revenue'
))

fig.add_trace(go.Scatter(
    x=monthly["Month"],
    y=monthly["Profit"],
    mode='lines+markers',
    name='Profit'
))

fig.update_layout(
    template="plotly_white",
    title="Monthly Revenue & Profit Trend",
    height=450
)

st.plotly_chart(fig, use_container_width=True)

# ============================================================
# CATEGORY ANALYSIS
# ============================================================

col1, col2 = st.columns(2)

category_sales = filtered_df.groupby(
    "Category"
)["Revenue"].sum().reset_index()

with col1:

    fig = px.bar(
        category_sales,
        x="Category",
        y="Revenue",
        color="Category",
        template="plotly_white",
        title="Revenue by Category"
    )

    st.plotly_chart(fig, use_container_width=True)

category_profit = filtered_df.groupby(
    "Category"
)["Profit"].sum().reset_index()

with col2:

    fig = px.pie(
        category_profit,
        names="Category",
        values="Profit",
        hole=0.5,
        template="plotly_white",
        title="Profit Share by Category"
    )

    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# STATE ANALYSIS
# ============================================================

st.subheader("🏆 Top States Performance")

top_states = filtered_df.groupby("State")[
    "Revenue"
].sum().sort_values(
    ascending=False
).head(10).reset_index()

fig = px.bar(
    top_states,
    x="Revenue",
    y="State",
    orientation="h",
    color="Revenue",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# ============================================================
# CITY ANALYSIS
# ============================================================

st.subheader("🌆 Top Cities")

top_cities = filtered_df.groupby("City")[
    "Revenue"
].sum().sort_values(
    ascending=False
).head(15).reset_index()

fig = px.bar(
    top_cities,
    x="Revenue",
    y="City",
    orientation="h",
    color="Revenue",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# ============================================================
# HEATMAP
# ============================================================

st.subheader("🔥 Revenue Heatmap")

heatmap_df = filtered_df.pivot_table(
    index="Category",
    columns="Region",
    values="Revenue",
    aggfunc="sum"
)

fig = px.imshow(
    heatmap_df,
    text_auto=True,
    aspect="auto",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# ============================================================
# DISCOUNT VS PROFIT
# ============================================================

st.subheader("📉 Discount vs Profit")

fig = px.scatter(
    filtered_df,
    x="Discount",
    y="Profit",
    size="Revenue",
    color="Category",
    hover_data=["State", "City"],
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# ============================================================
# LIVE TRANSACTION TABLE
# ============================================================

st.subheader("⚡ Live Transactions")

table_df = filtered_df[[
    "State",
    "City",
    "Category",
    "Sub_Category",
    "Revenue",
    "Profit",
    "Quantity"
]].tail(20)

st.dataframe(
    table_df,
    use_container_width=True,
    height=400
)

# ============================================================
# AUTO REFRESH
# ============================================================

st.success(
    f"✅ Dashboard Live • Last Updated: "
    f"{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
)

st_autorefresh(
    interval=5000,
    key="live_dashboard_refresh"
)
