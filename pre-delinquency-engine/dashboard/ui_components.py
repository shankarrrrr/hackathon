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
            color: #374151 !important;
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


def render_pie_chart(labels, values, title, color_map=None):
    """Render pie chart."""
    colors = [color_map.get(label, '#6B7280') for label in labels] if color_map else None
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        hole=0.4,
        textfont={'size': 12, 'color': '#000000'}
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
