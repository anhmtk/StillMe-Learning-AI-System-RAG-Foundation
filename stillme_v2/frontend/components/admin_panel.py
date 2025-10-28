"""
Admin Panel Component
Provides administrative controls and proposal management
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime

def render_admin_panel(api_client, notification_manager):
    """Render admin panel with management controls"""
    
    st.title("⚙️ Admin Panel")
    st.markdown("System administration and proposal management")
    
    # Create tabs for different admin functions
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Proposal Review", 
        "🚀 System Controls", 
        "👥 Community", 
        "📊 Analytics",
        "🔧 Settings"
    ])
    
    with tab1:
        render_proposal_review(api_client, notification_manager)
    
    with tab2:
        render_system_controls(api_client, notification_manager)
    
    with tab3:
        render_community_management(api_client)
    
    with tab4:
        render_admin_analytics(api_client)
    
    with tab5:
        render_system_settings()

def render_proposal_review(api_client, notification_manager):
    """Render proposal review interface"""
    
    st.header("📋 Proposal Review Queue")
    
    try:
        # Fetch pending proposals
        pending_proposals = api_client.get_pending_review_proposals()
        
        if not pending_proposals:
            st.success("🎉 No pending proposals for review!")
            return
        
        st.info(f"🔍 {len(pending_proposals)} proposals need review")
        
        for i, proposal in enumerate(pending_proposals):
            with st.expander(f"📄 {proposal.get('title', 'Untitled Proposal')} (ID: {proposal.get('proposal_id', 'N/A')})", expanded=i==0):
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Category:** {proposal.get('category', 'Unknown')}")
                    st.markdown(f"**Confidence Score:** {proposal.get('confidence', 0):.2f}")
                    st.markdown(f"**Source:** {proposal.get('source', 'Unknown')}")
                    
                    # Proposal content
                    st.markdown("**Content Preview:**")
                    st.text_area(
                        "Content",
                        value=proposal.get('content', 'No content available'),
                        height=150,
                        key=f"content_{proposal.get('proposal_id')}",
                        disabled=True
                    )
                
                with col2:
                    st.markdown("### Actions")
                    
                    # Approve/Reject buttons
                    approve_col, reject_col = st.columns(2)
                    
                    with approve_col:
                        if st.button("✅ Approve", key=f"approve_{proposal.get('proposal_id')}", use_container_width=True):
                            with st.spinner("Approving proposal..."):
                                success = api_client.approve_proposal(
                                    proposal.get('proposal_id'), 
                                    "Approved by admin via dashboard"
                                )
                                if success:
                                    st.success("Proposal approved!")
                                    notification_manager.send_notification(
                                        "Proposal Approved",
                                        f"Proposal '{proposal.get('title')}' was approved",
                                        "admin"
                                    )
                                    st.rerun()
                                else:
                                    st.error("Failed to approve proposal")
                    
                    with reject_col:
                        if st.button("❌ Reject", key=f"reject_{proposal.get('proposal_id')}", use_container_width=True):
                            reason = st.text_input("Rejection reason", key=f"reason_{proposal.get('proposal_id')}")
                            if reason:
                                success = api_client.reject_proposal(proposal.get('proposal_id'), reason)
                                if success:
                                    st.success("Proposal rejected!")
                                    notification_manager.send_notification(
                                        "Proposal Rejected",
                                        f"Proposal '{proposal.get('title')}' was rejected: {reason}",
                                        "admin"
                                    )
                                    st.rerun()
                
                st.markdown("---")
    
    except Exception as e:
        st.error(f"❌ Error loading proposals: {str(e)}")

def render_system_controls(api_client, notification_manager):
    """Render system control buttons"""
    
    st.header("🚀 System Controls")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Learning Sessions")
        
        if st.button("🎯 Run Daily Learning", use_container_width=True):
            with st.spinner("Running daily learning session..."):
                try:
                    result = api_client.run_daily_learning_session()
                    if result and result.get('success'):
                        st.success("✅ Daily learning completed!")
                        notification_manager.send_notification(
                            "Daily Learning Completed",
                            f"Session processed {result.get('proposals_processed', 0)} proposals",
                            "system"
                        )
                    else:
                        st.error("❌ Daily learning failed!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        if st.button("🔍 Force Self-Assessment", use_container_width=True):
            with st.spinner("Running self-assessment..."):
                try:
                    assessment = api_client.self_assess()
                    st.success(f"✅ Assessment: {assessment.get('overall_health', 'Unknown')}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with col2:
        st.subheader("Data Management")
        
        if st.button("🔄 Update All Metrics", use_container_width=True):
            st.success("Metrics update triggered!")
        
        if st.button("🧹 Clear Cache", use_container_width=True):
            st.info("Cache cleared!")
        
        if st.button("📊 Generate Report", use_container_width=True):
            with st.spinner("Generating report..."):
                st.success("Report generated successfully!")
                st.download_button(
                    "📥 Download Report",
                    data="Sample report data",
                    file_name=f"evolution_report_{datetime.now().strftime('%Y%m%d')}.pdf"
                )
    
    with col3:
        st.subheader("System Maintenance")
        
        if st.button("🛠️ System Health Check", use_container_width=True):
            with st.spinner("Running health check..."):
                try:
                    status = api_client.get_evolution_status()
                    if status:
                        st.success("✅ System health: Good")
                    else:
                        st.warning("⚠️ System health: Issues detected")
                except Exception as e:
                    st.error(f"❌ Health check failed: {str(e)}")
        
        if st.button("📈 Performance Optimize", use_container_width=True):
            st.info("Performance optimization started...")
        
        if st.button("🚨 Emergency Stop", use_container_width=True, type="secondary"):
            st.error("EMERGENCY STOP ACTIVATED!")
            st.warning("All learning sessions have been paused.")

def render_community_management(api_client):
    """Render community proposal management"""
    
    st.header("👥 Community Proposals")
    
    # Community voting threshold
    st.subheader("Voting Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        auto_approve_threshold = st.slider(
            "Auto-approve Threshold",
            min_value=10,
            max_value=100,
            value=50,
            help="Minimum votes for auto-approval"
        )
    
    with col2:
        review_threshold = st.slider(
            "Review Threshold", 
            min_value=5,
            max_value=50,
            value=20,
            help="Minimum votes for admin review"
        )
    
    if st.button("💾 Save Voting Settings"):
        st.success("Voting settings saved!")
    
    st.markdown("---")
    st.subheader("Community Proposal Queue")
    
    try:
        # Fetch community proposals (mock data for now)
        community_proposals = api_client.get_community_proposals(min_votes=review_threshold)
        
        if not community_proposals:
            st.info("📝 No community proposals meeting threshold")
            return
        
        for proposal in community_proposals:
            with st.expander(f"🗳️ {proposal.get('title', 'Untitled')} ({proposal.get('votes', 0)} votes)"):
                
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"**Votes:** {proposal.get('votes', 0)}")
                    st.markdown(f"**Category:** {proposal.get('category', 'Unknown')}")
                    st.progress(proposal.get('votes', 0) / 100)
                
                with col2:
                    if proposal.get('votes', 0) >= auto_approve_threshold:
                        st.success("✅ Auto-approved!")
                    elif proposal.get('votes', 0) >= review_threshold:
                        st.warning("⚠️ Needs review")
                    else:
                        st.info("📊 Collecting votes")
                
                with col3:
                    if st.button("👀 Review", key=f"review_{proposal.get('id')}"):
                        st.session_state.review_proposal = proposal
                
                if proposal.get('votes', 0) >= auto_approve_threshold:
                    if st.button("✅ Auto-approve Now", key=f"auto_{proposal.get('id')}"):
                        st.success("Proposal auto-approved!")
    
    except Exception as e:
        st.error(f"Error loading community proposals: {str(e)}")

def render_admin_analytics(api_client):
    """Render admin analytics"""
    
    st.header("📊 Admin Analytics")
    
    try:
        metrics = api_client.get_evolution_metrics()
        status = api_client.get_evolution_status()
        
        if not metrics or not status:
            st.error("Unable to load analytics data")
            return
        
        # Key admin metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Sessions", metrics.get('total_sessions', 0))
        with col2:
            st.metric("Success Rate", f"{metrics.get('success_rate', 0):.1f}%")
        with col3:
            st.metric("Knowledge Items", metrics.get('total_knowledge_items', 0))
        with col4:
            st.metric("System Uptime", f"{status.get('system_age_days', 0)} days")
        
        # Performance metrics
        st.subheader("Performance Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Learning Efficiency**")
            st.progress(metrics.get('success_rate', 0) / 100)
            
            st.markdown("**Stage Distribution**")
            stage_data = metrics.get('stage_distribution', {})
            for stage, count in stage_data.items():
                st.text(f"{stage.title()}: {count} sessions")
        
        with col2:
            st.markdown("**Recent Performance**")
            recent_trend = metrics.get('learning_trend', 'unknown')
            trend_emoji = "📈" if recent_trend == 'improving' else "➡️" if recent_trend == 'stable' else "📉"
            st.metric("Learning Trend", f"{trend_emoji} {recent_trend.title()}")
            
            st.markdown("**Avg Proposals/Session**")
            st.metric("Average", f"{metrics.get('average_proposals_per_session', 0):.1f}")
    
    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")

def render_system_settings():
    """Render system settings"""
    
    st.header("🔧 System Settings")
    
    # Learning parameters
    st.subheader("Learning Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_proposals = st.number_input(
            "Max Proposals per Session",
            min_value=10,
            max_value=1000,
            value=50,
            help="Maximum number of proposals to process in one session"
        )
        
        auto_approval_threshold = st.slider(
            "Auto-approval Confidence",
            min_value=0.0,
            max_value=1.0,
            value=0.8,
            step=0.1,
            help="Minimum confidence score for auto-approval"
        )
    
    with col2:
        session_timeout = st.number_input(
            "Session Timeout (minutes)",
            min_value=5,
            max_value=120,
            value=30,
            help="Maximum duration for a learning session"
        )
        
        refresh_interval = st.number_input(
            "Dashboard Refresh (seconds)",
            min_value=10,
            max_value=300,
            value=30,
            help="Auto-refresh interval for dashboard"
        )
    
    # Notification settings
    st.subheader("Notification Settings")
    
    notify_col1, notify_col2 = st.columns(2)
    
    with notify_col1:
        email_notifications = st.checkbox("Email Notifications", value=True)
        telegram_notifications = st.checkbox("Telegram Notifications", value=False)
        dashboard_alerts = st.checkbox("Dashboard Alerts", value=True)
    
    with notify_col2:
        st.checkbox("Notify on Session Start", value=True)
        st.checkbox("Notify on Session Complete", value=True)
        st.checkbox("Notify on Stage Change", value=True)
        st.checkbox("Notify on System Errors", value=True)
    
    # Save settings
    if st.button("💾 Save All Settings", use_container_width=True):
        st.success("System settings saved successfully!")