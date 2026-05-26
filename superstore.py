import os, time, random, json
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta
from collections import deque

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="India Retail — Live Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CSS — trading terminal style ────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}
#MainMenu{visibility:hidden;}footer{visibility:hidden;}header{visibility:hidden;}
[data-testid="collapsedControl"]{display:none!important;}
[data-testid="stSidebar"]{display:none!important;}
.stApp{background:#050a0f;}

/* ── Header ── */
.terminal-header{
  background:linear-gradient(90deg,#060f1a 0%,#0a1628 60%,#060f1a 100%);
  border-bottom:1px solid #00ff8820;
  padding:12px 20px 10px;
  display:flex;align-items:center;justify-content:space-between;
  margin-bottom:14px;
}
.terminal-title{font-family:'DM Mono',monospace;font-size:18px;font-weight:500;
  color:#00ff88;letter-spacing:0.08em;}
.terminal-sub{font-size:11px;color:#1a4a30;margin-top:2px;font-family:'DM Mono',monospace;}
.live-pill{display:inline-flex;align-items:center;gap:6px;background:#001a0a;
  border:1px solid #00ff88;border-radius:4px;padding:4px 12px;
  font-family:'DM Mono',monospace;font-size:12px;color:#00ff88;font-weight:500;}
.live-dot{width:8px;height:8px;border-radius:50%;background:#00ff88;
  animation:blink 1s infinite;}
@keyframes blink{0%,100%{opacity:1;box-shadow:0 0 6px #00ff88;}50%{opacity:0.2;box-shadow:none;}}

/* ── KPI ticker row ── */
.kpi-bar{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-bottom:12px;}
.kpi-tick{background:#060f1a;border:1px solid #0a2a15;border-radius:6px;
  padding:10px 14px;position:relative;overflow:hidden;}
.kpi-tick::before{content:'';position:absolute;bottom:0;left:0;height:2px;width:100%;}
.kpi-tick.g::before{background:linear-gradient(90deg,#00ff88,#00aa55);}
.kpi-tick.r::before{background:linear-gradient(90deg,#ff4444,#cc2222);}
.kpi-tick.b::before{background:linear-gradient(90deg,#4f8ef7,#2255cc);}
.kpi-tick.o::before{background:linear-gradient(90deg,#FF9933,#cc6600);}
.kpi-tick.p::before{background:linear-gradient(90deg,#a78bfa,#7755cc);}
.kpi-tick.y::before{background:linear-gradient(90deg,#f7a83e,#cc7700);}
.kp-lbl{font-size:9px;text-transform:uppercase;letter-spacing:0.1em;color:#1a4a30;
  font-family:'DM Mono',monospace;margin-bottom:4px;}
.kp-val{font-size:20px;font-weight:700;font-family:'DM Mono',monospace;color:#e8ecf5;line-height:1;}
.kp-delta{font-size:11px;font-family:'DM Mono',monospace;margin-top:4px;}
.kp-delta.up{color:#00ff88;} .kp-delta.dn{color:#ff4444;}

/* ── Ticker tape ── */
.ticker-wrap{background:#060f1a;border-top:1px solid #0a2a15;border-bottom:1px solid #0a2a15;
  padding:7px 0;margin-bottom:12px;overflow:hidden;white-space:nowrap;}
.ticker-item{display:inline-block;margin-right:40px;font-family:'DM Mono',monospace;font-size:12px;}
.ticker-item .sym{color:#7c8db5;} 
.ticker-item .val{color:#e8ecf5;font-weight:500;}
.ticker-item.up .chg{color:#00ff88;}
.ticker-item.dn .chg{color:#ff4444;}

/* ── Section label ── */
.sec{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;
  color:#1a4a30;padding:7px 0 7px;border-bottom:1px solid #0a1e10;
  margin-bottom:2px;font-family:'DM Mono',monospace;display:flex;align-items:center;gap:8px;}

/* ── Order feed ── */
.order-feed{background:#060f1a;border:1px solid #0a2a15;border-radius:8px;
  padding:10px;height:420px;overflow-y:auto;font-family:'DM Mono',monospace;font-size:11px;}
.order-row{display:flex;justify-content:space-between;align-items:center;
  padding:5px 6px;border-bottom:1px solid #0a1820;margin-bottom:2px;border-radius:4px;}
.order-row.new{background:#001a0a;animation:flash 0.8s ease-out;}
@keyframes flash{0%{background:#003a20;}100%{background:#001a0a;}}
.order-row .time{color:#1a4a30;font-size:10px;}
.order-row .city{color:#7c8db5;}
.order-row .prod{color:#c8ccd8;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.order-row .amt{font-weight:500;}
.order-row .amt.pos{color:#00ff88;}
.order-row .amt.neg{color:#ff4444;}
.order-row .seg{font-size:9px;padding:2px 6px;border-radius:3px;background:#0a1820;color:#5a7ab5;}

/* ── Chart panel ── */
.chart-panel{background:#060f1a;border:1px solid #0a2a15;border-radius:8px;padding:4px;}

/* ── Candlestick-style revenue bar ── */
hr{border-color:#0a1820!important;}

/* Streamlit overrides */
[data-testid="stMultiSelect"]>div{background:#060f1a!important;border:1px solid #0a2a15!important;border-radius:6px!important;}
[data-testid="stMultiSelect"] span{color:#c8ccd8!important;}
.stMultiSelect label{color:#1a4a30!important;font-size:9px!important;text-transform:uppercase;letter-spacing:0.1em;font-family:'DM Mono',monospace;}
.stSlider label{color:#1a4a30!important;font-size:9px!important;font-family:'DM Mono',monospace;}
div[data-testid="stNumberInput"] label{color:#1a4a30!important;font-size:9px!important;}
.stButton button{background:#001a0a;border:1px solid #00ff88;color:#00ff88;
  font-family:'DM Mono',monospace;font-size:11px;border-radius:4px;padding:4px 12px;}
.stButton button:hover{background:#003a20;}
</style>
""", unsafe_allow_html=True)

# ─── COLOUR PALETTE ───────────────────────────────────────────────────────────
C = {
    "green":"#00ff88","red":"#ff4444","blue":"#4f8ef7","orange":"#FF9933",
    "purple":"#a78bfa","yellow":"#f7a83e","teal":"#34d399","gray":"#1a4a30",
    "cat":{"Electronics":"#4f8ef7","Furniture":"#f7a83e","Office Supplies":"#00ff88",
           "Clothing":"#FF9933","Home & Kitchen":"#a78bfa"},
    "region":{"North":"#FF9933","South":"#00ff88","East":"#4f8ef7","West":"#a78bfa","Central":"#f7a83e"},
}

# ─── MASTER DATA TABLES (static reference) ────────────────────────────────────
STATE_REGION = {
    "Uttar Pradesh":"North","Delhi":"North","Haryana":"North","Punjab":"North",
    "Rajasthan":"North","Uttarakhand":"North","Himachal Pradesh":"North","Jammu & Kashmir":"North",
    "Tamil Nadu":"South","Karnataka":"South","Kerala":"South","Andhra Pradesh":"South",
    "Telangana":"South","Puducherry":"South",
    "West Bengal":"East","Bihar":"East","Odisha":"East","Jharkhand":"East",
    "Assam":"East","Meghalaya":"East","Tripura":"East",
    "Maharashtra":"West","Gujarat":"West","Goa":"West",
    "Madhya Pradesh":"Central","Chhattisgarh":"Central",
}
STATE_CITIES = {
    "Uttar Pradesh":["Lucknow","Kanpur","Agra","Varanasi","Noida","Ghaziabad","Meerut"],
    "Delhi":["New Delhi","Dwarka","Rohini","Karol Bagh","Saket","Pitampura"],
    "Haryana":["Gurugram","Faridabad","Ambala","Karnal","Panipat"],
    "Punjab":["Ludhiana","Amritsar","Jalandhar","Patiala","Mohali"],
    "Rajasthan":["Jaipur","Jodhpur","Udaipur","Kota","Ajmer"],
    "Uttarakhand":["Dehradun","Haridwar","Roorkee","Haldwani"],
    "Himachal Pradesh":["Shimla","Manali","Dharamsala"],
    "Jammu & Kashmir":["Srinagar","Jammu","Baramulla"],
    "Tamil Nadu":["Chennai","Coimbatore","Madurai","Salem","Vellore"],
    "Karnataka":["Bengaluru","Mysuru","Hubli","Mangaluru","Belagavi"],
    "Kerala":["Kochi","Thiruvananthapuram","Kozhikode","Thrissur","Kollam"],
    "Andhra Pradesh":["Visakhapatnam","Vijayawada","Guntur","Tirupati"],
    "Telangana":["Hyderabad","Warangal","Karimnagar","Secunderabad"],
    "Puducherry":["Puducherry","Karaikal"],
    "West Bengal":["Kolkata","Howrah","Asansol","Durgapur","Siliguri"],
    "Bihar":["Patna","Gaya","Muzaffarpur","Bhagalpur"],
    "Odisha":["Bhubaneswar","Cuttack","Rourkela","Sambalpur"],
    "Jharkhand":["Ranchi","Jamshedpur","Dhanbad","Bokaro"],
    "Assam":["Guwahati","Dibrugarh","Jorhat","Silchar"],
    "Meghalaya":["Shillong","Tura"],"Tripura":["Agartala","Udaipur"],
    "Maharashtra":["Mumbai","Pune","Nagpur","Nashik","Thane","Navi Mumbai","Kolhapur"],
    "Gujarat":["Ahmedabad","Surat","Vadodara","Rajkot","Gandhinagar"],
    "Goa":["Panaji","Margao","Vasco da Gama"],
    "Madhya Pradesh":["Bhopal","Indore","Gwalior","Jabalpur","Ujjain"],
    "Chhattisgarh":["Raipur","Bhilai","Bilaspur","Korba"],
}
PRODUCTS = [
    # (name, category, subcategory, base_price, base_margin)
    ("Samsung Galaxy A55","Electronics","Mobile Phones",21999,0.28),
    ("iPhone 15","Electronics","Mobile Phones",84999,0.42),
    ("Redmi Note 13","Electronics","Mobile Phones",16999,0.25),
    ("OnePlus Nord 3","Electronics","Mobile Phones",26999,0.32),
    ("Dell Inspiron 15","Electronics","Laptops",58000,0.35),
    ("HP Pavilion","Electronics","Laptops",51000,0.33),
    ("Lenovo IdeaPad","Electronics","Laptops",45000,0.30),
    ("Samsung 43 4K TV","Electronics","Televisions",40000,0.30),
    ("LG OLED 55","Electronics","Televisions",89000,0.38),
    ("boAt Rockerz 550","Electronics","Accessories",1499,0.20),
    ("JBL Speaker Pro","Electronics","Accessories",3999,0.22),
    ("Ergonomic Chair","Furniture","Chairs",9499,0.22),
    ("Gaming Chair","Furniture","Chairs",13999,0.25),
    ("Office Desk","Furniture","Tables",12999,0.20),
    ("Dining Table 6 Seater","Furniture","Tables",24999,0.18),
    ("3 Seater Fabric Sofa","Furniture","Sofas",26999,0.18),
    ("5-Door Wardrobe","Furniture","Storage",19999,0.15),
    ("Queen Size Bed","Furniture","Beds",19999,0.18),
    ("A4 Ream 500 Sheets","Office Supplies","Paper",449,0.08),
    ("HP LaserJet","Office Supplies","Printers",13999,0.28),
    ("Classmate Notebook","Office Supplies","Stationery",349,0.12),
    ("Ring Binder A4","Office Supplies","Binders",379,0.15),
    ("Levis Jeans","Clothing","Mens Wear",2699,0.35),
    ("Nike Running Shoes","Clothing","Footwear",6499,0.38),
    ("Banarasi Saree","Clothing","Womens Wear",5499,0.25),
    ("Kurti Ethnic","Clothing","Womens Wear",999,0.28),
    ("Puma Sneakers","Clothing","Footwear",4799,0.35),
    ("Prestige Pressure Cooker","Home & Kitchen","Cookware",1899,0.22),
    ("Bajaj Mixer Grinder","Home & Kitchen","Appliances",2499,0.25),
    ("Havells Toaster","Home & Kitchen","Appliances",1599,0.22),
    ("Cotton Bedsheet Set","Home & Kitchen","Bedding",1099,0.18),
    ("Wall Clock Ajanta","Home & Kitchen","Decor",649,0.18),
]
SEGMENTS   = ["Consumer","Corporate","Small Business","Government"]
SHIP_MODES = ["Standard Delivery","Express Delivery","Same Day Delivery","Economy Delivery"]

# ─── ORDER GENERATOR ─────────────────────────────────────────────────────────
def generate_order(order_id: int) -> dict:
    now      = datetime.now()
    state    = random.choice(list(STATE_CITIES.keys()))
    city     = random.choice(STATE_CITIES[state])
    prod     = random.choice(PRODUCTS)
    qty      = random.choices([1,2,3,4,5],[50,25,12,8,5])[0]
    discount = random.choices([0,.05,.10,.15,.20,.25,.30],[25,20,20,15,10,7,3])[0]
    # time-of-day price noise + small random spike
    hour_mult = 1.0 + 0.05 * np.sin(now.hour * np.pi / 12)
    price    = prod[3] * random.uniform(0.94, 1.06) * hour_mult
    sales    = round(price * qty * (1 - discount), 2)
    profit   = round(sales * (prod[4] - discount * 0.7), 2)
    return {
        "id":        f"IND-{order_id:05d}",
        "time":      now.strftime("%H:%M:%S"),
        "timestamp": now,
        "state":     state,
        "city":      city,
        "region":    STATE_REGION[state],
        "segment":   random.choices(SEGMENTS,[45,30,15,10])[0],
        "ship_mode": random.choices(SHIP_MODES,[50,25,10,15])[0],
        "product":   prod[0],
        "category":  prod[1],
        "subcategory": prod[2],
        "qty":       qty,
        "discount":  discount,
        "sales":     sales,
        "profit":    profit,
    }

# ─── SESSION STATE INIT ───────────────────────────────────────────────────────
if "orders" not in st.session_state:
    st.session_state.orders       = []
if "order_id" not in st.session_state:
    st.session_state.order_id     = 10000
if "live_mode" not in st.session_state:
    st.session_state.live_mode    = False
if "speed" not in st.session_state:
    st.session_state.speed        = 2       # seconds between orders
if "minute_sales" not in st.session_state:
    st.session_state.minute_sales = {}      # {HH:MM: sales_sum}
if "second_sales" not in st.session_state:
    st.session_state.second_sales = deque(maxlen=120)  # last 120 seconds
if "prev_sales" not in st.session_state:
    st.session_state.prev_sales   = 0.0
if "last_gen" not in st.session_state:
    st.session_state.last_gen     = time.time()

# ─── GENERATE ORDERS if LIVE ─────────────────────────────────────────────────
now_ts = time.time()
if st.session_state.live_mode:
    elapsed = now_ts - st.session_state.last_gen
    n_new   = int(elapsed // st.session_state.speed)
    if n_new > 0:
        for _ in range(min(n_new, 5)):   # max 5 at once to avoid lag
            o = generate_order(st.session_state.order_id)
            st.session_state.orders.append(o)
            st.session_state.order_id += 1
            # accumulate per-minute and per-second
            mn = o["timestamp"].strftime("%H:%M")
            st.session_state.minute_sales[mn] = \
                st.session_state.minute_sales.get(mn, 0) + o["sales"]
            st.session_state.second_sales.append({
                "ts": o["timestamp"].strftime("%H:%M:%S"),
                "sales": o["sales"],
                "profit": o["profit"],
            })
        st.session_state.last_gen = now_ts

# ─── BUILD DATAFRAME ─────────────────────────────────────────────────────────
orders = st.session_state.orders
df = pd.DataFrame(orders) if orders else pd.DataFrame()

# ─── HEADER ──────────────────────────────────────────────────────────────────
now_str  = datetime.now().strftime("%d %b %Y  %H:%M:%S")
n_orders = len(orders)

st.markdown(f"""
<div class="terminal-header">
  <div>
    <div class="terminal-title">🇮🇳 INDIA RETAIL — LIVE TRADING TERMINAL</div>
    <div class="terminal-sub">Real-time order flow &nbsp;|&nbsp; {now_str} IST</div>
  </div>
  <div class="live-pill">
    <span class="live-dot"></span>
    {'LIVE — ' + str(n_orders) + ' orders' if st.session_state.live_mode else 'PAUSED'}
  </div>
</div>
""", unsafe_allow_html=True)

# ─── CONTROLS ────────────────────────────────────────────────────────────────
ctrl1, ctrl2, ctrl3, ctrl4, ctrl5 = st.columns([1,1,1,1,2])

with ctrl1:
    if st.button("▶  START LIVE" if not st.session_state.live_mode else "⏸  PAUSE"):
        st.session_state.live_mode = not st.session_state.live_mode
        st.session_state.last_gen  = time.time()
        st.rerun()

with ctrl2:
    if st.button("🔄  RESET DATA"):
        st.session_state.orders       = []
        st.session_state.order_id     = 10000
        st.session_state.minute_sales = {}
        st.session_state.second_sales = deque(maxlen=120)
        st.session_state.live_mode    = False
        st.rerun()

with ctrl3:
    speed = st.selectbox("Order Speed", [0.5,1,2,3,5], index=2,
        format_func=lambda x: f"Every {x}s")
    st.session_state.speed = speed

with ctrl4:
    if st.button("➕  Add 50 Orders"):
        for _ in range(50):
            o = generate_order(st.session_state.order_id)
            o["timestamp"] = datetime.now() - timedelta(seconds=random.randint(0,300))
            o["time"] = o["timestamp"].strftime("%H:%M:%S")
            st.session_state.orders.append(o)
            st.session_state.order_id += 1
            mn = o["timestamp"].strftime("%H:%M")
            st.session_state.minute_sales[mn] = \
                st.session_state.minute_sales.get(mn, 0) + o["sales"]
        st.rerun()

with ctrl5:
    if orders:
        tot = sum(o["sales"] for o in orders)
        pft = sum(o["profit"] for o in orders)
        last_10 = orders[-10:] if len(orders) >= 10 else orders
        prev_10 = orders[-20:-10] if len(orders) >= 20 else []
        last10_s = sum(o["sales"] for o in last_10)
        prev10_s = sum(o["sales"] for o in prev_10) if prev_10 else last10_s
        chg = ((last10_s - prev10_s) / prev10_s * 100) if prev10_s else 0
        arrow = "▲" if chg >= 0 else "▼"
        col = "#00ff88" if chg >= 0 else "#ff4444"
        st.markdown(
            f"<div style='font-family:DM Mono,monospace;font-size:11px;color:#1a4a30;padding-top:8px'>"
            f"Total: <b style='color:#e8ecf5'>₹{tot:,.0f}</b> &nbsp;|&nbsp; "
            f"Profit: <b style='color:#00ff88'>₹{pft:,.0f}</b> &nbsp;|&nbsp; "
            f"Last 10 orders: <b style='color:{col}'>{arrow}{abs(chg):.1f}%</b></div>",
            unsafe_allow_html=True
        )

st.markdown("---")

# ─── NO DATA STATE ────────────────────────────────────────────────────────────
if not orders:
    st.markdown("""
    <div style='text-align:center;padding:80px;font-family:DM Mono,monospace;'>
      <div style='font-size:48px;margin-bottom:16px;opacity:0.4'>📊</div>
      <div style='font-size:16px;color:#1a4a30;margin-bottom:8px'>NO LIVE DATA</div>
      <div style='font-size:12px;color:#0a2a15'>Press ▶ START LIVE to begin real-time order stream<br>or click ➕ Add 50 Orders to seed with data</div>
    </div>""", unsafe_allow_html=True)

    if st.session_state.live_mode:
        time.sleep(0.5)
        st.rerun()
    st.stop()

# ─── KPI TICKER BAR ──────────────────────────────────────────────────────────
tot_sales  = sum(o["sales"]  for o in orders)
tot_profit = sum(o["profit"] for o in orders)
tot_orders = len(orders)
avg_order  = tot_sales / max(tot_orders, 1)
margin_pct = (tot_profit / tot_sales * 100) if tot_sales else 0

# today's orders only
today_str  = datetime.now().strftime("%Y-%m-%d")
today_ord  = [o for o in orders if o["timestamp"].strftime("%Y-%m-%d") == today_str]
today_rev  = sum(o["sales"] for o in today_ord)

# last order delta
prev_sales_val = st.session_state.prev_sales
delta_pct      = ((tot_sales - prev_sales_val) / prev_sales_val * 100) if prev_sales_val else 0
st.session_state.prev_sales = tot_sales
d_col  = "up" if delta_pct >= 0 else "dn"
d_arr  = "▲" if delta_pct >= 0 else "▼"
p_col  = "up" if tot_profit >= 0 else "dn"

st.markdown(f"""
<div class="kpi-bar">
  <div class="kpi-tick g">
    <div class="kp-lbl">SESSION REVENUE</div>
    <div class="kp-val">₹{tot_sales/1e5:.2f}L</div>
    <div class="kp-delta {d_col}">{d_arr} {abs(delta_pct):.2f}%</div>
  </div>
  <div class="kpi-tick {'g' if tot_profit>=0 else 'r'}">
    <div class="kp-lbl">SESSION PROFIT</div>
    <div class="kp-val">₹{tot_profit/1e5:.2f}L</div>
    <div class="kp-delta {p_col}">{'▲' if tot_profit>=0 else '▼'} {margin_pct:.1f}% margin</div>
  </div>
  <div class="kpi-tick b">
    <div class="kp-lbl">TOTAL ORDERS</div>
    <div class="kp-val">{tot_orders:,}</div>
    <div class="kp-delta up">▲ AOV ₹{avg_order:,.0f}</div>
  </div>
  <div class="kpi-tick o">
    <div class="kp-lbl">TODAY REVENUE</div>
    <div class="kp-val">₹{today_rev/1e5:.2f}L</div>
    <div class="kp-delta up">▲ {len(today_ord)} orders today</div>
  </div>
  <div class="kpi-tick p">
    <div class="kp-lbl">ACTIVE CITIES</div>
    <div class="kp-val">{len(set(o['city'] for o in orders))}</div>
    <div class="kp-delta up">▲ {len(set(o['state'] for o in orders))} states</div>
  </div>
  <div class="kpi-tick y">
    <div class="kp-lbl">LAST ORDER</div>
    <div class="kp-val">₹{orders[-1]['sales']:,.0f}</div>
    <div class="kp-delta {'up' if orders[-1]['profit']>=0 else 'dn'}">
      {'▲' if orders[-1]['profit']>=0 else '▼'} ₹{orders[-1]['profit']:,.0f} profit
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── TICKER TAPE ─────────────────────────────────────────────────────────────
recent = orders[-15:] if len(orders) >= 15 else orders
tape_html = ""
for o in reversed(recent):
    sign  = "up" if o["profit"] >= 0 else "dn"
    chg   = "▲" if o["profit"] >= 0 else "▼"
    tape_html += (
        f'<span class="ticker-item {sign}">'
        f'<span class="sym">{o["city"][:3].upper()}</span> '
        f'<span class="val">₹{o["sales"]:,.0f}</span> '
        f'<span class="chg">{chg}₹{abs(o["profit"]):,.0f}</span>'
        f'</span>'
    )
st.markdown(f'<div class="ticker-wrap">📡 &nbsp;{tape_html}</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ROW 1 — Live Revenue Chart  |  Order Feed
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec">📈 &nbsp;LIVE REVENUE STREAM &nbsp;|&nbsp; REAL-TIME ORDER FEED</div>', unsafe_allow_html=True)
lc1, lc2 = st.columns([1.6, 1])

with lc1:
    # Build per-second time series from all orders (group by minute for chart)
    mn_data = st.session_state.minute_sales
    if mn_data:
        mn_df = pd.DataFrame(list(mn_data.items()), columns=["time","sales"]).sort_values("time")
        mn_df["profit"] = mn_df["sales"] * (margin_pct / 100)
        mn_df["cumrev"] = mn_df["sales"].cumsum()

        fig_live = go.Figure()

        # candlestick-style: area for cumulative revenue
        fig_live.add_trace(go.Scatter(
            x=mn_df["time"], y=mn_df["cumrev"],
            name="Cumulative Revenue",
            line=dict(color=C["green"], width=2.5),
            fill="tozeroy", fillcolor="rgba(0,255,136,0.06)",
            mode="lines",
        ))
        # per-minute sales bars
        fig_live.add_trace(go.Bar(
            x=mn_df["time"], y=mn_df["sales"],
            name="Per-Minute Revenue",
            marker_color="rgba(79,142,247,0.6)",
            marker_line_width=0,
            yaxis="y2",
        ))
        # profit line
        fig_live.add_trace(go.Scatter(
            x=mn_df["time"], y=mn_df["cumrev"] * (margin_pct/100),
            name="Cumulative Profit",
            line=dict(color=C["orange"], width=1.5, dash="dot"),
            mode="lines",
        ))

        # annotate last value
        last_cum = mn_df["cumrev"].iloc[-1]
        fig_live.add_annotation(
            x=mn_df["time"].iloc[-1], y=last_cum,
            text=f"₹{last_cum/1e5:.2f}L",
            showarrow=False, font=dict(size=11, color=C["green"], family="DM Mono"),
            yshift=14,
        )
        fig_live.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="DM Mono", color="#c8ccd8", size=10),
            height=310, margin=dict(l=8,r=8,t=30,b=8),
            title=dict(text="Cumulative Revenue (green) &amp; Per-Minute Volume (blue)", font=dict(size=11,color="#1a4a30")),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=9,color="#5a7ab5"), orientation="h", y=1.08),
            xaxis=dict(gridcolor="#0a1820", linecolor="#0a2a15", tickfont=dict(size=9,color="#1a4a30"), zeroline=False, tickangle=-30, nticks=20),
            yaxis=dict(gridcolor="#0a1820", linecolor="#0a2a15", tickfont=dict(size=9,color="#1a4a30"), zeroline=False, tickprefix="₹", tickformat=",.0f"),
            yaxis2=dict(overlaying="y", side="right", showgrid=False,
                        tickfont=dict(size=9,color="#4f8ef7"), tickprefix="₹", tickformat=",.0f"),
            barmode="overlay",
        )
        st.plotly_chart(fig_live, use_container_width=True)
    else:
        st.info("Waiting for first minute data...")

with lc2:
    # Live order feed — most recent 40 orders
    feed_html = '<div class="order-feed">'
    show_orders = list(reversed(orders[-40:]))
    for i, o in enumerate(show_orders):
        sign = "pos" if o["profit"] >= 0 else "neg"
        new_cls = " new" if i == 0 else ""
        feed_html += (
            f'<div class="order-row{new_cls}">'
            f'<span class="time">{o["time"]}</span>'
            f'<span class="city">{o["city"][:10]}</span>'
            f'<span class="prod">{o["product"][:18]}</span>'
            f'<span class="amt {sign}">₹{o["sales"]:,.0f}</span>'
            f'<span class="seg">{o["segment"][:4].upper()}</span>'
            f'</div>'
        )
    feed_html += '</div>'
    st.markdown(feed_html, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ROW 2 — Category Donut (live)  |  Region Bar (live)  |  Last 30 orders scatter
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec">🔄 &nbsp;LIVE CATEGORY, REGION & ORDER FLOW</div>', unsafe_allow_html=True)
r1, r2, r3 = st.columns(3)

with r1:
    cat_live = {}
    for o in orders:
        cat_live[o["category"]] = cat_live.get(o["category"],0) + o["sales"]
    fig_cat = go.Figure(go.Pie(
        labels=list(cat_live.keys()), values=list(cat_live.values()), hole=0.6,
        marker_colors=[C["cat"].get(k,"#888") for k in cat_live.keys()],
        textinfo="label+percent", textfont=dict(size=10,color="#c8ccd8",family="DM Mono"),
        insidetextorientation="radial",
    ))
    fig_cat.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False, height=260, margin=dict(l=4,r=4,t=30,b=4),
        title=dict(text="Revenue by Category", font=dict(size=11,color="#1a4a30",family="DM Mono")),
        font=dict(family="DM Mono"),
    )
    st.plotly_chart(fig_cat, use_container_width=True)

with r2:
    reg_live = {}
    for o in orders:
        reg_live[o["region"]] = reg_live.get(o["region"],0) + o["sales"]
    reg_s = sorted(reg_live.items(), key=lambda x: -x[1])
    fig_reg = go.Figure(go.Bar(
        x=[r[1] for r in reg_s], y=[r[0] for r in reg_s],
        orientation="h",
        marker_color=[C["region"].get(r[0],"#888") for r in reg_s],
        marker_line_width=0,
        text=[f"₹{v/1e3:.0f}K" for _,v in reg_s], textposition="outside",
        textfont=dict(size=9,color="#c8ccd8",family="DM Mono"),
    ))
    fig_reg.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=260, margin=dict(l=4,r=60,t=30,b=4),
        title=dict(text="Revenue by Region", font=dict(size=11,color="#1a4a30",family="DM Mono")),
        font=dict(family="DM Mono"),
        xaxis=dict(gridcolor="#0a1820", linecolor="#0a2a15", tickfont=dict(size=9,color="#1a4a30"), tickprefix="₹", tickformat=",.0f", zeroline=False),
        yaxis=dict(gridcolor="rgba(0,0,0,0)", linecolor="#0a2a15", tickfont=dict(size=9,color="#c8ccd8")),
    )
    st.plotly_chart(fig_reg, use_container_width=True)

with r3:
    # Scatter: last 60 orders — time vs sales, colour = profit
    recent60 = orders[-60:]
    fig_sc = go.Figure(go.Scatter(
        x=[o["time"]  for o in recent60],
        y=[o["sales"] for o in recent60],
        mode="markers",
        marker=dict(
            size=[max(5, o["qty"]*2) for o in recent60],
            color=[o["profit"] for o in recent60],
            colorscale=[[0,"#ff4444"],[0.5,"#1a3a1a"],[1,"#00ff88"]],
            showscale=True,
            colorbar=dict(title=dict(text="Profit",font=dict(size=8,color="#1a4a30",family="DM Mono")),
                          tickfont=dict(size=8,color="#1a4a30",family="DM Mono"),thickness=8,len=0.6),
            line=dict(width=0), opacity=0.8,
        ),
        hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>",
    ))
    fig_sc.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=260, margin=dict(l=4,r=60,t=30,b=4),
        title=dict(text="Last 60 Orders (size=qty, color=profit)", font=dict(size=11,color="#1a4a30",family="DM Mono")),
        font=dict(family="DM Mono"),
        xaxis=dict(gridcolor="#0a1820", linecolor="#0a2a15", tickfont=dict(size=8,color="#1a4a30"), tickangle=-30, zeroline=False),
        yaxis=dict(gridcolor="#0a1820", linecolor="#0a2a15", tickfont=dict(size=9,color="#1a4a30"), tickprefix="₹", tickformat=",.0f", zeroline=False),
    )
    st.plotly_chart(fig_sc, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ROW 3 — Top States Bar  |  Segment split  |  Ship mode
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec">🗺️ &nbsp;STATE · SEGMENT · SHIP MODE — LIVE BREAKDOWN</div>', unsafe_allow_html=True)
b1, b2, b3 = st.columns(3)

with b1:
    state_live = {}
    for o in orders:
        state_live[o["state"]] = state_live.get(o["state"],0) + o["sales"]
    top10 = sorted(state_live.items(), key=lambda x: -x[1])[:10]
    fig_st = go.Figure(go.Bar(
        x=[v for _,v in reversed(top10)], y=[s for s,_ in reversed(top10)],
        orientation="h", marker_color=C["orange"], marker_line_width=0,
        text=[f"₹{v/1e3:.0f}K" for _,v in reversed(top10)],
        textposition="outside", textfont=dict(size=9,color="#c8ccd8",family="DM Mono"),
    ))
    fig_st.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=300, margin=dict(l=4,r=60,t=30,b=4),
        title=dict(text="Top 10 States by Revenue", font=dict(size=11,color="#1a4a30",family="DM Mono")),
        font=dict(family="DM Mono"),
        xaxis=dict(gridcolor="#0a1820",linecolor="#0a2a15",tickfont=dict(size=9,color="#1a4a30"),tickprefix="₹",tickformat=",.0f",zeroline=False),
        yaxis=dict(gridcolor="rgba(0,0,0,0)",linecolor="#0a2a15",tickfont=dict(size=9,color="#c8ccd8")),
    )
    st.plotly_chart(fig_st, use_container_width=True)

with b2:
    seg_live = {}
    for o in orders:
        seg_live[o["segment"]] = seg_live.get(o["segment"],0) + o["sales"]
    seg_profit_live = {}
    for o in orders:
        seg_profit_live[o["segment"]] = seg_profit_live.get(o["segment"],0) + o["profit"]
    segs = list(seg_live.keys())
    seg_colors = {"Consumer":C["blue"],"Corporate":C["orange"],"Small Business":C["green"],"Government":C["purple"]}
    fig_seg = go.Figure()
    fig_seg.add_trace(go.Bar(name="Revenue", x=segs, y=[seg_live[s] for s in segs],
        marker_color=[seg_colors.get(s,"#888") for s in segs], marker_line_width=0))
    fig_seg.add_trace(go.Bar(name="Profit", x=segs, y=[seg_profit_live[s] for s in segs],
        marker_color=[C["green"] if seg_profit_live[s]>=0 else C["red"] for s in segs],
        marker_line_width=0, opacity=0.7))
    fig_seg.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=300, margin=dict(l=4,r=4,t=30,b=4),
        title=dict(text="Revenue & Profit by Segment", font=dict(size=11,color="#1a4a30",family="DM Mono")),
        barmode="group", font=dict(family="DM Mono"),
        legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(size=9,color="#5a7ab5")),
        xaxis=dict(gridcolor="#0a1820",linecolor="#0a2a15",tickfont=dict(size=9,color="#c8ccd8"),zeroline=False),
        yaxis=dict(gridcolor="#0a1820",linecolor="#0a2a15",tickfont=dict(size=9,color="#1a4a30"),tickprefix="₹",tickformat=",.0f",zeroline=False),
    )
    st.plotly_chart(fig_seg, use_container_width=True)

with b3:
    ship_live = {}
    for o in orders:
        ship_live[o["ship_mode"]] = ship_live.get(o["ship_mode"],0) + o["sales"]
    ship_colors = {"Standard Delivery":C["blue"],"Express Delivery":C["orange"],
                   "Same Day Delivery":C["red"],"Economy Delivery":C["green"]}
    fig_ship = go.Figure(go.Pie(
        labels=list(ship_live.keys()), values=list(ship_live.values()), hole=0.55,
        marker_colors=[ship_colors.get(k,"#888") for k in ship_live.keys()],
        textinfo="label+percent", textfont=dict(size=9,color="#c8ccd8",family="DM Mono"),
        insidetextorientation="radial",
    ))
    fig_ship.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False, height=300, margin=dict(l=4,r=4,t=30,b=4),
        title=dict(text="Revenue by Ship Mode", font=dict(size=11,color="#1a4a30",family="DM Mono")),
        font=dict(family="DM Mono"),
    )
    st.plotly_chart(fig_ship, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ROW 4 — Sub-category live  |  Discount vs Profit scatter
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec">📦 &nbsp;SUB-CATEGORY PERFORMANCE &nbsp;|&nbsp; DISCOUNT IMPACT</div>', unsafe_allow_html=True)
s1, s2 = st.columns([1.2, 0.8])

with s1:
    subcat_live = {}
    subcat_cat  = {}
    subcat_prof = {}
    for o in orders:
        subcat_live[o["subcategory"]] = subcat_live.get(o["subcategory"],0) + o["sales"]
        subcat_cat[o["subcategory"]]  = o["category"]
        subcat_prof[o["subcategory"]] = subcat_prof.get(o["subcategory"],0) + o["profit"]
    sub_sorted = sorted(subcat_live.items(), key=lambda x: x[1])
    fig_sub = go.Figure(go.Bar(
        x=[v for _,v in sub_sorted], y=[k for k,_ in sub_sorted],
        orientation="h",
        marker_color=[C["cat"].get(subcat_cat.get(k,""),"#888") for k,_ in sub_sorted],
        marker_line_width=0,
        text=[f"₹{v/1e3:.0f}K" for _,v in sub_sorted],
        textposition="outside", textfont=dict(size=9,color="#c8ccd8",family="DM Mono"),
    ))
    fig_sub.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=360, margin=dict(l=4,r=60,t=30,b=4),
        title=dict(text="Revenue by Sub-Category (colour = category)", font=dict(size=11,color="#1a4a30",family="DM Mono")),
        font=dict(family="DM Mono"),
        xaxis=dict(gridcolor="#0a1820",linecolor="#0a2a15",tickfont=dict(size=9,color="#1a4a30"),tickprefix="₹",tickformat=",.0f",zeroline=False),
        yaxis=dict(gridcolor="rgba(0,0,0,0)",linecolor="#0a2a15",tickfont=dict(size=9,color="#c8ccd8")),
    )
    st.plotly_chart(fig_sub, use_container_width=True)

with s2:
    fig_disc = go.Figure(go.Scatter(
        x=[o["discount"] for o in orders],
        y=[o["profit"]   for o in orders],
        mode="markers",
        marker=dict(
            size=5,
            color=[o["sales"] for o in orders],
            colorscale=[[0,"#0a1628"],[0.5,"#FF9933"],[1,"#00ff88"]],
            showscale=True,
            colorbar=dict(title=dict(text="Sales",font=dict(size=8,color="#1a4a30",family="DM Mono")),
                          tickfont=dict(size=8,color="#1a4a30",family="DM Mono"),thickness=8,len=0.6),
            opacity=0.7, line=dict(width=0),
        ),
        hovertemplate="Discount: %{x:.0%}<br>Profit: ₹%{y:,.0f}<extra></extra>",
    ))
    fig_disc.add_hline(y=0, line_color=C["red"], line_dash="dot", line_width=1.5,
                       annotation_text="Break-even", annotation_font_color=C["red"], annotation_font_size=9)
    fig_disc.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=360, margin=dict(l=4,r=60,t=30,b=4),
        title=dict(text="Discount vs Profit (all orders)", font=dict(size=11,color="#1a4a30",family="DM Mono")),
        font=dict(family="DM Mono"),
        xaxis=dict(gridcolor="#0a1820",linecolor="#0a2a15",tickfont=dict(size=9,color="#1a4a30"),
                   tickformat=".0%",title_text="Discount %",title_font=dict(size=9,color="#1a4a30"),zeroline=False),
        yaxis=dict(gridcolor="#0a1820",linecolor="#0a2a15",tickfont=dict(size=9,color="#1a4a30"),
                   tickprefix="₹",title_text="Profit",title_font=dict(size=9,color="#1a4a30"),zeroline=False),
    )
    st.plotly_chart(fig_disc, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ROW 5 — Live Orders Table
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec">📋 &nbsp;LIVE ORDER LOG</div>', unsafe_allow_html=True)

recent_df = pd.DataFrame(list(reversed(orders[-50:])))
if not recent_df.empty:
    show_cols = ["id","time","city","state","region","product","category","segment","qty","discount","sales","profit"]
    show_cols = [c for c in show_cols if c in recent_df.columns]
    display_df = recent_df[show_cols].copy()
    display_df["sales"]    = display_df["sales"].map("₹{:,.0f}".format)
    display_df["profit"]   = display_df["profit"].map("₹{:,.0f}".format)
    display_df["discount"] = display_df["discount"].map("{:.0%}".format)
    display_df.columns     = [c.upper() for c in display_df.columns]
    st.dataframe(display_df, use_container_width=True, hide_index=True, height=320)

# ─── FOOTER + AUTO REFRESH ────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f"<div style='text-align:center;color:#0a2a15;font-size:11px;padding:6px 0;font-family:DM Mono,monospace'>"
    f"🇮🇳 INDIA RETAIL LIVE TERMINAL &nbsp;•&nbsp; {len(orders)} orders streamed &nbsp;•&nbsp; "
    f"Total ₹{tot_sales:,.0f} &nbsp;•&nbsp; {datetime.now().strftime('%H:%M:%S IST')}"
    f"</div>",
    unsafe_allow_html=True,
)

# ─── AUTO-RERUN when LIVE ─────────────────────────────────────────────────────
if st.session_state.live_mode:
    time.sleep(max(0.5, st.session_state.speed))
    st.rerun()
