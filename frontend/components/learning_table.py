"""
Learning Table Component
Displays learning sessions in a table format
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime

def render_learning_table(learning_history: List[Dict[str, Any]]):
    """Render learning sessions table"""
    
    st.header("📋 Recent Learning Sessions")
    
    if not learning_history:
        st.info("📝 No learning sessions recorded yet")
        return
    
    # Convert to DataFrame for easier display
    df_data = []
    for session in learning_history[:10]:  # Show last 10 sessions
        df_data.append({
            'Session ID': session.get('session_id', '')[:8] + '...',
            'Date': session.get('date', ''),
            'Proposals Learned': session.get('proposals_learned', 0),
            'Evolution Stage': session.get('evolution_stage', 'unknown').title(),
            'Duration (min)': session.get('duration_minutes', 0),
            'Success': '✅' if session.get('success', False) else '❌',
            'Accuracy Δ': f"{session.get('accuracy_delta', 0):+.2f}%"
        })
    
    if df_data:
        df = pd.DataFrame(df_data)
        
        # Style the DataFrame
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Proposals Learned": st.column_config.ProgressColumn(
                    "Proposals Learned",
                    help="Number of proposals learned",
                    format="%d",
                    min_value=0,
                    max_value=max([s.get('proposals_learned', 0) for s in learning_history]) or 10
                ),
                "Success": st.column_config.TextColumn(
                    "Status",
                    help="Session success status"
                )
            }
        )
        
        # Session statistics
        st.subheader("📊 Session Statistics")
        
        total_sessions = len(learning_history)
        successful_sessions = sum(1 for s in learning_history if s.get('success', False))
        success_rate = (successful_sessions / total_sessions) * 100 if total_sessions > 0 else 0
        total_proposals = sum(s.get('proposals_learned', 0) for s in learning_history)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Sessions", total_sessions)
        with col2:
            st.metric("Success Rate", f"{success_rate:.1f}%")
        with col3:
            st.metric("Total Proposals", total_proposals)
        with col4:
            avg_duration = sum(s.get('duration_minutes', 0) for s in learning_history) / total_sessions
            st.metric("Avg Duration", f"{avg_duration:.1f}m")
        
    else:
        st.warning("No session data available to display")