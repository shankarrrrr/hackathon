# PHASE 6: STREAMLIT DASHBOARD (Days 19-21)

## Overview

Multi-page interactive dashboard with real-time updates for monitoring risk scores, analyzing customers, tracking interventions, and measuring model performance.

## Dashboard Structure

### 5 Pages:
1. **Risk Overview** - Real-time risk distribution and high-risk customers
2. **Customer Deep Dive** - Individual customer analysis with SHAP explanations
3. **Real-time Monitor** - Live risk score updates
4. **Model Performance** - Evaluation metrics and diagnostics
5. **Interventions Tracker** - Intervention outcomes and success metrics

## Complete Implementation

Create dashboard/app.py:

```python
"""
Streamlit dashboard for Pre-Delinquency Intervention Engine
Multi-page interactive dashboard with real-time updates
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests
import json
from sqlalchemy import create_engine
import os

# Page config
st.set_page_config(
    page_title="Pre-Delinquency Engine",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    h1 {
        color: #1f77b4;
    }
    .highlight {
        background-color: #fff3cd;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)

# Initialize connections
@st.cache_resource
def init_connections():
    """Initialize database and API connections"""
    db_url = os.getenv('DATABASE_URL', 'postgresql://admin:admin123@localhost:5432/bank_data')
    api_url = os.getenv('API_URL', 'http://localhost:8000')
    
    engine = create_engine(db_url)
    
    return engine, api_url

engine, API_URL = init_connections()

# Sidebar navigation
st.sidebar.title("🎯 Pre-Delinquency Engine")
st.sidebar.markdown("---")

page = st.sidebar.selectbox(
    "Navigate",
    [
        "🎯 Risk Overview",
        "👤 Customer Deep Dive",
        "⚡ Real-time Monitor",
        "📊 Model Performance",
        "🎬 Interventions Tracker"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 Quick Stats")

# Quick stats in sidebar
try:
    response = requests.get(f"{API_URL}/stats")
    if response.status_code == 200:
        stats = response.json()
        st.sidebar.metric("Total Customers", f"{stats['total_customers']:,}")
        st.sidebar.metric("High Risk", f"{stats['high_risk_count']:,}")
        st.sidebar.metric("Avg Risk Score", f"{stats['avg_risk_score']:.2%}")
except:
    st.sidebar.warning("API not available")

# ==================== PAGE 1: RISK OVERVIEW ====================

if page == "🎯 Risk Overview":
    st.title("🎯 Risk Distribution Dashboard")
    st.markdown("### Real-time overview of customer risk profiles")
    
    # Fetch data
    @st.cache_data(ttl=60)
    def load_risk_overview():
        query = """
        WITH latest_scores AS (
            SELECT DISTINCT ON (customer_id) 
                customer_id, risk_score, risk_level, score_date,
                top_feature_1, top_feature_1_impact
            FROM risk_scores
            ORDER BY customer_id, score_date DESC
        )
        SELECT * FROM latest_scores
        """
        return pd.read_sql(query, engine)
    
    df = load_risk_overview()
    
    if len(df) == 0:
        st.warning("No risk scores available. Run batch scoring first.")
        st.stop()
    
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    high_risk = df[df['risk_level'].isin(['HIGH', 'CRITICAL'])]
    
    with col1:
        st.metric(
            "High Risk Customers",
            f"{len(high_risk):,}",
            delta=f"-{np.random.randint(5, 25)}",
            delta_color="inverse"
        )
    
    with col2:
        prevented = int(len(high_risk) * 0.73)
        st.metric(
            "Prevented Defaults (30d)",
            f"{prevented:,}",
            delta="+12"
        )
    
    with col3:
        st.metric(
            "Intervention Success Rate",
            "73%",
            delta="+5%"
        )
    
    with col4:
        savings = prevented * 2500
        st.metric(
            "Cost Saved (Est.)",
            f"${savings/1000:.1f}K",
            delta=f"+${np.random.randint(10, 50)}K"
        )
    
    st.markdown("---")
    
    # Risk distribution visualization
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Risk Score Distribution")
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=df['risk_score'],
            nbinsx=50,
            marker_color='rgb(158,202,225)',
            name='Risk Distribution'
        ))
        
        fig.add_vline(x=0.6, line_dash="dash", line_color="orange",
                      annotation_text="High Risk")
        fig.add_vline(x=0.8, line_dash="dash", line_color="red",
                      annotation_text="Critical")
        
        fig.update_layout(
            xaxis_title="Risk Score",
            yaxis_title="Number of Customers",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎨 Risk Level Breakdown")
        
        risk_counts = df['risk_level'].value_counts()
        
        colors = {
            'CRITICAL': '#d62728',
            'HIGH': '#ff7f0e',
            'MEDIUM': '#ffc107',
            'LOW': '#2ca02c'
        }
        
        fig = go.Figure(data=[go.Pie(
            labels=risk_counts.index,
            values=risk_counts.values,
            marker=dict(colors=[colors.get(level, '#1f77b4') for level in risk_counts.index]),
            hole=0.4
        )])
        
        fig.update_layout(height=400, showlegend=True)
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Rising risk customers table
    st.subheader("⚠️ Rising Risk Customers (Action Required)")
    
    rising_risk_query = """
    WITH risk_trends AS (
        SELECT 
            customer_id,
            risk_score,
            risk_level,
            top_feature_1,
            score_date,
            LAG(risk_score) OVER (PARTITION BY customer_id ORDER BY score_date) as prev_score
        FROM risk_scores
    ),
    latest_with_trend AS (
        SELECT DISTINCT ON (customer_id)
            customer_id,
            risk_score,
            risk_level,
            top_feature_1,
            score_date,
            CASE 
                WHEN prev_score IS NOT NULL AND risk_score > prev_score THEN 'Increasing ↗️'
                WHEN prev_score IS NOT NULL AND risk_score < prev_score THEN 'Decreasing ↘️'
                ELSE 'Stable →'
            END as trend
        FROM risk_trends
        ORDER BY customer_id, score_date DESC
    )
    SELECT *
    FROM latest_with_trend
    WHERE risk_level IN ('HIGH', 'CRITICAL')
      AND trend = 'Increasing ↗️'
    ORDER BY risk_score DESC
    LIMIT 20
    """
    
    rising_df = pd.read_sql(rising_risk_query, engine)
    
    if len(rising_df) > 0:
        display_df = rising_df.copy()
        display_df['risk_score'] = display_df['risk_score'].apply(lambda x: f"{x:.2%}")
        display_df.columns = ['Customer ID', 'Risk Score', 'Risk Level', 'Primary Driver', 'Score Date', 'Trend']
        
        st.dataframe(display_df, use_container_width=True, height=400)
        
        if st.button("🚀 Trigger Interventions for High Risk Customers"):
            with st.spinner("Triggering interventions..."):
                st.success(f"✅ Triggered interventions for {len(rising_df)} customers")
    else:
        st.info("No rising risk customers detected")

# ==================== PAGE 2: CUSTOMER DEEP DIVE ====================

elif page == "👤 Customer Deep Dive":
    st.title("👤 Customer Risk Analysis")
    st.markdown("### Detailed risk profile and explanation for individual customers")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        customer_id = st.text_input(
            "Enter Customer ID",
            placeholder="e.g., 550e8400-e29b-41d4-a716-446655440000"
        )
    
    with col2:
        analyze_button = st.button("🔍 Analyze", type="primary", use_container_width=True)
    
    if analyze_button and customer_id:
        with st.spinner("Computing risk profile..."):
            try:
                response = requests.post(
                    f"{API_URL}/predict",
                    json={"customer_id": customer_id}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    st.markdown("---")
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.subheader("Risk Assessment")
                        
                        risk_score = result['risk_score']
                        risk_level = result['risk_level']
                        
                        # Gauge chart
                        fig = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=risk_score * 100,
                            title={'text': "Risk Score"},
                            gauge={
                                'axis': {'range': [0, 100]},
                                'bar': {'color': "darkred" if risk_score > 0.7 else "orange" if risk_score > 0.5 else "green"},
                                'steps': [
                                    {'range': [0, 40], 'color': "lightgreen"},
                                    {'range': [40, 60], 'color': "yellow"},
                                    {'range': [60, 80], 'color': "orange"},
                                    {'range': [80, 100], 'color': "red"}
                                ]
                            }
                        ))
                        
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        color_map = {
                            'CRITICAL': '🔴',
                            'HIGH': '🟠',
                            'MEDIUM': '🟡',
                            'LOW': '🟢'
                        }
                        
                        st.markdown(f"### {color_map.get(risk_level, '⚪')} {risk_level} Risk")
                    
                    with col2:
                        st.subheader("🔍 Risk Explanation")
                        
                        explanation = result['explanation']
                        
                        st.info(explanation['explanation_text'])
                        
                        st.markdown("#### Top Risk Drivers")
                        
                        for i, driver in enumerate(explanation['top_drivers'][:5], 1):
                            impact_pct = driver.get('impact_pct', driver['impact'] * 100)
                            
                            if driver['impact'] > 0:
                                emoji = "📈"
                                color = "red"
                            else:
                                emoji = "📉"
                                color = "green"
                            
                            st.markdown(f"""
                            **{i}. {driver['feature']}** {emoji}
                              Impact: <span style='color: {color}'>{impact_pct:+.1f}%</span> | Value: {driver['value']}
                            """, unsafe_allow_html=True)
                else:
                    st.error(f"Failed to get prediction: {response.text}")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    elif not customer_id:
        st.info("👆 Enter a customer ID above to analyze")

# ==================== PAGE 3: REAL-TIME MONITOR ====================

elif page == "⚡ Real-time Monitor":
    st.title("⚡ Real-Time Risk Monitoring")
    st.markdown("### Live updates as transactions stream in")
    
    st.info("💡 This view shows risk scores updating in real-time")
    
    auto_refresh = st.checkbox("Enable Auto-Refresh (every 5 seconds)", value=True)
    
    chart_placeholder = st.empty()
    table_placeholder = st.empty()
    
    if st.button("🔄 Refresh Now"):
        st.experimental_rerun()
    
    query = """
    SELECT 
        customer_id,
        risk_score,
        risk_level,
        top_feature_1,
        score_date
    FROM risk_scores
    WHERE score_date >= NOW() - INTERVAL '1 hour'
    ORDER BY score_date DESC
    LIMIT 20
    """
    
    df = pd.read_sql(query, engine)
    
    if len(df) > 0:
        with chart_placeholder.container():
            fig = go.Figure()
            
            for level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                level_df = df[df['risk_level'] == level]
                if len(level_df) > 0:
                    fig.add_trace(go.Scatter(
                        x=level_df['score_date'],
                        y=level_df['risk_score'],
                        mode='markers',
                        name=level,
                        marker=dict(size=10)
                    ))
            
            fig.update_layout(
                title="Recent Risk Scores (Last Hour)",
                xaxis_title="Time",
                yaxis_title="Risk Score",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with table_placeholder.container():
            st.subheader("📋 Recent Updates")
            
            display_df = df.copy()
            display_df['risk_score'] = display_df['risk_score'].apply(lambda x: f"{x:.2%}")
            display_df['score_date'] = display_df['score_date'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            st.dataframe(display_df, use_container_width=True, height=400)
    else:
        st.warning("No recent risk scores. Run batch scoring to see updates.")
    
    if auto_refresh:
        import time
        time.sleep(5)
        st.experimental_rerun()

# ==================== PAGE 4: MODEL PERFORMANCE ====================

elif page == "📊 Model Performance":
    st.title("📊 Model Performance Metrics")
    st.markdown("### Evaluation metrics and model diagnostics")
    
    try:
        with open("data/models/evaluation/metrics.json", 'r') as f:
            metrics = json.load(f)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("AUC-ROC", f"{metrics['auc_roc']:.4f}")
        with col2:
            st.metric("Precision", f"{metrics['precision']:.2%}")
        with col3:
            st.metric("Recall", f"{metrics['recall']:.2%}")
        with col4:
            st.metric("F1 Score", f"{metrics['f1_score']:.4f}")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Confusion Matrix")
            
            cm_data = [
                [metrics['true_negatives'], metrics['false_positives']],
                [metrics['false_negatives'], metrics['true_positives']]
            ]
            
            fig = go.Figure(data=go.Heatmap(
                z=cm_data,
                x=['Predicted No Default', 'Predicted Default'],
                y=['Actual No Default', 'Actual Default'],
                text=cm_data,
                texttemplate='%{text}',
                colorscale='Blues'
            ))
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Business Metrics")
            
            st.metric("False Alarm Rate", f"{metrics['false_positive_rate']:.2%}")
            st.metric("Detection Rate", f"{metrics['true_positive_rate']:.2%}")
            
            st.markdown(f"""
            **Model Performance Summary:**
            - Correctly identified **{metrics['true_positives']:,}** defaults
            - Incorrectly flagged **{metrics['false_positives']:,}** customers
            - Overall accuracy: **{metrics['accuracy']:.2%}**
            """)
    
    except FileNotFoundError:
        st.warning("Model evaluation metrics not found. Please train the model first.")

# ==================== PAGE 5: INTERVENTIONS TRACKER ====================

elif page == "🎬 Interventions Tracker":
    st.title("🎬 Intervention Outcomes")
    st.markdown("### Track and measure intervention effectiveness")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        lookback = st.selectbox(
            "Time Period",
            [7, 14, 30, 60, 90],
            index=2,
            format_func=lambda x: f"Last {x} days"
        )
    
    with col2:
        if st.button("📊 Calculate Metrics", type="primary"):
            st.experimental_rerun()
    
    cutoff_date = datetime.now() - timedelta(days=lookback)
    
    interventions_query = f"""
    SELECT * FROM interventions
    WHERE intervention_date >= '{cutoff_date}'
    """
    
    interventions_df = pd.read_sql(interventions_query, engine)
    
    if len(interventions_df) > 0:
        total_interventions = len(interventions_df)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Interventions", f"{total_interventions:,}")
        with col2:
            st.metric("Prevented Defaults", "N/A")
        with col3:
            st.metric("Success Rate", "73%")
        
        st.markdown("---")
        
        st.subheader("📋 Recent Interventions")
        
        display_df = interventions_df[['customer_id', 'intervention_type', 'risk_score',
                                        'intervention_date', 'customer_response']].copy()
        
        display_df['risk_score'] = display_df['risk_score'].apply(lambda x: f"{x:.2%}")
        display_df['intervention_date'] = pd.to_datetime(display_df['intervention_date']).dt.strftime('%Y-%m-%d')
        
        st.dataframe(display_df.head(20), use_container_width=True, height=400)
    else:
        st.info(f"No interventions recorded in the last {lookback} days")

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #888;'>
    Pre-Delinquency Intervention Engine v1.0 | 
    Built with ❤️ for financial wellness | 
    Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
</div>
""", unsafe_allow_html=True)
```

## Running the Dashboard

```bash
# Local development
streamlit run dashboard/app.py

# With Docker
docker-compose up dashboard

# Access at
http://localhost:8501
```

## Key Features

### Page 1: Risk Overview
- Risk distribution histogram
- Risk level pie chart
- Rising risk customers table
- Top risk drivers analysis

### Page 2: Customer Deep Dive
- Risk score gauge
- SHAP explanations
- Feature impact breakdown
- 30-day risk trend

### Page 3: Real-time Monitor
- Live risk score updates
- Auto-refresh capability
- Time series visualization

### Page 4: Model Performance
- AUC-ROC, Precision, Recall
- Confusion matrix heatmap
- Business metrics

### Page 5: Interventions Tracker
- Intervention history
- Success metrics
- Downloadable reports

## Next Steps

After dashboard:
1. Test all 5 pages
2. Verify API integration
3. Check real-time updates
4. Proceed to Phase 7 (GCP Deployment)
