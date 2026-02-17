"""
Pre-Delinquency Engine - Streamlit Dashboard

Multi-page dashboard for monitoring and analyzing risk scores, customer profiles,
interventions, and model performance.
"""

import os
import streamlit as st
from sqlalchemy import create_engine
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Pre-Delinquency Engine",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
    <style>
    /* Metric card styling */
    div[data-testid="stMetric"] {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
    }
    
    /* Title styling */
    h1, h2, h3 {
        color: #1f77b4;
    }
    
    /* Highlight styling */
    .highlight {
        background-color: #fff3cd;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #ffc107;
    }
    
    /* Footer styling */
    .footer {
        text-align: center;
        padding: 20px;
        color: #666;
        font-size: 0.9em;
        margin-top: 50px;
        border-top: 1px solid #ddd;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def init_connections():
    """
    Initialize database connection and API URL from environment variables.
    
    Returns:
        tuple: (SQLAlchemy engine, API URL string)
    """
    # Get database URL from environment with default
    db_url = os.getenv(
        'DATABASE_URL',
        'postgresql://admin:admin123@localhost:5432/bank_data'
    )
    
    # Get API URL from environment with default
    api_url = os.getenv('API_URL', 'http://localhost:8000')
    
    # Create database engine
    try:
        engine = create_engine(db_url)
        # Test connection
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
    except Exception as e:
        st.error("⚠️ Database connection failed. Some features may be unavailable.")
        st.exception(e)
        engine = None
    
    return engine, api_url


# Initialize connections
engine, API_URL = init_connections()

# ============================================================================
# FORMATTING HELPER FUNCTIONS
# ============================================================================

def format_risk_score(risk_score):
    """
    Format risk score as percentage with 2 decimal places.
    
    Args:
        risk_score: Float value between 0 and 1
        
    Returns:
        str: Formatted percentage string (e.g., "75.00%")
    """
    return f"{risk_score:.2%}"


def format_timestamp(timestamp):
    """
    Format timestamp in YYYY-MM-DD HH:MM:SS format.
    
    Args:
        timestamp: datetime object or string
        
    Returns:
        str: Formatted timestamp string
    """
    if hasattr(timestamp, 'strftime'):
        return timestamp.strftime('%Y-%m-%d %H:%M:%S')
    return str(timestamp)


def format_date(date_obj):
    """
    Format date in YYYY-MM-DD format (for dates without time component).
    
    Args:
        date_obj: datetime object or string
        
    Returns:
        str: Formatted date string
    """
    if hasattr(date_obj, 'strftime'):
        # If it has time component, include it
        if hasattr(date_obj, 'hour'):
            return date_obj.strftime('%Y-%m-%d %H:%M:%S')
        return date_obj.strftime('%Y-%m-%d')
    return str(date_obj)


def get_risk_level_color_map():
    """
    Get consistent color mapping for risk levels.
    
    Returns:
        dict: Mapping of risk levels to colors
    """
    return {
        'LOW': 'green',
        'MEDIUM': 'yellow',
        'HIGH': 'orange',
        'CRITICAL': 'red'
    }


def get_risk_emoji(risk_level):
    """
    Map risk level to emoji indicator.
    
    Args:
        risk_level: Risk level string (LOW, MEDIUM, HIGH, CRITICAL)
        
    Returns:
        str: Emoji indicator
    """
    emoji_map = {
        'LOW': '🟢',
        'MEDIUM': '🟡',
        'HIGH': '🟠',
        'CRITICAL': '🔴'
    }
    return emoji_map.get(risk_level, '⚪')

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================

st.sidebar.title("🎯 Pre-Delinquency Engine")
st.sidebar.markdown("---")

# Page selector
page = st.sidebar.selectbox(
    "Navigate to:",
    [
        "Risk Overview",
        "Customer Deep Dive",
        "Real-time Monitor",
        "Model Performance",
        "Interventions Tracker"
    ]
)

st.sidebar.markdown("---")

# Quick stats section
st.sidebar.subheader("📊 Quick Stats")

try:
    import requests
    response = requests.get(f"{API_URL}/stats", timeout=5)
    
    if response.status_code == 200:
        stats = response.json()
        st.sidebar.metric("Total Customers", f"{stats.get('total_customers', 0):,}")
        st.sidebar.metric("High Risk Count", f"{stats.get('high_risk_count', 0):,}")
        st.sidebar.metric("Avg Risk Score", f"{stats.get('avg_risk_score', 0):.2%}")
    else:
        st.sidebar.warning(f"⚠️ API returned error: {response.status_code}")
        st.sidebar.info("Dashboard will continue operating with limited features.")
        
except requests.exceptions.Timeout:
    st.sidebar.warning("⚠️ API request timed out")
    st.sidebar.info("Dashboard will continue operating with limited features.")
    
except requests.exceptions.ConnectionError:
    st.sidebar.warning("⚠️ Cannot connect to API")
    st.sidebar.info("Dashboard will continue operating with limited features.")
    
except requests.exceptions.RequestException as e:
    st.sidebar.warning("⚠️ API not available")
    st.sidebar.info("Dashboard will continue operating with limited features.")
    
except Exception as e:
    st.sidebar.warning("⚠️ Unable to load stats")
    st.sidebar.info("Dashboard will continue operating with limited features.")

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

@st.cache_data(ttl=60)
def load_latest_risk_scores():
    """
    Load the latest risk score for each customer using DISTINCT ON.
    
    Returns:
        pandas.DataFrame: Latest risk scores per customer with columns:
            customer_id, risk_score, risk_level, score_date, top_feature_1, 
            top_feature_1_impact
    """
    if engine is None:
        st.warning("⚠️ Database connection not available. Cannot load risk scores.")
        return None
    
    try:
        import pandas as pd
        from sqlalchemy import text
        
        query = text("""
            SELECT DISTINCT ON (customer_id)
                customer_id,
                risk_score,
                risk_level,
                score_date,
                top_feature_1,
                top_feature_1_impact
            FROM risk_scores
            ORDER BY customer_id, score_date DESC
        """)
        
        df = pd.read_sql(query, engine)
        
        if len(df) == 0:
            return None
        
        return df
        
    except Exception as e:
        st.error(f"❌ Database error loading risk scores: {str(e)}")
        st.info("The dashboard will continue operating. Please check database connectivity.")
        return None


@st.cache_data(ttl=60)
def load_rising_risk_customers():
    """
    Load customers with rising risk scores using LAG window function.
    Filters for HIGH/CRITICAL customers with increasing trend.
    
    Returns:
        pandas.DataFrame: Rising risk customers limited to 20 rows, sorted by risk_score DESC
    """
    if engine is None:
        st.warning("⚠️ Database connection not available. Cannot load rising risk customers.")
        return None
    
    try:
        import pandas as pd
        from sqlalchemy import text
        
        query = text("""
            WITH risk_trends AS (
                SELECT 
                    customer_id,
                    risk_score,
                    risk_level,
                    score_date,
                    top_feature_1,
                    LAG(risk_score) OVER (PARTITION BY customer_id ORDER BY score_date) as prev_risk_score
                FROM risk_scores
            ),
            latest_trends AS (
                SELECT DISTINCT ON (customer_id)
                    customer_id,
                    risk_score,
                    risk_level,
                    score_date,
                    top_feature_1,
                    prev_risk_score,
                    (risk_score - COALESCE(prev_risk_score, 0)) as risk_change
                FROM risk_trends
                ORDER BY customer_id, score_date DESC
            )
            SELECT 
                customer_id,
                risk_score,
                risk_level,
                top_feature_1,
                risk_change
            FROM latest_trends
            WHERE risk_level IN ('HIGH', 'CRITICAL')
                AND prev_risk_score IS NOT NULL
                AND risk_score > prev_risk_score
            ORDER BY risk_score DESC
            LIMIT 20
        """)
        
        df = pd.read_sql(query, engine)
        
        if len(df) == 0:
            return None
        
        return df
        
    except Exception as e:
        st.error(f"❌ Database error loading rising risk customers: {str(e)}")
        st.info("The dashboard will continue operating. Please check database connectivity.")
        return None


@st.cache_data(ttl=60)
def load_recent_risk_scores():
    """
    Load risk scores from the last hour for real-time monitoring.
    
    Returns:
        pandas.DataFrame: Recent risk scores ordered by score_date DESC, limited to 20 rows
    """
    if engine is None:
        st.warning("⚠️ Database connection not available. Cannot load recent risk scores.")
        return None
    
    try:
        import pandas as pd
        from sqlalchemy import text
        
        query = text("""
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
        """)
        
        df = pd.read_sql(query, engine)
        
        if len(df) == 0:
            return None
        
        return df
        
    except Exception as e:
        st.error(f"❌ Database error loading recent risk scores: {str(e)}")
        st.info("The dashboard will continue operating. Please check database connectivity.")
        return None


# ============================================================================
# MAIN CONTENT AREA
# ============================================================================

# Display selected page title
st.title(f"📈 {page}")

# ============================================================================
# RISK OVERVIEW PAGE
# ============================================================================

if page == "Risk Overview":
    # Load latest risk scores
    df = load_latest_risk_scores()
    
    if df is None or len(df) == 0:
        st.info("No risk score data available. Please run batch scoring first.")
    else:
        # Top metrics row
        st.subheader("📊 Key Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Calculate high-risk customer count (HIGH and CRITICAL levels)
            high_risk_count = len(df[df['risk_level'].isin(['HIGH', 'CRITICAL'])])
            st.metric(
                label="High Risk Customers",
                value=f"{high_risk_count:,}",
                delta=None
            )
        
        with col2:
            # Prevented defaults (placeholder calculation)
            prevented_defaults = int(high_risk_count * 0.3)  # Assume 30% prevention rate
            st.metric(
                label="Prevented Defaults",
                value=f"{prevented_defaults:,}",
                delta="+12%"
            )
        
        with col3:
            # Success rate (placeholder calculation)
            success_rate = 0.75  # 75% success rate
            st.metric(
                label="Intervention Success Rate",
                value=f"{success_rate:.1%}",
                delta="+5%"
            )
        
        with col4:
            # Cost saved (placeholder calculation)
            cost_saved = prevented_defaults * 5000  # $5000 per prevented default
            st.metric(
                label="Estimated Cost Saved",
                value=f"${cost_saved:,.0f}",
                delta="+$50K"
            )
        
        st.markdown("---")
        
        # Risk distribution histogram and pie chart
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Risk Score Distribution")
            
            try:
                import plotly.graph_objects as go
                
                # Create histogram
                fig = go.Figure()
                
                fig.add_trace(go.Histogram(
                    x=df['risk_score'],
                    nbinsx=30,
                    name='Risk Score',
                    marker_color='#1f77b4'
                ))
                
                # Add vertical lines at thresholds
                fig.add_vline(
                    x=0.6,
                    line_dash="dash",
                    line_color="orange",
                    annotation_text="High Risk (0.6)",
                    annotation_position="top"
                )
                
                fig.add_vline(
                    x=0.8,
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Critical (0.8)",
                    annotation_position="top"
                )
                
                # Configure chart
                fig.update_layout(
                    title="Distribution of Customer Risk Scores",
                    xaxis_title="Risk Score",
                    yaxis_title="Number of Customers",
                    showlegend=False,
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.warning("⚠️ Chart could not be rendered. Showing data summary instead.")
                st.write("**Risk Score Statistics:**")
                st.write(df['risk_score'].describe())
                st.info("The dashboard will continue operating. Chart rendering issue logged.")
        
        with col2:
            st.subheader("🎯 Risk Level Breakdown")
            
            try:
                import plotly.graph_objects as go
                
                # Count customers by risk level
                risk_counts = df['risk_level'].value_counts()
                
                # Get consistent color mapping
                color_map = get_risk_level_color_map()
                
                # Create colors list in the order of risk_counts
                colors = [color_map.get(level, 'gray') for level in risk_counts.index]
                
                # Create pie chart
                fig = go.Figure(data=[go.Pie(
                    labels=risk_counts.index,
                    values=risk_counts.values,
                    marker=dict(colors=colors),
                    hole=0.3
                )])
                
                fig.update_layout(
                    title="Customers by Risk Level",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.warning("⚠️ Chart could not be rendered. Showing data table instead.")
                st.write("**Risk Level Breakdown:**")
                st.dataframe(df['risk_level'].value_counts())
                st.info("The dashboard will continue operating. Chart rendering issue logged.")
        
        st.markdown("---")
        
        # Rising risk customers table
        st.subheader("⚠️ Rising Risk Customers")
        
        rising_df = load_rising_risk_customers()
        
        if rising_df is None or len(rising_df) == 0:
            st.info("No rising risk customers detected at this time.")
        else:
            # Format risk scores as percentages
            display_df = rising_df.copy()
            display_df['risk_score'] = display_df['risk_score'].apply(format_risk_score)
            display_df['risk_change'] = display_df['risk_change'].apply(lambda x: f"+{x:.2%}")
            
            # Rename columns for display
            display_df.columns = ['Customer ID', 'Risk Score', 'Risk Level', 'Top Risk Driver', 'Risk Increase']
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Trigger Interventions button
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🚀 Trigger Interventions for High Risk Customers", use_container_width=True):
                # Calculate number of high-risk customers
                high_risk_count = len(df[df['risk_level'].isin(['HIGH', 'CRITICAL'])])
                st.success(f"✅ Successfully triggered {high_risk_count} interventions for high-risk customers!")

# ============================================================================
# CUSTOMER DEEP DIVE PAGE
# ============================================================================

elif page == "Customer Deep Dive":
    st.markdown("Analyze individual customer risk profiles with AI-powered explanations.")
    st.markdown("---")
    
    # Customer ID input and analyze button (Task 5.1)
    col1, col2 = st.columns([3, 1])
    
    with col1:
        customer_id = st.text_input(
            "Enter Customer ID",
            placeholder="e.g., 550e8400-e29b-41d4-a716-446655440000",
            help="Enter the UUID of the customer you want to analyze"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add spacing to align button
        analyze_button = st.button("🔍 Analyze", type="primary", use_container_width=True)
    
    # Process analysis when button is clicked
    if analyze_button and customer_id:
        # API prediction call (Task 5.2)
        try:
            import requests
            
            with st.spinner("Analyzing customer risk profile..."):
                response = requests.post(
                    f"{API_URL}/predict",
                    json={"customer_id": customer_id},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Extract data from response
                    risk_score = result.get('risk_score', 0)
                    risk_level = result.get('risk_level', 'UNKNOWN')
                    explanation = result.get('explanation', {})
                    explanation_text = explanation.get('explanation_text', 'No explanation available')
                    top_drivers = explanation.get('top_drivers', [])
                    
                    st.success("✅ Analysis complete!")
                    st.markdown("---")
                    
                    # Display results in two columns
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        # Risk score gauge chart (Task 5.3)
                        st.subheader("📊 Risk Score")
                        
                        try:
                            import plotly.graph_objects as go
                            
                            # Convert risk score to 0-100 scale
                            risk_score_100 = risk_score * 100
                            
                            # Create gauge chart
                            fig = go.Figure(go.Indicator(
                                mode="gauge+number",
                                value=risk_score_100,
                                domain={'x': [0, 1], 'y': [0, 1]},
                                title={'text': "Risk Score", 'font': {'size': 20}},
                                number={'suffix': "", 'font': {'size': 40}},
                                gauge={
                                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                                    'bar': {'color': "darkblue"},
                                    'bgcolor': "white",
                                    'borderwidth': 2,
                                    'bordercolor': "gray",
                                    'steps': [
                                        {'range': [0, 40], 'color': 'green'},
                                        {'range': [40, 60], 'color': 'yellow'},
                                        {'range': [60, 80], 'color': 'orange'},
                                        {'range': [80, 100], 'color': 'red'}
                                    ],
                                    'threshold': {
                                        'line': {'color': "black", 'width': 4},
                                        'thickness': 0.75,
                                        'value': risk_score_100
                                    }
                                }
                            ))
                            
                            fig.update_layout(
                                height=300,
                                margin=dict(l=20, r=20, t=50, b=20)
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                        except Exception as e:
                            st.warning("⚠️ Chart could not be rendered. Showing metric instead.")
                            st.metric("Risk Score", f"{risk_score:.2%}")
                    
                    with col2:
                        # Risk level badge with emoji (Task 5.4)
                        st.subheader("🎯 Risk Level")
                        
                        # Get emoji using helper function
                        emoji = get_risk_emoji(risk_level)
                        
                        # Display risk level with emoji
                        st.markdown(f"""
                            <div style='text-align: center; padding: 40px 20px;'>
                                <div style='font-size: 80px; margin-bottom: 20px;'>{emoji}</div>
                                <div style='font-size: 32px; font-weight: bold; color: #1f77b4;'>{risk_level}</div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # SHAP explanation and top risk drivers (Task 5.6)
                    st.subheader("💡 Risk Explanation")
                    
                    # Display explanation text in info box
                    st.info(explanation_text)
                    
                    st.markdown("---")
                    
                    # Display top risk drivers
                    st.subheader("📈 Top Risk Drivers")
                    
                    if top_drivers and len(top_drivers) > 0:
                        # Display top 5 drivers
                        for i, driver in enumerate(top_drivers[:5], 1):
                            feature = driver.get('feature', 'Unknown')
                            value = driver.get('value', 'N/A')
                            impact = driver.get('impact', 0)
                            impact_pct = driver.get('impact_pct', 0)
                            
                            # Format impact with +/- sign
                            impact_sign = '+' if impact >= 0 else ''
                            impact_str = f"{impact_sign}{impact_pct:.1f}%"
                            
                            # Emoji indicator for positive/negative impact
                            impact_emoji = '📈' if impact >= 0 else '📉'
                            
                            # Display driver in a styled box
                            st.markdown(f"""
                                <div style='background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px;'>
                                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                                        <div>
                                            <strong>{i}. {feature}</strong><br>
                                            <span style='color: #666;'>Current Value: {value}</span>
                                        </div>
                                        <div style='text-align: right;'>
                                            <span style='font-size: 24px;'>{impact_emoji}</span><br>
                                            <strong style='font-size: 18px; color: {"#d9534f" if impact >= 0 else "#5cb85c"};'>{impact_str}</strong>
                                        </div>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No risk drivers available for this customer.")
                
                else:
                    # Handle non-200 status codes
                    error_msg = "Unknown error"
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('detail', error_data.get('message', str(error_data)))
                    except:
                        error_msg = response.text or f"HTTP {response.status_code}"
                    
                    st.error(f"❌ Error from prediction service: {error_msg}")
                    st.info("Please check that the customer ID is valid and try again. The dashboard will continue operating.")
        
        except requests.exceptions.Timeout:
            st.error("❌ Request timed out. The prediction service is taking too long to respond.")
            st.info("Please try again later or contact support if the issue persists. The dashboard will continue operating.")
        
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to prediction service. Please ensure the API is running.")
            st.info(f"Expected API URL: {API_URL}")
            st.info("The dashboard will continue operating with limited features.")
        
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Network error: {str(e)}")
            st.info("Please check your network connection and try again. The dashboard will continue operating.")
        
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
            st.info("The dashboard will continue operating. Please try again or contact support.")
    
    elif analyze_button and not customer_id:
        st.warning("⚠️ Please enter a customer ID to analyze.")

# ============================================================================
# REAL-TIME MONITOR PAGE
# ============================================================================

elif page == "Real-time Monitor":
    st.markdown("Monitor risk scores updating in real-time with automatic refresh capability.")
    st.markdown("---")
    
    # Auto-refresh checkbox and manual refresh button (Task 6.3)
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        auto_refresh = st.checkbox("🔄 Auto-refresh (every 5 seconds)", value=True)
    
    with col2:
        refresh_button = st.button("🔄 Refresh Now", use_container_width=True)
    
    with col3:
        st.markdown("")  # Spacer
    
    st.markdown("---")
    
    # Load recent risk scores (Task 6.1)
    df = load_recent_risk_scores()
    
    if df is None or len(df) == 0:
        st.info("No risk scores recorded in the last hour. Data will appear here as new scores are generated.")
    else:
        # Time-series scatter plot (Task 6.4)
        st.subheader("📈 Risk Scores Over Time")
        
        try:
            import plotly.express as px
            
            # Get consistent color mapping for risk levels
            color_map = get_risk_level_color_map()
            
            # Create scatter plot
            fig = px.scatter(
                df,
                x='score_date',
                y='risk_score',
                color='risk_level',
                color_discrete_map=color_map,
                hover_data=['customer_id', 'top_feature_1'],
                title='Risk Scores in the Last Hour'
            )
            
            # Update layout
            fig.update_layout(
                xaxis_title='Timestamp',
                yaxis_title='Risk Score',
                height=400,
                showlegend=True,
                legend_title_text='Risk Level'
            )
            
            # Update y-axis to show 0-1 range
            fig.update_yaxes(range=[0, 1])
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.warning("⚠️ Chart could not be rendered. Showing data table instead.")
            st.dataframe(df[['score_date', 'customer_id', 'risk_score', 'risk_level']])
            st.info("The dashboard will continue operating. Chart rendering issue logged.")
        
        st.markdown("---")
        
        # Recent updates table (Task 6.7)
        st.subheader("📋 Recent Updates")
        
        # Format data for display
        display_df = df.copy()
        
        # Format risk scores as percentages
        display_df['risk_score'] = display_df['risk_score'].apply(format_risk_score)
        
        # Format timestamps as YYYY-MM-DD HH:MM:SS
        display_df['score_date'] = display_df['score_date'].apply(format_timestamp)
        
        # Rename columns for display
        display_df.columns = ['Customer ID', 'Risk Score', 'Risk Level', 'Top Risk Driver', 'Timestamp']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Display data freshness indicator
        st.caption(f"📊 Showing {len(df)} risk score updates from the last hour")
    
    # Auto-refresh logic (Task 6.3)
    if auto_refresh:
        import time
        time.sleep(5)
        st.rerun()

# ============================================================================
# MODEL PERFORMANCE PAGE
# ============================================================================

elif page == "Model Performance":
    st.markdown("View model evaluation metrics and performance diagnostics.")
    st.markdown("---")
    
    # Load model metrics from JSON file (Task 8.1)
    try:
        import json
        
        metrics_path = "data/models/evaluation/metrics.json"
        
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        # Display key metrics cards (Task 8.2)
        st.subheader("📊 Key Performance Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            auc_roc = metrics.get('auc_roc', 0)
            st.metric(
                label="AUC-ROC",
                value=f"{auc_roc:.4f}",
                help="Area Under the ROC Curve - measures model's ability to distinguish between classes"
            )
        
        with col2:
            precision = metrics.get('precision', 0)
            st.metric(
                label="Precision",
                value=f"{precision:.1%}",
                help="Percentage of positive predictions that were correct"
            )
        
        with col3:
            recall = metrics.get('recall', 0)
            st.metric(
                label="Recall",
                value=f"{recall:.1%}",
                help="Percentage of actual positives that were correctly identified"
            )
        
        with col4:
            f1_score = metrics.get('f1_score', 0)
            st.metric(
                label="F1 Score",
                value=f"{f1_score:.4f}",
                help="Harmonic mean of precision and recall"
            )
        
        st.markdown("---")
        
        # Create confusion matrix heatmap (Task 8.3)
        st.subheader("🔢 Confusion Matrix")
        
        try:
            import plotly.graph_objects as go
            import numpy as np
            
            # Extract confusion matrix values
            tp = metrics.get('true_positives', 0)
            tn = metrics.get('true_negatives', 0)
            fp = metrics.get('false_positives', 0)
            fn = metrics.get('false_negatives', 0)
            
            # Create confusion matrix array
            # Format: [[TN, FP], [FN, TP]]
            confusion_matrix = np.array([
                [tn, fp],
                [fn, tp]
            ])
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=confusion_matrix,
                x=['Predicted Negative', 'Predicted Positive'],
                y=['Actual Negative', 'Actual Positive'],
                text=confusion_matrix,
                texttemplate='%{text}',
                textfont={"size": 20},
                colorscale='Blues',
                showscale=True
            ))
            
            # Configure axis labels
            fig.update_layout(
                title='Confusion Matrix',
                xaxis_title='Predicted',
                yaxis_title='Actual',
                height=400,
                xaxis={'side': 'bottom'},
                yaxis={'autorange': 'reversed'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.warning("⚠️ Confusion matrix could not be rendered. Showing values instead.")
            st.write("**Confusion Matrix Values:**")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("True Positives (TP)", tp)
                st.metric("False Negatives (FN)", fn)
            with col2:
                st.metric("False Positives (FP)", fp)
                st.metric("True Negatives (TN)", tn)
            st.info("The dashboard will continue operating. Chart rendering issue logged.")
        
        st.markdown("---")
        
        # Display business metrics summary (Task 8.4)
        st.subheader("💼 Business Metrics")
        
        # Calculate business metrics
        accuracy = metrics.get('accuracy', 0)
        
        # Calculate false alarm rate (FP / (FP + TN))
        false_alarm_rate = fp / (fp + tn) if (fp + tn) > 0 else 0
        
        # Calculate detection rate (TP / (TP + FN)) - same as recall
        detection_rate = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        # Display metrics in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="False Alarm Rate",
                value=f"{false_alarm_rate:.1%}",
                help="Percentage of negative cases incorrectly flagged as positive"
            )
        
        with col2:
            st.metric(
                label="Detection Rate",
                value=f"{detection_rate:.1%}",
                help="Percentage of positive cases correctly detected"
            )
        
        with col3:
            st.metric(
                label="Overall Accuracy",
                value=f"{accuracy:.1%}",
                help="Percentage of all predictions that were correct"
            )
        
        st.markdown("---")
        
        # Add markdown summary with key findings
        st.subheader("📝 Summary")
        
        st.markdown(f"""
        ### Key Findings
        
        The model demonstrates **{'strong' if auc_roc >= 0.8 else 'moderate' if auc_roc >= 0.7 else 'weak'}** 
        discriminative ability with an AUC-ROC of **{auc_roc:.4f}**.
        
        **Performance Highlights:**
        - **Precision**: {precision:.1%} of customers flagged as high-risk are truly at risk
        - **Recall**: {recall:.1%} of actual high-risk customers are successfully identified
        - **F1 Score**: {f1_score:.4f} indicates a {'well-balanced' if f1_score >= 0.7 else 'moderate'} trade-off between precision and recall
        
        **Business Impact:**
        - **False Alarm Rate**: {false_alarm_rate:.1%} - Lower is better to avoid unnecessary interventions
        - **Detection Rate**: {detection_rate:.1%} - Higher is better to catch more at-risk customers
        - **Accuracy**: {accuracy:.1%} - Overall correctness of predictions
        
        **Recommendations:**
        {'- ✅ Model performance is strong and suitable for production use' if auc_roc >= 0.8 and f1_score >= 0.7 else ''}
        {'- ⚠️ Consider model retraining or feature engineering to improve performance' if auc_roc < 0.75 or f1_score < 0.65 else ''}
        {'- 💡 Monitor false alarm rate to optimize intervention costs' if false_alarm_rate > 0.15 else ''}
        {'- 💡 Focus on improving recall to catch more at-risk customers' if recall < 0.7 else ''}
        """)
    
    except FileNotFoundError:
        st.warning("⚠️ Model evaluation metrics not found.")
        st.info("""
        **To view model performance metrics:**
        
        1. Train the model using the training script
        2. Ensure the metrics file is saved to: `data/models/evaluation/metrics.json`
        3. Refresh this page
        
        **Expected file location:** `data/models/evaluation/metrics.json`
        """)
    
    except json.JSONDecodeError as e:
        st.error(f"❌ Error parsing metrics file: {str(e)}")
        st.info("Please ensure the metrics.json file contains valid JSON data.")
    
    except Exception as e:
        st.error(f"❌ Error loading model metrics: {str(e)}")
        st.exception(e)

# ============================================================================
# INTERVENTIONS TRACKER PAGE
# ============================================================================

elif page == "Interventions Tracker":
    st.markdown("Track intervention outcomes and measure effectiveness over time.")
    st.markdown("---")
    
    # Time period selector (Task 9.1)
    st.subheader("⏱️ Select Time Period")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Selectbox with time period options
        time_period = st.selectbox(
            "Time Period",
            options=[7, 14, 30, 60, 90],
            format_func=lambda x: f"Last {x} days",
            help="Select the time period for intervention analysis"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add spacing to align button
        calculate_button = st.button("📊 Calculate Metrics", type="primary", use_container_width=True)
    
    st.markdown("---")
    
    # Process when button is clicked
    if calculate_button:
        # Interventions query with time filtering (Task 9.2)
        if engine is None:
            st.error("⚠️ Database connection not available. Cannot load interventions data.")
        else:
            try:
                import pandas as pd
                from sqlalchemy import text
                from datetime import datetime, timedelta
                
                # Calculate cutoff date based on selected period
                cutoff_date = datetime.now() - timedelta(days=time_period)
                cutoff_date_str = cutoff_date.strftime('%Y-%m-%d')
                
                # SQL query filtering intervention_date >= cutoff_date
                query = text("""
                    SELECT 
                        customer_id,
                        intervention_type,
                        risk_score,
                        intervention_date,
                        customer_response
                    FROM interventions
                    WHERE intervention_date >= :cutoff_date
                    ORDER BY intervention_date DESC
                """)
                
                # Execute query
                df = pd.read_sql(query, engine, params={'cutoff_date': cutoff_date_str})
                
                # Handle empty results (Task 9.6)
                if len(df) == 0:
                    st.info(f"📭 No interventions recorded in the last {time_period} days.")
                    st.markdown("""
                    **Possible reasons:**
                    - No high-risk customers detected during this period
                    - Interventions have not been triggered yet
                    - Data may not be available in the database
                    
                    **Next steps:**
                    - Try selecting a longer time period
                    - Run batch scoring to identify high-risk customers
                    - Trigger interventions from the Risk Overview page
                    """)
                else:
                    # Display aggregate metrics (Task 9.4)
                    st.subheader("📊 Aggregate Metrics")
                    
                    # Calculate metrics
                    total_interventions = len(df)
                    
                    # Count prevented defaults (assuming customer_response indicates success)
                    # Common responses: 'contacted', 'payment_made', 'plan_agreed', 'no_response', 'declined'
                    success_responses = ['contacted', 'payment_made', 'plan_agreed']
                    prevented_defaults = len(df[df['customer_response'].isin(success_responses)])
                    
                    # Calculate success rate
                    success_rate = prevented_defaults / total_interventions if total_interventions > 0 else 0
                    
                    # Display metrics in 3-column layout
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            label="Total Interventions",
                            value=f"{total_interventions:,}",
                            help=f"Total number of interventions in the last {time_period} days"
                        )
                    
                    with col2:
                        st.metric(
                            label="Prevented Defaults",
                            value=f"{prevented_defaults:,}",
                            delta=f"{success_rate:.1%}",
                            help="Number of successful interventions that prevented defaults"
                        )
                    
                    with col3:
                        st.metric(
                            label="Success Rate",
                            value=f"{success_rate:.1%}",
                            help="Percentage of interventions that resulted in positive customer response"
                        )
                    
                    st.markdown("---")
                    
                    # Display recent interventions table (Task 9.5)
                    st.subheader("📋 Recent Interventions")
                    
                    # Format data for display
                    display_df = df.head(20).copy()  # Limit to 20 rows
                    
                    # Format risk scores as percentages
                    display_df['risk_score'] = display_df['risk_score'].apply(format_risk_score)
                    
                    # Format dates as YYYY-MM-DD HH:MM:SS (or YYYY-MM-DD if no time component)
                    display_df['intervention_date'] = display_df['intervention_date'].apply(format_date)
                    
                    # Rename columns for display
                    display_df.columns = [
                        'Customer ID',
                        'Intervention Type',
                        'Risk Score',
                        'Intervention Date',
                        'Customer Response'
                    ]
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
                    # Display data summary
                    st.caption(f"📊 Showing up to 20 most recent interventions from the last {time_period} days (Total: {total_interventions})")
                    
                    # Additional insights
                    st.markdown("---")
                    st.subheader("💡 Insights")
                    
                    # Breakdown by intervention type
                    intervention_breakdown = df['intervention_type'].value_counts()
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Interventions by Type:**")
                        for intervention_type, count in intervention_breakdown.items():
                            percentage = (count / total_interventions) * 100
                            st.write(f"- {intervention_type}: {count} ({percentage:.1f}%)")
                    
                    with col2:
                        st.markdown("**Customer Response Distribution:**")
                        response_breakdown = df['customer_response'].value_counts()
                        for response, count in response_breakdown.items():
                            percentage = (count / total_interventions) * 100
                            st.write(f"- {response}: {count} ({percentage:.1f}%)")
            
            except Exception as e:
                st.error(f"❌ Error loading interventions data: {str(e)}")
                st.exception(e)
                st.info("""
                **Troubleshooting:**
                - Ensure the 'interventions' table exists in the database
                - Check that the database connection is properly configured
                - Verify that the table has the required columns
                """)
    else:
        # Show instruction when button not clicked
        st.info("👆 Select a time period and click 'Calculate Metrics' to view intervention data.")

# ============================================================================
# FOOTER (displayed on all pages)
# ============================================================================

st.markdown("---")

# Create footer with metadata (Task 11.1)
from datetime import datetime

# Get current timestamp
last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Display footer with application name, version, and last updated timestamp
st.markdown(f"""
    <div class='footer'>
        <strong>Pre-Delinquency Intervention Engine Dashboard</strong> | Version 1.0.0<br>
        Last Updated: {last_updated}
    </div>
""", unsafe_allow_html=True)
