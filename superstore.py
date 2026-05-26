# ============================================================
# 🇮🇳 INDIA LIVE BUSINESS ANALYTICS DASHBOARD
# Real-Time Professional Business Dashboard
# Streamlit + Plotly + Faker
# ============================================================

# RUN:
# streamlit run app.py

# INSTALL:
# pip install streamlit pandas numpy plotly faker

# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from faker import Faker
from datetime import datetime, timedelta
import random
import time

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="India Live Retail Dashboard",
    layout="wide",
    page_icon="📈",
)

# ============================================================
# CUSTOM CSS
# ============================================================

# ============================================================
# LIGHT PROFESSIONAL CSS
# ============================================================

st.markdown("""
<style>

/* MAIN APP */

.stApp {
    background-color: #f4f7fb;
    color: #1e293b;
}

/* MAIN CONTAINER */

.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* HEADINGS */

h1, h2, h3, h4, h5 {
    color: #0f172a !important;
    font-family: 'Segoe UI', sans-serif;
    font-weight: 700;
}

/* METRIC CARDS */

[data-testid="stMetric"] {
    background: white;
    border: 1px solid #e2e8f0;
    padding: 22px;
    border-radius: 18px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.06);
    transition: 0.3s ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.10);
}

/* METRIC LABEL */

[data-testid="stMetricLabel"] {
    color: #64748b !important;
    font-size: 15px;
    font-weight: 600;
}

/* METRIC VALUE */

[data-testid="stMetricValue"] {
    color: #0f172a !important;
    font-size: 34px;
    font-weight: 700;
}

/* SIDEBAR */

section[data-testid="stSidebar"] {
    background: white;
    border-right: 1px solid #e2e8f0;
}

/* SIDEBAR TEXT */

section[data-testid="stSidebar"] * {
    color: #1e293b !important;
}

/* FILTER DROPDOWN */

.stMultiSelect div[data-baseweb="select"] {
    background-color: white;
    border-radius: 12px;
    border: 1px solid #cbd5e1;
}

/* DATAFRAME */

[data-testid="stDataFrame"] {
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid #e2e8f0;
}

/* BUTTONS */

.stButton button {
    background: linear-gradient(90deg,#2563eb,#3b82f6);
    color: white;
    border-radius: 10px;
    border: none;
    padding: 10px 22px;
    font-weight: 600;
}

.stButton button:hover {
    background: linear-gradient(90deg,#1d4ed8,#2563eb);
    color: white;
}

/* SUCCESS BOX */

.stAlert {
    border-radius: 14px;
}

/* PLOTLY CHART AREA */

.js-plotly-plot {
    border-radius: 18px;
    background: white !important;
    padding: 10px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.05);
}

/* DIVIDER */

hr {
    border-color: #cbd5e1;
}

/* SCROLLBAR */

::-webkit-scrollbar {
    width: 10px;
}

::-webkit-scrollbar-track {
    background: #f1f5f9;
}

::-webkit-scrollbar-thumb {
    background: #94a3b8;
    border-radius: 20px;
}

::-webkit-scrollbar-thumb:hover {
    background: #64748b;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# LIVE DATA GENERATOR
# ============================================================

fake = Faker()

regions = ["North", "South", "East", "West", "Central"]

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
        "Rajkot", "Gandhinagar", "Bhavnagar"
    ],

    "Haryana": [
        "Gurugram", "Faridabad", "Panipat",
        "Ambala", "Karnal"
    ],

    "Himachal Pradesh": [
        "Shimla", "Manali", "Dharamshala"
    ],

    "Jharkhand": [
        "Ranchi", "Jamshedpur", "Dhanbad",
        "Bokaro"
    ],

    "Karnataka": [
        "Bengaluru", "Mysuru", "Hubli",
        "Mangalore", "Belgaum"
    ],

    "Kerala": [
        "Kochi", "Thiruvananthapuram",
        "Kozhikode", "Thrissur"
    ],

    "Madhya Pradesh": [
        "Bhopal", "Indore", "Gwalior",
        "Jabalpur", "Ujjain"
    ],

    "Maharashtra": [
        "Mumbai", "Pune", "Nagpur",
        "Nashik", "Thane", "Aurangabad"
    ],

    "Manipur": [
        "Imphal", "Thoubal"
    ],

    "Meghalaya": [
        "Shillong", "Tura"
    ],

    "Mizoram": [
        "Aizawl", "Lunglei"
    ],

    "Nagaland": [
        "Kohima", "Dimapur"
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
        "Udaipur", "Kota", "Ajmer"
    ],

    "Sikkim": [
        "Gangtok", "Namchi"
    ],

    "Tamil Nadu": [
        "Chennai", "Coimbatore",
        "Madurai", "Salem", "Tiruppur"
    ],

    "Telangana": [
        "Hyderabad", "Warangal",
        "Karimnagar", "Nizamabad"
    ],

    "Tripura": [
        "Agartala", "Udaipur"
    ],

    "Uttar Pradesh": [
        "Lucknow", "Kanpur",
        "Noida", "Agra", "Varanasi"
    ],

    "Uttarakhand": [
        "Dehradun", "Haridwar",
        "Roorkee", "Nainital"
    ],

    "West Bengal": [
        "Kolkata", "Howrah",
        "Siliguri", "Durgapur"
    ],

    # UNION TERRITORIES

    "Delhi": [
        "New Delhi", "Dwarka",
        "Rohini", "Karol Bagh"
    ],

    "Jammu & Kashmir": [
        "Srinagar", "Jammu"
    ],

    "Ladakh": [
        "Leh", "Kargil"
    ],

    "Puducherry": [
        "Puducherry", "Karaikal"
    ],

    "Chandigarh": [
        "Chandigarh"
    ]
}

categories = [
    "Electronics",
    "Furniture",
    "Clothing",
    "Home & Kitchen",
    "Office Supplies"
]

sub_categories = {
    "Electronics": ["Laptops", "Mobiles", "Televisions", "Accessories"],
    "Furniture": ["Chairs", "Tables", "Beds", "Sofas"],
    "Clothing": ["Men Wear", "Women Wear", "Kids Wear", "Footwear"],
    "Home & Kitchen": ["Cookware", "Decor", "Storage", "Appliances"],
    "Office Supplies": ["Printers", "Paper", "Labels", "Binders"]
}

segments = ["Consumer", "Corporate", "Government", "Small Business"]

ship_modes = [
    "Express Delivery",
    "Economy",
    "Standard",
    "Same Day"
]

# ============================================================
# GENERATE LIVE DATA
# ============================================================

@st.cache_data(ttl=10)
def generate_live_data(rows=5000):

    data = []

    for _ in range(rows):

        category = random.choice(categories)

        revenue = random.randint(2000, 150000)

        discount = random.choice([0, 5, 10, 15, 20, 30, 40])

        profit = revenue * random.uniform(0.05, 0.35)

        quantity = random.randint(1, 10)

        order_date = datetime.now() - timedelta(
            days=random.randint(0, 365)
        )

        data.append({

            "Region": random.choice(regions),

            "State": random.choice(states),

            "City": random.choice(cities),

            "Category": category,

            "Sub_Category": random.choice(sub_categories[category]),

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
# SIDEBAR FILTERS
# ============================================================

st.sidebar.title("📊 Dashboard Filters")

selected_region = st.sidebar.multiselect(
    "Region",
    options=df["Region"].unique(),
    default=df["Region"].unique()
)

selected_category = st.sidebar.multiselect(
    "Category",
    options=df["Category"].unique(),
    default=df["Category"].unique()
)

selected_segment = st.sidebar.multiselect(
    "Segment",
    options=df["Segment"].unique(),
    default=df["Segment"].unique()
)

# FILTER DATA

filtered_df = df[
    (df["Region"].isin(selected_region)) &
    (df["Category"].isin(selected_category)) &
    (df["Segment"].isin(selected_segment))
]

# ============================================================
# HEADER
# ============================================================

st.markdown("""
# 🇮🇳 India Live Retail Analytics Dashboard
### Real-Time Business Intelligence • Live Market Scenario • AI Business View
""")

st.markdown("---")

# ============================================================
# KPI SECTION
# ============================================================

total_revenue = filtered_df["Revenue"].sum()
total_profit = filtered_df["Profit"].sum()
units_sold = filtered_df["Quantity"].sum()
avg_order = filtered_df["Revenue"].mean()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "💰 Total Revenue",
        f"₹ {total_revenue:,.0f}",
        "+12%"
    )

with col2:
    st.metric(
        "📈 Net Profit",
        f"₹ {total_profit:,.0f}",
        "+8%"
    )

with col3:
    st.metric(
        "📦 Units Sold",
        f"{units_sold:,}",
        "+15%"
    )

with col4:
    st.metric(
        "🛒 Avg Order Value",
        f"₹ {avg_order:,.0f}",
        "+5%"
    )

st.markdown("---")

# ============================================================
# MONTHLY TREND
# ============================================================

trend = filtered_df.copy()

trend["Month"] = trend["Order_Date"].dt.strftime("%b")

monthly = trend.groupby("Month")[["Revenue", "Profit"]].sum().reset_index()

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
    template="plotly_dark",
    title="Monthly Revenue & Profit Trend",
    height=450
)

st.plotly_chart(fig, use_container_width=True)

# ============================================================
# CATEGORY ANALYSIS
# ============================================================

col1, col2 = st.columns(2)

category_sales = filtered_df.groupby("Category")["Revenue"].sum().reset_index()

with col1:

    fig = px.bar(
        category_sales,
        x="Category",
        y="Revenue",
        color="Category",
        title="Revenue by Category",
        template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True)

category_profit = filtered_df.groupby("Category")["Profit"].sum().reset_index()

with col2:

    fig = px.pie(
        category_profit,
        names="Category",
        values="Profit",
        hole=0.5,
        title="Profit Share by Category",
        template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TOP STATES
# ============================================================

st.markdown("## 🏆 Top Performing States")

top_states = (
    filtered_df.groupby("State")["Revenue"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)

fig = px.bar(
    top_states,
    x="Revenue",
    y="State",
    orientation="h",
    color="Revenue",
    template="plotly_dark",
    title="Top States by Revenue"
)

st.plotly_chart(fig, use_container_width=True)

# ============================================================
# HEATMAP
# ============================================================

st.markdown("## 🔥 Cross-Dimensional Analysis")

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
    template="plotly_dark",
    title="Revenue Heatmap: Category vs Region"
)

st.plotly_chart(fig, use_container_width=True)

# ============================================================
# DISCOUNT VS PROFIT
# ============================================================

st.markdown("## 📉 Discount vs Profit Impact")

fig = px.scatter(
    filtered_df,
    x="Discount",
    y="Profit",
    size="Revenue",
    color="Category",
    hover_data=["Sub_Category"],
    template="plotly_dark"
)

st.plotly_chart(fig, use_container_width=True)

# ============================================================
# LIVE TRANSACTIONS TABLE
# ============================================================

st.markdown("## ⚡ Live Transactions Feed")

live_table = filtered_df[[
    "State",
    "City",
    "Category",
    "Sub_Category",
    "Revenue",
    "Profit",
    "Quantity"
]].tail(20)

st.dataframe(
    live_table,
    use_container_width=True,
    height=400
)

# ============================================================
# AUTO REFRESH
# ============================================================

st.markdown("---")

st.success(
    f"✅ Live Dashboard Running • Last Updated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
)

time.sleep(2)

st.rerun()

# ============================================================
# END
# ============================================================
