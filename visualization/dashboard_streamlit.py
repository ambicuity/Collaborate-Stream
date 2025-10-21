"""
Streamlit Dashboard for Collaborate-Stream
Real-time analytics dashboard showing meeting health and engagement metrics
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# Page configuration
st.set_page_config(
    page_title="Collaborate-Stream Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def generate_sample_data():
    """Generate sample metrics for demonstration"""
    import random
    
    num_meetings = 20
    current_time = datetime.now()
    
    meetings = []
    for i in range(num_meetings):
        meetings.append({
            'meeting_id': f'meeting_{i}',
            'timestamp': current_time - timedelta(minutes=random.randint(0, 60)),
            'active_users': random.randint(2, 15),
            'message_count': random.randint(10, 200),
            'avg_latency_ms': random.uniform(20, 300),
            'engagement_score': random.uniform(30, 95),
            'meeting_health': random.choice(['good', 'fair', 'poor']),
            'churn_rate': random.uniform(0, 0.5)
        })
    
    return pd.DataFrame(meetings)


def create_health_gauge(health_score, title="Meeting Health"):
    """Create a gauge chart for health score"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=health_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 40], 'color': "lightgray"},
                {'range': [40, 70], 'color': "gray"},
                {'range': [70, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    fig.update_layout(height=250)
    return fig


def main():
    """Main dashboard"""
    
    # Header
    st.markdown('<h1 class="main-header">📊 Collaborate-Stream Analytics</h1>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.header("Dashboard Controls")
    refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 5, 60, 10)
    auto_refresh = st.sidebar.checkbox("Auto Refresh", value=False)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Filters")
    time_range = st.sidebar.selectbox(
        "Time Range",
        ["Last 5 minutes", "Last 15 minutes", "Last hour", "Last 24 hours"]
    )
    health_filter = st.sidebar.multiselect(
        "Meeting Health",
        ["good", "fair", "poor"],
        default=["good", "fair", "poor"]
    )
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Now"):
        st.rerun()
    
    # Load data
    df = generate_sample_data()
    df = df[df['meeting_health'].isin(health_filter)]
    
    # Key Metrics Row
    st.markdown("## 📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Active Meetings",
            len(df),
            delta=f"+{len(df) // 10}",
            delta_color="normal"
        )
    
    with col2:
        total_users = df['active_users'].sum()
        st.metric(
            "Total Active Users",
            total_users,
            delta=f"+{total_users // 20}",
            delta_color="normal"
        )
    
    with col3:
        avg_latency = df['avg_latency_ms'].mean()
        st.metric(
            "Avg Latency (ms)",
            f"{avg_latency:.1f}",
            delta=f"-{avg_latency * 0.1:.1f}",
            delta_color="inverse"
        )
    
    with col4:
        avg_engagement = df['engagement_score'].mean()
        st.metric(
            "Avg Engagement",
            f"{avg_engagement:.1f}%",
            delta=f"+{avg_engagement * 0.05:.1f}%",
            delta_color="normal"
        )
    
    st.markdown("---")
    
    # Charts Row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Meeting Health Distribution")
        health_counts = df['meeting_health'].value_counts()
        fig = px.pie(
            values=health_counts.values,
            names=health_counts.index,
            color=health_counts.index,
            color_discrete_map={'good': 'green', 'fair': 'orange', 'poor': 'red'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📊 Engagement Score Distribution")
        fig = px.histogram(
            df,
            x='engagement_score',
            nbins=20,
            title="",
            color_discrete_sequence=['#1f77b4']
        )
        fig.update_layout(xaxis_title="Engagement Score", yaxis_title="Count")
        st.plotly_chart(fig, use_container_width=True)
    
    # Charts Row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ⚡ Latency vs Active Users")
        fig = px.scatter(
            df,
            x='active_users',
            y='avg_latency_ms',
            size='message_count',
            color='meeting_health',
            hover_data=['meeting_id'],
            color_discrete_map={'good': 'green', 'fair': 'orange', 'poor': 'red'}
        )
        fig.update_layout(xaxis_title="Active Users", yaxis_title="Avg Latency (ms)")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 💬 Message Activity")
        fig = px.bar(
            df.nlargest(10, 'message_count'),
            x='meeting_id',
            y='message_count',
            color='engagement_score',
            color_continuous_scale='Viridis'
        )
        fig.update_layout(xaxis_title="Meeting ID", yaxis_title="Message Count")
        st.plotly_chart(fig, use_container_width=True)
    
    # Gauge Charts
    st.markdown("---")
    st.markdown("## 🎚️ Health Indicators")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        overall_health = (df['meeting_health'] == 'good').sum() / len(df) * 100
        st.plotly_chart(
            create_health_gauge(overall_health, "Overall Health"),
            use_container_width=True
        )
    
    with col2:
        engagement_health = df['engagement_score'].mean()
        st.plotly_chart(
            create_health_gauge(engagement_health, "Engagement Health"),
            use_container_width=True
        )
    
    with col3:
        latency_health = max(0, 100 - (df['avg_latency_ms'].mean() / 3))
        st.plotly_chart(
            create_health_gauge(latency_health, "Network Health"),
            use_container_width=True
        )
    
    # Meeting Details Table
    st.markdown("---")
    st.markdown("## 📋 Meeting Details")
    
    # Format dataframe for display
    display_df = df.copy()
    display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    display_df['avg_latency_ms'] = display_df['avg_latency_ms'].round(2)
    display_df['engagement_score'] = display_df['engagement_score'].round(2)
    display_df['churn_rate'] = display_df['churn_rate'].round(3)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Auto refresh
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()
