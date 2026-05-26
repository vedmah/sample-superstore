import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from streamlit_autorefresh import st_autorefresh

DB_PATH = "business_live.db"
CSV_PATH = "IndiaSuperstore-1.csv"
TABLE_NAME = "orders"

st.set_page_config(page_title="Business Live Dashboard", layout="wide")


def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def load_raw_csv(path=CSV_PATH):
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    rename_map = {
        "Order ID": "order_id",
        "Order Date": "order_date",
        "Ship Date": "ship_date",
        "Ship Mode": "ship_mode",
        "Customer ID": "customer_id",
        "Segment": "segment",
        "Country": "country",
        "City": "city",
        "State": "state",
        "Postal Code": "postal_code",
        "Region": "region",
        "Category": "category",
        "Sub-Category": "sub_category",
        "Product Name": "product_name",
        "Sales": "sales",
        "Quantity": "quantity",
        "Discount": "discount",
        "Profit": "profit",
    }
    df = df.rename(columns=rename_map)

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["ship_date"] = pd.to_datetime(df["ship_date"], errors="coerce")

    for c in ["sales", "quantity", "discount", "profit", "postal_code"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["order_date", "sales", "profit"])
    df["order_day"] = df["order_date"].dt.date.astype(str)
    df["year_month"] = df["order_date"].dt.to_period("M").astype(str)
    return df


def init_db():
    df = load_raw_csv()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            order_id TEXT PRIMARY KEY,
            order_date TEXT,
            ship_date TEXT,
            ship_mode TEXT,
            customer_id TEXT,
            segment TEXT,
            country TEXT,
            city TEXT,
            state TEXT,
            postal_code REAL,
            region TEXT,
            category TEXT,
            sub_category TEXT,
            product_name TEXT,
            sales REAL,
            quantity REAL,
            discount REAL,
            profit REAL,
            order_day TEXT,
            year_month TEXT
        )
        """
    )
    conn.commit()

    existing = pd.read_sql_query(f"SELECT COUNT(*) AS n FROM {TABLE_NAME}", conn)["n"][0]
    if existing == 0:
        df.to_sql(TABLE_NAME, conn, if_exists="append", index=False)

    conn.close()


@st.cache_data(ttl=5)
def read_live_data():
    conn = get_conn()
    df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn)
    conn.close()
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["ship_date"] = pd.to_datetime(df["ship_date"], errors="coerce")
    return df


def insert_order(row: dict):
    conn = get_conn()
    cols = [
        "order_id",
        "order_date",
        "ship_date",
        "ship_mode",
        "customer_id",
        "segment",
        "country",
        "city",
        "state",
        "postal_code",
        "region",
        "category",
        "sub_category",
        "product_name",
        "sales",
        "quantity",
        "discount",
        "profit",
        "order_day",
        "year_month",
    ]
    vals = [row.get(c) for c in cols]
    placeholders = ",".join(["?"] * len(cols))
    conn.execute(
        f"INSERT OR REPLACE INTO {TABLE_NAME} ({','.join(cols)}) VALUES ({placeholders})",
        vals,
    )
    conn.commit()
    conn.close()
    st.cache_data.clear()


def summarize(df):
    total_sales = df["sales"].sum()
    total_profit = df["profit"].sum()
    total_orders = len(df)
    margin = (total_profit / total_sales * 100) if total_sales else 0
    return total_sales, total_profit, total_orders, margin


def build_rag_index(df):
    daily = (
        df.groupby("order_day")
        .agg({"sales": "sum", "profit": "sum", "quantity": "sum", "order_id": "count"})
        .reset_index()
    )
    daily["doc"] = daily.apply(
        lambda r: (
            f"Date {r['order_day']}: sales {r['sales']:.2f}, "
            f"profit {r['profit']:.2f}, quantity {int(r['quantity'])}, orders {int(r['order_id'])}"
        ),
        axis=1,
    )

    cat = df.groupby("category").agg({"sales": "sum", "profit": "sum", "order_id": "count"}).reset_index()
    cat["doc"] = cat.apply(
        lambda r: f"Category {r['category']}: sales {r['sales']:.2f}, profit {r['profit']:.2f}, orders {int(r['order_id'])}",
        axis=1,
    )

    texts = daily["doc"].tolist() + cat["doc"].tolist()
    vect = TfidfVectorizer(stop_words="english")
    X = vect.fit_transform(texts)
    return vect, X, texts


def rag_answer(query, vect, X, texts, df):
    qvec = vect.transform([query])
    sims = cosine_similarity(qvec, X).ravel()
    idx = sims.argsort()[::-1][:4]
    context = "\n".join([texts[i] for i in idx])

    recent = (
        df.sort_values("order_date", ascending=False)
        .head(7)[["order_day", "sales", "profit", "category", "state", "product_name"]]
        .to_dict("records")
    )
    return f"Best match:\n{context}\n\nRecent activity:\n{recent}"


init_db()
raw = read_live_data().sort_values("order_date")
vect, X, texts = build_rag_index(raw)

st.title("Business Live Dashboard")
st.caption("Trading-style live business monitoring with automatic refresh and RAG insights")

st_autorefresh(interval=5000, key="live_refresh")

sales, profit, orders, margin = summarize(raw)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Sales", f"₹{sales:,.0f}")
c2.metric("Profit", f"₹{profit:,.0f}")
c3.metric("Orders", f"{orders:,}")
c4.metric("Margin %", f"{margin:,.2f}")

left, right = st.columns([2, 1])

with left:
    daily = raw.groupby("order_day").agg(sales=("sales", "sum"), profit=("profit", "sum")).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily["order_day"], y=daily["sales"], name="Sales", mode="lines+markers"))
    fig.add_trace(go.Scatter(x=daily["order_day"], y=daily["profit"], name="Profit", mode="lines+markers"))
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h"))
    st.plotly_chart(fig, use_container_width=True)

with right:
    by_cat = raw.groupby("category")["sales"].sum().sort_values(ascending=False).reset_index()
    fig2 = px.bar(by_cat, x="category", y="sales", title="Sales by Category", text_auto=".2s")
    fig2.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig2, use_container_width=True)

c5, c6 = st.columns(2)

with c5:
    by_state = raw.groupby("state")["profit"].sum().sort_values(ascending=False).head(10).reset_index()
    fig3 = px.bar(by_state, x="state", y="profit", title="Top States by Profit", text_auto=".2s")
    fig3.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig3, use_container_width=True)

with c6:
    latest = raw.tail(15)[["order_date", "order_id", "state", "category", "sales", "profit"]].copy()
    latest["order_date"] = latest["order_date"].dt.strftime("%Y-%m-%d")
    st.subheader("Latest Orders")
    st.dataframe(latest, use_container_width=True, height=380)

st.subheader("Live Order Ingestion")
with st.form("manual_order"):
    cols = st.columns(4)
    order_id = cols[0].text_input("Order ID")
    order_date = cols[1].date_input("Order Date")
    ship_date = cols[2].date_input("Ship Date")
    ship_mode = cols[3].selectbox(
        "Ship Mode",
        ["Standard Delivery", "Express Delivery", "Same Day Delivery", "Economy Delivery"],
    )

    cols2 = st.columns(4)
    customer_id = cols2[0].text_input("Customer ID")
    segment = cols2[1].selectbox("Segment", ["Consumer", "Corporate", "Small Business", "Government"])
    country = cols2[2].text_input("Country", value="India")
    city = cols2[3].text_input("City")

    cols3 = st.columns(4)
    state = cols3[0].text_input("State")
    postal_code = cols3[1].number_input("Postal Code", min_value=0, step=1)
    region = cols3[2].selectbox("Region", ["North", "South", "East", "West", "Central"])
    category = cols3[3].selectbox("Category", sorted(raw["category"].dropna().unique().tolist()))

    cols4 = st.columns(4)
    sub_category = cols4[0].text_input("Sub Category")
    product_name = cols4[1].text_input("Product Name")
    sales_i = cols4[2].number_input("Sales", min_value=0.0, step=1.0)
    profit_i = cols4[3].number_input("Profit", step=1.0)

    cols5 = st.columns(2)
    qty = cols5[0].number_input("Quantity", min_value=0.0, step=1.0)
    disc = cols5[1].number_input("Discount", min_value=0.0, step=0.01, format="%.2f")

    submitted = st.form_submit_button("Append Live Order")
    if submitted and order_id:
        insert_order(
            {
                "order_id": order_id,
                "order_date": pd.to_datetime(order_date).isoformat(),
                "ship_date": pd.to_datetime(ship_date).isoformat(),
                "ship_mode": ship_mode,
                "customer_id": customer_id,
                "segment": segment,
                "country": country,
                "city": city,
                "state": state,
                "postal_code": postal_code,
                "region": region,
                "category": category,
                "sub_category": sub_category,
                "product_name": product_name,
                "sales": sales_i,
                "quantity": qty,
                "discount": disc,
                "profit": profit_i,
                "order_day": str(order_date),
                "year_month": pd.Timestamp(order_date).to_period("M").astype(str),
            }
        )
        st.success("Order added and dashboard refreshed.")

st.subheader("RAG Business Copilot")
query = st.chat_input("Ask about sales, profit, trends, risky categories, or best state")

if "chat" not in st.session_state:
    st.session_state.chat = []

if query:
    answer = rag_answer(query, vect, X, texts, raw)
    st.session_state.chat.append(("user", query))
    st.session_state.chat.append(("assistant", answer))

for role, msg in st.session_state.chat:
    with st.chat_message(role):
        st.write(msg)
