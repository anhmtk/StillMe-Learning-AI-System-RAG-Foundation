"""
StillMe IPC Simple Learning Dashboard
====================================

A simple, clean dashboard without complex imports to avoid issues.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time

# Page config
st.set_page_config(
    page_title="StillMe IPC Learning Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    text-align: center;
    color: #1f77b4;
    font-size: 2.5rem;
    margin-bottom: 2rem;
}

.status-indicators {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid #dee2e6;
}

.learning-session-card {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid #dee2e6;
    margin-bottom: 0.5rem;
    cursor: pointer;
    transition: all 0.3s ease;
}

.learning-session-card:hover {
    background-color: #e9ecef;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.session-details {
    background-color: #ffffff;
    padding: 1.5rem;
    border-radius: 8px;
    border: 1px solid #dee2e6;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.quick-report {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid #dee2e6;
}

.session-selected {
    background-color: #e3f2fd !important;
    border: 2px solid #2196f3 !important;
}

.session-button {
    transition: all 0.3s ease;
    margin-bottom: 0.5rem;
}

.session-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

class SimpleDashboard:
    def __init__(self):
        """Initialize the simple dashboard"""
        # Initialize session state
        if 'selected_session' not in st.session_state:
            st.session_state.selected_session = 'Machine Learning Basics'
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = False

    def render_header(self):
        """Render dashboard header"""
        st.markdown('<h1 class="main-header">🧠 StillMe IPC Learning Dashboard</h1>', unsafe_allow_html=True)

        col1, col2 = st.columns([3, 1])

        with col1:
            # Get pending proposals from session state and database
            sample_proposals = st.session_state.get('sample_proposals', [])
            
            # Also get proposals from database
            try:
                from stillme_core.learning.proposals_manager import ProposalsManager
                manager = ProposalsManager()
                db_proposals = manager.get_pending_proposals(limit=10)
                pending_count = len(sample_proposals) + len(db_proposals)
            except Exception as e:
                # Fallback: try to get count directly from database
                try:
                    import sqlite3
                    from stillme_core.learning.proposals_manager import ProposalsManager
                    manager = ProposalsManager()
                    with sqlite3.connect(manager.db_path) as conn:
                        cursor = conn.execute("SELECT COUNT(*) FROM proposals WHERE status = 'pending'")
                        db_count = cursor.fetchone()[0]
                        pending_count = len(sample_proposals) + db_count
                except:
                    pending_count = len(sample_proposals)
            
            new_today = len([p for p in sample_proposals if p.get('created_today', False)])

            if st.button(
                f"📋 **{pending_count} Pending Proposals**\n\n"
                f"🆕 {new_today} new today\n"
                f"⏰ Click to review & approve",
                key="pending_proposals_button",
                help="Click to view and manage pending learning proposals",
                use_container_width=True
            ):
                st.session_state.show_pending_details = True
                st.rerun()
            
            # Show status message
            if st.session_state.get('show_pending_details', False):
                st.info("📋 Reviewing pending proposals")
            else:
                st.info("ℹ️ Click the button above to view pending proposals")

        with col2:
            st.markdown('<div class="status-indicators">', unsafe_allow_html=True)
            st.markdown("### 📊 Status")

            # Mock stats
            approved_count = 3
            completed_count = 0

            st.markdown(f"✅ **Approved:** {approved_count} (+0)")
            st.markdown(f"🎓 **Completed:** {completed_count} (+0)")
            st.markdown("⚡ **Learning:** Active")

            # Learning progress bar
            if approved_count > 0:
                progress = 0.75  # 75% completion
                st.progress(progress)
                st.markdown(f"**Progress:** {progress*100:.0f}% complete")
            else:
                st.markdown("**Status:** Waiting for approval")
                st.info("No approved proposals to learn from yet")
            
            st.markdown('</div>', unsafe_allow_html=True)

    def render_learning_section(self):
        """Render the main learning section with 3 columns"""
        st.markdown("---")
        st.markdown("## 📚 Learning Management")
        
        # Create 3 columns
        col_learning_list, col_learning_details, col_learning_report = st.columns([1, 2, 1])
        
        with col_learning_list:
            st.markdown("### 📚 Learning Sessions")
            
            # Learning sessions data - include approved proposals
            approved_proposals = st.session_state.get('approved_proposals', [])
            
            # Base sessions
            sessions = [
                {"name": "Python Fundamentals", "status": "✅ Completed", "progress": 100},
                {"name": "Data Structures", "status": "✅ Completed", "progress": 100},
                {"name": "Deep Learning", "status": "⏳ Pending", "progress": 0}
            ]
            
            # Add approved proposals as active learning sessions
            for proposal in approved_proposals:
                if proposal.get('status') == 'learning':
                    sessions.insert(0, {
                        "name": proposal['title'],
                        "status": "🔄 Learning",
                        "progress": 25,  # Start at 25% when approved
                        "proposal_id": proposal['id']
                    })
            
            for i, session in enumerate(sessions):
                is_selected = st.session_state.get('selected_session') == session['name']
                
                # Create session card with better styling
                button_style = "background-color: #e3f2fd;" if is_selected else ""
                
                if st.button(
                    f"**{session['name']}**\n"
                    f"{session['status']} - {session['progress']}%",
                    key=f"session_{i}",
                    help=f"Click to view details of: {session['name']}",
                    use_container_width=True
                ):
                    st.session_state.selected_session = session['name']
                    st.rerun()
                
                # Show selection indicator
                if is_selected:
                    st.markdown("👈 **Selected** - Click to view details")
        
        with col_learning_details:
            st.markdown("### 📄 Session Details")
            
            # Get selected session - default to first approved proposal if available
            approved_proposals = st.session_state.get('approved_proposals', [])
            if approved_proposals and not st.session_state.get('selected_session'):
                # Auto-select first approved proposal
                st.session_state.selected_session = approved_proposals[0]['title']
            
            selected_session = st.session_state.get('selected_session', 'Python Fundamentals')
            
            # Check if selected session is an approved proposal
            selected_proposal = None
            for proposal in approved_proposals:
                if proposal['title'] == selected_session:
                    selected_proposal = proposal
                    break
            
            if selected_proposal:
                st.markdown("**🔄 Active Learning Session:**")
                st.markdown(f"• **Topic:** {selected_proposal['title']}")
                st.markdown(f"• **Started:** {selected_proposal['approved_at']}")
                st.markdown(f"• **Progress:** 25% (Just started)")
                st.markdown(f"• **Quality Score:** {selected_proposal['quality_score']:.2f}")
                st.markdown(f"• **Estimated Duration:** {selected_proposal['estimated_duration']} minutes")

                st.markdown("**📚 Learning Content:**")
                st.markdown(f"• {selected_proposal['description']}")
                
                st.markdown("**🎯 Learning Objectives:**")
                st.markdown("• Understanding core concepts")
                st.markdown("• Practical application")
                st.markdown("• Skill development")
                
                # Progress bar for this session
                st.progress(0.25)
                st.markdown("*StillMe IPC is actively learning this content...*")
            
            elif selected_session == "Python Fundamentals":
                st.markdown("**✅ Completed Session:**")
                st.markdown("• Topic: Python Programming")
                st.markdown("• Duration: 3 hours")
                st.markdown("• Completed: 2 days ago")
                st.markdown("• Quality Score: 0.92")

                st.markdown("**Skills Learned:**")
                st.markdown("• Python syntax ✅")
                st.markdown("• Data manipulation ✅")
                st.markdown("• Functions & classes ✅")
                st.markdown("• Error handling ✅")
            
            elif selected_session == "Data Structures":
                st.markdown("**✅ Completed Session:**")
                st.markdown("• Topic: Data Structures")
                st.markdown("• Duration: 2.5 hours")
                st.markdown("• Completed: 1 day ago")
                st.markdown("• Quality Score: 0.88")

                st.markdown("**Skills Learned:**")
                st.markdown("• Arrays & Lists ✅")
                st.markdown("• Stacks & Queues ✅")
                st.markdown("• Trees & Graphs ✅")
                st.markdown("• Algorithm complexity ✅")
            
            else:
                # Check if this is a pending session (Deep Learning)
                if selected_session == "Deep Learning":
                    st.markdown("**⏳ Pending Session:**")
                    st.markdown(f"• **Topic:** {selected_session}")
                    st.markdown("• **Status:** Waiting to start")
                    st.markdown("• **Progress:** 0%")
                    st.markdown("• **Prerequisites:** Complete previous sessions")
                else:
                    st.markdown("**ℹ️ No Active Learning:**")
                    st.markdown("• **Status:** No proposals approved yet")
                    st.markdown("• **Action:** Go to 'Learning Proposals' tab to approve proposals")
                    st.markdown("• **Next:** Approved proposals will appear here as learning sessions")
        
        with col_learning_report:
            st.markdown("### 📊 Quick Report")
            
            # Quick report data
            st.markdown("**📈 Today's Progress:**")
            st.markdown("• Sessions: 2/4")
            st.markdown("• Time: 3.5h")
            st.markdown("• Quality: 0.89")
            
            st.markdown("**🎯 Next Steps:**")
            st.markdown("• Complete ML basics")
            st.markdown("• Start Deep Learning")
            st.markdown("• Review Python")
            
            # Quick link to Full Learning Report
            if st.button("📊 View Full Learning Report", key="quick_report_button"):
                st.info("💡 Click on the '📊 Learning Report' tab above to view the complete learning report!")

    def render_sidebar(self):
        """Render sidebar filters"""
        st.sidebar.markdown("## 🔧 Filters & Controls")
        
        # Date range
        st.sidebar.markdown("### 📅 Date Range")
        days = st.sidebar.selectbox(
            "Select period:",
            [7, 14, 30, 90],
            index=1,
            help="Select the time period for data analysis"
        )
        
        # Proposal status
        st.sidebar.markdown("### 📄 Proposal Status")
        statuses = st.sidebar.multiselect(
            "Select statuses:",
            ["pending", "approved", "rejected", "completed"],
            default=["pending", "approved"],
            help="Filter proposals by status"
        )
        
        # Priority
        st.sidebar.markdown("### ⚡ Priority")
        priorities = st.sidebar.multiselect(
            "Select priorities:",
            ["low", "medium", "high", "critical"],
            default=["high", "critical"],
            help="Filter proposals by priority"
        )
        
        # Sources
        st.sidebar.markdown("### 📚 Sources")
        sources = st.sidebar.multiselect(
            "Select sources:",
            ["community", "ai_generated", "manual", "imported"],
            default=["community", "ai_generated"],
            help="""Filter proposals by source:
            • **Community**: Đề xuất từ cộng đồng opensource
            • **AI Generated**: Đề xuất tự động từ AI
            • **Manual**: Bạn tự tạo đề xuất
            • **Imported**: Import từ file/tài liệu bên ngoài"""
        )
        
        # Auto-refresh
        st.sidebar.markdown("### 🔄 Auto-Refresh")
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
        
        # Automation Control
        st.sidebar.markdown("### 🤖 Automation Control")
        
        # Initialize automation state
        if 'automation_enabled' not in st.session_state:
            st.session_state.automation_enabled = False
        
        # Automation toggle
        automation_enabled = st.sidebar.checkbox(
            "Enable Auto-Proposals",
            value=st.session_state.automation_enabled,
            help="When enabled, StillMe IPC will automatically create learning proposals every 30 minutes"
        )
        
        if automation_enabled != st.session_state.automation_enabled:
            st.session_state.automation_enabled = automation_enabled
            
            # Update smart automation config
            try:
                import json
                from pathlib import Path
                
                config_file = Path("artifacts/automation_config.json")
                config_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Load existing config or create new
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                else:
                    config = {
                        "enabled": False,
                        "max_proposals_per_hour": 2,
                        "max_proposals_per_day": 10,
                        "proposal_interval_minutes": 30,
                        "last_proposal_time": None,
                        "proposals_created_today": 0,
                        "proposals_created_this_hour": 0,
                        "last_reset_date": datetime.now().strftime("%Y-%m-%d")
                    }
                
                # Update enabled status
                config["enabled"] = automation_enabled
                
                # Save config
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)
                
                # Also save to session file for smart automation
                session_file = Path("artifacts/dashboard_session.json")
                session_file.parent.mkdir(parents=True, exist_ok=True)
                with open(session_file, 'w') as f:
                    json.dump({"automation_enabled": automation_enabled}, f, indent=2)
                
                if automation_enabled:
                    st.sidebar.success("🤖 Automation enabled! StillMe IPC will create proposals automatically.")
                else:
                    st.sidebar.warning("⏸️ Automation disabled. No new auto-proposals will be created.")
                    
            except Exception as e:
                st.sidebar.error(f"❌ Failed to update automation config: {e}")
            
            st.rerun()
        
        # Automation status
        if st.session_state.automation_enabled:
            st.sidebar.info("🟢 **Automation Active**\n\nStillMe IPC is creating proposals automatically.")
        else:
            st.sidebar.info("🔴 **Automation Inactive**\n\nStillMe IPC will not create proposals automatically.")
        
        # Create sample proposal button
        if st.sidebar.button("📝 Create Sample Proposal", type="secondary"):
            # Add to session state
            if 'sample_proposals' not in st.session_state:
                st.session_state.sample_proposals = []
            
            # Create new sample proposal
            new_proposal = {
                "id": f"sample_{len(st.session_state.sample_proposals) + 1}",
                "title": f"Sample Proposal {len(st.session_state.sample_proposals) + 1}",
                "description": f"This is a sample learning proposal #{len(st.session_state.sample_proposals) + 1}",
                "quality_score": 0.8 + (len(st.session_state.sample_proposals) * 0.05),
                "estimated_duration": 60 + (len(st.session_state.sample_proposals) * 30),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            st.session_state.sample_proposals.append(new_proposal)
            st.success(f"Sample proposal created! Total: {len(st.session_state.sample_proposals)}")
            st.rerun()
        
        # Create auto proposal button
        if st.sidebar.button("🤖 Create Auto Proposal", type="primary"):
            try:
                from stillme_core.learning.proposals_manager import ProposalsManager
                manager = ProposalsManager()
                
                # Create an automatic proposal
                proposal_data = {
                    "title": "Advanced Python Programming",
                    "description": "Learn advanced Python concepts including decorators, generators, and async programming",
                    "learning_objectives": [
                        "Master Python decorators and their applications",
                        "Understand generator functions and memory efficiency",
                        "Learn async/await programming patterns"
                    ],
                    "prerequisites": [
                        "Basic Python knowledge",
                        "Understanding of functions and classes"
                    ],
                    "expected_outcomes": [
                        "Write efficient Python code using advanced features",
                        "Implement decorators for code reuse",
                        "Create async applications"
                    ],
                    "estimated_duration": 120,
                    "quality_score": 0.88,
                    "source": "ai_generated",
                    "priority": "high",
                    "risk_assessment": {
                        "complexity": "medium",
                        "time_commitment": "high",
                        "prerequisites": "medium",
                        "practical_value": "high"
                    }
                }
                
                proposal = manager.create_proposal(**proposal_data)
                st.success(f"✅ Auto proposal created: {proposal.title}")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Failed to create auto proposal: {e}")
        
        return {
            'days': days,
            'statuses': statuses,
            'priorities': priorities,
            'sources': sources,
            'auto_refresh': auto_refresh,
            'refresh_interval': refresh_interval
        }

    def render_pending_proposals_details(self):
        """Render detailed pending proposals view"""
        st.markdown("## 📋 Pending Proposals - Review & Approve")

        # Back button
        if st.button("← Back to Dashboard", key="back_to_dashboard"):
            st.session_state.show_pending_details = False
            st.rerun()

        st.markdown("---")

        # Get proposals from session state and database
        sample_proposals = st.session_state.get('sample_proposals', [])
        
        # Also get proposals from database
        try:
            from stillme_core.learning.proposals_manager import ProposalsManager
            manager = ProposalsManager()
            db_proposals = manager.get_pending_proposals(limit=10)
            
            # Convert database proposals to session state format
            for db_proposal in db_proposals:
                # Handle None values safely
                created_at = db_proposal.created_at
                if created_at:
                    created_at_str = created_at.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    created_at_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                proposal_data = {
                    "id": db_proposal.id or f"db_{len(sample_proposals) + 1}",
                    "title": db_proposal.title or "Untitled Proposal",
                    "description": db_proposal.description or "No description available",
                    "quality_score": float(db_proposal.quality_score) if db_proposal.quality_score else 0.5,
                    "estimated_duration": int(db_proposal.estimated_duration) if db_proposal.estimated_duration else 60,
                    "created_at": created_at_str
                }
                sample_proposals.append(proposal_data)
        except Exception as e:
            # Try to get basic count from database without parsing complex data
            try:
                import sqlite3
                from stillme_core.learning.proposals_manager import ProposalsManager
                manager = ProposalsManager()
                
                with sqlite3.connect(manager.db_path) as conn:
                    cursor = conn.execute("SELECT id, title, description, quality_score, estimated_duration, created_at FROM proposals WHERE status = 'pending' LIMIT 10")
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        proposal_data = {
                            "id": row[0] or f"db_{len(sample_proposals) + 1}",
                            "title": row[1] or "Untitled Proposal",
                            "description": row[2] or "No description available",
                            "quality_score": float(row[3]) if row[3] else 0.5,
                            "estimated_duration": int(row[4]) if row[4] else 60,
                            "created_at": row[5] or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        sample_proposals.append(proposal_data)
                        
            except Exception as e2:
                st.warning(f"Could not load database proposals: {e}")
                # Try to get basic count from database
                try:
                    import sqlite3
                    with sqlite3.connect(manager.db_path) as conn:
                        cursor = conn.execute("SELECT COUNT(*) FROM proposals WHERE status = 'pending'")
                        count = cursor.fetchone()[0]
                        if count > 0:
                            st.info(f"Found {count} pending proposals in database, but couldn't load details.")
                except:
                    pass
        
        # Use sample_proposals as proposals
        proposals = sample_proposals
        
        if not proposals:
            st.info("No pending proposals found. Create a sample proposal using the sidebar button.")
            return

        # Create two columns: List on left, Details on right
        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("### 📝 Proposals List")
            
            # Add explanation of icons and metrics
            with st.expander("ℹ️ What do these numbers mean?"):
                st.markdown("""
                **📊 Understanding Proposal Metrics:**
                
                **⭐ Quality Score (0.91, 0.92):**
                - Range: 0.0 to 1.0 (higher is better)
                - 0.9+ = Excellent quality
                - 0.8-0.9 = Good quality  
                - 0.7-0.8 = Average quality
                - <0.7 = Needs improvement
                
                **⏱️ Duration (180min, 240min):**
                - Estimated time to complete learning
                - 180min = 3 hours
                - 240min = 4 hours
                - Based on content complexity
                
                **📅 Created Date:**
                - When the proposal was generated
                - Format: YYYY-MM-DDTHH:MM:SS
                - Helps track proposal freshness
                """)
            
            # Initialize selected proposal in session state
            if 'selected_proposal_id' not in st.session_state:
                st.session_state.selected_proposal_id = proposals[0]['id'] if proposals else None

            # Display proposal list with individual approve/reject buttons
            for i, proposal in enumerate(proposals):
                is_selected = st.session_state.get('selected_proposal_id') == proposal['id']
                
                # Create proposal card with approve/reject buttons
                is_selected = st.session_state.get('selected_proposal_id') == proposal['id']
                container_style = "border: 2px solid #00ff00; background-color: #1a1a1a;" if is_selected else ""
                
                with st.container():
                    if is_selected:
                        st.markdown(f"**🟢 {proposal['title']}** *(Đang xem)*")
                    else:
                        st.markdown(f"**{proposal['title']}**")
                    st.write(f"📅 {proposal['created_at']}")
                    st.write(f"⭐ Quality: {proposal['quality_score']:.2f} | ⏱️ Duration: {proposal['estimated_duration']}min")
                    
                    # Approve/Reject buttons for each proposal
                    col_approve, col_reject, col_view = st.columns([1, 1, 1])
                    
                    with col_approve:
                        if st.button("✅ Approve", key=f"approve_{proposal['id']}", type="primary"):
                            try:
                                # Update database status to approved
                                from stillme_core.learning.proposals_manager import ProposalsManager
                                manager = ProposalsManager()
                                manager.approve_proposal(proposal['id'], "user")
                                
                                # Remove from session state
                                if 'sample_proposals' in st.session_state:
                                    st.session_state.sample_proposals = [p for p in st.session_state.sample_proposals if p['id'] != proposal['id']]
                                
                                # Add to approved proposals
                                if 'approved_proposals' not in st.session_state:
                                    st.session_state.approved_proposals = []
                                
                                approved_proposal = {
                                    **proposal,
                                    'status': 'learning',
                                    'approved_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                                st.session_state.approved_proposals.append(approved_proposal)
                                
                                st.success(f"✅ Approved: {proposal['title']}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Failed to approve: {e}")
                    
                    with col_reject:
                        if st.button("❌ Reject", key=f"reject_{proposal['id']}", type="secondary"):
                            try:
                                # Update database status to rejected
                                from stillme_core.learning.proposals_manager import ProposalsManager
                                manager = ProposalsManager()
                                manager.reject_proposal(proposal['id'], "user", "User rejected")
                                
                                # Remove from session state
                                if 'sample_proposals' in st.session_state:
                                    st.session_state.sample_proposals = [p for p in st.session_state.sample_proposals if p['id'] != proposal['id']]
                                
                                st.warning(f"❌ Rejected: {proposal['title']}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Failed to reject: {e}")
                    
                    with col_view:
                        if is_selected:
                            if st.button("👁️ Đang xem", key=f"view_{proposal['id']}", disabled=True):
                                pass
                        else:
                            if st.button("👁️ View", key=f"view_{proposal['id']}"):
                                st.session_state.selected_proposal_id = proposal['id']
                                st.session_state.show_proposal_details = True
                                st.success(f"✅ Đang xem: {proposal['title']}")
                                st.rerun()
                    
                    st.markdown("---")

        with col2:
            st.markdown("### 📄 Proposal Details")
            
            # Check if we should show proposal details
            if st.session_state.get('show_proposal_details', False):
                # Find selected proposal
                selected_proposal = None
                for proposal in proposals:
                    if proposal['id'] == st.session_state.get('selected_proposal_id'):
                        selected_proposal = proposal
                        break

                if selected_proposal:
                    # Show clear header with proposal being viewed
                    st.markdown(f"### 🟢 Đang xem: {selected_proposal['title']}")
                    st.markdown(f"**📋 Proposal ID:** `{selected_proposal['id'][:8]}...`")
                    st.markdown("---")

                    # Main info
                    col1, col2 = st.columns([1, 1])

                    with col1:
                        st.markdown("**📋 Basic Info:**")
                        st.write(f"**Source:** AI Generated")
                        st.write(f"**Priority:** High")
                        st.write(f"**Duration:** {selected_proposal['estimated_duration']} minutes")
                        st.write(f"**Quality Score:** {selected_proposal['quality_score']:.2f}")
                        st.write(f"**Created:** {selected_proposal['created_at']}")

                    with col2:
                        st.markdown("**📊 Risk Assessment:**")
                        st.write("**Complexity:** Medium")
                        st.write("**Time Commitment:** High")
                        st.write("**Prerequisites:** Medium")
                        st.write("**Practical Value:** High")

                    # Description
                    st.markdown("**📝 Description:**")
                    st.write(selected_proposal['description'])

                    # Learning Objectives
                    st.markdown("**🎯 Learning Objectives:**")
                    st.write("• Master advanced Python concepts")
                    st.write("• Understand decorators and generators")
                    st.write("• Learn async/await programming")
                    st.write("• Apply concepts in real projects")

                    # Close button
                    if st.button("❌ Close Details", key="close_details"):
                        st.session_state.show_proposal_details = False
                        st.rerun()

                    # Control info
                    st.info("💡 **Your Control:** You decide what StillMe IPC learns. Only approved content will be processed. All decisions are logged and auditable.")
                else:
                    st.warning("⚠️ Không tìm thấy proposal được chọn. Vui lòng click 'View' trên một proposal khác.")
            else:
                st.info("👈 **Hướng dẫn:** Click nút '👁️ View' trên bất kỳ proposal nào để xem chi tiết nội dung học tập.")
                st.markdown("**💡 Mẹo:** Proposal được chọn sẽ có dấu 🟢 và hiển thị '*(Đang xem)*'")

    def render_analytics(self):
        """Render analytics tab"""
        st.markdown("### 📊 Analytics")
        
        # Create metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Proposals", 12)
        with col2:
            st.metric("Pending", 3)
        with col3:
            st.metric("Approved", 3)
        with col4:
            st.metric("Completed", 0)
        
        # Status distribution
        status_data = {
            'Status': ['Pending', 'Approved', 'Rejected', 'Completed'],
            'Count': [3, 3, 1, 0]
        }
        
        df = pd.DataFrame(status_data)
        fig = px.pie(df, values='Count', names='Status', title='Proposal Status Distribution')
        st.plotly_chart(fig, use_container_width=True)

    def render_learning_curve(self, days):
        """Render learning curve tab"""
        st.markdown("### 📈 Learning Curve")
        
        # Generate sample learning data
        dates = pd.date_range(start=datetime.now() - timedelta(days=days), end=datetime.now(), freq='D')
        learning_data = {
            'Date': dates,
            'Knowledge_Score': [0.6 + 0.3 * (i / len(dates)) + 0.1 * (i % 3) for i in range(len(dates))],
            'Skills_Learned': [2 + i % 5 for i in range(len(dates))],
            'Time_Spent': [30 + i * 2 for i in range(len(dates))]
        }
        
        df = pd.DataFrame(learning_data)
        
        # Knowledge score over time
        fig1 = px.line(df, x='Date', y='Knowledge_Score', title='Knowledge Score Over Time')
        st.plotly_chart(fig1, use_container_width=True)
        
        # Skills learned
        fig2 = px.bar(df, x='Date', y='Skills_Learned', title='Skills Learned Per Day')
        st.plotly_chart(fig2, use_container_width=True)

    def render_full_learning_report(self):
        """Render full learning report tab"""
        st.markdown("### 📊 Full Learning Report")
        
        # Top row: Knowledge and Skills side by side
        top_row1, top_row2 = st.columns([3, 2])
        
        with top_row1:
            st.markdown("**📚 Completed Topics:**")
            st.markdown("• **Machine Learning Fundamentals** ✅ - Understanding basic ML algorithms, practicing with Python and scikit-learn")
            st.markdown("• **Python Programming** ✅ - Basic Python syntax, data processing with pandas, visualization with matplotlib")
            
            st.markdown("**📈 Learning Statistics:**")
            st.markdown("• **Total Learning Time:** 4.5 hours | **Completed Topics:** 2 | **Average Quality Score:** 0.87 | **Success Rate:** 95%")
        
        with top_row2:
            st.markdown("**🛠️ Skills Acquired:**")
            st.markdown("**Machine Learning:** Linear Regression • Decision Trees • Random Forest")
            st.markdown("**Python:** Data Manipulation • Statistical Analysis • Data Visualization")
            st.markdown("**Tools:** scikit-learn • pandas • matplotlib")
        
        # Progress bars in horizontal layout
        st.markdown("**📊 Learning Progress by Topic:**")
        progress_row1, progress_row2, progress_row3, progress_row4 = st.columns(4)
        
        with progress_row1:
            st.markdown("**Machine Learning:**")
            st.progress(1.0)
            st.markdown("*100% completed*")
        
        with progress_row2:
            st.markdown("**Python Programming:**")
            st.progress(1.0)
            st.markdown("*100% completed*")
        
        with progress_row3:
            st.markdown("**Data Science:**")
            st.progress(0.75)
            st.markdown("*75% completed*")
        
        with progress_row4:
            st.markdown("**Deep Learning:**")
            st.progress(0.25)
            st.markdown("*25% completed*")
        
        # Next learning suggestions in horizontal layout
        st.markdown("**🎯 Suggested Next Learning:**")
        next_row1, next_row2, next_row3, next_row4 = st.columns(4)
        
        with next_row1:
            st.markdown("**Deep Learning with TensorFlow**")
            st.markdown("*Expand ML knowledge*")
        
        with next_row2:
            st.markdown("**Natural Language Processing**")
            st.markdown("*Process natural language*")
        
        with next_row3:
            st.markdown("**Computer Vision**")
            st.markdown("*Image recognition*")
        
        with next_row4:
            st.markdown("**Time Series Analysis**")
            st.markdown("*Analyze time series data*")

    def render_security_privacy(self):
        """Render security and privacy tab"""
        st.markdown("### 🔒 Security & Privacy")
        
        st.info("""
        **Your learning data is protected:**
        - All proposals require your explicit approval
        - No one can modify StillMe IPC without your permission
        - Community can only suggest content, not control learning
        - All actions are logged and auditable
        - Personal data is encrypted and secure
        """)
        
        st.markdown("### 🛡️ Access Control")
        col1, col2 = st.columns(2)
        
        with col1:
            st.success("✅ You have full control")
            st.write("• Approve/reject learning proposals")
            st.write("• Control what StillMe IPC learns")
            st.write("• Monitor all learning activities")
        
        with col2:
            st.warning("⚠️ Community limitations")
            st.write("• Can only suggest content")
            st.write("• Cannot access personal data")
            st.write("• Cannot modify learning behavior")

    def run(self):
        """Run the simple dashboard"""
        # Render header
        self.render_header()
        
        # Render sidebar
        filters = self.render_sidebar()
        
        # Auto-refresh logic
        if st.session_state.auto_refresh and filters['refresh_interval']:
            time.sleep(filters['refresh_interval'])
            st.rerun()
        
        # Check if we should show pending details
        if st.session_state.get('show_pending_details', False):
            self.render_pending_proposals_details()
        else:
            # Render main learning section
            self.render_learning_section()
            
            # Render tabs
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                "📋 Learning Proposals",
                "👑 Founder Mode",
                "📊 Analytics", 
                "📈 Learning Curve",
                "📊 Learning Report",
                "🔒 Security & Privacy"
            ])
            
            with tab1:
                st.markdown("### 📋 Learning Proposals")
                st.info("This is a demo dashboard. In the real system, this would show actual learning proposals.")
            
            with tab2:
                self.render_founder_mode()
            
            with tab3:
                self.render_analytics()
            
            with tab4:
                self.render_learning_curve(filters['days'])
            
            with tab5:
                self.render_full_learning_report()
            
            with tab6:
                self.render_security_privacy()
        
        # Footer
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🧠 StillMe IPC**")
            st.markdown("Intelligent Personal Companion - Self-evolving AI learning system")
        
        with col2:
            st.markdown("**📊 Dashboard v2.0**")
            st.markdown("Enhanced Learning Management System")
        
        with col3:
            st.markdown("**🔒 Your Control**")
            st.markdown("You decide what StillMe IPC learns")

    def render_founder_mode(self):
        """Render founder mode section"""
        st.markdown("### 👑 Founder Mode")
        st.info("👑 **Founder Mode**: Add knowledge directly - AUTO-APPROVED (no need to approve/reject)")
        
        # Founder knowledge input form
        with st.form("founder_knowledge_form"):
            st.markdown("#### 📚 Add New Knowledge")
            
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("📝 Knowledge Title", placeholder="e.g., Advanced AI Ethics")
                priority = st.selectbox("⚡ Priority", ["high", "critical", "medium", "low"], index=0)
                
            with col2:
                source_url = st.text_input("🔗 Source URL (optional)", placeholder="https://example.com/article")
                content_type = st.selectbox("📄 Content Type", ["text", "url", "image"], index=0)
            
            description = st.text_area("📖 Knowledge Description", 
                                     placeholder="Describe what StillMe should learn from this knowledge...",
                                     height=100)
            
            submitted = st.form_submit_button("👑 Add Founder Knowledge (AUTO-APPROVED)")
            
            if submitted:
                if title and description:
                    try:
                        # Import founder input
                        import sys
                        import os
                        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                        
                        from scripts.founder_knowledge_input import FounderKnowledgeInput
                        
                        founder_input = FounderKnowledgeInput()
                        proposal = founder_input.add_founder_knowledge(
                            title=title,
                            description=description,
                            source_url=source_url if source_url else None,
                            content_type=content_type,
                            priority=priority
                        )
                        
                        if proposal:
                            st.success(f"✅ Founder knowledge added and AUTO-APPROVED: {title}")
                            st.info(f"🆔 Proposal ID: {proposal.id}")
                            st.info("💡 StillMe IPC will start learning immediately!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to add founder knowledge")
                            
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                else:
                    st.error("❌ Please fill in title and description")
        
        # Show recent founder knowledge
        st.markdown("#### 📋 Recent Founder Knowledge")
        try:
            # Load recent founder knowledge from artifacts
            founder_dir = Path("artifacts/founder_knowledge")
            if founder_dir.exists():
                founder_files = list(founder_dir.glob("founder_*.json"))
                if founder_files:
                    # Sort by modification time (newest first)
                    founder_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    
                    for i, file_path in enumerate(founder_files[:5]):  # Show last 5
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                founder_data = json.load(f)
                            
                            with st.expander(f"👑 {founder_data.get('title', 'Untitled')} - {founder_data.get('created_at', 'Unknown date')[:10]}"):
                                st.markdown(f"**📝 Description:** {founder_data.get('description', 'No description')[:200]}...")
                                if founder_data.get('source_url'):
                                    st.markdown(f"**🔗 Source:** {founder_data['source_url']}")
                                st.markdown(f"**🆔 Proposal ID:** {founder_data.get('proposal_id', 'Unknown')[:8]}...")
                                st.markdown(f"**✅ Status:** AUTO-APPROVED (Founder Mode)")
                        except Exception as e:
                            st.error(f"Error loading founder knowledge: {e}")
                else:
                    st.info("No founder knowledge added yet")
            else:
                st.info("No founder knowledge directory found")
        except Exception as e:
            st.error(f"Error loading founder knowledge: {e}")

# Main execution
if __name__ == "__main__":
    dashboard = SimpleDashboard()
    dashboard.run()
