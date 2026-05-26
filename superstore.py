# India Retail Analytics Dashboard (Live Data Version)

```python
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Live Trading Analytics Dashboard",
    page_icon="📈",
    layout="wide"
)

# -------------------------------------------------
# CUSTOM CSS
# -------------------------------------------------
st.markdown("""
<style>
body {
    background-color: #020817;
}

.main {
    background-color: #020817;
    color: white;
}

.metric-card {
    background: linear-gradient(135deg,#0f172a,#111827);
    padding: 20px;
    border-radius: 18px;
    border: 1px solid #1e293b;
    box-shadow: 0px 0px 10px rgba(0,0,0,0.4);
}

.dashboard-title {
    background: linear-gradient(90deg,#172554,#1e3a8a);
    padding: 25px;
    border-radius: 20px;
    margin-bottom: 20px;
}

.small-text {
    color: #94a3b8;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# TITLE
# -------------------------------------------------
st.markdown("""
<div class='dashboard-title'>
    <h1>📈 IN Live Trading Analytics Dashboard</h1>
    <p class='small-text'>Real-Time Market Analytics • NSE/BSE Stocks • Live Financial Dashboard</p>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------
# LIVE STOCK DATA
# -------------------------------------------------
STOCKS = {
    "Reliance": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "Infosys": "INFY.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "Wipro": "WIPRO.NS",
    "SBI": "SBIN.NS",
    "Adani Ports": "ADANIPORTS.NS"
}

# -------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------
st.sidebar.header("📊 Dashboard Filters")

selected_stock = st.sidebar.selectbox(
    "Select Stock",
    list(STOCKS.keys())
)

selected_period = st.sidebar.selectbox(
    "Select Time Period",
    ["1d", "5d", "1mo", "3mo", "6mo", "1y"]
)

selected_interval = st.sidebar.selectbox(
    "Select Interval",
    ["1m", "5m", "15m", "30m", "1h", "1d"]
)

# -------------------------------------------------
# FETCH LIVE DATA
# -------------------------------------------------
stock_symbol = STOCKS[selected_stock]

@st.cache_data(ttl=60)
def load_data(symbol, period, interval):
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)
    df.reset_index(inplace=True)
    return df

try:
    df = load_data(stock_symbol, selected_period, selected_interval)

    latest_close = df['Close'].iloc[-1]
    previous_close = df['Close'].iloc[-2]
    price_change = latest_close - previous_close
    percentage_change = (price_change / previous_close) * 100

    highest_price = df['High'].max()
    lowest_price = df['Low'].min()
    total_volume = int(df['Volume'].sum())

    # -------------------------------------------------
    # KPI CARDS
    # -------------------------------------------------
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class='metric-card'>
            <h4>💰 Current Price</h4>
            <h2>₹{:.2f}</h2>
        </div>
        """.format(latest_close), unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class='metric-card'>
            <h4>📈 Price Change</h4>
            <h2>{:.2f}%</h2>
        </div>
        """.format(percentage_change), unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class='metric-card'>
            <h4>🚀 Highest Price</h4>
            <h2>₹{:.2f}</h2>
        </div>
        """.format(highest_price), unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class='metric-card'>
            <h4>📦 Total Volume</h4>
            <h2>{:,}</h2>
        </div>
        """.format(total_volume), unsafe_allow_html=True)

    st.markdown("---")

    # -------------------------------------------------
    # PRICE TREND CHART
    # -------------------------------------------------
    st.subheader("📉 Live Stock Price Trend")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df.iloc[:, 0],
        y=df['Close'],
        mode='lines',
        fill='tozeroy',
        name='Close Price'
    ))

    fig.update_layout(
        template='plotly_dark',
        height=500,
        paper_bgcolor='#020817',
        plot_bgcolor='#020817'
    )

    st.plotly_chart(fig, use_container_width=True)

    # -------------------------------------------------
    # CANDLESTICK CHART
    # -------------------------------------------------
    st.subheader("🕯️ Candlestick Analysis")

    candle = go.Figure(data=[go.Candlestick(
        x=df.iloc[:, 0],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    )])

    candle.update_layout(
        template='plotly_dark',
        height=600,
        paper_bgcolor='#020817',
        plot_bgcolor='#020817'
    )

    st.plotly_chart(candle, use_container_width=True)

    # -------------------------------------------------
    # VOLUME ANALYSIS
    # -------------------------------------------------
    col5, col6 = st.columns(2)

    with col5:
        st.subheader("📊 Trading Volume")

        volume_fig = px.bar(
            df,
            x=df.iloc[:, 0],
            y='Volume',
            template='plotly_dark'
        )

        volume_fig.update_layout(
            paper_bgcolor='#020817',
            plot_bgcolor='#020817',
            height=450
        )

        st.plotly_chart(volume_fig, use_container_width=True)

    # -------------------------------------------------
    # MOVING AVERAGE
    # -------------------------------------------------
    with col6:
        st.subheader("📈 Moving Average Analysis")

        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA50'] = df['Close'].rolling(50).mean()

        ma_fig = go.Figure()

        ma_fig.add_trace(go.Scatter(
            x=df.iloc[:, 0],
            y=df['Close'],
            mode='lines',
            name='Close Price'
        ))

        ma_fig.add_trace(go.Scatter(
            x=df.iloc[:, 0],
            y=df['MA20'],
            mode='lines',
            name='MA20'
        ))

        ma_fig.add_trace(go.Scatter(
            x=df.iloc[:, 0],
            y=df['MA50'],
            mode='lines',
            name='MA50'
        ))

        ma_fig.update_layout(
            template='plotly_dark',
            height=450,
            paper_bgcolor='#020817',
            plot_bgcolor='#020817'
        )

        st.plotly_chart(ma_fig, use_container_width=True)

    # -------------------------------------------------
    # LIVE MARKET TABLE
    # -------------------------------------------------
    st.subheader("📋 Live Market Snapshot")

    market_data = []

    for name, symbol in STOCKS.items():
        try:
            temp = yf.Ticker(symbol).history(period='1d')
            latest = temp['Close'].iloc[-1]
            open_price = temp['Open'].iloc[-1]
            change = latest - open_price

            market_data.append({
                'Stock': name,
                'Price': round(latest, 2),
                'Open': round(open_price, 2),
                'Change': round(change, 2)
            })
        except:
            pass

    market_df = pd.DataFrame(market_data)

    st.dataframe(
        market_df,
        use_container_width=True,
        height=400
    )

    # -------------------------------------------------
    # AUTO REFRESH
    # -------------------------------------------------
    st.caption("🔄 Dashboard auto-refreshes every 60 seconds")

except Exception as e:
    st.error(f"Error loading live data: {e}")

