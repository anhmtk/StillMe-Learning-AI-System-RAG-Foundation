"""
Streamlit Dashboard for Evolution AI System
Main application file
"""

import streamlit as st
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Import components
from components.evolution_panel import render_evolution_panel
from components.learning_table import render_learning_table
from components.metrics_charts import render_metrics_charts
from components.chat_interface import render_chat_interface
from components.admin_panel import render_admin_panel
from components.notification_manager import NotificationManager

from utils.api_client import EvolutionAPIClient
from utils.config import API_BASE_URL, REFRESH_INTERVAL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Evolution AI Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

class EvolutionDashboard:
    """Main dashboard class for Evolution AI System"""
    
    def __init__(self):
        self.api_client = EvolutionAPIClient(API_BASE_URL)
        self.notification_manager = NotificationManager()
        self.last_update = None
        self.data_cache = {}
        
    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'page' not in st.session_state:
            st.session_state.page = "dashboard"
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = True
        if 'last_notification_check' not in st.session_state:
            st.session_state.last_notification_check = datetime.now()
            
    def render_sidebar(self):
        """Render sidebar navigation"""
        with st.sidebar:
            st.title("🧠 Evolution AI")
            st.markdown("---")
            
            # Navigation
            page = st.radio(
                "Navigate to:",
                [
                    "📊 Dashboard",
                    "💬 Chat with AI", 
                    "🔍 Knowledge Browser",
                    "⚙️ Admin Panel",
                    "📱 Notifications"
                ]
            )
            
            # Extract page key
            page_map = {
                "📊 Dashboard": "dashboard",
                "💬 Chat with AI": "chat", 
                "🔍 Knowledge Browser": "knowledge",
                "⚙️ Admin Panel": "admin",
                "📱 Notifications": "notifications"
            }
            st.session_state.page = page_map[page]
            
            st.markdown("---")
            
            # System status
            self.render_system_status()
            
            # Auto-refresh toggle
            st.session_state.auto_refresh = st.checkbox(
                "🔄 Auto-refresh", 
                value=st.session_state.auto_refresh,
                help="Automatically refresh data every 30 seconds"
            )
            
            # Manual refresh button
            if st.button("🔄 Refresh Now"):
                st.rerun()
                
            st.markdown("---")
            st.markdown("**System Info**")
            st.markdown(f"🕒 Last update: {self.last_update or 'Never'}")
            
    def render_system_status(self):
        """Render system status in sidebar"""
        try:
            status = self.api_client.get_evolution_status()
            if status and 'current_stage' in status:
                stage_emoji = {
                    'infant': '👶', 'child': '🧒', 'adolescent': '👦', 
                    'adult': '👨', 'expert': '🧠', 'sage': '🎓'
                }
                
                current_stage = status['current_stage']
                emoji = stage_emoji.get(current_stage, '🤖')
                
                st.markdown(f"**System Status:** {emoji} {current_stage.title()}")
                st.markdown(f"**Age:** {status.get('system_age_days', 0)} days")
                st.markdown(f"**Success Rate:** {status.get('success_rate', 0):.1f}%")
                
                # Progress bar for stage progression
                stage_progress = status.get('stage_progress', 0)
                st.progress(stage_progress / 100)
                st.markdown(f"Stage progress: {stage_progress:.1f}%")
                
            else:
                st.warning("⚠️ Unable to fetch system status")
                
        except Exception as e:
            st.error(f"❌ Error fetching status: {str(e)}")
    
    def render_dashboard_page(self):
        """Render main dashboard page"""
        st.title("📊 Evolution AI Dashboard")
        st.markdown("Live monitoring of AI learning and evolution process")
        
        # Fetch latest data
        try:
            with st.spinner("🔄 Loading evolution data..."):
                evolution_status = self.api_client.get_evolution_status()
                learning_history = self.api_client.get_learning_history(days=7)
                evolution_metrics = self.api_client.get_evolution_metrics()
                
            self.last_update = datetime.now().strftime("%H:%M:%S")
            
            # Evolution Panel
            render_evolution_panel(evolution_status)
            
            # Metrics Charts
            render_metrics_charts(evolution_metrics, learning_history)
            
            # Learning Table
            render_learning_table(learning_history)
            
            # Quick actions
            self.render_quick_actions()
            
        except Exception as e:
            st.error(f"❌ Error loading dashboard: {str(e)}")
            logger.error(f"Dashboard error: {str(e)}")
    
    def render_chat_page(self):
        """Render chat interface page"""
        render_chat_interface(self.api_client)
    
    def render_knowledge_page(self):
        """Render knowledge browser page"""
        st.title("🔍 Knowledge Browser")
        st.markdown("Explore what the AI has learned")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.subheader("Filters")
            category = st.selectbox(
                "Category",
                ["All", "Technology", "Science", "History", "Culture", "Other"]
            )
            
            date_range = st.selectbox(
                "Time Range",
                ["Last 7 days", "Last 30 days", "Last 90 days", "All time"]
            )
            
            confidence_threshold = st.slider(
                "Confidence Threshold",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1
            )
            
            if st.button("🔍 Search Knowledge"):
                with st.spinner("Searching..."):
                    # This would integrate with knowledge search API
                    pass
        
        with col2:
            st.subheader("Knowledge Base")
            
            # Mock knowledge items - in real implementation, fetch from API
            knowledge_items = [
                {
                    "title": "Machine Learning Basics",
                    "content": "Supervised learning uses labeled data...",
                    "category": "Technology",
                    "confidence": 0.95,
                    "learned_date": "2024-01-15"
                },
                {
                    "title": "Quantum Physics Principles", 
                    "content": "Quantum entanglement describes...",
                    "category": "Science",
                    "confidence": 0.88,
                    "learned_date": "2024-01-14"
                }
            ]
            
            for item in knowledge_items:
                with st.expander(f"📚 {item['title']} ({item['category']})"):
                    st.markdown(f"**Content:** {item['content']}")
                    st.markdown(f"**Confidence:** {item['confidence']:.2f}")
                    st.markdown(f"**Learned:** {item['learned_date']}")
    
    def render_admin_page(self):
        """Render admin panel page"""
        render_admin_panel(self.api_client, self.notification_manager)
    
    def render_notifications_page(self):
        """Render notifications management page"""
        st.title("📱 Notifications")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Notification Settings")
            
            # Notification channels
            st.markdown("#### 🔔 Notification Channels")
            email_notifications = st.checkbox("Email Notifications", value=True)
            telegram_notifications = st.checkbox("Telegram Notifications", value=False)
            dashboard_notifications = st.checkbox("Dashboard Notifications", value=True)
            
            # Notification triggers
            st.markdown("#### ⚡ Notification Triggers")
            st.checkbox("Learning Session Started", value=True)
            st.checkbox("Learning Session Completed", value=True)
            st.checkbox("Evolution Stage Changed", value=True)
            st.checkbox("System Errors", value=True)
            st.checkbox("Proposals Need Review", value=True)
            st.checkbox("Community Votes Threshold Reached", value=True)
            
            if st.button("💾 Save Notification Settings"):
                st.success("Notification settings saved!")
        
        with col2:
            st.subheader("Recent Notifications")
            
            # Mock notifications
            notifications = [
                {"type": "success", "message": "Daily learning session completed", "time": "2 hours ago"},
                {"type": "info", "message": "New proposals need review", "time": "4 hours ago"},
                {"type": "warning", "message": "Community vote threshold reached", "time": "1 day ago"},
            ]
            
            for notification in notifications:
                emoji = "✅" if notification["type"] == "success" else "ℹ️" if notification["type"] == "info" else "⚠️"
                st.markdown(f"{emoji} {notification['message']}")
                st.caption(notification["time"])
    
    def render_quick_actions(self):
        """Render quick action buttons"""
        st.markdown("---")
        st.subheader("🚀 Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎯 Run Learning Session", use_container_width=True):
                with st.spinner("Running learning session..."):
                    try:
                        result = self.api_client.run_daily_learning_session()
                        if result.get('success'):
                            st.success("Learning session completed successfully!")
                            self.notification_manager.send_notification(
                                "Learning Session Completed",
                                f"Session {result.get('session_id')} finished with {result.get('proposals_processed', 0)} proposals"
                            )
                        else:
                            st.error("Learning session failed!")
                    except Exception as e:
                        st.error(f"Error running session: {str(e)}")
        
        with col2:
            if st.button("🔍 Self Assessment", use_container_width=True):
                with st.spinner("Performing self-assessment..."):
                    try:
                        assessment = self.api_client.self_assess()
                        st.success(f"Assessment completed: {assessment.get('overall_health', 'Unknown')}")
                    except Exception as e:
                        st.error(f"Assessment failed: {str(e)}")
        
        with col3:
            if st.button("📊 Update Metrics", use_container_width=True):
                st.rerun()
    
    def check_notifications(self):
        """Check and display new notifications"""
        current_time = datetime.now()
        if (current_time - st.session_state.last_notification_check).seconds > 300:  # 5 minutes
            try:
                # Check for pending reviews
                pending_reviews = self.api_client.get_pending_review_proposals()
                if pending_reviews:
                    st.warning(f"⚠️ {len(pending_reviews)} proposals need review!")
                
                # Update last check time
                st.session_state.last_notification_check = current_time
                
            except Exception as e:
                logger.error(f"Notification check failed: {str(e)}")
    
    def run(self):
        """Main application runner"""
        self.initialize_session_state()
        self.render_sidebar()
        
        # Check for notifications
        self.check_notifications()
        
        # Render selected page
        if st.session_state.page == "dashboard":
            self.render_dashboard_page()
        elif st.session_state.page == "chat":
            self.render_chat_page()
        elif st.session_state.page == "knowledge":
            self.render_knowledge_page()
        elif st.session_state.page == "admin":
            self.render_admin_page()
        elif st.session_state.page == "notifications":
            self.render_notifications_page()
        
        # Auto-refresh logic
        if st.session_state.auto_refresh:
            time.sleep(REFRESH_INTERVAL)
            st.rerun()

def main():
    """Main function"""
    try:
        dashboard = EvolutionDashboard()
        dashboard.run()
    except Exception as e:
        st.error(f"🚨 Application error: {str(e)}")
        logger.error(f"Application crashed: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()