"""
Metrics Charts Component
Displays various charts and visualizations for evolution metrics
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, Any, List

def render_metrics_charts(evolution_metrics: Dict[str, Any], learning_history: List[Dict[str, Any]]):
    """Render metrics charts and visualizations"""
    
    st.header("📈 Evolution Metrics")
    
    if not evolution_metrics or 'error' in evolution_metrics:
        st.error("❌ Unable to load evolution metrics")
        return
    
    # Create tabs for different chart types
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📚 Learning", "🎯 Performance", "📅 Timeline"])
    
    with tab1:
        render_overview_charts(evolution_metrics)
    
    with tab2:
        render_learning_charts(evolution_metrics, learning_history)
    
    with tab3:
        render_performance_charts(evolution_metrics)
    
    with tab4:
        render_timeline_charts(learning_history)

def render_overview_charts(metrics: Dict[str, Any]):
    """Render overview charts"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Stage distribution pie chart
        stage_distribution = metrics.get('stage_distribution', {})
        if stage_distribution:
            stages = list(stage_distribution.keys())
            counts = list(stage_distribution.values())
            
            fig = px.pie(
                values=counts,
                names=stages,
                title="Stage Distribution",
                color_discrete_sequence=px.colors.sequential.Blues
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No stage distribution data available")
    
    with col2:
        # Success rate gauge
        success_rate = metrics.get('success_rate', 0)
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = success_rate,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Overall Success Rate"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightcoral"},
                    {'range': [50, 80], 'color': "lightyellow"},
                    {'range': [80, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        st.plotly_chart(fig, use_container_width=True)

def render_learning_charts(metrics: Dict[str, Any], learning_history: List[Dict[str, Any]]):
    """Render learning-related charts"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Knowledge acquisition over time
        if learning_history:
            dates = [session.get('date', '') for session in learning_history]
            proposals = [session.get('proposals_learned', 0) for session in learning_history]
            
            fig = px.line(
                x=dates[-10:],  # Last 10 sessions
                y=proposals[-10:],
                title="Proposals Learned (Last 10 Sessions)",
                labels={'x': 'Session Date', 'y': 'Proposals Learned'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No learning history data available")
    
    with col2:
        # Knowledge items bar chart
        total_knowledge = metrics.get('total_knowledge_items', 0)
        recent_knowledge = metrics.get('recent_knowledge_items', 0)
        
        fig = px.bar(
            x=['Total Knowledge', 'Recent Knowledge (7 days)'],
            y=[total_knowledge, recent_knowledge],
            title="Knowledge Base Size",
            color=['Total', 'Recent'],
            color_discrete_sequence=['blue', 'lightblue']
        )
        st.plotly_chart(fig, use_container_width=True)

def render_performance_charts(metrics: Dict[str, Any]):
    """Render performance charts"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Average proposals per session
        avg_proposals = metrics.get('average_proposals_per_session', 0)
        
        fig = go.Figure(go.Indicator(
            mode = "number",
            value = avg_proposals,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Avg Proposals/Session"},
            number = {'suffix': " proposals"}
        ))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Learning trend
        learning_trend = metrics.get('learning_trend', 'unknown')
        trend_color = {
            'improving': 'green',
            'stable': 'blue', 
            'declining': 'red',
            'unknown': 'gray'
        }.get(learning_trend, 'gray')
        
        fig = go.Figure(go.Indicator(
            mode = "delta",
            value = 0,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Learning Trend"},
            delta = {
                'reference': 0,
                'increasing': {'color': trend_color},
                'decreasing': {'color': trend_color}
            }
        ))
        
        fig.add_annotation(
            text=f"Trend: {learning_trend.title()}",
            x=0.5,
            y=0.3,
            showarrow=False
        )
        
        st.plotly_chart(fig, use_container_width=True)

def render_timeline_charts(learning_history: List[Dict[str, Any]]):
    """Render timeline charts"""
    
    if learning_history:
        # Prepare data for timeline
        sessions_data = []
        for session in learning_history[-20:]:  # Last 20 sessions
            sessions_data.append({
                'date': session.get('date', ''),
                'proposals_learned': session.get('proposals_learned', 0),
                'stage': session.get('evolution_stage', 'unknown'),
                'success': session.get('success', False)
            })
        
        # Create timeline chart
        fig = px.scatter(
            sessions_data,
            x='date',
            y='proposals_learned',
            color='stage',
            size='proposals_learned',
            title="Learning Timeline",
            labels={'proposals_learned': 'Proposals Learned', 'date': 'Session Date'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("No timeline data available")