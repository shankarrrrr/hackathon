"""
Simple UI Components for Banking Dashboard
Clean, professional, functional design
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime


def apply_custom_css():
    """Apply simple, clean CSS for professional banking dashboard."""
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        * {
            font-family: 'Inter', sans-serif;
        }
        
        .main {
            padding: 1.5rem 2rem;
            background-color: #F5F5F5;
        }
        
        .stApp {
            background-color: #F5F5F5;
        }
        
        /* Page Title */
        h1 {
            font-size: 1.25rem;
            font-weight: 600;
            color: #000000 !important;
            margin-bottom: 1.5rem;
        }
        
        /* Section Headers */
        h2, h3 {
            font-size: 0.75rem;
            font-weight: 500;
            color: #000000 !important;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        /* All markdown text */
        .stMarkdown, .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
            color: #000000 !important;
        }
        
        /* Paragraph text */
        p {
            color: #000000 !important;
        }
        
        /* Metric Cards */
        div[data-testid="stMetric"] {
            background: #FFFFFF;
            padding: 1.25rem;
            border-radius: 8px;
            border: 1px solid #E5E7EB;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        }
        
        div[data-testid="stMetric"] label {
            font-size: 0.6875rem;
            font-weight: 500;
            color: #9CA3AF;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            font-size: 1.75rem;
            font-weight: 700;
            color: #111827;
        }
        
        div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
            font-size: 0.75rem;
            font-weight: 500;
        }
        
        /* Buttons */
        .stButton > button {
            border-radius: 6px;
            font-weight: 500;
            font-size: 0.875rem;
            padding: 0.5rem 1rem;
            border: 1px solid #D1D5DB;
            background-color: #FFFFFF !important;
            color: #374151 !important;
        }
        
        .stButton > button[kind="primary"] {
            background: #3B82F6 !important;
            color: white !important;
            border: none;
        }
        
        /* Sidebar */
        section[data-testid="stSidebar"] {
            background: #FFFFFF;
            border-right: 1px solid #E5E7EB;
            padding: 1.5rem 1rem;
        }
        
        section[data-testid="stSidebar"] h1 {
            font-size: 1.125rem !important;
            font-weight: 600 !important;
            color: #111827 !important;
            margin-bottom: 1rem !important;
        }
        
        section[data-testid="stSidebar"] h3 {
            font-size: 0.6875rem !important;
            font-weight: 600 !important;
            color: #6B7280 !important;
            margin-top: 1.5rem !important;
            margin-bottom: 0.75rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.1em !important;
        }
        
        section[data-testid="stSidebar"] .stMetric label {
            font-size: 0.6875rem !important;
            font-weight: 500 !important;
            color: #6B7280 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
        }
        
        section[data-testid="stSidebar"] .stMetric [data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
            font-weight: 700 !important;
            color: #111827 !important;
        }
        
        /* Tables */
        .dataframe {
            font-size: 0.8125rem;
            border: 1px solid #E5E7EB;
            border-radius: 8px;
        }
        
        .dataframe thead th {
            background-color: #F9FAFB !important;
            color: #6B7280 !important;
            font-weight: 600 !important;
            font-size: 0.6875rem !important;
            text-transform: uppercase;
            padding: 0.75rem 1rem !important;
        }
        
        .dataframe tbody td {
            padding: 0.75rem 1rem !important;
            color: #374151;
            border-bottom: 1px solid #F3F4F6;
        }
        
        /* Inputs */
        .stTextInput input, .stSelectbox select {
            border-radius: 6px;
            border: 1px solid #D1D5DB;
            padding: 0.5rem 0.75rem;
            font-size: 0.875rem;
            background-color: #FFFFFF !important;
            color: #000000 !important;
        }
        
        /* Text input specific - force black text */
        .stTextInput input {
            color: #000000 !important;
        }
        
        .stTextInput input::placeholder {
            color: #9CA3AF !important;
        }
        
        .stTextInput input:focus {
            color: #000000 !important;
            border-color: #3B82F6 !important;
            outline: none !important;
        }
        
        .stTextInput label, .stSelectbox label {
            font-size: 0.75rem;
            font-weight: 500;
            color: #000000 !important;
        }
        
        /* Selectbox specific styling */
        .stSelectbox > div > div {
            background-color: #FFFFFF !important;
            border: 1px solid #D1D5DB !important;
            border-radius: 6px;
        }
        
        .stSelectbox div[data-baseweb="select"] > div {
            background-color: #FFFFFF !important;
            color: #374151 !important;
        }
        
        .stSelectbox div[data-baseweb="select"] span {
            color: #374151 !important;
        }
        
        .stSelectbox [data-baseweb="popover"] {
            background-color: #FFFFFF !important;
        }
        
        .stSelectbox [role="option"] {
            background-color: #FFFFFF !important;
            color: #374151 !important;
        }
        
        /* Dropdown cursor fix */
        div[data-baseweb="select"] > div,
        div[data-baseweb="select"] * {
            cursor: pointer !important;
        }
        
        hr {
            margin: 1.5rem 0;
            border-color: #E5E7EB;
        }
        
        /* Radio button navigation styling */
        section[data-testid="stSidebar"] .stRadio > div {
            gap: 0.5rem;
        }
        
        section[data-testid="stSidebar"] .stRadio > div > label {
            background-color: transparent;
            padding: 0.625rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
            border: 1px solid transparent;
            font-size: 0.875rem;
            font-weight: 500;
            color: #6B7280;
        }
        
        section[data-testid="stSidebar"] .stRadio > div > label:hover {
            background-color: #F3F4F6;
            color: #111827;
        }
        
        section[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {
            background-color: #EFF6FF;
            color: #1E40AF;
            border: 1px solid #BFDBFE;
            font-weight: 600;
        }
        
        /* Hide radio button circles */
        section[data-testid="stSidebar"] .stRadio > div > label > div:first-child {
            display: none;
        }
        
        /* Adjust text positioning */
        section[data-testid="stSidebar"] .stRadio > div > label > div:last-child {
            padding-left: 0;
        }
        </style>
    """, unsafe_allow_html=True)


# Helper functions
def format_risk_score(risk_score):
    """Format risk score as percentage."""
    return f"{risk_score:.2%}"


def format_timestamp(timestamp):
    """Format timestamp."""
    if hasattr(timestamp, 'strftime'):
        return timestamp.strftime('%Y-%m-%d %H:%M:%S')
    return str(timestamp)


def format_date(date_obj):
    """Format date."""
    if hasattr(date_obj, 'strftime'):
        if hasattr(date_obj, 'hour'):
            return date_obj.strftime('%Y-%m-%d %H:%M:%S')
        return date_obj.strftime('%Y-%m-%d')
    return str(date_obj)


def get_risk_level_color_map():
    """Get color mapping for risk levels."""
    return {
        'LOW': '#10B981',
        'MEDIUM': '#F59E0B',
        'HIGH': '#EF4444',
        'CRITICAL': '#DC2626'
    }


def get_risk_emoji(risk_level):
    """Get emoji for risk level."""
    emoji_map = {
        'LOW': '🟢',
        'MEDIUM': '🟡',
        'HIGH': '🟠',
        'CRITICAL': '🔴'
    }
    return emoji_map.get(risk_level, '⚪')


# Chart components
def render_gauge_chart(risk_score, title="Risk Score"):
    """Render gauge chart."""
    risk_score_100 = risk_score * 100
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score_100,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 14, 'color': '#6B7280'}},
        number={'font': {'size': 40, 'color': '#111827'}},
        gauge={
            'axis': {'range': [0, 100], 'tickfont': {'size': 10, 'color': '#9CA3AF'}},
            'bar': {'color': "#3B82F6"},
            'bgcolor': "#F3F4F6",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 40], 'color': '#D1FAE5'},
                {'range': [40, 60], 'color': '#FEF3C7'},
                {'range': [60, 80], 'color': '#FEE2E2'},
                {'range': [80, 100], 'color': '#FECACA'}
            ]
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='#FFFFFF',
        font={'family': 'Inter'}
    )
    
    return fig


def render_histogram(data, title, xaxis_title, yaxis_title, thresholds=None):
    """Render histogram."""
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=data,
        nbinsx=30,
        marker_color='#3B82F6',
        opacity=0.8
    ))
    
    if thresholds:
        for value, label, color in thresholds:
            fig.add_vline(x=value, line_dash="dash", line_color=color, line_width=2)
    
    fig.update_layout(
        title={'text': title, 'font': {'size': 14, 'color': '#374151'}, 'x': 0},
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        showlegend=False,
        height=320,
        paper_bgcolor='#FFFFFF',
        plot_bgcolor='#F9FAFB',
        font={'family': 'Inter', 'size': 11, 'color': '#6B7280'},
        margin=dict(l=50, r=30, t=50, b=40)
    )
    
    fig.update_xaxes(showgrid=True, gridcolor='#E5E7EB')
    fig.update_yaxes(showgrid=True, gridcolor='#E5E7EB')
    
    return fig


def render_pie_chart(labels, values, title, color_map=None, customdata=None, hovertemplate=None):
    """
    Render pie chart with optional click event support and custom hover tooltips.
    
    Args:
        labels: List of labels for pie slices
        values: List of values for pie slices
        title: Chart title
        color_map: Optional dict mapping labels to colors
        customdata: Optional list of custom data for each slice (for tooltips)
        hovertemplate: Optional custom hover template string
    
    Returns:
        Plotly figure object
    """
    colors = [color_map.get(label, '#6B7280') for label in labels] if color_map else None
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        hole=0.4,
        textfont={'size': 12, 'color': '#000000'},
        customdata=customdata,
        hovertemplate=hovertemplate
    )])
    
    fig.update_layout(
        title={'text': title, 'font': {'size': 14, 'color': '#374151'}, 'x': 0},
        height=320,
        paper_bgcolor='#FFFFFF',
        font={'family': 'Inter', 'size': 11},
        showlegend=True,
        legend=dict(font={'size': 11, 'color': '#6B7280'}),
        margin=dict(l=30, r=30, t=50, b=30)
    )
    
    return fig


def render_scatter_plot(df, x_col, y_col, color_col, title, color_map=None, hover_data=None):
    """Render scatter plot."""
    fig = px.scatter(
        df, x=x_col, y=y_col, color=color_col,
        color_discrete_map=color_map, hover_data=hover_data
    )
    
    fig.update_layout(
        title={'text': title, 'font': {'size': 14, 'color': '#374151'}, 'x': 0},
        height=320,
        paper_bgcolor='#FFFFFF',
        plot_bgcolor='#F9FAFB',
        font={'family': 'Inter', 'size': 11, 'color': '#6B7280'},
        margin=dict(l=50, r=30, t=50, b=40)
    )
    
    fig.update_xaxes(showgrid=True, gridcolor='#E5E7EB')
    fig.update_yaxes(showgrid=True, gridcolor='#E5E7EB')
    
    return fig


def render_confusion_matrix(tp, tn, fp, fn, title="Confusion Matrix"):
    """Render confusion matrix."""
    import numpy as np
    
    confusion_matrix = np.array([[tn, fp], [fn, tp]])
    
    fig = go.Figure(data=go.Heatmap(
        z=confusion_matrix,
        x=['Predicted Negative', 'Predicted Positive'],
        y=['Actual Negative', 'Actual Positive'],
        text=confusion_matrix,
        texttemplate='<b>%{text}</b>',
        textfont={"size": 20, "color": "#000000"},
        colorscale=[[0, '#DBEAFE'], [1, '#3B82F6']],
        showscale=False
    ))
    
    fig.update_layout(
        title={'text': title, 'font': {'size': 14, 'color': '#374151'}, 'x': 0},
        height=350,
        paper_bgcolor='#FFFFFF',
        font={'family': 'Inter', 'size': 11},
        margin=dict(l=70, r=70, t=50, b=50)
    )
    
    return fig


def render_risk_badge(risk_level):
    """Render risk badge."""
    colors = {
        'LOW': ('background: #D1FAE5; color: #065F46; border: 1px solid #A7F3D0;'),
        'MEDIUM': ('background: #FEF3C7; color: #92400E; border: 1px solid #FDE68A;'),
        'HIGH': ('background: #FEE2E2; color: #991B1B; border: 1px solid #FECACA;'),
        'CRITICAL': ('background: #FEE2E2; color: #7F1D1D; border: 1px solid #FCA5A5;')
    }
    
    style = colors.get(risk_level, colors['LOW'])
    
    st.markdown(f"""
        <div style='text-align: center; padding: 2rem;'>
            <div style='{style} padding: 0.5rem 1rem; border-radius: 6px; 
                        display: inline-block; font-weight: 600; font-size: 0.875rem;'>
                {risk_level}
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_risk_driver_card(rank, feature, value, impact, impact_pct):
    """Render risk driver card."""
    impact_sign = '+' if impact >= 0 else ''
    impact_str = f"{impact_sign}{impact_pct:.1f}%"
    impact_color = '#EF4444' if impact >= 0 else '#10B981'
    
    st.markdown(f"""
        <div style='background: #FFFFFF; padding: 1rem; border-radius: 6px; 
                    margin-bottom: 0.75rem; border: 1px solid #E5E7EB;'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div style='display: flex; gap: 1rem; flex: 1;'>
                    <div style='color: #9CA3AF; font-weight: 600; font-size: 0.875rem;'>{rank}</div>
                    <div style='flex: 1;'>
                        <div style='font-weight: 600; color: #111827; font-size: 0.875rem; margin-bottom: 0.25rem;'>
                            {feature}
                        </div>
                        <div style='color: #9CA3AF; font-size: 0.75rem;'>{value}</div>
                    </div>
                </div>
                <div style='font-weight: 700; color: {impact_color}; font-size: 1.25rem;'>
                    {impact_str}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_footer():
    """Render footer."""
    last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    st.markdown("---")
    st.markdown(f"""
        <div style='text-align: center; padding: 1.5rem; color: #9CA3AF; font-size: 0.75rem;'>
            <div style='font-weight: 600; margin-bottom: 0.5rem;'>Pre-Delinquency Engine</div>
            <div>Last Updated: {last_updated}</div>
        </div>
    """, unsafe_allow_html=True)


def render_critical_action_panel(df, engine=None):
    """
    Render critical action panel with high-risk customers and action buttons.
    
    Args:
        df: DataFrame from load_latest_risk_scores() filtered for HIGH/CRITICAL
        engine: SQLAlchemy database engine (optional, for SLA tracking)
    
    Requirements: 1.1, 1.3, 1.6, 10.3
    """
    # Filter for HIGH and CRITICAL risk levels
    critical_df = df[df['risk_level'].isin(['HIGH', 'CRITICAL'])]
    critical_count = len(critical_df)
    
    # Display panel header with count
    st.markdown(f"""
        <div style='background: #FEF2F2; padding: 1.5rem; border-radius: 8px; 
                    border-left: 4px solid #DC2626; margin-bottom: 1.5rem;'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <div style='font-size: 0.75rem; font-weight: 600; color: #991B1B; 
                                text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;'>
                        🚨 Critical Action Required
                    </div>
                    <div style='font-size: 1.5rem; font-weight: 700; color: #7F1D1D;'>
                        {critical_count} Customers Requiring Immediate Attention
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Create three action buttons in horizontal layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        view_customers = st.button(
            "👁️ View Critical Customers",
            key="view_critical_customers",
            use_container_width=True
        )
    
    with col2:
        trigger_interventions = st.button(
            "⚡ Trigger Interventions",
            key="trigger_interventions",
            use_container_width=True
        )
    
    with col3:
        assign_to_agent = st.button(
            "👤 Assign to Agent",
            key="assign_to_agent",
            use_container_width=True
        )
    
    # Handle button actions
    if view_customers:
        st.session_state['show_critical_customers'] = True
    
    if trigger_interventions:
        st.session_state['trigger_interventions_action'] = True
    
    if assign_to_agent:
        st.session_state['show_agent_assignment'] = True
    
    # Display critical customers table if requested
    if st.session_state.get('show_critical_customers', False):
        with st.expander("Critical Customers List", expanded=True):
            if len(critical_df) > 0:
                # Import calculate_time_since_last_action function
                # Note: This function should be available in the app.py context
                # For now, we'll calculate it inline if engine is available
                
                # Format the dataframe for display
                display_df = critical_df[['customer_id', 'risk_score', 'risk_level', 'top_feature_1']].copy()
                display_df['risk_score'] = display_df['risk_score'].apply(lambda x: f"{x:.2%}")
                
                # Add "Time Since Last Action" column if engine is available
                if engine is not None:
                    from sqlalchemy import text
                    from datetime import datetime
                    
                    time_since_action_list = []
                    escalation_list = []
                    
                    for _, row in critical_df.iterrows():
                        customer_id = row['customer_id']
                        risk_level = row['risk_level']
                        
                        try:
                            # Query interventions table for most recent intervention_date
                            query = text("""
                                SELECT MAX(intervention_date) as last_intervention_date
                                FROM interventions
                                WHERE customer_id = :customer_id
                            """)
                            
                            with engine.connect() as conn:
                                query_result = conn.execute(query, {'customer_id': customer_id}).fetchone()
                                
                                if query_result and query_result[0] is not None:
                                    last_intervention_date = query_result[0]
                                    
                                    # Calculate hours since last action
                                    current_time = datetime.now()
                                    
                                    # Handle timezone-aware datetime
                                    if last_intervention_date.tzinfo is not None:
                                        import pytz
                                        current_time = current_time.replace(tzinfo=pytz.UTC)
                                    
                                    time_diff = current_time - last_intervention_date
                                    hours_since_last_action = time_diff.total_seconds() / 3600
                                    
                                    # Format time as "X days Y hours"
                                    days = int(hours_since_last_action // 24)
                                    hours = int(hours_since_last_action % 24)
                                    
                                    if days > 0:
                                        formatted_time = f"{days} days {hours} hours"
                                    else:
                                        formatted_time = f"{hours} hours"
                                    
                                    # Determine if escalation is required
                                    escalation_required = False
                                    if risk_level == 'CRITICAL' and hours_since_last_action > 48:
                                        escalation_required = True
                                    elif risk_level == 'HIGH' and hours_since_last_action > 72:
                                        escalation_required = True
                                    
                                    # Add escalation alert icon if required
                                    if escalation_required:
                                        formatted_time = f"🚨 {formatted_time}"
                                    
                                    time_since_action_list.append(formatted_time)
                                    escalation_list.append(escalation_required)
                                else:
                                    time_since_action_list.append("No previous action")
                                    escalation_list.append(False)
                        
                        except Exception as e:
                            time_since_action_list.append("Error")
                            escalation_list.append(False)
                    
                    # Add the time since last action column
                    display_df['Time Since Last Action'] = time_since_action_list
                    display_df.columns = ['Customer ID', 'Risk Score', 'Risk Level', 'Primary Risk Driver', 'Time Since Last Action']
                else:
                    display_df.columns = ['Customer ID', 'Risk Score', 'Risk Level', 'Primary Risk Driver']
                
                # Apply color coding for escalation required rows
                # Use st.dataframe with styling
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # Add close button
                if st.button("Close", key="close_critical_customers"):
                    st.session_state['show_critical_customers'] = False
                    st.rerun()
            else:
                st.info("No critical customers found.")
    
    # Display agent assignment form if requested
    if st.session_state.get('show_agent_assignment', False):
        with st.expander("Assign Customers to Agent", expanded=True):
            if len(critical_df) > 0:
                st.markdown("### 👤 Agent Assignment")
                st.markdown("<p style='color: #6B7280; font-size: 14px; margin-bottom: 1rem;'>Select an agent and customers to assign</p>", unsafe_allow_html=True)
                
                # Agent selection dropdown
                agent_list = [
                    "Agent 1 - John Smith",
                    "Agent 2 - Sarah Johnson",
                    "Agent 3 - Michael Brown",
                    "Agent 4 - Emily Davis",
                    "Agent 5 - David Wilson"
                ]
                
                selected_agent = st.selectbox(
                    "Select Agent",
                    options=agent_list,
                    help="Choose an agent to assign the selected customers"
                )
                
                st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
                
                # Customer selection checkboxes
                st.markdown("**Select Customers to Assign:**")
                
                selected_customers = []
                
                for idx, row in critical_df.iterrows():
                    customer_id = row['customer_id']
                    risk_level = row['risk_level']
                    risk_score = row['risk_score']
                    
                    # Create checkbox for each customer
                    checkbox_label = f"{customer_id[:8]}... - {risk_level} ({risk_score:.2%})"
                    
                    if st.checkbox(checkbox_label, key=f"assign_customer_{customer_id}"):
                        selected_customers.append(customer_id)
                
                st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
                
                # Assignment button
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    if st.button("✅ Confirm Assignment", key="confirm_assignment", type="primary", use_container_width=True):
                        if len(selected_customers) > 0:
                            # Store assignment in session state (placeholder implementation)
                            if 'agent_assignments' not in st.session_state:
                                st.session_state['agent_assignments'] = {}
                            
                            for customer_id in selected_customers:
                                st.session_state['agent_assignments'][customer_id] = selected_agent
                            
                            # Display confirmation message
                            st.success(f"✅ Successfully assigned {len(selected_customers)} customer(s) to {selected_agent}")
                            
                            # Clear the form
                            st.session_state['show_agent_assignment'] = False
                            st.rerun()
                        else:
                            st.warning("⚠️ Please select at least one customer to assign.")
                
                with col2:
                    if st.button("❌ Cancel", key="cancel_assignment", use_container_width=True):
                        st.session_state['show_agent_assignment'] = False
                        st.rerun()
            else:
                st.info("No critical customers available for assignment.")


def render_rising_risk_panel_enhanced(df):
    """
    Render enhanced rising risk panel with early warning signals.
    
    Args:
        df: DataFrame from load_rising_risk_customers() with columns:
            - customer_id: str
            - risk_score: float
            - risk_level: str
            - top_feature_1: str
            - risk_change: float
    
    Requirements: 4.1, 4.3, 4.4, 4.5
    """
    if df is None or len(df) == 0:
        st.info("📭 No rising risk customers detected at this time.")
        return
    
    # Display panel header
    st.markdown("""
        <div style='font-size: 1.25rem; font-weight: 700; color: #1F2937; margin-bottom: 1rem;'>
            ⚠️ Rising Risk Customers
        </div>
        <p style='color: #6B7280; font-size: 14px; margin-bottom: 1.5rem;'>
            Early warning signals for customers with rapidly increasing risk
        </p>
    """, unsafe_allow_html=True)
    
    # Helper function to get early warning signal
    def get_early_warning_signal(feature_name):
        """
        Determine early warning signal based on top_feature_1 keywords.
        
        Returns:
            tuple: (emoji, label) for the warning signal
        """
        if feature_name is None:
            return ("", "")
        
        feature_lower = str(feature_name).lower()
        
        if "payment" in feature_lower:
            return ("🔴", "Missed Payment")
        elif "utilization" in feature_lower:
            return ("📈", "Utilization Spike")
        elif "bureau" in feature_lower or "credit" in feature_lower:
            return ("⚠️", "Bureau Downgrade")
        else:
            return ("", "")
    
    # Display each rising risk customer
    for idx, row in df.iterrows():
        customer_id = row['customer_id']
        risk_score = row['risk_score']
        risk_level = row['risk_level']
        top_feature = row.get('top_feature_1', 'Unknown')
        risk_change = row.get('risk_change', 0)
        
        # Determine if risk acceleration badge should be shown
        is_accelerating = risk_change > 0.1
        
        # Get early warning signal
        signal_emoji, signal_label = get_early_warning_signal(top_feature)
        
        # Get risk level color
        risk_color = "#DC2626" if risk_level == "CRITICAL" else "#F59E0B"
        
        # Build the card HTML
        acceleration_badge = ""
        if is_accelerating:
            acceleration_badge = """
                <span style='background: #FEE2E2; color: #991B1B; padding: 0.25rem 0.5rem; 
                             border-radius: 4px; font-size: 0.75rem; font-weight: 600; 
                             margin-left: 0.5rem;'>
                    ⚡ RAPID ACCELERATION
                </span>
            """
        
        warning_signal = ""
        if signal_emoji and signal_label:
            warning_signal = f"""
                <div style='display: flex; align-items: center; gap: 0.5rem; margin-top: 0.5rem;'>
                    <span style='font-size: 1.25rem;'>{signal_emoji}</span>
                    <span style='color: #DC2626; font-weight: 600; font-size: 0.875rem;'>
                        {signal_label}
                    </span>
                </div>
            """
        
        # Format risk change with sign
        risk_change_str = f"+{risk_change:.3f}" if risk_change >= 0 else f"{risk_change:.3f}"
        risk_change_color = "#DC2626" if risk_change > 0.1 else "#F59E0B"
        
        st.markdown(f"""
            <div style='background: white; padding: 1rem; border-radius: 8px; 
                        border: 1px solid #E5E7EB; margin-bottom: 1rem;
                        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);'>
                <div style='display: flex; justify-content: space-between; align-items: start;'>
                    <div style='flex: 1;'>
                        <div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
                            <span style='font-weight: 600; color: #1F2937; font-size: 0.875rem;'>
                                Customer: {customer_id[:8]}...
                            </span>
                            <span style='background: {risk_color}; color: white; 
                                         padding: 0.125rem 0.5rem; border-radius: 4px; 
                                         font-size: 0.75rem; font-weight: 600; margin-left: 0.5rem;'>
                                {risk_level}
                            </span>
                            {acceleration_badge}
                        </div>
                        <div style='color: #6B7280; font-size: 0.875rem; margin-bottom: 0.25rem;'>
                            Risk Score: <span style='font-weight: 600; color: #1F2937;'>{risk_score:.2%}</span>
                        </div>
                        <div style='color: #6B7280; font-size: 0.875rem;'>
                            Primary Driver: <span style='font-weight: 600; color: #1F2937;'>{top_feature}</span>
                        </div>
                        {warning_signal}
                    </div>
                    <div style='text-align: right;'>
                        <div style='font-size: 0.75rem; color: #6B7280; margin-bottom: 0.25rem;'>
                            Risk Change
                        </div>
                        <div style='font-size: 1.25rem; font-weight: 700; color: {risk_change_color};'>
                            {risk_change_str}
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Display summary statistics
    total_customers = len(df)
    accelerating_count = len(df[df['risk_change'] > 0.1])
    avg_risk_change = df['risk_change'].mean()
    
    st.markdown(f"""
        <div style='background: #F9FAFB; padding: 1rem; border-radius: 8px; 
                    margin-top: 1rem; border: 1px solid #E5E7EB;'>
            <div style='display: flex; justify-content: space-around; text-align: center;'>
                <div>
                    <div style='font-size: 0.75rem; color: #6B7280; margin-bottom: 0.25rem;'>
                        Total Rising Risk
                    </div>
                    <div style='font-size: 1.5rem; font-weight: 700; color: #1F2937;'>
                        {total_customers}
                    </div>
                </div>
                <div>
                    <div style='font-size: 0.75rem; color: #6B7280; margin-bottom: 0.25rem;'>
                        Rapid Acceleration
                    </div>
                    <div style='font-size: 1.5rem; font-weight: 700; color: #DC2626;'>
                        {accelerating_count}
                    </div>
                </div>
                <div>
                    <div style='font-size: 0.75rem; color: #6B7280; margin-bottom: 0.25rem;'>
                        Avg Risk Change
                    </div>
                    <div style='font-size: 1.5rem; font-weight: 700; color: #F59E0B;'>
                        +{avg_risk_change:.3f}
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_risk_driver_explainability(drivers_df):
    """
    Render risk driver explainability panel showing why portfolio risk is increasing.
    
    Args:
        drivers_df: DataFrame from calculate_portfolio_risk_drivers() with columns:
            - driver_name: str (feature name)
            - contribution_pct: float (percentage contribution)
            - customer_count: int (number of customers affected)
    
    Requirements: 5.1, 5.2, 5.3
    """
    # Handle empty or None DataFrame
    if drivers_df is None or len(drivers_df) == 0:
        st.info("📭 No risk driver data available at this time.")
        return
    
    # Display panel header
    st.markdown("""
        <div style='font-size: 1.25rem; font-weight: 700; color: #1F2937; margin-bottom: 1rem;'>
            🔍 Why is risk increasing?
        </div>
        <p style='color: #6B7280; font-size: 14px; margin-bottom: 1.5rem;'>
            Top risk drivers contributing to portfolio risk increase
        </p>
    """, unsafe_allow_html=True)
    
    # Helper function to determine color based on contribution level
    def get_contribution_color(contribution_pct):
        """
        Determine color based on contribution percentage.
        
        Args:
            contribution_pct: float percentage value
            
        Returns:
            str: hex color code (red for high, yellow for medium, gray for low)
        """
        if contribution_pct >= 25:
            return "#DC2626"  # Red for high impact
        elif contribution_pct >= 15:
            return "#F59E0B"  # Yellow/Orange for medium impact
        else:
            return "#6B7280"  # Gray for lower impact
    
    # Render each risk driver
    for idx, row in drivers_df.iterrows():
        driver_name = row['driver_name']
        contribution_pct = row['contribution_pct']
        customer_count = row.get('customer_count', 0)
        
        # Determine color based on impact level
        color = get_contribution_color(contribution_pct)
        
        # Format contribution with positive indicator and arrow
        contribution_str = f"+{contribution_pct:.1f}%"
        
        # Build the driver card HTML
        st.markdown(f"""
            <div style='background: white; padding: 1rem; border-radius: 8px; 
                        border: 1px solid #E5E7EB; margin-bottom: 0.75rem;
                        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div style='flex: 1;'>
                        <div style='font-weight: 600; color: #1F2937; font-size: 0.9375rem; 
                                    margin-bottom: 0.25rem;'>
                            {driver_name}
                        </div>
                        <div style='color: #6B7280; font-size: 0.8125rem;'>
                            Affecting {customer_count} customer{'s' if customer_count != 1 else ''}
                        </div>
                    </div>
                    <div style='text-align: right; display: flex; align-items: center; gap: 0.5rem;'>
                        <div style='font-size: 1.5rem; font-weight: 700; color: {color};'>
                            {contribution_str}
                        </div>
                        <div style='font-size: 1.5rem; color: {color};'>
                            ↑
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Display summary information
    total_drivers = len(drivers_df)
    total_contribution = drivers_df['contribution_pct'].sum()
    total_customers_affected = drivers_df['customer_count'].sum()
    
    st.markdown(f"""
        <div style='background: #F9FAFB; padding: 1rem; border-radius: 8px; 
                    margin-top: 1rem; border: 1px solid #E5E7EB;'>
            <div style='display: flex; justify-content: space-around; text-align: center;'>
                <div>
                    <div style='font-size: 0.75rem; color: #6B7280; margin-bottom: 0.25rem;'>
                        Top Drivers
                    </div>
                    <div style='font-size: 1.5rem; font-weight: 700; color: #1F2937;'>
                        {total_drivers}
                    </div>
                </div>
                <div>
                    <div style='font-size: 0.75rem; color: #6B7280; margin-bottom: 0.25rem;'>
                        Total Contribution
                    </div>
                    <div style='font-size: 1.5rem; font-weight: 700; color: #DC2626;'>
                        +{total_contribution:.1f}%
                    </div>
                </div>
                <div>
                    <div style='font-size: 0.75rem; color: #6B7280; margin-bottom: 0.25rem;'>
                        Customers Affected
                    </div>
                    <div style='font-size: 1.5rem; font-weight: 700; color: #1F2937;'>
                        {total_customers_affected}
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def suggest_interventions(risk_level, top_drivers):
    """
    Suggest intervention types based on risk level and drivers.
    
    Args:
        risk_level: Customer's risk level (LOW, MEDIUM, HIGH, CRITICAL)
        top_drivers: List of dicts with 'feature' and 'impact' keys
        
    Returns:
        dict with keys: intervention_type, rationale, priority
    
    Requirements: 6.2, 6.3, 6.4
    """
    # Determine intervention type and priority based on risk level
    if risk_level == 'CRITICAL':
        intervention_type = 'urgent_contact'
        priority = 'IMMEDIATE'
    elif risk_level == 'HIGH':
        intervention_type = 'proactive_outreach'
        priority = 'HIGH'
    else:
        intervention_type = 'monitoring'
        priority = 'NORMAL'
    
    # Generate rationale based on top risk drivers
    rationale = ""
    
    if top_drivers and len(top_drivers) > 0:
        # Check for specific driver patterns to customize rationale
        driver_features = [d.get('feature', '').lower() for d in top_drivers if d.get('feature')]
        
        # Check for payment-related drivers
        if any('payment' in feature for feature in driver_features):
            rationale = "Payment behavior indicates immediate default risk. Customer has missed or delayed payments, requiring urgent intervention to prevent delinquency."
        
        # Check for utilization-related drivers
        elif any('utilization' in feature for feature in driver_features):
            rationale = "Credit utilization spike suggests financial stress. Customer may be overextending credit, indicating potential cash flow issues."
        
        # Check for bureau/credit-related drivers
        elif any('bureau' in feature or 'credit' in feature for feature in driver_features):
            rationale = "Bureau indicators show credit deterioration. External credit factors suggest increased risk across customer's financial profile."
        
        # Check for income-related drivers
        elif any('income' in feature for feature in driver_features):
            rationale = "Income volatility detected. Changes in income patterns may affect customer's ability to meet payment obligations."
        
        # Check for account age or history drivers
        elif any('account' in feature or 'age' in feature for feature in driver_features):
            rationale = "Account behavior patterns indicate risk. Historical account management shows concerning trends."
        
        # Default rationale for other drivers
        else:
            rationale = "Multiple risk factors detected across customer profile. Combination of behavioral and financial indicators suggest elevated risk."
    else:
        # Default rationale when no drivers available
        rationale = f"Customer classified as {risk_level} risk based on overall risk assessment. Intervention recommended based on risk level classification."
    
    return {
        'intervention_type': intervention_type,
        'rationale': rationale,
        'priority': priority
    }
