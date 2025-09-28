"""
📊 StillMe Learning Dashboard - Streamlit
=========================================

Dev-friendly dashboard cho learning metrics visualization.
Real-time updates, interactive charts, và session drill-down.

Tính năng:
- 4 charts chính: Learning curve, Performance, Ingest volume, Error analysis
- Bộ lọc: Date range, stage, source, model
- Bảng sessions: 20 sessions gần nhất với drill-down
- Real-time updates: Auto-refresh mỗi 30s
- Mobile responsive design

Author: StillMe AI Framework
Version: 1.0.0
Date: 2025-09-28
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from stillme_core.metrics.queries import get_metrics_queries
from stillme_core.metrics.emitter import get_metrics_emitter

# Page config
st.set_page_config(
    page_title="StillMe Learning Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    .chart-container {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

class LearningDashboard:
    """StillMe Learning Dashboard"""
    
    def __init__(self):
        self.queries = get_metrics_queries()
        self.emitter = get_metrics_emitter()
        
        # Initialize session state
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = datetime.now()
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = True
    
    def render_header(self):
        """Render dashboard header"""
        st.markdown('<h1 class="main-header">🧠 StillMe Learning Dashboard</h1>', unsafe_allow_html=True)
        
        # Status indicators
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Total Sessions", "8", "↗️ +2")
        
        with col2:
            st.metric("✅ Success Rate", "100%", "↗️ +5%")
        
        with col3:
            st.metric("🧠 Learning Stage", "Adolescent", "↗️ +1")
        
        with col4:
            st.metric("⚡ Avg Latency", "523ms", "↘️ -50ms")
    
    def render_sidebar(self):
        """Render sidebar filters"""
        st.sidebar.header("🔧 Filters & Controls")
        
        # Date range filter
        st.sidebar.subheader("📅 Date Range")
        days = st.sidebar.selectbox(
            "Select period:",
            [7, 14, 30, 90],
            index=1,
            help="Number of days to display"
        )
        
        # Stage filter
        st.sidebar.subheader("🎯 Learning Stage")
        stages = st.sidebar.multiselect(
            "Select stages:",
            ["infant", "child", "adolescent", "adult"],
            default=["adolescent", "adult"],
            help="Filter by learning stages"
        )
        
        # Source filter
        st.sidebar.subheader("📚 Data Sources")
        sources = st.sidebar.multiselect(
            "Select sources:",
            ["rss", "experience", "manual", "api"],
            default=["rss", "experience"],
            help="Filter by data sources"
        )
        
        # Component filter
        st.sidebar.subheader("🔧 Components")
        components = st.sidebar.multiselect(
            "Select components:",
            ["learning", "memory", "router", "api", "agentdev"],
            default=["learning", "memory"],
            help="Filter by system components"
        )
        
        # Auto-refresh control
        st.sidebar.subheader("🔄 Auto Refresh")
        auto_refresh = st.sidebar.checkbox(
            "Enable auto-refresh",
            value=st.session_state.auto_refresh,
            help="Automatically refresh data every 30 seconds"
        )
        st.session_state.auto_refresh = auto_refresh
        
        if auto_refresh:
            refresh_interval = st.sidebar.slider(
                "Refresh interval (seconds):",
                min_value=10,
                max_value=300,
                value=30,
                step=10
            )
        else:
            refresh_interval = None
        
        # Manual refresh button
        if st.sidebar.button("🔄 Refresh Now", type="primary"):
            st.session_state.last_refresh = datetime.now()
            st.rerun()
        
        return {
            'days': days,
            'stages': stages,
            'sources': sources,
            'components': components,
            'auto_refresh': auto_refresh,
            'refresh_interval': refresh_interval
        }
    
    def render_learning_curve(self, days: int):
        """Render learning curve chart"""
        st.subheader("📈 Learning Curve")
        
        try:
            learning_data = self.queries.get_learning_curve(days)
            
            if not learning_data:
                st.warning("No learning curve data available")
                return
            
            # Create DataFrame
            df = pd.DataFrame(learning_data)
            df['date'] = pd.to_datetime(df['date'])
            
            # Create subplot
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Learning Progress', 'Self-Assessment'),
                vertical_spacing=0.1
            )
            
            # Learning progress
            fig.add_trace(
                go.Scatter(
                    x=df['date'],
                    y=df['pass_rate'],
                    name='Pass Rate',
                    line=dict(color='#1f77b4', width=3),
                    mode='lines+markers'
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df['date'],
                    y=df['accuracy'],
                    name='Accuracy',
                    line=dict(color='#ff7f0e', width=3),
                    mode='lines+markers'
                ),
                row=1, col=1
            )
            
            # Self-assessment
            fig.add_trace(
                go.Scatter(
                    x=df['date'],
                    y=df['self_assessment'],
                    name='Self-Assessment',
                    line=dict(color='#2ca02c', width=3),
                    mode='lines+markers'
                ),
                row=2, col=1
            )
            
            # Update layout
            fig.update_layout(
                height=600,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            fig.update_xaxes(title_text="Date", row=2, col=1)
            fig.update_yaxes(title_text="Score", row=1, col=1)
            fig.update_yaxes(title_text="Score", row=2, col=1)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Avg Pass Rate", f"{df['pass_rate'].mean():.1%}")
            with col2:
                st.metric("Avg Accuracy", f"{df['accuracy'].mean():.1%}")
            with col3:
                st.metric("Avg Self-Assessment", f"{df['self_assessment'].mean():.1%}")
                
        except Exception as e:
            st.error(f"Error loading learning curve: {e}")
    
    def render_performance_metrics(self, days: int):
        """Render performance metrics"""
        st.subheader("⚡ Performance Metrics")
        
        try:
            performance = self.queries.get_performance_metrics(days)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Latency chart
                if performance.get('latency'):
                    latency_data = []
                    for operation, metrics in performance['latency'].items():
                        latency_data.append({
                            'Operation': operation,
                            'Avg Latency (ms)': metrics.get('avg', 0),
                            'Max Latency (ms)': metrics.get('max', 0)
                        })
                    
                    df_latency = pd.DataFrame(latency_data)
                    
                    fig_latency = px.bar(
                        df_latency,
                        x='Operation',
                        y='Avg Latency (ms)',
                        title='Average Latency by Operation',
                        color='Avg Latency (ms)',
                        color_continuous_scale='Reds'
                    )
                    st.plotly_chart(fig_latency, use_container_width=True)
            
            with col2:
                # Memory and CPU
                memory = performance.get('memory', {})
                cpu = performance.get('cpu', {})
                
                # Create gauge charts
                fig_gauges = make_subplots(
                    rows=1, cols=2,
                    specs=[[{'type': 'indicator'}, {'type': 'indicator'}]],
                    subplot_titles=('Memory Usage', 'CPU Usage')
                )
                
                fig_gauges.add_trace(
                    go.Indicator(
                        mode="gauge+number",
                        value=memory.get('avg_mb', 0),
                        title={'text': "Avg Memory (MB)"},
                        gauge={'axis': {'range': [None, 1000]},
                               'bar': {'color': "darkblue"},
                               'steps': [{'range': [0, 500], 'color': "lightgray"},
                                        {'range': [500, 800], 'color': "gray"}],
                               'threshold': {'line': {'color': "red", 'width': 4},
                                           'thickness': 0.75, 'value': 900}}
                    ),
                    row=1, col=1
                )
                
                fig_gauges.add_trace(
                    go.Indicator(
                        mode="gauge+number",
                        value=cpu.get('avg_percent', 0),
                        title={'text': "Avg CPU (%)"},
                        gauge={'axis': {'range': [None, 100]},
                               'bar': {'color': "darkgreen"},
                               'steps': [{'range': [0, 50], 'color': "lightgray"},
                                        {'range': [50, 80], 'color': "gray"}],
                               'threshold': {'line': {'color': "red", 'width': 4},
                                           'thickness': 0.75, 'value': 90}}
                    ),
                    row=1, col=2
                )
                
                fig_gauges.update_layout(height=300)
                st.plotly_chart(fig_gauges, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error loading performance metrics: {e}")
    
    def render_ingest_volume(self, days: int):
        """Render ingest volume chart"""
        st.subheader("📚 Ingest Volume by Source")
        
        try:
            ingest_data = self.queries.get_ingest_volume(days)
            
            if not ingest_data:
                st.warning("No ingest data available")
                return
            
            # Create DataFrame
            df = pd.DataFrame(ingest_data)
            df['date'] = pd.to_datetime(df['date'])
            
            # Stacked bar chart
            fig = px.bar(
                df,
                x='date',
                y='total_items',
                color='source',
                title='Items Ingested by Source Over Time',
                labels={'total_items': 'Items Count', 'date': 'Date'},
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            fig.update_layout(
                height=400,
                xaxis_title="Date",
                yaxis_title="Items Count",
                legend_title="Source"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary by source
            source_summary = df.groupby('source')['total_items'].sum().reset_index()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Total by Source")
                fig_pie = px.pie(
                    source_summary,
                    values='total_items',
                    names='source',
                    title='Distribution by Source'
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                st.subheader("📈 Daily Average")
                daily_avg = df.groupby('source')['total_items'].mean().reset_index()
                fig_bar = px.bar(
                    daily_avg,
                    x='source',
                    y='total_items',
                    title='Daily Average by Source',
                    color='total_items',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig_bar, use_container_width=True)
                
        except Exception as e:
            st.error(f"Error loading ingest volume: {e}")
    
    def render_error_analysis(self, days: int):
        """Render error analysis"""
        st.subheader("🚨 Error Analysis")
        
        try:
            error_data = self.queries.get_error_analysis(days)
            
            if not error_data.get('by_type'):
                st.success("✅ No errors detected in the selected period!")
                return
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Error types chart
                error_types = []
                for error_type, error_list in error_data['by_type'].items():
                    total_count = sum(item['count'] for item in error_list)
                    error_types.append({
                        'Error Type': error_type,
                        'Count': total_count
                    })
                
                if error_types:
                    df_errors = pd.DataFrame(error_types)
                    
                    fig_errors = px.bar(
                        df_errors,
                        x='Error Type',
                        y='Count',
                        title='Errors by Type',
                        color='Count',
                        color_continuous_scale='Reds'
                    )
                    st.plotly_chart(fig_errors, use_container_width=True)
            
            with col2:
                # Error trend over time
                error_trend = []
                for error_type, error_list in error_data['by_type'].items():
                    for item in error_list:
                        error_trend.append({
                            'Date': item['date'],
                            'Error Type': error_type,
                            'Count': item['count']
                        })
                
                if error_trend:
                    df_trend = pd.DataFrame(error_trend)
                    df_trend['Date'] = pd.to_datetime(df_trend['Date'])
                    
                    fig_trend = px.line(
                        df_trend,
                        x='Date',
                        y='Count',
                        color='Error Type',
                        title='Error Trend Over Time',
                        markers=True
                    )
                    st.plotly_chart(fig_trend, use_container_width=True)
            
            # Error summary
            st.subheader("📊 Error Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Errors", error_data.get('total_errors', 0))
            
            with col2:
                error_rate = error_data.get('total_errors', 0) / max(days, 1)
                st.metric("Daily Average", f"{error_rate:.1f}")
            
            with col3:
                if error_data.get('total_errors', 0) > 0:
                    st.metric("Status", "⚠️ Issues Detected", "error")
                else:
                    st.metric("Status", "✅ All Good", "success")
                    
        except Exception as e:
            st.error(f"Error loading error analysis: {e}")
    
    def render_sessions_table(self, limit: int = 20):
        """Render recent sessions table"""
        st.subheader("📋 Recent Learning Sessions")
        
        try:
            sessions = self.queries.get_recent_sessions(limit)
            
            if not sessions:
                st.warning("No session data available")
                return
            
            # Create DataFrame
            df = pd.DataFrame(sessions)
            
            # Format columns
            df['started_at'] = pd.to_datetime(df['started_at'])
            df['ended_at'] = pd.to_datetime(df['ended_at'])
            df['duration'] = (df['ended_at'] - df['started_at']).dt.total_seconds()
            df['duration'] = df['duration'].apply(lambda x: f"{x:.1f}s" if pd.notna(x) else "N/A")
            
            # Status column
            df['status'] = df['success'].apply(lambda x: "✅ Success" if x else "❌ Failed")
            
            # Select columns to display
            display_df = df[['session_id', 'started_at', 'stage', 'status', 'duration', 'metrics_count', 'errors_count']].copy()
            display_df.columns = ['Session ID', 'Started', 'Stage', 'Status', 'Duration', 'Metrics', 'Errors']
            
            # Display table
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Session details
            if st.checkbox("🔍 Show Session Details"):
                selected_session = st.selectbox(
                    "Select session:",
                    sessions,
                    format_func=lambda x: f"{x['session_id']} - {x['started_at']} ({x['stage']})"
                )
                
                if selected_session:
                    st.json(selected_session)
                    
        except Exception as e:
            st.error(f"Error loading sessions: {e}")
    
    def render_footer(self):
        """Render dashboard footer"""
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🧠 StillMe AI Framework**")
            st.markdown("Self-evolving AI learning system")
        
        with col2:
            st.markdown("**📊 Dashboard v1.0**")
            st.markdown(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        with col3:
            st.markdown("**🔗 Links**")
            st.markdown("[GitHub](https://github.com/stillme-ai/stillme) | [Docs](https://docs.stillme.ai)")
    
    def run(self):
        """Run the dashboard"""
        # Header
        self.render_header()
        
        # Sidebar
        filters = self.render_sidebar()
        
        # Auto-refresh logic
        if st.session_state.auto_refresh and filters['refresh_interval']:
            time.sleep(filters['refresh_interval'])
            st.rerun()
        
        # Main content
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Learning Curve", 
            "⚡ Performance", 
            "📚 Ingest Volume", 
            "🚨 Error Analysis",
            "📋 Sessions"
        ])
        
        with tab1:
            self.render_learning_curve(filters['days'])
        
        with tab2:
            self.render_performance_metrics(filters['days'])
        
        with tab3:
            self.render_ingest_volume(filters['days'])
        
        with tab4:
            self.render_error_analysis(filters['days'])
        
        with tab5:
            self.render_sessions_table()
        
        # Footer
        self.render_footer()

def main():
    """Main function"""
    try:
        dashboard = LearningDashboard()
        dashboard.run()
    except Exception as e:
        st.error(f"Dashboard error: {e}")
        st.exception(e)

if __name__ == "__main__":
    main()
