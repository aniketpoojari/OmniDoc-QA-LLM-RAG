import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import plotly.express as px

# Page configuration
st.set_page_config(
    page_title="OmniDoc RAG Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Professional dark theme
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #31333f;
    }
    </style>
    """, unsafe_allow_html=True)

LOG_FILE = 'logs/rag_requests.jsonl'
COST_PER_1K_TOKENS = 0.0001  # Example pricing

def load_data():
    if not os.path.exists(LOG_FILE):
        return pd.DataFrame()

    data = []
    with open(LOG_FILE, 'r') as f:
        for line in f:
            try:
                data.append(json.loads(line))
            except:
                continue

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    if not df.empty:
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        df['date'] = df['datetime'].dt.date
        df['hour'] = df['datetime'].dt.hour
    return df

# Sidebar
st.sidebar.title("OmniDoc Monitor")
page = st.sidebar.radio("Navigate", ["Overview", "Performance", "Usage", "Retrieval Quality", "Logs"])
auto_refresh = st.sidebar.checkbox("Auto-refresh", value=False)
refresh_interval = st.sidebar.slider("Refresh Interval (s)", 5, 60, 10)

df = load_data()

if df.empty:
    st.warning("No data found in logs. Start using the RAG system to generate logs.")
    st.stop()

# Helper for status
def get_status(df):
    now = pd.Timestamp.now()
    recent = df[df['datetime'] > (now - timedelta(minutes=15))]
    recent_errors = recent['error'].notnull().sum()
    if recent_errors == 0:
        return "Green", "#28a745"
    elif recent_errors < 5:
        return "Yellow", "#ffc107"
    else:
        return "Red", "#dc3545"

# --- PAGES ---

if page == "Overview":
    st.title("🚀 RAG System Overview")

    status_text, status_color = get_status(df)
    st.markdown(f"### System Status: <span style='color:{status_color}'>{status_text}</span>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    today = datetime.now().date()
    week_ago = today - timedelta(days=7)

    req_today = len(df[df['date'] == today])
    req_week = len(df[df['date'] >= week_ago])
    avg_latency = df['latency'].mean()
    error_rate = (df['error'].notnull().sum() / len(df)) * 100

    col1.metric("Requests Today", req_today)
    col2.metric("Requests (7D)", req_week)
    col3.metric("Avg Latency", f"{avg_latency:.2f}s")
    col4.metric("Error Rate", f"{error_rate:.1f}%")

    st.subheader("Latency Trend")
    trend_df = df.groupby(pd.Grouper(key='datetime', freq='1h'))['latency'].mean().dropna().reset_index()
    if not trend_df.empty:
        fig = px.line(trend_df, x='datetime', y='latency', template="plotly_dark")
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data for latency trend.")

elif page == "Performance":
    st.title("⏱️ Performance Analysis")

    col1, col2, col3 = st.columns(3)
    p50 = df['latency'].quantile(0.5)
    p95 = df['latency'].quantile(0.95)
    p99 = df['latency'].quantile(0.99)

    col1.metric("p50 Latency", f"{p50:.2f}s")
    col2.metric("p95 Latency", f"{p95:.2f}s")
    col3.metric("p99 Latency", f"{p99:.2f}s")

    st.subheader("Latency Distribution")
    fig = px.histogram(df, x='latency', nbins=30, template="plotly_dark", color_discrete_sequence=['#00d4ff'])
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Slowest Queries")
    slow_df = df.sort_values('latency', ascending=False).head(10)[['datetime', 'query', 'latency', 'tokens_output']]
    st.table(slow_df)

elif page == "Usage":
    st.title("💳 Usage & Cost")

    total_tokens = df['tokens_input'].sum() + df['tokens_output'].sum()
    estimated_cost = (total_tokens / 1000) * COST_PER_1K_TOKENS

    col1, col2 = st.columns(2)
    col1.metric("Total Tokens", f"{total_tokens:,}")
    col2.metric("Estimated Cost", f"${estimated_cost:.4f}")

    st.subheader("Token Usage Over Time")
    usage_df = df.groupby(pd.Grouper(key='datetime', freq='1h'))[['tokens_input', 'tokens_output']].sum().dropna(how='all').reset_index()
    if not usage_df.empty:
        fig = px.area(usage_df, x='datetime', y=['tokens_input', 'tokens_output'], template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data for token usage trend.")

    st.subheader("Requests by Hour")
    hour_counts = df.groupby('hour').size().reset_index(name='count')
    fig = px.bar(hour_counts, x='hour', y='count', template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

elif page == "Retrieval Quality":
    st.title("🎯 Retrieval Quality")

    col1, col2 = st.columns(2)
    avg_chunks = df['chunks_retrieved'].mean()
    col1.metric("Avg Chunks Retrieved", f"{avg_chunks:.1f}")

    st.subheader("Chunks Retrieved Distribution")
    fig = px.box(df, y='chunks_retrieved', template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top Queries")
    top_queries = df['query'].value_counts().head(10)
    st.bar_chart(top_queries)

elif page == "Logs":
    st.title("📋 Request Logs")

    # Filters
    col1, col2 = st.columns(2)
    search = col1.text_input("Search Queries")
    min_latency = col2.slider("Min Latency (s)", 0.0, float(df['latency'].max()), 0.0)

    filtered_df = df[df['latency'] >= min_latency]
    if search:
        filtered_df = filtered_df[filtered_df['query'].str.contains(search, case=False, na=False)]

    st.dataframe(
        filtered_df.sort_values('datetime', ascending=False),
        column_config={
            "timestamp": None,
            "datetime": st.column_config.DatetimeColumn("Time"),
            "latency": st.column_config.NumberColumn("Latency (s)", format="%.2f"),
        },
        use_container_width=True
    )

# Auto-refresh at the end so the page renders first
if auto_refresh:
    import time
    time.sleep(refresh_interval)
    st.rerun()
