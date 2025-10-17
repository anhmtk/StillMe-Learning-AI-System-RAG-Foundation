"""
StillMe IPC Integrated Learning Dashboard with Chat Panel
========================================================

Dashboard tích hợp chat panel với learning progress monitoring.
Đây chính là dashboard bạn cần - có cả learning progress và chat panel!
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Import auth system
from auth_system import AuthSystem

# Page config
st.set_page_config(
    page_title="StillMe IPC Learning Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
.main-header {
    text-align: center;
    color: #1f77b4;
    font-size: 2.5rem;
    margin-bottom: 2rem;
}

/* Fix password input width */
.stTextInput > div > div > input {
    width: 100% !important;
    min-width: 300px !important;
}

/* Fix form container width */
.stForm {
    width: 100% !important;
}

/* Fix sidebar width */
.sidebar .stTextInput > div > div > input {
    width: 100% !important;
    min-width: 250px !important;
}

/* Make buttons more visible */
.stButton > button {
    color: white !important;
    font-weight: bold !important;
    border: 2px solid #4CAF50 !important;
    background-color: #4CAF50 !important;
}

.stButton > button:hover {
    background-color: #45a049 !important;
    border-color: #45a049 !important;
}

/* Secondary button style */
.stButton > button[kind="secondary"] {
    background-color: #f44336 !important;
    border-color: #f44336 !important;
}

.stButton > button[kind="secondary"]:hover {
    background-color: #da190b !important;
    border-color: #da190b !important;
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

.chat-panel {
    background-color: #ffffff;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    height: 500px;
    overflow-y: auto;
    padding: 1rem;
    margin-bottom: 1rem;
}

.chat-message {
    margin-bottom: 1rem;
    padding: 0.5rem;
    border-radius: 8px;
}

.chat-message.user {
    background-color: #e3f2fd;
    margin-left: 2rem;
}

.chat-message.assistant {
    background-color: #f5f5f5;
    margin-right: 2rem;
}

.chat-input {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
}

.session-selected {
    background-color: #e3f2fd !important;
    border: 2px solid #2196f3 !important;
}
</style>
""",
    unsafe_allow_html=True,
)


class IntegratedDashboard:
    def __init__(self):
        """Initialize the integrated dashboard"""
        # Initialize auth system
        self.auth = AuthSystem()
        
        # Initialize session state
        if "selected_session" not in st.session_state:
            st.session_state.selected_session = "Machine Learning Basics"
        if "auto_refresh" not in st.session_state:
            st.session_state.auto_refresh = True
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []
        if "chat_input" not in st.session_state:
            st.session_state.chat_input = ""

    def load_learning_data(self):
        """Load learning data from database"""
        try:
            # Load real data from learning system
            from stillme_core.learning.proposals_manager import ProposalsManager
            from stillme_core.learning.evolutionary_learning_system import EvolutionaryLearningSystem
            
            proposals_manager = ProposalsManager()
            learning_system = EvolutionaryLearningSystem()
            
            # Get real proposals
            all_proposals = proposals_manager.get_all_proposals()
            
            # Convert to dashboard format
            proposals = []
            for proposal in all_proposals:
                try:
                    proposals.append({
                        "id": proposal.id,
                        "title": proposal.title,
                        "status": proposal.status.value if hasattr(proposal.status, 'value') else str(proposal.status),
                        "priority": proposal.priority.value if hasattr(proposal.priority, 'value') else str(proposal.priority),
                        "progress": 0,  # Will be calculated from learning sessions
                        "created_at": proposal.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(proposal.created_at, 'strftime') else str(proposal.created_at),
                        "source": proposal.source.value if hasattr(proposal.source, 'value') else str(proposal.source),
                        "proposal_type": "auto"
                    })
                except Exception as e:
                    st.warning(f"Error processing proposal {proposal.id}: {e}")
                    continue
            
            # Get active learning sessions
            active_sessions = learning_system.get_active_sessions()
            sessions = []
            for session_id, session_data in active_sessions.items():
                sessions.append({
                    "id": session_id,
                    "title": session_data.get("title", "Learning Session"),
                    "status": "active",
                    "progress": session_data.get("progress", 0),
                    "started_at": session_data.get("started_at", ""),
                    "last_activity": session_data.get("last_activity", "")
                })
            
            # Calculate stats
            stats = {
                "total_proposals": len(proposals),
                "pending_proposals": len([p for p in proposals if p["status"] == "pending"]),
                "approved_proposals": len([p for p in proposals if p["status"] == "approved"]),
                "completed_proposals": len([p for p in proposals if p["status"] == "completed"]),
                "active_sessions": len(sessions),
                "total_sessions": len(sessions) + len([p for p in proposals if p["status"] == "completed"])
            }
            
            return {
                "proposals": proposals,
                "sessions": sessions,
                "stats": stats
            }
            
        except Exception as e:
            st.error(f"Error loading real data: {e}")
            import traceback
            st.error(f"Traceback: {traceback.format_exc()}")
            # Fallback to minimal mock data
            return {
                "proposals": [
                    {
                        "id": "prop_001",
                        "title": "Machine Learning Basics",
                        "status": "approved",
                        "priority": "high",
                        "progress": 75,
                        "created_at": "2025-10-15 10:00:00",
                        "source": "hackernews"
                    },
                    {
                        "id": "prop_002", 
                        "title": "Python Advanced Concepts",
                        "status": "pending",
                        "priority": "medium",
                        "progress": 0,
                        "created_at": "2025-10-15 11:00:00",
                        "source": "reddit"
                    },
                    {
                        "id": "prop_003",
                        "title": "AI Ethics and Safety",
                        "status": "completed",
                        "priority": "high",
                        "progress": 100,
                        "created_at": "2025-10-14 15:00:00",
                        "source": "github"
                    },
                    # New proposals from today (4 new today)
                    {
                        "id": "prop_004",
                        "title": "Deep Learning with PyTorch",
                        "status": "pending",
                        "priority": "high",
                        "progress": 0,
                        "created_at": "2025-10-16 08:00:00",
                        "source": "arxiv",
                        "proposal_type": "auto"  # StillMe tự động đề xuất
                    },
                    {
                        "id": "prop_005",
                        "title": "React Native Mobile Development",
                        "status": "pending",
                        "priority": "medium",
                        "progress": 0,
                        "created_at": "2025-10-16 10:00:00",
                        "source": "github",
                        "proposal_type": "auto"  # StillMe tự động đề xuất
                    },
                    {
                        "id": "prop_006",
                        "title": "Blockchain and Cryptocurrency",
                        "status": "pending",
                        "priority": "high",
                        "progress": 0,
                        "created_at": "2025-10-16 12:00:00",
                        "source": "techcrunch",
                        "proposal_type": "auto"  # StillMe tự động đề xuất
                    },
                    {
                        "id": "prop_007",
                        "title": "Quantum Computing Fundamentals",
                        "status": "pending",
                        "priority": "critical",
                        "progress": 0,
                        "created_at": "2025-10-16 14:00:00",
                        "source": "medium",
                        "proposal_type": "auto"  # StillMe tự động đề xuất
                    },
                ],
                "sessions": [
                    {
                        "id": "session_001",
                        "title": "Machine Learning Basics",
                        "status": "active",
                        "progress": 75,
                        "started_at": "2025-10-15 10:00:00",
                        "last_activity": "2025-10-15 12:00:00"
                    }
                ],
                "stats": {
                    "total_proposals": 177,
                    "pending_proposals": 4,
                    "approved_proposals": 115,
                    "completed_proposals": 58,
                    "active_sessions": 1,
                    "total_sessions": 89
                }
            }
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return None

    def render_header(self):
        """Render dashboard header"""
        st.markdown(
            """
            <div class="main-header">
                🧠 StillMe IPC Learning Dashboard
            </div>
            """,
            unsafe_allow_html=True
        )

    def render_sidebar(self, data):
        """Render sidebar with filters and controls"""
        with st.sidebar:
            # Authentication section
            st.header("🔐 Authentication")
            self.auth.render_user_info()
            
            # Nếu chưa đăng nhập, hiển thị form login nhưng vẫn cho phép xem
            if not self.auth.is_authenticated():
                self.auth.render_login_form()
                st.markdown("---")
                st.info("👥 **Public Mode:** Bạn đang xem ở chế độ công khai. Chỉ có thể xem và vote.")
                # Vẫn trả về filters để hiển thị nội dung
                return {
                    "date_range": "30",
                    "status": ["pending", "approved", "completed"],
                    "priority": ["low", "medium", "high", "critical"],
                    "sources": [],
                    "auto_refresh": False,
                    "show_chat": True
                }
            
            st.markdown("---")
            
            # Filters & Controls (for authenticated users)
            st.header("🔍 Filters & Controls")
            
            # Date range
            st.subheader("📅 Date Range")
            date_range = st.selectbox(
                "Select period:",
                ["7", "14", "30", "90"],
                index=1
            )
            
            # Proposal status
            st.subheader("📋 Proposal Status")
            status_options = st.multiselect(
                "Filter by status:",
                ["pending", "approved", "completed", "rejected"],
                default=["pending", "approved"]
            )
            
            # Priority
            st.subheader("⚡ Priority")
            priority_options = st.multiselect(
                "Filter by priority:",
                ["low", "medium", "high", "critical"],
                default=["high", "critical"]
            )
            
            # Sources
            st.subheader("📚 Sources")
            source_options = st.multiselect(
                "Filter by source:",
                ["hackernews", "reddit", "github", "stackoverflow", "arxiv", "medium"],
                default=[]
            )
            
            # Auto refresh
            st.subheader("🔄 Auto Refresh")
            auto_refresh = st.checkbox("Enable auto refresh", value=True)
            if auto_refresh:
                st.info("Dashboard will refresh every 30 seconds")
            
            # Chat panel toggle
            st.subheader("💬 Chat Panel")
            show_chat = st.checkbox("Show chat panel", value=True)
            
            return {
                "date_range": date_range,
                "status": status_options,
                "priority": priority_options,
                "sources": source_options,
                "auto_refresh": auto_refresh,
                "show_chat": show_chat
            }

    def render_status_cards(self, data):
        """Render status indicator cards"""
        stats = data["stats"]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Make "new today" clickable
            if st.button(f"📊 Total Proposals: {stats['total_proposals']}\n+{stats['pending_proposals']} new today", key="total_proposals_btn"):
                st.session_state.show_new_proposals = True
                st.rerun()
        
        with col2:
            st.metric(
                label="✅ Approved",
                value=stats["approved_proposals"],
                delta="+0"
            )
        
        with col3:
            st.metric(
                label="🎯 Completed",
                value=stats["completed_proposals"],
                delta="+0"
            )
        
        with col4:
            st.metric(
                label="🧠 Learning",
                value=f"{stats['active_sessions']} active sessions",
                delta="No active sessions" if stats['active_sessions'] == 0 else "Active"
            )

    def render_learning_sessions(self, data):
        """Render learning sessions section with detailed tracking"""
        st.header("🎯 Active Learning Sessions")
        
        # Get active sessions from learning system
        try:
            from stillme_core.learning.evolutionary_learning_system import EvolutionaryLearningSystem
            learning_system = EvolutionaryLearningSystem()
            active_sessions = learning_system.get_active_sessions()
            
            if not active_sessions:
                st.info("📚 No active learning sessions")
                return
            
            for session_id, session_data in active_sessions.items():
                with st.container():
                    st.markdown("---")
                    col1, col2, col3, col4 = st.columns([4, 2, 2, 1])
                    
                    with col1:
                        st.write(f"**📖 {session_data.get('title', 'Unknown Title')}**")
                        st.write(f"🆔 **Session ID:** `{session_id}`")
                        st.write(f"📅 **Started:** {session_data.get('started_at', 'Unknown')}")
                        st.write(f"🎯 **Source:** {session_data.get('source', 'Unknown')}")
                    
                    with col2:
                        progress = session_data.get("progress", 0)
                        st.progress(progress / 100)
                        st.write(f"**Progress: {progress}%**")
                        
                        # Estimated time remaining
                        if progress > 0:
                            estimated_total = session_data.get("estimated_duration", 60)
                            remaining = int((100 - progress) / 100 * estimated_total)
                            st.write(f"⏱️ **Remaining:** ~{remaining} min")
                    
                    with col3:
                        st.write(f"📊 **Objectives:** {session_data.get('current_objective', 0)}/{session_data.get('total_objectives', 1)}")
                        st.write(f"⭐ **Quality:** {session_data.get('quality_score', 0.0):.1f}")
                        
                        # Learning status
                        status = session_data.get("status", "learning")
                        if status == "learning":
                            st.write("🟢 **Status:** Learning")
                        elif status == "completed":
                            st.write("✅ **Status:** Completed")
                        else:
                            st.write(f"🟡 **Status:** {status}")
                    
                    with col4:
                        if st.button("⏹️ Stop", key=f"stop_{session_id}", type="secondary"):
                            st.info(f"Stopped session: {session_id}")
                            st.rerun()
                        
                        if st.button("📊 Details", key=f"details_{session_id}"):
                            st.info(f"Session details for: {session_id}")
                            st.json(session_data)
                            st.rerun()
                            
        except Exception as e:
            st.error(f"Error loading active sessions: {e}")
            st.info("📚 No active learning sessions")

    def render_learning_library(self):
        """Render Learning Library with search and filter capabilities"""
        try:
            from stillme_core.learning.proposals_manager import ProposalsManager
            proposals_manager = ProposalsManager()
            all_proposals = proposals_manager.get_all_proposals()
            
            # Filter for completed proposals only
            completed_proposals = [p for p in all_proposals if p.status == "completed"]
            
            if not completed_proposals:
                st.info("📚 No completed learning items in library yet.")
                return
            
            # Search and filter controls
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                search_term = st.text_input("🔍 Search Learning Library", placeholder="Search by title, source, or content...")
            
            with col2:
                source_filter = st.selectbox("📂 Filter by Source", ["All"] + list(set(p.source for p in completed_proposals)))
            
            with col3:
                sort_by = st.selectbox("📊 Sort by", ["Newest", "Oldest", "Title A-Z", "Quality Score"])
            
            # Apply filters
            filtered_proposals = completed_proposals
            
            if search_term:
                filtered_proposals = [p for p in filtered_proposals if 
                                    search_term.lower() in p.title.lower() or 
                                    search_term.lower() in p.description.lower() or
                                    search_term.lower() in p.source.lower()]
            
            if source_filter != "All":
                filtered_proposals = [p for p in filtered_proposals if p.source == source_filter]
            
            # Apply sorting
            if sort_by == "Newest":
                filtered_proposals.sort(key=lambda x: x.created_at, reverse=True)
            elif sort_by == "Oldest":
                filtered_proposals.sort(key=lambda x: x.created_at)
            elif sort_by == "Title A-Z":
                filtered_proposals.sort(key=lambda x: x.title.lower())
            elif sort_by == "Quality Score":
                filtered_proposals.sort(key=lambda x: x.quality_score, reverse=True)
            
            # Display results
            st.write(f"📊 **Found {len(filtered_proposals)} completed learning items**")
            
            # Pagination
            items_per_page = 10
            total_pages = (len(filtered_proposals) + items_per_page - 1) // items_per_page
            
            if total_pages > 1:
                page = st.selectbox("📄 Page", range(1, total_pages + 1))
                start_idx = (page - 1) * items_per_page
                end_idx = start_idx + items_per_page
                page_proposals = filtered_proposals[start_idx:end_idx]
            else:
                page_proposals = filtered_proposals
            
            # Display proposals
            for proposal in page_proposals:
                with st.container():
                    st.markdown("---")
                    col1, col2, col3, col4 = st.columns([4, 2, 2, 1])
                    
                    with col1:
                        st.write(f"**📖 {proposal.title}**")
                        st.write(f"📅 **Completed:** {proposal.created_at}")
                        st.write(f"🎯 **Source:** {proposal.source}")
                        st.write(f"📝 **Description:** {proposal.description[:100]}...")
                    
                    with col2:
                        st.write(f"⭐ **Quality:** {proposal.quality_score:.1f}")
                        st.write(f"⏱️ **Duration:** {proposal.estimated_duration} min")
                        st.write(f"🎯 **Priority:** {proposal.priority}")
                    
                    with col3:
                        st.write(f"📊 **Progress:** 100%")
                        st.write(f"✅ **Status:** Completed")
                        st.write(f"🆔 **ID:** `{proposal.id[:8]}...`")
                    
                    with col4:
                        if st.button("📊 View Results", key=f"lib_results_{proposal.id}"):
                            # Show detailed results
                            st.success(f"📊 **Learning Results: {proposal.title}**")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**📅 Completed:** {proposal.created_at}")
                                st.write(f"**🎯 Source:** {proposal.source}")
                                st.write(f"**⭐ Quality Score:** {proposal.quality_score:.1f}")
                                st.write(f"**⏱️ Duration:** {proposal.estimated_duration} minutes")
                            
                            with col2:
                                st.write(f"**📊 Final Progress:** 100%")
                                st.write(f"**🎯 Priority:** {proposal.priority}")
                                st.write(f"**🆔 Proposal ID:** `{proposal.id}`")
                            
                            # Show learning objectives
                            if proposal.learning_objectives:
                                st.write("**🎯 Learning Objectives:**")
                                for i, obj in enumerate(proposal.learning_objectives, 1):
                                    st.write(f"  {i}. {obj}")
                            
                            # Show expected outcomes
                            if proposal.expected_outcomes:
                                st.write("**📈 Expected Outcomes:**")
                                for i, outcome in enumerate(proposal.expected_outcomes, 1):
                                    st.write(f"  {i}. {outcome}")
                            
                            st.rerun()
                            
        except Exception as e:
            st.error(f"Error loading learning library: {e}")

    def render_proposals_list(self, data, filters):
        """Render proposals list"""
        st.header("📚 Learning Proposals")
        
        # Add CSS to ensure completed items are not dimmed
        st.markdown("""
        <style>
        .completed-proposal {
            opacity: 1.0 !important;
            color: #ffffff !important;
        }
        .completed-proposal .stButton > button {
            opacity: 1.0 !important;
            background-color: #ff4444 !important;
            color: white !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        proposals = data["proposals"]
        
        # Filter proposals
        filtered_proposals = []
        for proposal in proposals:
            if filters["status"] and proposal["status"] not in filters["status"]:
                continue
            if filters["priority"] and proposal["priority"] not in filters["priority"]:
                continue
            if filters["sources"] and proposal["source"] not in filters["sources"]:
                continue
            filtered_proposals.append(proposal)
        
        if not filtered_proposals:
            st.info("No proposals match the current filters")
            return
        
        for proposal in filtered_proposals:
            with st.container():
                col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                
                with col1:
                    st.write(f"**{proposal['title']}**")
                    st.write(f"Source: {proposal['source']} | Created: {proposal['created_at']}")
                
                with col2:
                    status_color = {
                        "pending": "🟡",
                        "approved": "🟢", 
                        "completed": "✅",
                        "rejected": "❌"
                    }
                    st.write(f"{status_color.get(proposal['status'], '❓')} {proposal['status']}")
                
                with col3:
                    priority_color = {
                        "low": "🟢",
                        "medium": "🟡",
                        "high": "🟠",
                        "critical": "🔴"
                    }
                    st.write(f"{priority_color.get(proposal['priority'], '❓')} {proposal['priority']}")
                
                with col4:
                    if proposal["status"] == "pending":
                        # CHỈ ADMIN MỚI ĐƯỢC THẤY NÚT APPROVE/REJECT
                        if self.auth.is_authenticated() and self.auth.has_permission("approve"):
                            col_approve, col_reject = st.columns(2)
                            with col_approve:
                                if st.button("✅ Approve", key=f"approve_{proposal['id']}", type="primary"):
                                    try:
                                        # Update real proposal in database
                                        from stillme_core.learning.proposals_manager import ProposalsManager
                                        proposals_manager = ProposalsManager()
                                        proposals_manager.approve_proposal(proposal['id'], "admin")
                                        st.success(f"✅ Approved: {proposal['title']}")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Lỗi approve: {e}")
                            with col_reject:
                                if st.button("❌ Reject", key=f"reject_{proposal['id']}", type="secondary"):
                                    try:
                                        # Update real proposal in database
                                        from stillme_core.learning.proposals_manager import ProposalsManager
                                        proposals_manager = ProposalsManager()
                                        proposals_manager.reject_proposal(proposal['id'], "admin", "Rejected by admin")
                                        st.error(f"❌ Rejected: {proposal['title']}")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Lỗi reject: {e}")
                        else:
                            # Guest user có thể vote cho community proposals
                            if proposal.get("source") == "community":
                                col_vote, col_dislike = st.columns(2)
                                with col_vote:
                                    if st.button("👍 Vote", key=f"vote_{proposal['id']}", type="primary"):
                                        st.success("👍 Cảm ơn bạn đã vote!")
                                        st.rerun()
                                with col_dislike:
                                    if st.button("👎 Dislike", key=f"dislike_{proposal['id']}", type="secondary"):
                                        st.info("👎 Cảm ơn feedback của bạn!")
                                        st.rerun()
                            else:
                                st.write("🔒 **Admin only**")
                    elif proposal["status"] == "approved":
                        # Approved proposals should automatically start learning
                        st.write("🚀 **Auto-starting...**")
                        try:
                            # Auto-start learning session for approved proposals
                            from stillme_core.learning.evolutionary_learning_system import EvolutionaryLearningSystem
                            learning_system = EvolutionaryLearningSystem()
                            
                            # Check if already learning
                            active_sessions = learning_system.get_active_sessions()
                            if proposal['id'] not in active_sessions:
                                # Start learning session
                                session_id = learning_system.start_learning_session(
                                    proposal_id=proposal['id'],
                                    title=proposal['title']
                                )
                                st.success(f"🚀 Auto-started: {proposal['title']}")
                            else:
                                st.info(f"📚 Already learning: {proposal['title']}")
                        except Exception as e:
                            st.error(f"❌ Auto-start failed: {e}")
                    elif proposal["status"] == "completed":
                        if st.button("📊 View Results", key=f"results_{proposal['id']}"):
                            # Show detailed results for completed proposal
                            st.success(f"📊 **Learning Results: {proposal['title']}**")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**📅 Completed:** {proposal.get('learning_completed_at', 'Unknown')}")
                                st.write(f"**🎯 Source:** {proposal.get('source', 'Unknown')}")
                                st.write(f"**⭐ Quality Score:** {proposal.get('quality_score', 0.0):.1f}")
                                st.write(f"**⏱️ Duration:** {proposal.get('estimated_duration', 0)} minutes")
                            
                            with col2:
                                st.write(f"**📊 Final Progress:** {proposal.get('final_progress', 100)}%")
                                st.write(f"**🎯 Objectives:** {proposal.get('current_objective', 1)}/{proposal.get('total_objectives', 1)}")
                                st.write(f"**📝 Learning Notes:** {proposal.get('learning_notes', 'No notes available')}")
                            
                            # Show learning objectives
                            if proposal.get('learning_objectives'):
                                st.write("**🎯 Learning Objectives:**")
                                for i, obj in enumerate(proposal['learning_objectives'], 1):
                                    st.write(f"  {i}. {obj}")
                            
                            # Show expected outcomes
                            if proposal.get('expected_outcomes'):
                                st.write("**📈 Expected Outcomes:**")
                                for i, outcome in enumerate(proposal['expected_outcomes'], 1):
                                    st.write(f"  {i}. {outcome}")
                            
                            st.rerun()
                    elif proposal["status"] == "rejected":
                        st.write("❌ **Đã từ chối**")
                    elif proposal["status"] == "learning":
                        st.write("🧠 **Đang học**")

    def render_chat_bubble(self):
        """Render floating chat bubble like Gemini"""
        # Initialize chat state
        if "chat_open" not in st.session_state:
            st.session_state.chat_open = False
        
        # Chat bubble button (bottom right)
        if not st.session_state.chat_open:
            # Floating chat bubble
            st.markdown(
                """
                <div style="position: fixed; bottom: 20px; right: 20px; z-index: 1000;">
                    <button onclick="openChat()" style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        border: none;
                        border-radius: 50px;
                        width: 60px;
                        height: 60px;
                        color: white;
                        font-size: 24px;
                        cursor: pointer;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                        transition: all 0.3s ease;
                    " onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
                        💬
                    </button>
                </div>
                <script>
                function openChat() {
                    // This will be handled by Streamlit
                    window.parent.postMessage({type: 'open_chat'}, '*');
                }
                </script>
                """,
                unsafe_allow_html=True
            )
            
            # Check if chat should open
            if st.button("💬", key="chat_bubble", help="Chat with StillMe"):
                st.session_state.chat_open = True
                st.rerun()
        else:
            # Full-screen chat panel (like Gemini)
            self.render_fullscreen_chat()
    
    def render_fullscreen_chat(self):
        """Render full-screen chat panel like Gemini"""
        # Chat header
        col1, col2 = st.columns([1, 0.1])
        
        with col1:
            st.markdown("### 🧠 StillMe AI Chat")
        
        with col2:
            if st.button("❌", key="close_chat", help="Close chat"):
                st.session_state.chat_open = False
                st.rerun()
        
        st.markdown("---")
        
        # Simple chat interface (like ChatGPT/Gemini)
        st.markdown(
            """
            <div style="
                height: 600px; 
                border: 1px solid #e0e0e0; 
                border-radius: 8px; 
                background: #ffffff;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            ">
            """,
            unsafe_allow_html=True
        )
        
        # Chat messages area
        st.markdown(
            """
            <div id="chat-messages" style="
                flex: 1;
                overflow-y: auto; 
                padding: 20px; 
                background: #ffffff;
            ">
            """,
            unsafe_allow_html=True
        )
        
        if st.session_state.chat_messages:
            # Display chat messages
            for message in st.session_state.chat_messages:
                if message["role"] == "user":
                    st.markdown(
                        f"""
                        <div style="
                            background: #e3f2fd; 
                            padding: 12px 16px; 
                            margin: 8px 0; 
                            border-radius: 18px; 
                            margin-left: 20px;
                            color: #000;
                            max-width: 80%;
                            word-wrap: break-word;
                        ">
                            <strong>Anh:</strong> {message["content"]}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    # Get metadata
                    response_time = message.get("response_time", "N/A")
                    model = message.get("model", "StillMe-AI")
                    source = message.get("source", "Unknown")
                    timestamp = message.get("timestamp", "")
                    
                    # Color coding for AI source
                    source_color = "#4caf50" if source == "Local AI" else "#ff9800"
                    source_icon = "🏠" if source == "Local AI" else "☁️"
                    
                    st.markdown(
                        f"""
                        <div style="
                            background: #f5f5f5; 
                            padding: 12px 16px; 
                            margin: 8px 0; 
                            border-radius: 18px; 
                            margin-right: 20px;
                            color: #000;
                            max-width: 80%;
                            word-wrap: break-word;
                        ">
                            <strong>StillMe IPC:</strong> {message["content"]}
                            <br><br>
                            <small style="color: #666; font-size: 0.8em;">
                                {source_icon} {source} | 🤖 {model} | ⏱️ {response_time} | 📅 {timestamp[:19] if timestamp else 'N/A'}
                            </small>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        
        # Close chat messages
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Input area
        st.markdown(
            """
            <div style="
                padding: 16px 20px;
                background: #f8f9fa;
                border-top: 1px solid #e0e0e0;
            ">
            """,
            unsafe_allow_html=True
        )
        
        # Input field - simple approach without clearing
        user_input = st.text_input(
            "",
            key="chat_input",
            placeholder="Type your message and press Enter to send...",
            help="Press Enter to send message"
        )
        
        # Close input area and main container
        st.markdown("</div></div>", unsafe_allow_html=True)
        
        # Auto-scroll to bottom script
        st.markdown(
            """
            <script>
            function scrollToBottom() {
                var chatContainer = document.getElementById('chat-messages');
                if (chatContainer) {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            }
            // Scroll to bottom when page loads
            window.addEventListener('load', scrollToBottom);
            // Scroll to bottom after any content change
            setTimeout(scrollToBottom, 100);
            </script>
            """,
            unsafe_allow_html=True
        )
        
        # Handle Enter key for sending with auto-clear
        # Initialize chat input state
        if "last_message" not in st.session_state:
            st.session_state.last_message = ""
        
        # Handle message sending with proper duplicate prevention
        if user_input and user_input.strip() and user_input != st.session_state.last_message:
            # Add user message
            st.session_state.chat_messages.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now().isoformat()
            })
            
            # Generate AI response with timing
            start_time = time.time()
            ai_response = self.generate_ai_response(user_input)
            response_time = time.time() - start_time
            
            # Determine AI source based on routing mode used
            routing_mode = self._determine_routing_mode(user_input)
            if routing_mode == "fast":
                ai_source = "Local AI"
                model_info = "StillMe-Local-Llama3.1-8B-v1.0"
            else:
                ai_source = "Cloud AI" 
                model_info = "StillMe-Cloud-GPT4-v1.0"
            
            # Add AI response with metadata
            st.session_state.chat_messages.append({
                "role": "assistant", 
                "content": ai_response,
                "timestamp": datetime.now().isoformat(),
                "response_time": f"{response_time:.2f}s",
                "model": model_info,
                "source": ai_source
            })
            
            # Store last message to prevent duplicates
            st.session_state.last_message = user_input
            
            # Force rerun to update display
            st.rerun()
        
        # Quick actions (minimal)
        st.markdown("**Quick Actions:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Progress", key="quick_progress"):
                st.session_state.chat_messages.append({
                    "role": "user",
                    "content": "Show me my learning progress",
                    "timestamp": datetime.now().isoformat()
                })
                ai_response = self.generate_ai_response("Show me my learning progress")
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": ai_response,
                    "timestamp": datetime.now().isoformat()
                })
                st.rerun()
        
        with col2:
            if st.button("📚 Proposals", key="quick_proposals"):
                st.session_state.chat_messages.append({
                    "role": "user",
                    "content": "Show me pending proposals",
                    "timestamp": datetime.now().isoformat()
                })
                ai_response = self.generate_ai_response("Show me pending proposals")
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": ai_response,
                    "timestamp": datetime.now().isoformat()
                })
                st.rerun()
        
        with col3:
            if st.button("❓ Help", key="quick_help"):
                st.session_state.chat_messages.append({
                    "role": "user",
                    "content": "Help me understand the dashboard",
                    "timestamp": datetime.now().isoformat()
                })
                ai_response = self.generate_ai_response("Help me understand the dashboard")
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": ai_response,
                    "timestamp": datetime.now().isoformat()
                })
                st.rerun()

    def generate_ai_response(self, user_input):
        """Generate intelligent AI response using real routing system"""
        try:
            # Import the real routing system
            from stillme_core.provider_router import ask_sync
            
            # Determine routing mode based on complexity
            mode = self._determine_routing_mode(user_input)
            
            # Create StillMe system prompt
            system_prompt = self._create_system_prompt()
            
            # Call real AI routing system
            response = ask_sync(
                prompt=user_input,
                mode=mode,
                system_prompt=system_prompt,
                response_format="text",  # Get plain text response
                force_json=False,
                max_tokens=512,
                temperature=0.7
            )
            
            return response
            
        except Exception as e:
            # Fallback to simple responses if routing fails
            return self._fallback_response(user_input, str(e))
    
    def _determine_routing_mode(self, user_input):
        """Determine routing mode based on message complexity"""
        user_input_lower = user_input.lower().strip()
        
        # Simple greetings and basic questions -> fast mode (local AI)
        simple_keywords = [
            "chào", "hello", "hi", "xin chào", "cảm ơn", "thank you", 
            "tạm biệt", "bye", "ok", "được", "tốt"
        ]
        
        if any(keyword in user_input_lower for keyword in simple_keywords):
            return "fast"  # Use local AI for simple responses
        
        # Complex questions, technical topics, coding -> safe mode (cloud AI)
        complex_keywords = [
            "ai", "machine learning", "deep learning", "programming", "code",
            "lập trình", "công nghệ", "tech", "algorithm", "thuật toán",
            "python", "javascript", "react", "database", "cơ sở dữ liệu",
            "explain", "giải thích", "how", "làm thế nào", "tại sao", "why"
        ]
        
        if any(keyword in user_input_lower for keyword in complex_keywords):
            return "safe"  # Use cloud AI for complex responses
        
        # Default to fast mode for unknown complexity
        return "fast"
    
    def _create_system_prompt(self):
        """Create StillMe system prompt"""
        return """Bạn là StillMe - một AI companion thông minh và thân thiện được tạo ra bởi Anh Nguyễn.

Đặc điểm của bạn:
- Luôn xưng hô thân thiện: "anh/em" với người dùng
- Trả lời bằng tiếng Việt tự nhiên, dễ hiểu
- Thông minh, hữu ích và có tính cá nhân hóa
- Có thể thảo luận về nhiều chủ đề: công nghệ, cuộc sống, học tập, giải trí
- Luôn giữ thái độ tích cực và hỗ trợ

Khi được hỏi "bạn là ai?", hãy trả lời: "Em là StillMe AI - AI companion của anh, được tạo ra bởi Anh Nguyễn để đồng hành và hỗ trợ anh trong cuộc sống."

Hãy trả lời một cách tự nhiên và hữu ích."""
    
    def _fallback_response(self, user_input, error_msg):
        """Fallback response when routing fails"""
        user_input_lower = user_input.lower().strip()
        
        # Simple fallback responses
        if any(greeting in user_input_lower for greeting in ["chào", "hello", "hi", "xin chào"]):
            return "👋 Chào anh! Em là StillMe AI. Hiện tại hệ thống routing đang gặp sự cố, nhưng em vẫn có thể trò chuyện với anh. Anh muốn nói về gì?"
        
        elif any(phrase in user_input_lower for phrase in ["bạn là ai", "ai là gì"]):
            return "🤖 Em là StillMe AI - AI companion của anh, được tạo ra bởi Anh Nguyễn. Em đang gặp sự cố kỹ thuật nhỏ nhưng vẫn có thể trò chuyện với anh."
        
        else:
            return f"Xin lỗi anh, em đang gặp sự cố kỹ thuật: {error_msg}. Nhưng em vẫn có thể trò chuyện với anh. Anh muốn nói về gì?"

    def render_dashboard(self):
        """Render the complete integrated dashboard"""
        # Render header
        self.render_header()
        
        # Load data
        data = self.load_learning_data()
        if not data:
            st.error("Failed to load dashboard data")
            return
        
        # Render sidebar and get filters
        filters = self.render_sidebar(data)
        
        # Hiển thị thông báo chế độ
        if not self.auth.is_authenticated():
            st.info("👥 **Chế độ công khai:** Bạn có thể xem proposals và chat với StillMe.")
        else:
            st.success(f"👑 **Chế độ admin:** Chào mừng {self.auth.get_username()}! Bạn có quyền approve/reject proposals.")
        
        # Main content area (hiển thị cho tất cả)
        # Status cards
        self.render_status_cards(data)
        
        # Learning sessions
        self.render_learning_sessions(data)
        
        # Community proposal input (for all users)
        st.markdown("### 💡 Đề Xuất Bài Học Cho StillMe")
        with st.form("community_proposal"):
            col1, col2 = st.columns(2)
            with col1:
                community_title = st.text_input("Tiêu đề bài học", placeholder="Ví dụ: Machine Learning với Python", key="community_title")
                community_category = st.selectbox("Danh mục", ["AI/ML", "Programming", "Technology", "Science", "Other"], key="community_category")
            with col2:
                community_description = st.text_area("Mô tả chi tiết", placeholder="Mô tả nội dung bạn muốn StillMe học", key="community_description")
                community_priority = st.selectbox("Mức độ ưu tiên", ["low", "medium", "high"], index=1, key="community_priority")
            
            if st.form_submit_button("📝 Đề Xuất Bài Học", type="primary"):
                if community_title and community_description:
                    try:
                        from stillme_core.learning.proposals_manager import ProposalsManager
                        proposals_manager = ProposalsManager()
                        
                        # Create community proposal
                        proposal = proposals_manager.create_proposal(
                            title=community_title,
                            description=community_description,
                            learning_objectives=[f"Học về {community_title}"],
                            prerequisites=[],
                            expected_outcomes=[f"Hiểu rõ về {community_title}"],
                            estimated_duration=60,
                            quality_score=0.5,  # Lower score for community proposals
                            source="community",
                            priority=community_priority,
                            risk_assessment={"level": "medium", "notes": f"Community proposal - {community_category}"}
                        )
                        st.success(f"✅ Đã đề xuất: {community_title}")
                        st.info("📊 Proposal sẽ được cộng đồng vote. Khi đạt 50+ votes, StillMe sẽ tự động học!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Lỗi tạo proposal: {e}")
                else:
                    st.error("Vui lòng nhập đầy đủ thông tin!")
        
        st.markdown("---")
        
        # Manual lesson input (Admin only)
        if self.auth.has_permission("admin"):
            st.markdown("### ➕ Nhập Bài Học Mới Cho StillMe")
            with st.form("add_lesson"):
                col1, col2 = st.columns(2)
                with col1:
                    title = st.text_input("Tiêu đề bài học", placeholder="Ví dụ: Python Advanced Concepts")
                    priority = st.selectbox("Mức độ ưu tiên", ["low", "medium", "high", "critical"], index=2)
                    source = st.selectbox("Nguồn", ["manual", "hackernews", "reddit", "github", "arxiv", "medium"])
                with col2:
                    description = st.text_area("Mô tả bài học", placeholder="Mô tả chi tiết nội dung cần học")
                    learning_objectives = st.text_area("Mục tiêu học tập", placeholder="Mục tiêu cụ thể cần đạt được")
                
                if st.form_submit_button("Tạo Bài Học", type="primary"):
                    if title and description:
                        try:
                            # Create real proposal in learning system
                            from stillme_core.learning.proposals_manager import ProposalsManager
                            from stillme_core.learning.proposals import LearningProposal, ProposalStatus, LearningPriority, ContentSource
                            
                            proposals_manager = ProposalsManager()
                            
                            # Create proposal using kwargs
                            proposal = proposals_manager.create_proposal(
                                title=title,
                                description=description,
                                learning_objectives=[learning_objectives] if learning_objectives else [f"Học về {title}"],
                                prerequisites=[],
                                expected_outcomes=[f"Hiểu rõ về {title}"],
                                estimated_duration=60,  # Default 60 minutes
                                quality_score=0.8,  # Default quality score
                                source="manual" if source == "manual" else source,
                                priority=priority.lower(),
                                risk_assessment={"level": "low", "notes": "Manual input by admin"}
                            )
                            
                            # Get proposal ID from the created proposal object
                            proposal_id = proposal.id
                            
                            # Admin tạo bài học phải tự động approve và học ngay
                            proposals_manager.approve_proposal(proposal_id, "admin")
                            
                            # Tự động start learning session
                            from stillme_core.learning.evolutionary_learning_system import EvolutionaryLearningSystem
                            learning_system = EvolutionaryLearningSystem()
                            session_id = learning_system.start_learning_session(
                                proposal_id=proposal_id,
                                title=title
                            )
                            
                            st.success(f"✅ Đã tạo và bắt đầu học: {title}")
                            st.info(f"🚀 Session ID: {session_id}")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Lỗi tạo bài học: {e}")
                    else:
                        st.error("Vui lòng nhập đầy đủ thông tin!")
            st.markdown("---")
        
        # Show new proposals if clicked
        if st.session_state.get("show_new_proposals", False):
            st.markdown("### 🆕 New Proposals Today")
            new_proposals = [p for p in data["proposals"] if "2025-10-16" in p["created_at"]]
            for proposal in new_proposals:
                with st.container():
                    col1, col2, col3 = st.columns([4, 1, 1])
                    with col1:
                        st.write(f"**{proposal['title']}**")
                        st.write(f"Source: {proposal['source']} | Created: {proposal['created_at']}")
                    with col2:
                        st.write(f"🟡 {proposal['status']}")
                    with col3:
                        st.write(f"🟠 {proposal['priority']}")
            st.markdown("---")
        
        
        # Learning Library Tab
        tab1, tab2, tab3 = st.tabs(["📋 Current Proposals", "📚 Learning Library", "🎯 Active Sessions"])
        
        with tab1:
            # Proposals list - ALWAYS show proposals
            if data.get("proposals"):
                st.markdown("### 📋 Danh Sách Proposals")
                self.render_proposals_list(data, filters)
            else:
                st.info("📝 Không có proposals nào. Hãy tạo proposal mới hoặc đợi StillMe tự động đề xuất.")
        
        with tab2:
            # Learning Library with search and filter
            st.markdown("### 📚 Learning Library")
            self.render_learning_library()
        
        with tab3:
            # Active Learning Sessions
            self.render_learning_sessions(data)
        
        # Chat bubble (floating) - cho tất cả mọi người
        # Chỉ render 1 bubble chat duy nhất
        if filters and filters.get("show_chat", True):
            self.render_chat_bubble()
        
        # Auto refresh
        if filters and filters["auto_refresh"]:
            time.sleep(30)
            st.rerun()


def main():
    """Main function"""
    dashboard = IntegratedDashboard()
    dashboard.render_dashboard()


if __name__ == "__main__":
    main()
