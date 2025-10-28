"""
Evolution Panel Component
Displays current evolution status and stage information
"""

import streamlit as st
import plotly.graph_objects as go
from typing import Dict, Any

def render_evolution_panel(evolution_status: Dict[str, Any]):
    """Render evolution status panel"""
    
    st.header("🚀 Evolution Status")
    
    if not evolution_status or 'error' in evolution_status:
        st.error("❌ Unable to load evolution status")
        return
    
    # Main metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Current stage with emoji
        stage_emoji = {
            'infant': '👶', 'child': '🧒', 'adolescent': '👦',
            'adult': '👨', 'expert': '🧠', 'sage': '🎓'
        }
        current_stage = evolution_status.get('current_stage', 'unknown')
        emoji = stage_emoji.get(current_stage, '🤖')
        st.metric(
            label="Current Stage",
            value=f"{emoji} {current_stage.title()}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="System Age",
            value=f"{evolution_status.get('system_age_days', 0)} days",
            delta=None
        )
    
    with col3:
        success_rate = evolution_status.get('success_rate', 0)
        st.metric(
            label="Success Rate",
            value=f"{success_rate:.1f}%",
            delta=None
        )
    
    with col4:
        total_sessions = evolution_status.get('total_sessions', 0)
        st.metric(
            label="Total Sessions",
            value=total_sessions,
            delta=None
        )
    
    # Stage progression visualization
    st.subheader("📈 Stage Progression")
    
    # Create stage progression chart
    stages = ['infant', 'child', 'adolescent', 'adult', 'expert', 'sage']
    stage_progress = {
        'infant': 100 if current_stage != 'infant' else 50,
        'child': 100 if current_stage not in ['infant', 'child'] else 50 if current_stage == 'child' else 0,
        'adolescent': 100 if current_stage not in ['infant', 'child', 'adolescent'] else 50 if current_stage == 'adolescent' else 0,
        'adult': 100 if current_stage not in ['infant', 'child', 'adolescent', 'adult'] else 50 if current_stage == 'adult' else 0,
        'expert': 100 if current_stage not in ['infant', 'child', 'adolescent', 'adult', 'expert'] else 50 if current_stage == 'expert' else 0,
        'sage': 100 if current_stage == 'sage' else 50 if current_stage == 'sage' else 0
    }
    
    # Create gauge chart for current stage progress
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = stage_progress.get(current_stage, 0),
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"Stage Progress: {current_stage.title()}"},
        delta = {'reference': 0},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 33], 'color': "lightgray"},
                {'range': [33, 66], 'color': "gray"},
                {'range': [66, 100], 'color': "darkgray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)
    
    # Recent performance
    st.subheader("📊 Recent Performance")
    
    recent_sessions = evolution_status.get('recent_sessions', [])
    if recent_sessions:
        # Calculate recent success rate
        recent_success = sum(1 for session in recent_sessions if session.get('success', False))
        recent_success_rate = (recent_success / len(recent_sessions)) * 100
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Recent Sessions",
                value=len(recent_sessions),
                delta=None
            )
        
        with col2:
            st.metric(
                label="Recent Success Rate",
                value=f"{recent_success_rate:.1f}%",
                delta=None
            )
        
        with col3:
            avg_proposals = sum(session.get('proposals_learned', 0) for session in recent_sessions) / len(recent_sessions)
            st.metric(
                label="Avg Proposals/Session",
                value=f"{avg_proposals:.1f}",
                delta=None
            )
    else:
        st.info("📝 No recent sessions data available")