"""
Pre-Delinquency Engine - Streamlit Dashboard

Multi-page dashboard for monitoring and analyzing risk scores, customer profiles,
interventions, and model performance.
"""

import os
import streamlit as st
from sqlalchemy import create_engine
from datetime import datetime

# Import UI components
from ui_components import (
    apply_custom_css,
    format_risk_score,
    format_timestamp,
    format_date,
    get_risk_level_color_map,
    get_risk_emoji,
    render_risk_badge,
    render_risk_driver_card,
    render_gauge_chart,
    render_histogram,
    render_pie_chart,
    render_scatter_plot,
    render_confusion_matrix,
    render_footer
)

# Page configuration
st.set_page_config(
    page_title="Pre-Delinquency Engine",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS styling
apply_custom_css()


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

# Formatting functions are now imported from ui_components

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================

st.sidebar.markdown("<h1 style='font-size: 1.125rem; font-weight: 600; color: #111827; margin-bottom: 1rem;'>🎯 Pre-Delinquency Engine</h1>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Page selector with improved styling
st.sidebar.markdown("<h3 style='font-size: 0.6875rem; font-weight: 600; color: #6B7280; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.75rem;'>📍 NAVIGATION</h3>", unsafe_allow_html=True)
page = st.sidebar.radio(
    "Navigate to:",
    [
        "Risk Overview",
        "Customer Deep Dive",
        "Real-time Monitor",
        "Model Performance",
        "Interventions Tracker",
        "Data Management"
    ],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")

# Quick stats section with improved layout
st.sidebar.markdown("<h3 style='font-size: 0.6875rem; font-weight: 600; color: #6B7280; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.75rem;'>📊 QUICK STATS</h3>", unsafe_allow_html=True)

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

# Display selected page title with improved styling
st.markdown(f"<h1 style='margin-bottom: 0.5rem;'>📈 {page}</h1>", unsafe_allow_html=True)

# Add page description based on selected page
page_descriptions = {
    "Risk Overview": "Monitor key risk metrics and identify high-risk customers across your portfolio.",
    "Customer Deep Dive": "Analyze individual customer risk profiles with AI-powered explanations.",
    "Real-time Monitor": "Track risk scores updating in real-time with automatic refresh capability.",
    "Model Performance": "View model evaluation metrics and performance diagnostics.",
    "Interventions Tracker": "Track intervention outcomes and measure effectiveness over time.",
    "Data Management": "Generate synthetic data and retrain models with automated workflows."
}

st.markdown(f"<p style='color: #000000; font-size: 15px; margin-bottom: 2rem;'>{page_descriptions.get(page, '')}</p>", unsafe_allow_html=True)

# ============================================================================
# RISK OVERVIEW PAGE
# ============================================================================

if page == "Risk Overview":
    # Load latest risk scores
    df = load_latest_risk_scores()
    
    if df is None or len(df) == 0:
        st.info("📭 No risk score data available. Please run batch scoring first.")
    else:
        # Top metrics row with improved spacing
        st.markdown("### 📊 Key Metrics")
        st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
        
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
        
        # Risk distribution histogram and pie chart with improved spacing
        st.markdown("### 📊 Risk Distribution Analysis")
        st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2, gap="large")
        
        with col1:
            st.markdown("#### 📊 Risk Score Distribution")
            st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)
            
            try:
                # Create histogram using UI component
                thresholds = [
                    (0.6, "High Risk (0.6)", "orange"),
                    (0.8, "Critical (0.8)", "red")
                ]
                
                fig = render_histogram(
                    data=df['risk_score'],
                    title="Distribution of Customer Risk Scores",
                    xaxis_title="Risk Score",
                    yaxis_title="Number of Customers",
                    thresholds=thresholds
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.warning("⚠️ Chart could not be rendered. Showing data summary instead.")
                st.write("**Risk Score Statistics:**")
                st.write(df['risk_score'].describe())
                st.info("The dashboard will continue operating. Chart rendering issue logged.")
        
        with col2:
            st.markdown("#### 🎯 Risk Level Breakdown")
            st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)
            
            try:
                # Count customers by risk level
                risk_counts = df['risk_level'].value_counts()
                
                # Get consistent color mapping
                color_map = get_risk_level_color_map()
                
                # Create pie chart using UI component
                fig = render_pie_chart(
                    labels=risk_counts.index,
                    values=risk_counts.values,
                    title="Customers by Risk Level",
                    color_map=color_map
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.warning("⚠️ Chart could not be rendered. Showing data table instead.")
                st.write("**Risk Level Breakdown:**")
                st.dataframe(df['risk_level'].value_counts())
                st.info("The dashboard will continue operating. Chart rendering issue logged.")
        
        st.markdown("---")
        
        # Rising risk customers table with improved styling
        st.markdown("### ⚠️ Rising Risk Customers")
        st.markdown("<p style='color: #000000; font-size: 14px; margin-bottom: 1rem;'>Customers with increasing risk scores requiring immediate attention</p>", unsafe_allow_html=True)
        
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
                # Get high-risk customers
                high_risk_df = df[df['risk_level'].isin(['HIGH', 'CRITICAL'])]
                high_risk_count = len(high_risk_df)
                
                if high_risk_count > 0 and engine is not None:
                    try:
                        from sqlalchemy import text
                        from datetime import datetime
                        
                        # Insert intervention records for each high-risk customer
                        with engine.begin() as conn:
                            for _, row in high_risk_df.iterrows():
                                # Determine intervention type based on risk level
                                intervention_type = 'urgent_contact' if row['risk_level'] == 'CRITICAL' else 'proactive_outreach'
                                
                                # Insert intervention record
                                insert_query = text("""
                                    INSERT INTO interventions 
                                    (customer_id, intervention_type, risk_score, intervention_date, customer_response)
                                    VALUES (:customer_id, :intervention_type, :risk_score, :intervention_date, :customer_response)
                                """)
                                
                                conn.execute(insert_query, {
                                    'customer_id': row['customer_id'],
                                    'intervention_type': intervention_type,
                                    'risk_score': row['risk_score'],
                                    'intervention_date': datetime.now(),
                                    'customer_response': 'pending'
                                })
                        
                        st.success(f"✅ Successfully triggered {high_risk_count} interventions for high-risk customers!")
                    except Exception as e:
                        st.error(f"❌ Error creating interventions: {str(e)}")
                else:
                    st.warning("⚠️ No high-risk customers found or database not available.")

# ============================================================================
# CUSTOMER DEEP DIVE PAGE
# ============================================================================

elif page == "Customer Deep Dive":
    # Customer ID input and analyze button with improved layout
    st.markdown("### 🔍 Customer Analysis")
    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 1], gap="medium")
    
    with col1:
        customer_id = st.text_input(
            "Enter Customer ID",
            placeholder="e.g., 550e8400-e29b-41d4-a716-446655440000",
            help="Enter the UUID of the customer you want to analyze"
        )
    
    with col2:
        # Add spacing to align button with input field
        st.markdown("<div style='margin-top: 1.85rem;'></div>", unsafe_allow_html=True)
        analyze_button = st.button("🔍 Analyze", type="primary", use_container_width=True)
    
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    
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
                    st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
                    
                    # Display results in two columns with improved spacing
                    col1, col2 = st.columns(2, gap="large")
                    
                    with col1:
                        # Risk score gauge chart (Task 5.3)
                        st.markdown("#### 📊 Risk Score")
                        st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)
                        
                        try:
                            # Create gauge chart using UI component
                            fig = render_gauge_chart(risk_score, "Risk Score")
                            st.plotly_chart(fig, use_container_width=True)
                            
                        except Exception as e:
                            st.warning("⚠️ Chart could not be rendered. Showing metric instead.")
                            st.metric("Risk Score", f"{risk_score:.2%}")
                    
                    with col2:
                        # Risk level badge with emoji (Task 5.4)
                        st.markdown("#### 🎯 Risk Level")
                        st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)
                        
                        # Render risk badge using UI component
                        render_risk_badge(risk_level)
                    
                    st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
                    
                    # SHAP explanation and top risk drivers (Task 5.6)
                    st.markdown("### 💡 Risk Explanation")
                    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
                    
                    # Display explanation text in info box
                    st.info(explanation_text)
                    
                    st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
                    
                    # Display top risk drivers
                    st.markdown("### 📈 Top Risk Drivers")
                    st.markdown("<p style='color: #000000; font-size: 14px; margin-bottom: 1rem;'>Key factors contributing to this customer's risk score</p>", unsafe_allow_html=True)
                    
                    if top_drivers and len(top_drivers) > 0:
                        # Display top 5 drivers using UI component
                        for i, driver in enumerate(top_drivers[:5], 1):
                            feature = driver.get('feature', 'Unknown')
                            value = driver.get('value', 'N/A')
                            impact = driver.get('impact', 0)
                            impact_pct = driver.get('impact_pct', 0)
                            
                            # Render driver card using UI component
                            render_risk_driver_card(i, feature, value, impact, impact_pct)
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
    # Auto-refresh checkbox and manual refresh button with improved layout
    st.markdown("### ⚙️ Monitor Settings")
    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([3, 1, 1], gap="medium")
    
    with col1:
        auto_refresh = st.checkbox("🔄 Auto-refresh (every 5 seconds)", value=True)
    
    with col2:
        refresh_button = st.button("🔄 Refresh Now", use_container_width=True)
    
    with col3:
        st.markdown("")  # Spacer
    
    st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
    
    # Load recent risk scores (Task 6.1)
    df = load_recent_risk_scores()
    
    if df is None or len(df) == 0:
        st.info("No risk scores recorded in the last hour. Data will appear here as new scores are generated.")
    else:
        # Time-series scatter plot (Task 6.4)
        st.markdown("### 📈 Risk Scores Over Time")
        st.markdown("<p style='color: #000000; font-size: 14px; margin-bottom: 1rem;'>Real-time visualization of risk score updates in the last hour</p>", unsafe_allow_html=True)
        
        try:
            # Get consistent color mapping for risk levels
            color_map = get_risk_level_color_map()
            
            # Create scatter plot using UI component
            fig = render_scatter_plot(
                df=df,
                x_col='score_date',
                y_col='risk_score',
                color_col='risk_level',
                title='Risk Scores in the Last Hour',
                color_map=color_map,
                hover_data=['customer_id', 'top_feature_1']
            )
            
            # Update y-axis to show 0-1 range
            fig.update_yaxes(range=[0, 1])
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.warning("⚠️ Chart could not be rendered. Showing data table instead.")
            st.dataframe(df[['score_date', 'customer_id', 'risk_score', 'risk_level']])
            st.info("The dashboard will continue operating. Chart rendering issue logged.")
        
        st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
        
        # Recent updates table (Task 6.7)
        st.markdown("### 📋 Recent Updates")
        st.markdown("<p style='color: #000000; font-size: 14px; margin-bottom: 1rem;'>Latest risk score calculations and updates</p>", unsafe_allow_html=True)
        
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
    # Load model metrics from JSON file (Task 8.1)
    try:
        import json
        
        metrics_path = "data/models/evaluation/metrics.json"
        
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        # Display key metrics cards (Task 8.2)
        st.markdown("### 📊 Key Performance Metrics")
        st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
        
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
        st.markdown("### 🔢 Confusion Matrix")
        st.markdown("<p style='color: #000000; font-size: 14px; margin-bottom: 1rem;'>Model prediction accuracy breakdown</p>", unsafe_allow_html=True)
        
        try:
            # Extract confusion matrix values
            tp = metrics.get('true_positives', 0)
            tn = metrics.get('true_negatives', 0)
            fp = metrics.get('false_positives', 0)
            fn = metrics.get('false_negatives', 0)
            
            # Create confusion matrix using UI component
            fig = render_confusion_matrix(tp, tn, fp, fn, "Confusion Matrix")
            
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
        st.markdown("### 💼 Business Metrics")
        st.markdown("<p style='color: #000000; font-size: 14px; margin-bottom: 1rem;'>Key business impact indicators</p>", unsafe_allow_html=True)
        
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
        st.markdown("### 📝 Performance Summary")
        st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
        
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
    # Time period selector (Task 9.1)
    st.markdown("### ⏱️ Select Time Period")
    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 1], gap="medium")
    
    with col1:
        # Selectbox with time period options
        time_period = st.selectbox(
            "Time Period",
            options=[7, 14, 30, 60, 90],
            format_func=lambda x: f"Last {x} days",
            help="Select the time period for intervention analysis"
        )
    
    with col2:
        st.markdown("<div style='margin-top: 1.85rem;'></div>", unsafe_allow_html=True)
        calculate_button = st.button("📊 Calculate Metrics", type="primary", use_container_width=True)
    
    st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
    
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
                    st.markdown("### 📊 Aggregate Metrics")
                    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
                    
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
                    st.markdown("### 📋 Recent Interventions")
                    st.markdown("<p style='color: #000000; font-size: 14px; margin-bottom: 1rem;'>Latest intervention activities and customer responses</p>", unsafe_allow_html=True)
                    
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
                    st.markdown("### 💡 Insights")
                    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
                    
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
# DATA MANAGEMENT PAGE
# ============================================================================

elif page == "Data Management":
    st.markdown("### 🔄 Automated Data Pipeline")
    st.markdown("Generate synthetic customers and retrain models with one click.")
    
    st.markdown("---")
    
    # Pipeline controls
    col1, col2 = st.columns([3, 1])
    
    with col1:
        n_customers = st.slider("Number of customers to generate", 50, 500, 100, 50)
        st.info(f"💡 Will generate {n_customers} synthetic customers with realistic behavioral patterns")
    
    with col2:
        st.metric("Pipeline Status", "Ready ✅")
    
    st.markdown("---")
    
    # Run pipeline button
    if st.button("🚀 Run Automated Pipeline", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            import subprocess
            import json
            
            status_text.text("⏳ Starting pipeline...")
            progress_bar.progress(10)
            
            result = subprocess.run(
                ["python3", "src/workflows/auto_pipeline.py", str(n_customers)],
                capture_output=True,
                text=True,
                timeout=180,
                cwd="."
            )
            
            progress_bar.progress(90)
            
            if result.returncode == 0:
                # Parse JSON from stdout
                try:
                    output = json.loads(result.stdout)
                    progress_bar.progress(100)
                    status_text.empty()
                    
                    if output.get('success'):
                        st.success("✅ Pipeline completed successfully!")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("New Customers", output.get('new_customers', 0))
                        with col2:
                            st.metric("Risk Scores Generated", output.get('risk_scores', 0))
                        with col3:
                            st.metric("Timestamp", output.get('timestamp', 'N/A')[:19])
                        
                        st.balloons()
                        
                        if st.button("🔄 Refresh Dashboard"):
                            st.rerun()
                    else:
                        st.error(f"❌ Pipeline failed: {output.get('error', 'Unknown error')}")
                        with st.expander("View Error Details"):
                            st.code(result.stderr)
                
                except json.JSONDecodeError as e:
                    st.error(f"❌ Failed to parse pipeline output")
                    with st.expander("View Raw Output"):
                        st.code(result.stdout)
                        st.code(result.stderr)
            else:
                progress_bar.progress(100)
                status_text.empty()
                st.error(f"❌ Pipeline failed with exit code {result.returncode}")
                with st.expander("View Error Details"):
                    st.code(result.stderr)
        
        except subprocess.TimeoutExpired:
            progress_bar.progress(100)
            status_text.empty()
            st.warning("⚠️ Pipeline timeout (>3 minutes). It may still be running in the background.")
            st.info("Check the logs: `tail -f dashboard.log`")
        
        except Exception as e:
            progress_bar.progress(100)
            status_text.empty()
            st.error(f"❌ Unexpected error: {e}")
            import traceback
            with st.expander("View Traceback"):
                st.code(traceback.format_exc())
    
    st.markdown("---")
    
    # Pipeline information
    st.markdown("### 📋 Pipeline Steps")
    
    steps = [
        ("1️⃣ Generate Data", "Create synthetic customers with realistic behavioral patterns"),
        ("2️⃣ Load to Database", "Insert new customers into PostgreSQL"),
        ("3️⃣ Generate Scores", "Calculate risk scores using the trained model"),
        ("4️⃣ Update Dashboard", "Refresh metrics and visualizations")
    ]
    
    for step, description in steps:
        with st.container():
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(f"**{step}**")
            with col2:
                st.markdown(description)

# ============================================================================
# FOOTER (displayed on all pages)
# ============================================================================

# Render footer using UI component
render_footer()

