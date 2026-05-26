import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="IN India Retail Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------
st.markdown(
    """
    <style>
    .main {
        background-color: #030b1f;
        color: white;
    }

    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }

    .dashboard-title {
        background: linear-gradient(90deg,#102b5c,#1d2c68);
        padding: 30px;
        border-radius: 20px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0px 0px 20px rgba(0,0,0,0.4);
    }

    .metric-card {
        background: linear-gradient(145deg,#0b1635,#101f45);
        border: 1px solid #2a4c8f;
        padding: 20px;
        border-radius: 18px;
        color: white;
        box-shadow: 0px 0px 15px rgba(0,0,0,0.5);
    }

    .section-title {
        color: #7fb3ff;
        font-size: 18px;
        font-weight: bold;
        margin-top: 20px;
        margin-bottom: 15px;
    }

    hr {
        border: 1px solid #1f2d4f;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# SAMPLE DATA GENERATION
# --------------------------------------------------
np.random.seed(42)

states = [
    'Maharashtra', 'Delhi', 'Tamil Nadu', 'Karnataka', 'Punjab',
    'Rajasthan', 'Kerala', 'Assam', 'Tripura', 'Telangana',
    'Haryana', 'Chhattisgarh', 'Andhra Pradesh', 'Bihar', 'Jammu & Kashmir'
]

regions = ['North', 'South', 'East', 'West', 'Central']
categories = ['Electronics', 'Furniture', 'Clothing', 'Office Supplies', 'Home & Kitchen']
segments = ['Consumer', 'Corporate', 'Government', 'Small Business']
ship_modes = ['Standard', 'Express Delivery', 'Economy', 'Same Day']
sub_categories = [
    'Laptops', 'Televisions', 'Mobile Phones', 'Printers', 'Chairs',
    'Tables', 'Storage', 'Beds', 'Sofas', 'Cookware', 'Accessories',
    'Appliances', 'Women\'s Wear', 'Men\'s Wear', 'Footwear'
]

months = pd.date_range('2021-01-01', '2024-12-01', freq='MS')

rows = []

for month in months:
    for _ in range(80):
        category = np.random.choice(categories)
        sub_category = np.random.choice(sub_categories)
        sales = np.random.randint(5000, 500000)
        profit = sales * np.random.uniform(0.05, 0.30)
        discount = np.random.choice([0, 5, 10, 15, 20, 30, 40, 50])
        quantity = np.random.randint(1, 15)

        rows.append({
            'Order Date': month,
            'Year': month.year,
            'Month': month.strftime('%b'),
            'State': np.random.choice(states),
            'Region': np.random.choice(regions),
            'Category': category,
            'Sub-Category': sub_category,
            'Segment': np.random.choice(segments),
            'Ship Mode': np.random.choice(ship_modes),
            'Sales': sales,
            'Profit': profit,
            'Discount': discount,
            'Quantity': quantity
        })


df = pd.DataFrame(rows)

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.markdown(
    """
    <div class='dashboard-title'>
        <h1>🇮🇳 India Retail Analytics Dashboard</h1>
        <p>State-wise Sales Intelligence • 26 States • 156 Cities • 5 Categories • 2021–2024</p>
    </div>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# FILTERS
# --------------------------------------------------
st.markdown("<div class='section-title'>🧩 DASHBOARD FILTERS</div>", unsafe_allow_html=True)

c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    selected_region = st.multiselect("REGION", regions, default=regions)

with c2:
    selected_state = st.multiselect("STATE", states, default=states[:5])

with c3:
    selected_category = st.multiselect("CATEGORY", categories, default=categories)

with c4:
    selected_segment = st.multiselect("SEGMENT", segments, default=segments)

with c5:
    selected_ship = st.multiselect("SHIP MODE", ship_modes, default=ship_modes)

with c6:
    selected_year = st.multiselect("YEAR", sorted(df['Year'].unique()), default=sorted(df['Year'].unique()))

# --------------------------------------------------
# FILTERED DATA
# --------------------------------------------------
filtered_df = df[
    (df['Region'].isin(selected_region)) &
    (df['State'].isin(selected_state)) &
    (df['Category'].isin(selected_category)) &
    (df['Segment'].isin(selected_segment)) &
    (df['Ship Mode'].isin(selected_ship)) &
    (df['Year'].isin(selected_year))
]

# --------------------------------------------------
# KPI SECTION
# --------------------------------------------------
total_sales = filtered_df['Sales'].sum()
total_profit = filtered_df['Profit'].sum()
total_orders = len(filtered_df)
avg_order_value = filtered_df['Sales'].mean()
active_states = filtered_df['State'].nunique()

st.markdown("<hr>", unsafe_allow_html=True)

m1, m2, m3, m4, m5 = st.columns(5)

metrics = [
    (m1, '💰', 'TOTAL REVENUE', f'₹{total_sales/10000000:.2f} Cr'),
    (m2, '📈', 'NET PROFIT', f'₹{total_profit/10000000:.2f} Cr'),
    (m3, '📦', 'UNITS SOLD', f'{filtered_df["Quantity"].sum():,}'),
    (m4, '🏷️', 'AVG ORDER VALUE', f'₹{avg_order_value:,.0f}'),
    (m5, '🏙️', 'ACTIVE STATES', f'{active_states}')
]

for col, icon, title, value in metrics:
    with col:
        st.markdown(
            f"""
            <div class='metric-card'>
                <h3>{icon}</h3>
                <p style='color:#7da9ff;font-size:12px'>{title}</p>
                <h1>{value}</h1>
            </div>
            """,
            unsafe_allow_html=True
        )

# --------------------------------------------------
# REVENUE TREND
# --------------------------------------------------
st.markdown("<div class='section-title'>📅 REVENUE TREND & SEASONALITY</div>", unsafe_allow_html=True)

trend = filtered_df.groupby('Order Date')[['Sales', 'Profit']].sum().reset_index()

left, right = st.columns([2, 1])

with left:
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=trend['Order Date'],
        y=trend['Sales'],
        mode='lines+markers',
        name='Revenue',
        line=dict(color='#ff9f3d', width=3)
    ))

    fig.add_trace(go.Scatter(
        x=trend['Order Date'],
        y=trend['Profit'],
        mode='lines+markers',
        name='Profit',
        line=dict(color='#00d26a', width=3)
    ))

    fig.update_layout(
        paper_bgcolor='#030b1f',
        plot_bgcolor='#030b1f',
        font_color='white',
        height=450
    )

    st.plotly_chart(fig, use_container_width=True)

with right:
    season = filtered_df.groupby('Month')['Sales'].sum().reset_index()

    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    season['Month'] = pd.Categorical(season['Month'], categories=month_order, ordered=True)
    season = season.sort_values('Month')

    fig2 = px.bar(
        season,
        x='Month',
        y='Sales',
        color='Sales',
        height=450
    )

    fig2.update_layout(
        paper_bgcolor='#030b1f',
        plot_bgcolor='#030b1f',
        font_color='white',
        coloraxis_showscale=False
    )

    st.plotly_chart(fig2, use_container_width=True)

# --------------------------------------------------
# CATEGORY PERFORMANCE
# --------------------------------------------------
st.markdown("<div class='section-title'>📦 CATEGORY PERFORMANCE</div>", unsafe_allow_html=True)

cat_sales = filtered_df.groupby('Category')['Sales'].sum().reset_index()
cat_profit = filtered_df.groupby('Category')['Profit'].sum().reset_index()
cat_qty = filtered_df.groupby('Category')['Quantity'].sum().reset_index()

cc1, cc2, cc3 = st.columns(3)

with cc1:
    fig3 = px.bar(cat_sales, x='Category', y='Sales', color='Category', title='Revenue by Category')
    fig3.update_layout(
        paper_bgcolor='#030b1f',
        plot_bgcolor='#030b1f',
        font_color='white',
        showlegend=False,
        height=420
    )
    st.plotly_chart(fig3, use_container_width=True)

with cc2:
    fig4 = px.bar(cat_profit, x='Category', y='Profit', color='Category', title='Profit by Category')
    fig4.update_layout(
        paper_bgcolor='#030b1f',
        plot_bgcolor='#030b1f',
        font_color='white',
        showlegend=False,
        height=420
    )
    st.plotly_chart(fig4, use_container_width=True)

with cc3:
    fig5 = px.pie(
        cat_qty,
        values='Quantity',
        names='Category',
        hole=0.55,
        title='Units Share by Category'
    )

    fig5.update_layout(
        paper_bgcolor='#030b1f',
        plot_bgcolor='#030b1f',
        font_color='white',
        height=420
    )

    st.plotly_chart(fig5, use_container_width=True)

# --------------------------------------------------
# SUB CATEGORY ANALYSIS
# --------------------------------------------------
st.markdown("<div class='section-title'>📚 SUB-CATEGORY DEEP DIVE</div>", unsafe_allow_html=True)

sub_sales = filtered_df.groupby('Sub-Category')['Sales'].sum().sort_values(ascending=False).reset_index()
sub_profit = filtered_df.groupby('Sub-Category')['Profit'].sum().sort_values(ascending=False).reset_index()

s1, s2 = st.columns(2)

with s1:
    fig6 = px.bar(
        sub_sales,
        x='Sales',
        y='Sub-Category',
        orientation='h',
        color='Sales',
        title='Revenue by Sub-Category'
    )

    fig6.update_layout(
        paper_bgcolor='#030b1f',
        plot_bgcolor='#030b1f',
        font_color='white',
        height=650
    )

    st.plotly_chart(fig6, use_container_width=True)

with s2:
    fig7 = px.bar(
        sub_profit,
        x='Profit',
        y='Sub-Category',
        orientation='h',
        color='Profit',
        title='Profit/Loss by Sub-Category'
    )

    fig7.update_layout(
        paper_bgcolor='#030b1f',
        plot_bgcolor='#030b1f',
        font_color='white',
        height=650
    )

    st.plotly_chart(fig7, use_container_width=True)

# --------------------------------------------------
# STATE ANALYSIS
# --------------------------------------------------
st.markdown("<div class='section-title'>🗺️ STATE-WISE & REGIONAL ANALYSIS</div>", unsafe_allow_html=True)

state_data = filtered_df.groupby('State')[['Sales', 'Profit']].sum().sort_values(by='Sales', ascending=False).head(15)

left2, right2 = st.columns([2, 1])

with left2:
    fig8 = go.Figure()

    fig8.add_trace(go.Bar(
        x=state_data['Sales'],
        y=state_data.index,
        orientation='h',
        name='Revenue'
    ))

    fig8.add_trace(go.Bar(
        x=state_data['Profit'],
        y=state_data.index,
        orientation='h',
        name='Profit'
    ))

    fig8.update_layout(
        barmode='overlay',
        paper_bgcolor='#030b1f',
        plot_bgcolor='#030b1f',
        font_color='white',
        height=650,
        title='Top States — Revenue vs Profit'
    )

    st.plotly_chart(fig8, use_container_width=True)

with right2:
    region_sales = filtered_df.groupby('Region')['Sales'].sum().reset_index()
    region_profit = filtered_df.groupby('Region')['Profit'].sum().reset_index()

    fig9 = px.pie(
        region_sales,
        names='Region',
        values='Sales',
        hole=0.55,
        title='Revenue by Region'
    )

    fig9.update_layout(
        paper_bgcolor='#030b1f',
        plot_bgcolor='#030b1f',
        font_color='white',
        height=320
    )

    st.plotly_chart(fig9, use_container_width=True)

    fig10 = px.bar(
        region_profit,
        x='Region',
        y='Profit',
        color='Region',
        title='Profit by Region'
    )

    fig10.update_layout(
        paper_bgcolor='#030b1f',
        plot_bgcolor='#030b1f',
        font_color='white',
        height=320,
        showlegend=False
    )

    st.plotly_chart(fig10, use_container_width=True)

# --------------------------------------------------
# HEATMAPS & CROSS ANALYSIS
# --------------------------------------------------
st.markdown("<div class='section-title'>🔥 CROSS-DIMENSIONAL ANALYSIS</div>", unsafe_allow_html=True)

heat1, heat2 = st.columns(2)

with heat1:
    heatmap_data = filtered_df.pivot_table(
        index='Category',
        columns='Region',
        values='Sales',
        aggfunc='sum'
    )

    fig11 = px.imshow(
        heatmap_data,
        text_auto=True,
        aspect='auto',
        title='Revenue Heatmap: Category × Region'
    )

    fig11.update_layout(
        paper_bgcolor='#030b1f',
        plot_bgcolor='#030b1f',
        font_color='white',
        height=450
    )

    st.plotly_chart(fig11, use_container_width=True)

with heat2:
    heatmap_data2 = filtered_df.pivot_table(
        index='Segment',
        columns='Category',
        values='Sales',
        aggfunc='sum'
    )

    fig12 = px.imshow(
        heatmap_data2,
        text_auto=True,
        aspect='auto',
        title='Revenue Heatmap: Segment × Category'
    )

    fig12.update_layout(
        paper_bgcolor='#030b1f',
        plot_bgcolor='#030b1f',
        font_color='white',
        height=450
    )

    st.plotly_chart(fig12, use_container_width=True)

# --------------------------------------------------
# PROFIT MARGIN & DISCOUNT IMPACT
# --------------------------------------------------
margin_data = filtered_df.groupby('Sub-Category').agg({
    'Sales': 'sum',
    'Profit': 'sum'
}).reset_index()

margin_data['Profit Margin'] = (margin_data['Profit'] / margin_data['Sales']) * 100
margin_data = margin_data.sort_values(by='Profit Margin', ascending=False)

p1, p2 = st.columns(2)

with p1:
    fig13 = px.bar(
        margin_data,
        x='Sub-Category',
        y='Profit Margin',
        color='Profit Margin',
        title='Profit Margin % by Sub-Category'
    )

    fig13.update_layout(
        paper_bgcolor='#030b1f',
        plot_bgcolor='#030b1f',
        font_color='white',
        height=500
    )

    st.plotly_chart(fig13, use_container_width=True)

with p2:
    fig14 = px.scatter(
        filtered_df,
        x='Discount',
        y='Profit',
        size='Sales',
        color='Sales',
        title='Discount vs Profit Impact'
    )

    fig14.update_layout(
        paper_bgcolor='#030b1f',
        plot_bgcolor='#030b1f',
        font_color='white',
        height=500
    )

    st.plotly_chart(fig14, use_container_width=True)

# --------------------------------------------------
# SEGMENT & SHIPPING ANALYSIS
# --------------------------------------------------
st.markdown("<div class='section-title'>🚚 SEGMENT & SHIPPING ANALYSIS</div>", unsafe_allow_html=True)

seg1, seg2, seg3, seg4 = st.columns(4)

segment_sales = filtered_df.groupby('Segment')['Sales'].sum().reset_index()
ship_sales = filtered_df.groupby('Ship Mode')['Sales'].sum().reset_index()
quarter_sales = filtered_df.copy()
quarter_sales['Quarter'] = quarter_sales['Order Date'].dt.quarter
quarter_data = quarter_sales.groupby('Quarter')['Sales'].sum().reset_index()
segment_profit = filtered_df.groupby('Segment')['Profit'].sum().reset_index()

with seg1:
    fig15 = px.pie(segment_sales, values='Sales', names='Segment', hole=0.55, title='Sales by Segment')
    fig15.update_layout(paper_bgcolor='#030b1f', plot_bgcolor='#030b1f', font_color='white', height=350)
    st.plotly_chart(fig15, use_container_width=True)

with seg2:
    fig16 = px.pie(ship_sales, values='Sales', names='Ship Mode', hole=0.55, title='Sales by Ship Mode')
    fig16.update_layout(paper_bgcolor='#030b1f', plot_bgcolor='#030b1f', font_color='white', height=350)
    st.plotly_chart(fig16, use_container_width=True)

with seg3:
    fig17 = px.pie(quarter_data, values='Sales', names='Quarter', hole=0.55, title='Sales by Quarter')
    fig17.update_layout(paper_bgcolor='#030b1f', plot_bgcolor='#030b1f', font_color='white', height=350)
    st.plotly_chart(fig17, use_container_width=True)

with seg4:
    fig18 = px.bar(segment_profit, x='Segment', y='Profit', color='Segment', title='Profit by Segment')
    fig18.update_layout(
        paper_bgcolor='#030b1f',
        plot_bgcolor='#030b1f',
        font_color='white',
        showlegend=False,
        height=350
    )
    st.plotly_chart(fig18, use_container_width=True)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    """
    <center>
        <p style='color:#7da9ff'>Built with ❤️ using Streamlit + Plotly</p>
    </center>
    """,
    unsafe_allow_html=True
)
