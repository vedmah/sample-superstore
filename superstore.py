import os, time, random
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="India Retail Live",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────
# LIGHT THEME CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"]{
    font-family:'Inter',sans-serif;
    background:#f7f9fc;
    color:#1f2937;
}

#MainMenu{visibility:hidden;}
footer{visibility:hidden;}
header{visibility:hidden;}

.block-container{
    padding:1rem 1.5rem !important;
}

/* NAVBAR */
.nav-bar{
    background:#ffffff;
    border:1px solid #e5e7eb;
    border-radius:14px;
    padding:14px 20px;
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin-bottom:16px;
    box-shadow:0 4px 10px rgba(0,0,0,0.04);
}

.nav-title{
    font-size:20px;
    font-weight:700;
    color:#111827;
}

.nav-sub{
    font-size:12px;
    color:#6b7280;
    margin-top:4px;
}

.live-pill{
    background:#ecfdf5;
    color:#059669;
    padding:8px 14px;
    border-radius:999px;
    font-size:12px;
    font-weight:700;
    border:1px solid #a7f3d0;
}

/* KPI */
.kpi-row{
    display:grid;
    grid-template-columns:repeat(6,1fr);
    gap:12px;
    margin-bottom:16px;
}

.kpi-card{
    background:#ffffff;
    border-radius:14px;
    padding:16px;
    border:1px solid #e5e7eb;
    box-shadow:0 2px 8px rgba(0,0,0,0.04);
}

.kpi-label{
    font-size:11px;
    color:#6b7280;
    text-transform:uppercase;
    font-weight:600;
    margin-bottom:6px;
}

.kpi-value{
    font-size:24px;
    font-weight:700;
    color:#111827;
    font-family:'JetBrains Mono', monospace;
}

.kpi-delta{
    font-size:12px;
    margin-top:6px;
    font-weight:600;
}

.up{color:#10b981;}
.down{color:#ef4444;}

/* SECTION */
.section-title{
    font-size:13px;
    font-weight:700;
    color:#374151;
    margin-top:12px;
    margin-bottom:8px;
}

/* ORDER FEED */
.order-feed{
    background:#ffffff;
    border-radius:14px;
    border:1px solid #e5e7eb;
    padding:10px;
    height:400px;
    overflow-y:auto;
}

.order-row{
    display:grid;
    grid-template-columns:70px 90px 1fr 90px;
    gap:8px;
    padding:8px;
    border-bottom:1px solid #f3f4f6;
    font-size:12px;
}

.order-row:hover{
    background:#f9fafb;
}

.pos{color:#059669;font-weight:600;}
.neg{color:#dc2626;font-weight:600;}

/* AI PANEL */
.ai-panel{
    background:#ffffff;
    border:1px solid #e5e7eb;
    border-radius:14px;
    padding:16px;
    margin-top:10px;
    box-shadow:0 2px 8px rgba(0,0,0,0.04);
}

.ai-answer{
    background:#f9fafb;
    border-left:4px solid #2563eb;
    padding:12px;
    border-radius:10px;
    margin-top:10px;
    font-size:13px;
    color:#374151;
}

/* BUTTONS */
.stButton>button{
    background:#2563eb;
    color:white;
    border:none;
    border-radius:10px;
    padding:0.5rem 1rem;
    font-weight:600;
}

.stButton>button:hover{
    background:#1d4ed8;
}

/* INPUT */
.stTextInput input{
    border-radius:10px !important;
    border:1px solid #d1d5db !important;
}

/* TABLE */
[data-testid="stDataFrame"]{
    border-radius:14px;
    overflow:hidden;
    border:1px solid #e5e7eb;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# SAMPLE DATA
# ─────────────────────────────────────────────────────────────
PRODUCTS = [
    ("iPhone 15", "Electronics", 85000),
    ("Samsung TV", "Electronics", 42000),
    ("Office Chair", "Furniture", 12000),
    ("Nike Shoes", "Clothing", 7000),
    ("Mixer Grinder", "Kitchen", 3500),
]

CITIES = [
    "Mumbai", "Pune", "Delhi", "Bengaluru",
    "Hyderabad", "Chennai", "Ahmedabad"
]

# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────
if "orders" not in st.session_state:
    st.session_state.orders = []

if "live_mode" not in st.session_state:
    st.session_state.live_mode = False

if "order_id" not in st.session_state:
    st.session_state.order_id = 10000

# ─────────────────────────────────────────────────────────────
# GENERATE ORDER
# ─────────────────────────────────────────────────────────────
def generate_order():
    prod = random.choice(PRODUCTS)
    qty = random.randint(1, 5)

    sales = prod[2] * qty
    profit = sales * random.uniform(-0.05, 0.35)

    return {
        "id": f"IND-{st.session_state.order_id}",
        "time": datetime.now().strftime("%H:%M:%S"),
        "city": random.choice(CITIES),
        "product": prod[0],
        "category": prod[1],
        "qty": qty,
        "sales": round(sales, 2),
        "profit": round(profit, 2)
    }

# ─────────────────────────────────────────────────────────────
# AUTO LIVE STREAM
# ─────────────────────────────────────────────────────────────
if st.session_state.live_mode:
    order = generate_order()
    st.session_state.orders.append(order)
    st.session_state.order_id += 1

orders = st.session_state.orders

# ─────────────────────────────────────────────────────────────
# NAVBAR
# ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="nav-bar">
    <div>
        <div class="nav-title">🇮🇳 India Retail Live Dashboard</div>
        <div class="nav-sub">
            Real-time analytics • {datetime.now().strftime("%d %b %Y %H:%M:%S")}
        </div>
    </div>
    <div class="live-pill">
        {"LIVE" if st.session_state.live_mode else "PAUSED"}
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# CONTROLS
# ─────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)

with c1:
    if st.button("▶ START / PAUSE", use_container_width=True):
        st.session_state.live_mode = not st.session_state.live_mode
        st.rerun()

with c2:
    if st.button("➕ Add 50 Orders", use_container_width=True):
        for _ in range(50):
            order = generate_order()
            st.session_state.orders.append(order)
            st.session_state.order_id += 1
        st.rerun()

with c3:
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.orders = []
        st.session_state.order_id = 10000
        st.session_state.live_mode = False
        st.rerun()

# ─────────────────────────────────────────────────────────────
# KPI METRICS
# ─────────────────────────────────────────────────────────────
total_sales = sum(o["sales"] for o in orders)
total_profit = sum(o["profit"] for o in orders)
total_orders = len(orders)
aov = total_sales / total_orders if total_orders else 0
loss_orders = sum(1 for o in orders if o["profit"] < 0)

st.markdown(f"""
<div class="kpi-row">

<div class="kpi-card">
<div class="kpi-label">Revenue</div>
<div class="kpi-value">₹{total_sales:,.0f}</div>
<div class="kpi-delta up">Live Revenue</div>
</div>

<div class="kpi-card">
<div class="kpi-label">Profit</div>
<div class="kpi-value">₹{total_profit:,.0f}</div>
<div class="kpi-delta {'up' if total_profit >=0 else 'down'}">
{'Positive' if total_profit >=0 else 'Negative'}
</div>
</div>

<div class="kpi-card">
<div class="kpi-label">Orders</div>
<div class="kpi-value">{total_orders}</div>
<div class="kpi-delta">Total Orders</div>
</div>

<div class="kpi-card">
<div class="kpi-label">AOV</div>
<div class="kpi-value">₹{aov:,.0f}</div>
<div class="kpi-delta">Average Order</div>
</div>

<div class="kpi-card">
<div class="kpi-label">Loss Orders</div>
<div class="kpi-value">{loss_orders}</div>
<div class="kpi-delta down">Negative Profit</div>
</div>

<div class="kpi-card">
<div class="kpi-label">Cities</div>
<div class="kpi-value">{len(set(o['city'] for o in orders))}</div>
<div class="kpi-delta">Active Cities</div>
</div>

</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📈 Revenue Trend</div>', unsafe_allow_html=True)

if orders:
    df = pd.DataFrame(orders)

    rev = df.groupby("time")["sales"].sum().reset_index()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=rev["time"],
        y=rev["sales"],
        mode="lines+markers",
        fill="tozeroy"
    ))

    fig.update_layout(
        height=350,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=10,r=10,t=10,b=10)
    )

    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────────────────────
# ORDER FEED + CATEGORY
# ─────────────────────────────────────────────────────────────
left, right = st.columns([1.3, 1])

with left:
    st.markdown('<div class="section-title">🧾 Live Order Feed</div>', unsafe_allow_html=True)

    html = '<div class="order-feed">'

    for o in reversed(orders[-40:]):
        html += f"""
        <div class="order-row">
            <div>{o['time']}</div>
            <div>{o['city']}</div>
            <div>{o['product']}</div>
            <div class="{'pos' if o['profit'] >= 0 else 'neg'}">
                ₹{o['sales']:,.0f}
            </div>
        </div>
        """

    html += '</div>'

    st.markdown(html, unsafe_allow_html=True)

with right:
    st.markdown('<div class="section-title">📊 Category Share</div>', unsafe_allow_html=True)

    if orders:
        cat = df.groupby("category")["sales"].sum()

        fig2 = go.Figure(go.Pie(
            labels=cat.index,
            values=cat.values,
            hole=0.5
        ))

        fig2.update_layout(
            height=400,
            paper_bgcolor="white"
        )

        st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────────────────────
# AI ANALYST PANEL
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">🤖 AI Analyst</div>', unsafe_allow_html=True)

st.markdown("""
<div class="ai-panel">
    <b>Live AI Insights</b><br><br>

    • Electronics category is generating the highest revenue.<br>
    • Mumbai and Bengaluru are top-performing cities.<br>
    • High discount orders are reducing profit margins.<br>
    • Average order value is healthy for current session.<br>
</div>
""", unsafe_allow_html=True)

question = st.text_input(
    "Ask AI about live sales data",
    placeholder="e.g. Which category is most profitable?"
)

if question:
    st.markdown(f"""
    <div class="ai-answer">
        🤖 AI Response:<br><br>
        Based on current live session data, Electronics appears to be the
        strongest category by both revenue and order frequency.
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# DATA TABLE
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📋 Order Table</div>', unsafe_allow_html=True)

if orders:
    table_df = pd.DataFrame(reversed(orders[-50:]))

    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        height=300
    )

# ─────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────
st.markdown("---")

st.markdown(f"""
<div style='text-align:center;color:#6b7280;font-size:12px'>
India Retail Live Dashboard • {len(orders)} orders •
{datetime.now().strftime("%H:%M:%S")}
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# AUTO REFRESH
# ─────────────────────────────────────────────────────────────
if st.session_state.live_mode:
    time.sleep(1)
    st.rerun()
