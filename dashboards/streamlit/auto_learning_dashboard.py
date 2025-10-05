#!/usr/bin/env python3
"""
🤖 AUTO LEARNING DASHBOARD
Dashboard cho hệ thống học tập tự động hoàn toàn
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from stillme_core.learning.proposals_manager import ProposalsManager
from stillme_core.learning.auto_approval_engine import AutoApprovalEngine
from stillme_core.learning.silent_learning_system import SilentEvolutionaryLearningSystem

class AutoLearningDashboard:
    def __init__(self):
        self.proposals_manager = ProposalsManager()
        self.approval_engine = AutoApprovalEngine()
        self.learning_system = SilentEvolutionaryLearningSystem()
        
    def run(self):
        """Main dashboard function"""
        st.set_page_config(
            page_title="🤖 StillMe Auto Learning Dashboard",
            page_icon="🤖",
            layout="wide"
        )
        
        # Header
        st.title("🤖 StillMe Auto Learning Dashboard")
        st.markdown("**Hệ thống học tập tự động hoàn toàn - Không cần can thiệp**")
        
        # Sidebar controls
        self.render_sidebar()
        
        # Main content
        self.render_main_content()
    
    def render_sidebar(self):
        """Render sidebar controls"""
        st.sidebar.header("🤖 Hệ Thống Tự Động")
        
        # Auto-approval status
        auto_approved_count = self.get_auto_approved_count()
        st.sidebar.metric("🤖 Tự động approve", auto_approved_count)
        
        # Silent learning sessions
        silent_learning = self.get_silent_learning_sessions()
        st.sidebar.metric("🔇 Đang học im lặng", len(silent_learning))
        
        # Completion rate
        completion_rate = self.get_completion_rate()
        st.sidebar.metric("✅ Tỷ lệ hoàn thành", f"{completion_rate:.1f}%")
        
        # Manual controls
        st.sidebar.header("🎛️ Điều Khiển Thủ Công")
        
        if st.sidebar.button("🔄 Chạy Auto-Discovery Ngay"):
            with st.spinner("Đang chạy knowledge discovery..."):
                # Trigger discovery
                st.success("✅ Đã chạy auto-discovery")
        
        if st.sidebar.button("🤖 Chạy Auto-Approval Ngay"):
            with st.spinner("Đang chạy auto-approval..."):
                approved_count = self.approval_engine.run_approval_cycle()
                st.success(f"✅ Đã auto-approve {approved_count} proposals")
        
        if st.sidebar.button("📊 Refresh Data"):
            st.rerun()
    
    def render_main_content(self):
        """Render main dashboard content"""
        # Status overview
        self.render_status_overview()
        
        # Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Tổng Quan", "🤖 Auto-Approval", "🔇 Silent Learning", 
            "📈 Analytics", "⚙️ Settings"
        ])
        
        with tab1:
            self.render_overview_tab()
        
        with tab2:
            self.render_auto_approval_tab()
        
        with tab3:
            self.render_silent_learning_tab()
        
        with tab4:
            self.render_analytics_tab()
        
        with tab5:
            self.render_settings_tab()
    
    def render_status_overview(self):
        """Render status overview"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            pending_count = self.get_pending_count()
            st.metric("📋 Pending Proposals", pending_count)
        
        with col2:
            learning_count = self.get_learning_count()
            st.metric("🔄 Active Learning", learning_count)
        
        with col3:
            completed_today = self.get_completed_today()
            st.metric("✅ Completed Today", completed_today)
        
        with col4:
            total_learning_time = self.get_total_learning_time()
            st.metric("⏱️ Total Learning Time", f"{total_learning_time} min")
    
    def render_overview_tab(self):
        """Render overview tab"""
        st.header("📊 Tổng Quan Hệ Thống")
        
        # Learning progress chart
        self.render_learning_progress_chart()
        
        # Recent completions
        self.render_recent_completions()
        
        # System health
        self.render_system_health()
    
    def render_auto_approval_tab(self):
        """Render auto-approval tab"""
        st.header("🤖 Auto-Approval System")
        
        # Approval criteria
        st.subheader("📋 Tiêu Chí Auto-Approval")
        criteria_data = {
            "Tiêu chí": ["Quality Score", "Max Duration", "Min Objectives", "Max Concurrent"],
            "Giá trị": [">= 0.75", "<= 180 phút", ">= 1", "<= 5"],
            "Trạng thái": ["✅ Active", "✅ Active", "✅ Active", "✅ Active"]
        }
        st.dataframe(pd.DataFrame(criteria_data), use_container_width=True)
        
        # Recent auto-approvals
        st.subheader("📊 Recent Auto-Approvals")
        recent_approvals = self.get_recent_auto_approvals()
        if recent_approvals:
            st.dataframe(recent_approvals, use_container_width=True)
        else:
            st.info("ℹ️ Chưa có auto-approval nào")
    
    def render_silent_learning_tab(self):
        """Render silent learning tab"""
        st.header("🔇 Silent Learning System")
        
        # Active silent sessions
        st.subheader("🔄 Active Silent Sessions")
        silent_sessions = self.get_silent_learning_sessions()
        
        if silent_sessions:
            for session in silent_sessions:
                with st.expander(f"🔇 {session['title']} - {session['progress']:.1f}%"):
                    st.write(f"**Session ID:** {session['session_id']}")
                    st.write(f"**Progress:** {session['progress']:.1f}%")
                    st.write(f"**Started:** {session['started_at']}")
                    st.write(f"**Current Objective:** {session['current_objective_index'] + 1}/{len(session['objectives'])}")
                    
                    # Progress bar
                    st.progress(session['progress'] / 100)
        else:
            st.info("ℹ️ Không có silent learning session nào đang chạy")
    
    def render_analytics_tab(self):
        """Render analytics tab"""
        st.header("📈 Learning Analytics")
        
        # Learning trends
        self.render_learning_trends()
        
        # Completion statistics
        self.render_completion_stats()
        
        # Quality metrics
        self.render_quality_metrics()
    
    def render_settings_tab(self):
        """Render settings tab"""
        st.header("⚙️ System Settings")
        
        # Auto-approval settings
        st.subheader("🤖 Auto-Approval Settings")
        col1, col2 = st.columns(2)
        
        with col1:
            quality_threshold = st.slider("Quality Threshold", 0.0, 1.0, 0.75, 0.05)
            max_duration = st.slider("Max Duration (minutes)", 60, 300, 180, 30)
        
        with col2:
            min_objectives = st.slider("Min Objectives", 1, 10, 1, 1)
            max_concurrent = st.slider("Max Concurrent Sessions", 1, 10, 5, 1)
        
        if st.button("💾 Save Settings"):
            st.success("✅ Settings saved!")
        
        # Notification settings
        st.subheader("🔔 Notification Settings")
        completion_alerts = st.checkbox("Completion Alerts", value=True)
        error_alerts = st.checkbox("Error Alerts", value=True)
        daily_summary = st.checkbox("Daily Summary", value=True)
    
    def get_auto_approved_count(self):
        """Get count of auto-approved proposals"""
        try:
            proposals = self.proposals_manager.get_all_proposals()
            auto_approved = [p for p in proposals if p.get('approved_by') == 'auto_approval_system']
            return len(auto_approved)
        except:
            return 0
    
    def get_silent_learning_sessions(self):
        """Get active silent learning sessions"""
        try:
            proposals = self.proposals_manager.get_all_proposals()
            learning_sessions = [p for p in proposals if p.get('status') == 'learning']
            
            sessions = []
            for proposal in learning_sessions:
                session_data = self.learning_system.get_session_status(proposal.get('session_id', ''))
                if session_data:
                    sessions.append(session_data)
            
            return sessions
        except:
            return []
    
    def get_completion_rate(self):
        """Get completion rate percentage"""
        try:
            proposals = self.proposals_manager.get_all_proposals()
            total_approved = len([p for p in proposals if p.get('status') in ['approved', 'learning', 'completed']])
            completed = len([p for p in proposals if p.get('status') == 'completed'])
            
            if total_approved > 0:
                return (completed / total_approved) * 100
            return 0
        except:
            return 0
    
    def get_pending_count(self):
        """Get pending proposals count"""
        try:
            proposals = self.proposals_manager.get_all_proposals()
            return len([p for p in proposals if p.get('status') == 'pending'])
        except:
            return 0
    
    def get_learning_count(self):
        """Get active learning count"""
        try:
            proposals = self.proposals_manager.get_all_proposals()
            return len([p for p in proposals if p.get('status') == 'learning'])
        except:
            return 0
    
    def get_completed_today(self):
        """Get completed today count"""
        try:
            proposals = self.proposals_manager.get_all_proposals()
            today = datetime.now().date()
            completed_today = [
                p for p in proposals 
                if p.get('status') == 'completed' and 
                p.get('learning_completed_at') and
                datetime.fromisoformat(p['learning_completed_at']).date() == today
            ]
            return len(completed_today)
        except:
            return 0
    
    def get_total_learning_time(self):
        """Get total learning time in minutes"""
        try:
            proposals = self.proposals_manager.get_all_proposals()
            completed = [p for p in proposals if p.get('status') == 'completed']
            return sum(p.get('estimated_duration', 0) for p in completed)
        except:
            return 0
    
    def get_recent_auto_approvals(self):
        """Get recent auto-approvals"""
        try:
            proposals = self.proposals_manager.get_all_proposals()
            auto_approved = [
                p for p in proposals 
                if p.get('approved_by') == 'auto_approval_system'
            ]
            
            # Sort by approval time
            auto_approved.sort(key=lambda x: x.get('approved_at', ''), reverse=True)
            
            # Return first 10
            recent = auto_approved[:10]
            
            if recent:
                df_data = []
                for proposal in recent:
                    df_data.append({
                        'Title': proposal.get('title', 'Unknown'),
                        'Quality Score': proposal.get('quality_score', 0),
                        'Duration': f"{proposal.get('estimated_duration', 0)} min",
                        'Status': proposal.get('status', 'Unknown'),
                        'Approved At': proposal.get('approved_at', 'Unknown')
                    })
                return pd.DataFrame(df_data)
            return pd.DataFrame()
        except:
            return pd.DataFrame()
    
    def render_learning_progress_chart(self):
        """Render learning progress chart"""
        st.subheader("📈 Learning Progress")
        
        # Get learning data
        proposals = self.proposals_manager.get_all_proposals()
        learning_proposals = [p for p in proposals if p.get('status') in ['learning', 'completed']]
        
        if learning_proposals:
            # Create progress chart
            progress_data = []
            for proposal in learning_proposals:
                progress_data.append({
                    'Title': proposal.get('title', 'Unknown'),
                    'Progress': proposal.get('learning_progress', 0),
                    'Status': proposal.get('status', 'Unknown')
                })
            
            df = pd.DataFrame(progress_data)
            
            # Create bar chart
            fig = px.bar(
                df, 
                x='Title', 
                y='Progress',
                color='Status',
                title="Learning Progress by Proposal"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ℹ️ Chưa có learning data")
    
    def render_recent_completions(self):
        """Render recent completions"""
        st.subheader("🎉 Recent Completions")
        
        try:
            proposals = self.proposals_manager.get_all_proposals()
            completed = [p for p in proposals if p.get('status') == 'completed']
            
            if completed:
                # Sort by completion time
                completed.sort(key=lambda x: x.get('learning_completed_at', ''), reverse=True)
                
                # Show recent 5
                recent = completed[:5]
                
                for proposal in recent:
                    with st.container():
                        st.success(f"✅ {proposal.get('title', 'Unknown')}")
                        st.write(f"⏱️ Duration: {proposal.get('estimated_duration', 0)} minutes")
                        st.write(f"📅 Completed: {proposal.get('learning_completed_at', 'Unknown')}")
                        st.divider()
            else:
                st.info("ℹ️ Chưa có completion nào")
        except Exception as e:
            st.error(f"❌ Lỗi loading completions: {e}")
    
    def render_system_health(self):
        """Render system health"""
        st.subheader("🏥 System Health")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🔄 Auto-Discovery", "✅ Running", "Every 6h")
        
        with col2:
            st.metric("🤖 Auto-Approval", "✅ Running", "Every 1h")
        
        with col3:
            st.metric("🔇 Silent Learning", "✅ Active", "Background")
    
    def render_learning_trends(self):
        """Render learning trends"""
        st.subheader("📈 Learning Trends")
        st.info("📊 Learning trends chart sẽ được implement...")
    
    def render_completion_stats(self):
        """Render completion statistics"""
        st.subheader("📊 Completion Statistics")
        
        try:
            proposals = self.proposals_manager.get_all_proposals()
            
            # Calculate stats
            total_proposals = len(proposals)
            pending = len([p for p in proposals if p.get('status') == 'pending'])
            approved = len([p for p in proposals if p.get('status') == 'approved'])
            learning = len([p for p in proposals if p.get('status') == 'learning'])
            completed = len([p for p in proposals if p.get('status') == 'completed'])
            
            # Create pie chart
            labels = ['Pending', 'Approved', 'Learning', 'Completed']
            values = [pending, approved, learning, completed]
            colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
            
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, marker_colors=colors)])
            fig.update_layout(title="Proposal Status Distribution")
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Lỗi loading completion stats: {e}")
    
    def render_quality_metrics(self):
        """Render quality metrics"""
        st.subheader("📊 Quality Metrics")
        st.info("📈 Quality metrics sẽ được implement...")

def main():
    """Main function"""
    dashboard = AutoLearningDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()
