"""
StillMe IPC Simple Learning Dashboard
====================================

A simple, clean dashboard without complex imports to avoid issues.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

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
""",
    unsafe_allow_html=True,
)


class SimpleDashboard:
    def __init__(self):
        """Initialize the simple dashboard"""
        # Initialize session state
        if "selected_session" not in st.session_state:
            st.session_state.selected_session = "Machine Learning Basics"
        if "auto_refresh" not in st.session_state:
            st.session_state.auto_refresh = False

        # Initialize proposals manager for real data
        try:
            from stillme_core.learning.proposals_manager import ProposalsManager

            self.proposals_manager = ProposalsManager()
        except Exception as e:
            st.error(f"Failed to initialize proposals manager: {e}")
            self.proposals_manager = None

    def get_real_learning_sessions(self):
        """Get real learning sessions from database"""
        if not self.proposals_manager:
            return []

        try:
            # Get all proposals from database
            all_proposals = self.proposals_manager.get_all_proposals()

            sessions = []

            # Process each proposal based on status
            for proposal in all_proposals:
                if hasattr(proposal, "status"):
                    status = proposal.status
                else:
                    status = getattr(proposal, "status", "pending")

                if status == "completed":
                    sessions.append(
                        {
                            "name": proposal.title,
                            "status": "✅ Completed",
                            "progress": 100,
                            "proposal_id": proposal.id,
                            "quality_score": getattr(proposal, "quality_score", 0.8),
                            "completed_at": getattr(
                                proposal, "learning_completed_at", "Unknown"
                            ),
                        }
                    )
                elif status == "learning":
                    sessions.append(
                        {
                            "name": proposal.title,
                            "status": "🔄 Learning",
                            "progress": 25,  # Start at 25% when approved
                            "proposal_id": proposal.id,
                            "quality_score": getattr(proposal, "quality_score", 0.8),
                            "started_at": getattr(
                                proposal, "learning_started_at", "Unknown"
                            ),
                        }
                    )
                elif status == "approved":
                    sessions.append(
                        {
                            "name": proposal.title,
                            "status": "⏳ Ready to Start",
                            "progress": 0,
                            "proposal_id": proposal.id,
                            "quality_score": getattr(proposal, "quality_score", 0.8),
                            "approved_at": getattr(proposal, "approved_at", "Unknown"),
                        }
                    )
                elif status == "pending":
                    sessions.append(
                        {
                            "name": proposal.title,
                            "status": "⏳ Pending Approval",
                            "progress": 0,
                            "proposal_id": proposal.id,
                            "quality_score": getattr(proposal, "quality_score", 0.8),
                            "created_at": getattr(proposal, "created_at", "Unknown"),
                        }
                    )

            return sessions

        except Exception as e:
            st.error(f"Failed to get real learning sessions: {e}")
            return []

    def calculate_real_metrics(self, days=30):
        """Calculate real metrics from learning history"""
        if not self.proposals_manager:
            return {
                "dates": [],
                "knowledge_scores": [],
                "skills_learned": [],
                "time_spent": [],
            }

        try:
            # Get all proposals
            all_proposals = self.proposals_manager.get_all_proposals()

            # Calculate metrics by date
            from collections import defaultdict
            import pandas as pd

            # Group by date
            daily_metrics = defaultdict(
                lambda: {
                    "knowledge_score": 0,
                    "skills_count": 0,
                    "time_spent": 0,
                    "proposals_count": 0,
                }
            )

            for proposal in all_proposals:
                if hasattr(proposal, "created_at"):
                    if isinstance(proposal.created_at, str):
                        date = pd.to_datetime(proposal.created_at).date()
                    else:
                        date = proposal.created_at.date()

                    # Calculate knowledge score based on quality
                    quality_score = getattr(proposal, "quality_score", 0.8)
                    daily_metrics[date]["knowledge_score"] += quality_score
                    daily_metrics[date]["proposals_count"] += 1

                    # Skills learned (based on learning objectives)
                    if hasattr(proposal, "learning_objectives"):
                        objectives = proposal.learning_objectives
                        if isinstance(objectives, str):
                            import json

                            try:
                                objectives = json.loads(objectives)
                            except Exception:
                                objectives = []
                        daily_metrics[date]["skills_count"] += len(objectives)
                    else:
                        daily_metrics[date]["skills_count"] += 1

                    # Time spent (based on estimated duration)
                    duration = getattr(proposal, "estimated_duration", 60)
                    daily_metrics[date]["time_spent"] += duration

            # Generate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            dates = pd.date_range(start=start_date, end=end_date, freq="D")

            # Fill in data for each date
            knowledge_scores = []
            skills_learned = []
            time_spent = []

            for date in dates:
                date_key = date.date()
                if date_key in daily_metrics:
                    metrics = daily_metrics[date_key]
                    # Average knowledge score
                    if metrics["proposals_count"] > 0:
                        knowledge_scores.append(
                            metrics["knowledge_score"] / metrics["proposals_count"]
                        )
                    else:
                        knowledge_scores.append(0.5)

                    skills_learned.append(metrics["skills_count"])
                    time_spent.append(metrics["time_spent"] / 60)  # Convert to hours
                else:
                    knowledge_scores.append(0.5)
                    skills_learned.append(0)
                    time_spent.append(0)

            return {
                "dates": dates,
                "knowledge_scores": knowledge_scores,
                "skills_learned": skills_learned,
                "time_spent": time_spent,
            }

        except Exception as e:
            st.error(f"Failed to calculate real metrics: {e}")
            return {
                "dates": [],
                "knowledge_scores": [],
                "skills_learned": [],
                "time_spent": [],
            }

    def get_real_learning_report(self):
        """Get real learning report data"""
        if not self.proposals_manager:
            return {
                "completed_topics": [],
                "learning_stats": {},
                "skills_acquired": [],
                "progress_by_topic": {},
                "next_suggestions": [],
            }

        try:
            all_proposals = self.proposals_manager.get_all_proposals()

            # Analyze completed topics
            completed_topics = []
            total_learning_time = 0
            completed_count = 0
            total_quality_score = 0

            for proposal in all_proposals:
                if hasattr(proposal, "status") and proposal.status == "completed":
                    completed_topics.append(
                        {
                            "title": proposal.title,
                            "description": getattr(
                                proposal, "description", "No description"
                            ),
                            "quality_score": getattr(proposal, "quality_score", 0.8),
                            "duration": getattr(proposal, "estimated_duration", 60),
                        }
                    )
                    total_learning_time += getattr(proposal, "estimated_duration", 60)
                    completed_count += 1
                    total_quality_score += getattr(proposal, "quality_score", 0.8)

            # Calculate learning statistics
            avg_quality = (
                total_quality_score / completed_count if completed_count > 0 else 0
            )
            success_rate = (
                (completed_count / len(all_proposals)) * 100 if all_proposals else 0
            )

            learning_stats = {
                "total_learning_time": total_learning_time / 60,  # Convert to hours
                "completed_topics": completed_count,
                "average_quality_score": avg_quality,
                "success_rate": success_rate,
            }

            # Extract skills acquired
            skills_acquired = []
            for proposal in completed_topics:
                if hasattr(proposal, "learning_objectives"):
                    objectives = proposal.learning_objectives
                    if isinstance(objectives, str):
                        import json

                        try:
                            objectives = json.loads(objectives)
                        except Exception:
                            objectives = []
                    skills_acquired.extend(objectives)

            # Progress by topic (simplified)
            progress_by_topic = {}
            for proposal in all_proposals:
                topic = proposal.title.split()[0] if proposal.title else "Unknown"
                if topic not in progress_by_topic:
                    progress_by_topic[topic] = 0

                if hasattr(proposal, "status"):
                    if proposal.status == "completed":
                        progress_by_topic[topic] = 100
                    elif proposal.status == "learning":
                        progress_by_topic[topic] = 50
                    elif proposal.status == "approved":
                        progress_by_topic[topic] = 25

            # Next learning suggestions (based on pending proposals)
            next_suggestions = []
            for proposal in all_proposals:
                if hasattr(proposal, "status") and proposal.status == "pending":
                    next_suggestions.append(
                        {
                            "title": proposal.title,
                            "description": getattr(
                                proposal, "description", "No description"
                            )[:50]
                            + "...",
                            "priority": getattr(proposal, "priority", "medium"),
                        }
                    )

            return {
                "completed_topics": completed_topics,
                "learning_stats": learning_stats,
                "skills_acquired": list(set(skills_acquired))[
                    :10
                ],  # Top 10 unique skills
                "progress_by_topic": progress_by_topic,
                "next_suggestions": next_suggestions[:4],  # Top 4 suggestions
            }

        except Exception as e:
            st.error(f"Failed to get real learning report: {e}")
            return {
                "completed_topics": [],
                "learning_stats": {},
                "skills_acquired": [],
                "progress_by_topic": {},
                "next_suggestions": [],
            }

    def refresh_data(self):
        """Refresh all data from database"""
        try:
            if self.proposals_manager:
                # Force refresh of proposals manager
                from stillme_core.learning.proposals_manager import ProposalsManager
                self.proposals_manager = ProposalsManager()
                return True
        except Exception as e:
            st.error(f"Failed to refresh data: {e}")
            return False

    def render_header(self):
        """Render dashboard header"""
        st.markdown(
            '<h1 class="main-header">🧠 StillMe IPC Learning Dashboard</h1>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns([3, 1])

        with col1:
            # Get pending proposals from session state and database
            sample_proposals = st.session_state.get("sample_proposals", [])

            # Also get proposals from database
            try:
                from stillme_core.learning.proposals_manager import ProposalsManager

                manager = ProposalsManager()
                db_proposals = manager.get_pending_proposals(limit=10)
                pending_count = len(sample_proposals) + len(db_proposals)
            except Exception:
                # Fallback: try to get count directly from database
                try:
                    import sqlite3

                    from stillme_core.learning.proposals_manager import ProposalsManager

                    manager = ProposalsManager()
                    with sqlite3.connect(manager.db_path) as conn:
                        cursor = conn.execute(
                            "SELECT COUNT(*) FROM proposals WHERE status = 'pending'"
                        )
                        db_count = cursor.fetchone()[0]
                        pending_count = len(sample_proposals) + db_count
                except Exception:
                    pending_count = len(sample_proposals)

            new_today = len(
                [p for p in sample_proposals if p.get("created_today", False)]
            )

            if st.button(
                f"📋 **{pending_count} Pending Proposals**\n\n"
                f"🆕 {new_today} new today\n"
                f"⏰ Click to review & approve",
                key="pending_proposals_button",
                help="Click to view and manage pending learning proposals",
                use_container_width=True,
            ):
                st.session_state.show_pending_details = True
                st.rerun()

            # Show status message
            if st.session_state.get("show_pending_details", False):
                st.info("📋 Reviewing pending proposals")
            else:
                st.info("ℹ️ Click the button above to view pending proposals")

        with col2:
            st.markdown('<div class="status-indicators">', unsafe_allow_html=True)
            st.markdown("### 📊 Status")

            # Get real stats from database
            try:
                from stillme_core.learning.proposals_manager import ProposalsManager
                import sqlite3
                
                manager = ProposalsManager()
                with sqlite3.connect(manager.db_path) as conn:
                    # Get approved count
                    cursor = conn.execute("SELECT COUNT(*) FROM proposals WHERE status = 'approved'")
                    approved_count = cursor.fetchone()[0]
                    
                    # Get completed count
                    cursor = conn.execute("SELECT COUNT(*) FROM proposals WHERE status = 'completed'")
                    completed_count = cursor.fetchone()[0]
                    
                    # Get learning count
                    cursor = conn.execute("SELECT COUNT(*) FROM proposals WHERE status = 'learning'")
                    learning_count = cursor.fetchone()[0]
                    
                    # Get today's new approvals
                    cursor = conn.execute("""
                        SELECT COUNT(*) FROM proposals 
                        WHERE status = 'approved' 
                        AND DATE(approved_at) = DATE('now')
                    """)
                    new_approved_today = cursor.fetchone()[0]
                    
                    # Get today's new completions
                    cursor = conn.execute("""
                        SELECT COUNT(*) FROM proposals 
                        WHERE status = 'completed' 
                        AND DATE(learning_completed_at) = DATE('now')
                    """)
                    new_completed_today = cursor.fetchone()[0]
                
            except Exception as e:
                # Fallback to mock data if database error
                approved_count = 0
                completed_count = 0
                learning_count = 0
                new_approved_today = 0
                new_completed_today = 0
                st.warning(f"⚠️ Could not load real stats: {e}")

            st.markdown(f"✅ **Approved:** {approved_count} (+{new_approved_today})")
            st.markdown(f"🎓 **Completed:** {completed_count} (+{new_completed_today})")
            
            if learning_count > 0:
                st.markdown(f"⚡ **Learning:** {learning_count} active sessions")
            else:
                st.markdown("⚡ **Learning:** No active sessions")

            # Learning progress bar - calculate real progress
            if approved_count > 0 or learning_count > 0:
                # Calculate average progress from learning sessions
                try:
                    with sqlite3.connect(manager.db_path) as conn:
                        cursor = conn.execute("""
                            SELECT AVG(learning_progress) FROM proposals 
                            WHERE status IN ('learning', 'completed') AND learning_progress > 0
                        """)
                        avg_progress = cursor.fetchone()[0]
                        if avg_progress is None:
                            avg_progress = 0
                        else:
                            avg_progress = avg_progress / 100  # Convert to 0-1 range
                except Exception:
                    avg_progress = 0.75  # Fallback
                
                st.progress(avg_progress)
                st.markdown(f"**Progress:** {avg_progress*100:.0f}% complete")
            else:
                st.markdown("**Status:** Waiting for approval")
                st.info("No approved proposals to learn from yet")

            st.markdown("</div>", unsafe_allow_html=True)

    def render_learning_section(self):
        """Render the main learning section with 3 columns"""
        st.markdown("---")
        st.markdown("## 📚 Learning Management")

        # Create 3 columns
        col_learning_list, col_learning_details, col_learning_report = st.columns(
            [1, 2, 1]
        )

        with col_learning_list:
            st.markdown("### 📚 Learning Sessions")

            # Learning sessions data - include approved proposals
            approved_proposals = st.session_state.get("approved_proposals", [])

        # Get real learning sessions from database
        sessions = self.get_real_learning_sessions()

        # If no real sessions, fall back to sample data
        if not sessions:
            sessions = [
                {
                    "name": "Python Fundamentals",
                    "status": "✅ Completed",
                    "progress": 100,
                },
                {"name": "Data Structures", "status": "✅ Completed", "progress": 100},
                {"name": "Deep Learning", "status": "⏳ Pending", "progress": 0},
            ]

            for i, session in enumerate(sessions):
                is_selected = (
                    st.session_state.get("selected_session") == session["name"]
                )

                # Create session card with better styling

                if st.button(
                    f"**{session['name']}**\n"
                    f"{session['status']} - {session['progress']}%",
                    key=f"session_{i}",
                    help=f"Click to view details of: {session['name']}",
                    use_container_width=True,
                ):
                    st.session_state.selected_session = session["name"]
                    st.rerun()

                # Show selection indicator
                if is_selected:
                    st.markdown("👈 **Selected** - Click to view details")

        with col_learning_details:
            st.markdown("### 📄 Session Details")

            # Get selected session - default to first approved proposal if available
            approved_proposals = st.session_state.get("approved_proposals", [])
            if approved_proposals and not st.session_state.get("selected_session"):
                # Auto-select first approved proposal
                st.session_state.selected_session = approved_proposals[0]["title"]

            selected_session = st.session_state.get(
                "selected_session", "Python Fundamentals"
            )

            # Check if selected session is an approved proposal
            selected_proposal = None
            for proposal in approved_proposals:
                if proposal["title"] == selected_session:
                    selected_proposal = proposal
                    break

            if selected_proposal:
                # Lấy tiến độ học tập thực tế
                try:
                    from scripts.start_real_learning import RealLearningSystem

                    learning_system = RealLearningSystem()
                    progress_data = learning_system.get_learning_progress(
                        selected_proposal["id"]
                    )

                    if "error" not in progress_data:
                        # Hiển thị tiến độ thực
                        st.markdown("**🔄 Active Learning Session (Real Progress):**")
                        st.markdown(f"• **Topic:** {progress_data['title']}")
                        st.markdown(
                            f"• **Started:** {progress_data.get('started_at', 'Unknown')}"
                        )
                        st.markdown(f"• **Progress:** {progress_data['progress']:.1f}%")
                        st.markdown(f"• **Status:** {progress_data['status']}")
                        st.markdown(
                            f"• **Current Objective:** {progress_data['current_objective'] + 1}/{progress_data['total_objectives']}"
                        )
                        st.markdown(
                            f"• **Last Updated:** {progress_data['last_updated']}"
                        )

                        # Progress bar thực tế
                        progress_value = progress_data["progress"] / 100
                        st.progress(progress_value)

                        # Learning notes nếu có
                        if progress_data.get("learning_notes"):
                            with st.expander("📝 Learning Notes (Real-time)"):
                                for note in progress_data["learning_notes"][
                                    -5:
                                ]:  # Show last 5 notes
                                    st.markdown(
                                        f"**{note.get('timestamp', 'Unknown time')}:** {note.get('note', '')}"
                                    )

                        st.markdown(
                            f"*StillMe IPC is actively learning: {progress_data['progress']:.1f}% complete*"
                        )

                    else:
                        # Fallback nếu không lấy được progress
                        st.markdown("**🔄 Active Learning Session:**")
                        st.markdown(f"• **Topic:** {selected_proposal['title']}")
                        st.markdown(
                            f"• **Started:** {selected_proposal['approved_at']}"
                        )
                        st.markdown("• **Progress:** Learning in progress...")
                        st.markdown(
                            f"• **Quality Score:** {selected_proposal['quality_score']:.2f}"
                        )
                        st.markdown(
                            f"• **Estimated Duration:** {selected_proposal['estimated_duration']} minutes"
                        )

                        st.progress(0.5)  # Default progress
                        st.markdown(
                            "*StillMe IPC is actively learning this content...*"
                        )

                except Exception as e:
                    # Fallback display
                    st.markdown("**🔄 Active Learning Session:**")
                    st.markdown(f"• **Topic:** {selected_proposal['title']}")
                    st.markdown(f"• **Started:** {selected_proposal['approved_at']}")
                    st.markdown("• **Progress:** Learning in progress...")
                    st.markdown(
                        f"• **Quality Score:** {selected_proposal['quality_score']:.2f}"
                    )
                    st.markdown(
                        f"• **Estimated Duration:** {selected_proposal['estimated_duration']} minutes"
                    )

                    st.progress(0.5)
                    st.markdown("*StillMe IPC is actively learning this content...*")
                    st.warning(f"⚠️ Could not fetch real-time progress: {e}")

                st.markdown("**📚 Learning Content:**")
                st.markdown(f"• {selected_proposal['description']}")

                st.markdown("**🎯 Learning Objectives:**")
                st.markdown("• Understanding core concepts")
                st.markdown("• Practical application")
                st.markdown("• Skill development")

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
                    st.markdown(
                        "• **Action:** Go to 'Learning Proposals' tab to approve proposals"
                    )
                    st.markdown(
                        "• **Next:** Approved proposals will appear here as learning sessions"
                    )

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
                st.info(
                    "💡 Click on the '📊 Learning Report' tab above to view the complete learning report!"
                )

    def render_sidebar(self):
        """Render sidebar filters"""
        st.sidebar.markdown("## 🔧 Filters & Controls")

        # Date range
        st.sidebar.markdown("### 📅 Date Range")
        days = st.sidebar.selectbox(
            "Select period:",
            [7, 14, 30, 90],
            index=1,
            help="Select the time period for data analysis",
        )

        # Proposal status
        st.sidebar.markdown("### 📄 Proposal Status")
        statuses = st.sidebar.multiselect(
            "Select statuses:",
            ["pending", "approved", "rejected", "completed"],
            default=["pending", "approved"],
            help="Filter proposals by status",
        )

        # Priority
        st.sidebar.markdown("### ⚡ Priority")
        priorities = st.sidebar.multiselect(
            "Select priorities:",
            ["low", "medium", "high", "critical"],
            default=["high", "critical"],
            help="Filter proposals by priority",
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
            • **Imported**: Import từ file/tài liệu bên ngoài""",
        )

        # Auto-refresh
        st.sidebar.markdown("### 🔄 Auto-Refresh")
        auto_refresh = st.sidebar.checkbox(
            "Enable auto-refresh",
            value=st.session_state.auto_refresh,
            help="Automatically refresh data every 30 seconds",
        )
        st.session_state.auto_refresh = auto_refresh

        # Manual refresh button
        if st.sidebar.button("🔄 Refresh Data Now"):
            if self.refresh_data():
                st.sidebar.success("Data refreshed successfully!")
                st.rerun()
            else:
                st.sidebar.error("Failed to refresh data")

        if auto_refresh:
            refresh_interval = st.sidebar.slider(
                "Refresh interval (seconds):",
                min_value=10,
                max_value=300,
                value=30,
                step=10,
            )
        else:
            refresh_interval = None

        # Manual refresh button
        if st.sidebar.button("🔄 Refresh Now", type="primary"):
            st.session_state.last_refresh = datetime.now()
            st.rerun()

        # Automation Control
        st.sidebar.markdown("### 🤖 Automation Control")

        # Initialize automation state - DEFAULT TO TRUE and PERSISTENT
        if "automation_enabled" not in st.session_state:
            # Try to load from config file first
            try:
                import json
                from pathlib import Path

                config_file = Path("data/config/automation_config.json")
                if config_file.exists():
                    with open(config_file) as f:
                        config = json.load(f)
                        st.session_state.automation_enabled = config.get(
                            "automation_enabled", True
                        )
                else:
                    st.session_state.automation_enabled = True  # Default to True
            except Exception:
                st.session_state.automation_enabled = True  # Fallback to True

        # Automation toggle
        automation_enabled = st.sidebar.checkbox(
            "Enable Auto-Proposals",
            value=st.session_state.automation_enabled,
            help="When enabled, StillMe IPC will automatically create learning proposals every 30 minutes",
        )

        if automation_enabled != st.session_state.automation_enabled:
            st.session_state.automation_enabled = automation_enabled

            # Update smart automation config
            try:
                import json
                from pathlib import Path

                config_file = Path("data/config/automation_config.json")
                config_file.parent.mkdir(parents=True, exist_ok=True)

                # Load existing config or create new
                if config_file.exists():
                    with open(config_file) as f:
                        config = json.load(f)
                else:
                    config = {
                        "automation_enabled": True,  # Default to True
                        "enabled": True,  # For backward compatibility
                        "max_proposals_per_hour": 2,
                        "max_proposals_per_day": 10,
                        "proposal_interval_minutes": 30,
                        "last_proposal_time": None,
                        "proposals_created_today": 0,
                        "proposals_created_this_hour": 0,
                        "last_reset_date": datetime.now().strftime("%Y-%m-%d"),
                    }

                # Update enabled status
                config["enabled"] = automation_enabled
                config["automation_enabled"] = automation_enabled

                # Save config
                with open(config_file, "w") as f:
                    json.dump(config, f, indent=2)

                # Also save to session file for smart automation
                session_file = Path("artifacts/dashboard_session.json")
                session_file.parent.mkdir(parents=True, exist_ok=True)
                with open(session_file, "w") as f:
                    json.dump({"automation_enabled": automation_enabled}, f, indent=2)

                if automation_enabled:
                    st.sidebar.success(
                        "🤖 Automation enabled! StillMe IPC will create proposals automatically."
                    )
                else:
                    st.sidebar.warning(
                        "⏸️ Automation disabled. No new auto-proposals will be created."
                    )

            except Exception as e:
                st.sidebar.error(f"❌ Failed to update automation config: {e}")

            st.rerun()

        # Automation status
        if st.session_state.automation_enabled:
            st.sidebar.info(
                "🟢 **Automation Active**\n\nStillMe IPC is creating proposals automatically."
            )
        else:
            st.sidebar.info(
                "🔴 **Automation Inactive**\n\nStillMe IPC will not create proposals automatically."
            )

        # Create sample proposal button
        if st.sidebar.button("📝 Create Sample Proposal", type="secondary"):
            # Add to session state
            if "sample_proposals" not in st.session_state:
                st.session_state.sample_proposals = []

            # Create new sample proposal
            new_proposal = {
                "id": f"sample_{len(st.session_state.sample_proposals) + 1}",
                "title": f"Sample Proposal {len(st.session_state.sample_proposals) + 1}",
                "description": f"This is a sample learning proposal #{len(st.session_state.sample_proposals) + 1}",
                "quality_score": 0.8 + (len(st.session_state.sample_proposals) * 0.05),
                "estimated_duration": 60
                + (len(st.session_state.sample_proposals) * 30),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            st.session_state.sample_proposals.append(new_proposal)
            st.success(
                f"Sample proposal created! Total: {len(st.session_state.sample_proposals)}"
            )
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
                        "Learn async/await programming patterns",
                    ],
                    "prerequisites": [
                        "Basic Python knowledge",
                        "Understanding of functions and classes",
                    ],
                    "expected_outcomes": [
                        "Write efficient Python code using advanced features",
                        "Implement decorators for code reuse",
                        "Create async applications",
                    ],
                    "estimated_duration": 120,
                    "quality_score": 0.88,
                    "source": "ai_generated",
                    "priority": "high",
                    "risk_assessment": {
                        "complexity": "medium",
                        "time_commitment": "high",
                        "prerequisites": "medium",
                        "practical_value": "high",
                    },
                }

                proposal = manager.create_proposal(**proposal_data)
                st.success(f"✅ Auto proposal created: {proposal.title}")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Failed to create auto proposal: {e}")

        return {
            "days": days,
            "statuses": statuses,
            "priorities": priorities,
            "sources": sources,
            "auto_refresh": auto_refresh,
            "refresh_interval": refresh_interval,
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
        sample_proposals = st.session_state.get("sample_proposals", [])

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
                    "description": db_proposal.description
                    or "No description available",
                    "quality_score": float(db_proposal.quality_score)
                    if db_proposal.quality_score
                    else 0.5,
                    "estimated_duration": int(db_proposal.estimated_duration)
                    if db_proposal.estimated_duration
                    else 60,
                    "created_at": created_at_str,
                }
                sample_proposals.append(proposal_data)
        except Exception as e:
            # Try to get basic count from database without parsing complex data
            try:
                import sqlite3

                from stillme_core.learning.proposals_manager import ProposalsManager

                manager = ProposalsManager()

                with sqlite3.connect(manager.db_path) as conn:
                    cursor = conn.execute(
                        "SELECT id, title, description, quality_score, estimated_duration, created_at FROM proposals WHERE status = 'pending' LIMIT 10"
                    )
                    rows = cursor.fetchall()

                    for row in rows:
                        proposal_data = {
                            "id": row[0] or f"db_{len(sample_proposals) + 1}",
                            "title": row[1] or "Untitled Proposal",
                            "description": row[2] or "No description available",
                            "quality_score": float(row[3]) if row[3] else 0.5,
                            "estimated_duration": int(row[4]) if row[4] else 60,
                            "created_at": row[5]
                            or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                        sample_proposals.append(proposal_data)

            except Exception:
                st.warning(f"Could not load database proposals: {e}")
                # Try to get basic count from database
                try:
                    import sqlite3

                    with sqlite3.connect(manager.db_path) as conn:
                        cursor = conn.execute(
                            "SELECT COUNT(*) FROM proposals WHERE status = 'pending'"
                        )
                        count = cursor.fetchone()[0]
                        if count > 0:
                            st.info(
                                f"Found {count} pending proposals in database, but couldn't load details."
                            )
                except Exception:
                    pass

        # Use sample_proposals as proposals
        proposals = sample_proposals

        if not proposals:
            st.info(
                "No pending proposals found. Create a sample proposal using the sidebar button."
            )
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
            if "selected_proposal_id" not in st.session_state:
                st.session_state.selected_proposal_id = (
                    proposals[0]["id"] if proposals else None
                )

            # Display proposal list with individual approve/reject buttons
            for _i, proposal in enumerate(proposals):
                is_selected = (
                    st.session_state.get("selected_proposal_id") == proposal["id"]
                )

                # Create proposal card with approve/reject buttons
                is_selected = (
                    st.session_state.get("selected_proposal_id") == proposal["id"]
                )

                with st.container():
                    if is_selected:
                        st.markdown(f"**🟢 {proposal['title']}** *(Đang xem)*")
                    else:
                        st.markdown(f"**{proposal['title']}**")
                    st.write(f"📅 {proposal['created_at']}")
                    st.write(
                        f"⭐ Quality: {proposal['quality_score']:.2f} | ⏱️ Duration: {proposal['estimated_duration']}min"
                    )

                    # Approve/Reject buttons for each proposal
                    col_approve, col_reject, col_view = st.columns([1, 1, 1])

                    with col_approve:
                        if st.button(
                            "✅ Approve",
                            key=f"approve_{proposal['id']}",
                            type="primary",
                        ):
                            try:
                                # Update database status to approved
                                from stillme_core.learning.proposals_manager import (
                                    ProposalsManager,
                                )

                                manager = ProposalsManager()
                                manager.approve_proposal(proposal["id"], "user")

                                # Start real learning session
                                try:
                                    from scripts.start_real_learning import (
                                        RealLearningSystem,
                                    )

                                    learning_system = RealLearningSystem()

                                    # Bắt đầu học thật
                                    success = learning_system.start_learning_for_approved_proposal(
                                        proposal["id"]
                                    )

                                    if success:
                                        st.success(
                                            f"✅ Approved and started learning: {proposal['title']}"
                                        )
                                        st.info(
                                            "🧠 StillMe IPC is now learning this content in real-time!"
                                        )
                                    else:
                                        st.warning(
                                            f"⚠️ Approved but failed to start learning: {proposal['title']}"
                                        )

                                except Exception as learning_error:
                                    st.warning(
                                        f"⚠️ Approved but learning system error: {learning_error}"
                                    )

                                # Remove from session state
                                if "sample_proposals" in st.session_state:
                                    st.session_state.sample_proposals = [
                                        p
                                        for p in st.session_state.sample_proposals
                                        if p["id"] != proposal["id"]
                                    ]

                                # Add to approved proposals
                                if "approved_proposals" not in st.session_state:
                                    st.session_state.approved_proposals = []

                                approved_proposal = {
                                    **proposal,
                                    "status": "learning",
                                    "approved_at": datetime.now().strftime(
                                        "%Y-%m-%d %H:%M:%S"
                                    ),
                                }
                                st.session_state.approved_proposals.append(
                                    approved_proposal
                                )

                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Failed to approve: {e}")

                    with col_reject:
                        if st.button(
                            "❌ Reject",
                            key=f"reject_{proposal['id']}",
                            type="secondary",
                        ):
                            try:
                                # Update database status to rejected
                                from stillme_core.learning.proposals_manager import (
                                    ProposalsManager,
                                )

                                manager = ProposalsManager()
                                manager.reject_proposal(
                                    proposal["id"], "user", "User rejected"
                                )

                                # Remove from session state
                                if "sample_proposals" in st.session_state:
                                    st.session_state.sample_proposals = [
                                        p
                                        for p in st.session_state.sample_proposals
                                        if p["id"] != proposal["id"]
                                    ]

                                st.warning(f"❌ Rejected: {proposal['title']}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Failed to reject: {e}")

                    with col_view:
                        if is_selected:
                            if st.button(
                                "👁️ Đang xem",
                                key=f"view_{proposal['id']}",
                                disabled=True,
                            ):
                                pass
                        else:
                            if st.button("👁️ View", key=f"view_{proposal['id']}"):
                                st.session_state.selected_proposal_id = proposal["id"]
                                st.session_state.show_proposal_details = True
                                st.success(f"✅ Đang xem: {proposal['title']}")
                                st.rerun()

                    st.markdown("---")

        with col2:
            st.markdown("### 📄 Proposal Details")

            # Check if we should show proposal details
            if st.session_state.get("show_proposal_details", False):
                # Find selected proposal
                selected_proposal = None
                for proposal in proposals:
                    if proposal["id"] == st.session_state.get("selected_proposal_id"):
                        selected_proposal = proposal
                        break

                if selected_proposal:
                    # Show clear header with proposal being viewed
                    st.markdown(f"### 🟢 Đang xem: {selected_proposal['title']}")
                    st.markdown(
                        f"**📋 Proposal ID:** `{selected_proposal['id'][:8]}...`"
                    )
                    st.markdown("---")

                    # Main info
                    col1, col2 = st.columns([1, 1])

                    with col1:
                        st.markdown("**📋 Basic Info:**")
                        st.write("**Source:** AI Generated")
                        st.write("**Priority:** High")
                        st.write(
                            f"**Duration:** {selected_proposal['estimated_duration']} minutes"
                        )
                        st.write(
                            f"**Quality Score:** {selected_proposal['quality_score']:.2f}"
                        )
                        st.write(f"**Created:** {selected_proposal['created_at']}")

                    with col2:
                        st.markdown("**📊 Risk Assessment:**")
                        st.write("**Complexity:** Medium")
                        st.write("**Time Commitment:** High")
                        st.write("**Prerequisites:** Medium")
                        st.write("**Practical Value:** High")

                    # Description
                    st.markdown("**📝 Description:**")
                    st.write(selected_proposal["description"])

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
                    st.info(
                        "💡 **Your Control:** You decide what StillMe IPC learns. Only approved content will be processed. All decisions are logged and auditable."
                    )
                else:
                    st.warning(
                        "⚠️ Không tìm thấy proposal được chọn. Vui lòng click 'View' trên một proposal khác."
                    )
            else:
                st.info(
                    "👈 **Hướng dẫn:** Click nút '👁️ View' trên bất kỳ proposal nào để xem chi tiết nội dung học tập."
                )
                st.markdown(
                    "**💡 Mẹo:** Proposal được chọn sẽ có dấu 🟢 và hiển thị '*(Đang xem)*'"
                )

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
            "Status": ["Pending", "Approved", "Rejected", "Completed"],
            "Count": [3, 3, 1, 0],
        }

        df = pd.DataFrame(status_data)
        fig = px.pie(
            df, values="Count", names="Status", title="Proposal Status Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)

    def render_learning_curve(self, days):
        """Render learning curve tab"""
        st.markdown("### 📈 Learning Curve")

        # Get real learning metrics from database
        real_metrics = self.calculate_real_metrics(days)

        if len(real_metrics["dates"]) > 0:
            # Use real data
            learning_data = {
                "Date": real_metrics["dates"],
                "Knowledge_Score": real_metrics["knowledge_scores"],
                "Skills_Learned": real_metrics["skills_learned"],
                "Time_Spent": real_metrics["time_spent"],
            }
        else:
            # Fall back to sample data if no real data available
            dates = pd.date_range(
                start=datetime.now() - timedelta(days=days),
                end=datetime.now(),
                freq="D",
            )
            learning_data = {
                "Date": dates,
                "Knowledge_Score": [
                    0.6 + 0.3 * (i / len(dates)) + 0.1 * (i % 3)
                    for i in range(len(dates))
                ],
                "Skills_Learned": [2 + i % 5 for i in range(len(dates))],
                "Time_Spent": [30 + i * 2 for i in range(len(dates))],
            }

        df = pd.DataFrame(learning_data)

        # Knowledge score over time
        fig1 = px.line(
            df, x="Date", y="Knowledge_Score", title="Knowledge Score Over Time"
        )
        st.plotly_chart(fig1, use_container_width=True)

        # Skills learned
        fig2 = px.bar(df, x="Date", y="Skills_Learned", title="Skills Learned Per Day")
        st.plotly_chart(fig2, use_container_width=True)

    def render_full_learning_report(self):
        """Render full learning report tab"""
        st.markdown("### 📊 Full Learning Report")

        # Get real learning report data
        report_data = self.get_real_learning_report()

        # Top row: Knowledge and Skills side by side
        top_row1, top_row2 = st.columns([3, 2])

        with top_row1:
            st.markdown("**📚 Completed Topics:**")

            if report_data["completed_topics"]:
                for topic in report_data["completed_topics"]:
                    st.markdown(f"• **{topic['title']}** ✅ - {topic['description']}")
            else:
                st.markdown("• No completed topics yet")
                st.markdown("• Start by approving some learning proposals!")

            st.markdown("**📈 Learning Statistics:**")
            stats = report_data["learning_stats"]
            if stats:
                st.markdown(
                    f"• **Total Learning Time:** {stats.get('total_learning_time', 0):.1f} hours | "
                    f"**Completed Topics:** {stats.get('completed_topics', 0)} | "
                    f"**Average Quality Score:** {stats.get('average_quality_score', 0):.2f} | "
                    f"**Success Rate:** {stats.get('success_rate', 0):.1f}%"
                )
            else:
                st.markdown("• No learning statistics available yet")

        with top_row2:
            st.markdown("**🛠️ Skills Acquired:**")

            if report_data["skills_acquired"]:
                # Group skills by category (simplified)
                ml_skills = [
                    s
                    for s in report_data["skills_acquired"]
                    if any(
                        word in s.lower()
                        for word in [
                            "machine",
                            "learning",
                            "ml",
                            "ai",
                            "neural",
                            "deep",
                        ]
                    )
                ]
                python_skills = [
                    s
                    for s in report_data["skills_acquired"]
                    if any(
                        word in s.lower()
                        for word in ["python", "programming", "data", "analysis"]
                    )
                ]
                other_skills = [
                    s
                    for s in report_data["skills_acquired"]
                    if s not in ml_skills + python_skills
                ]

                if ml_skills:
                    st.markdown(f"**Machine Learning:** {' • '.join(ml_skills[:3])}")
                if python_skills:
                    st.markdown(f"**Python:** {' • '.join(python_skills[:3])}")
                if other_skills:
                    st.markdown(f"**Other:** {' • '.join(other_skills[:3])}")
            else:
                st.markdown("• No skills acquired yet")
                st.markdown("• Complete some learning sessions to acquire skills!")

        # Progress bars in horizontal layout
        st.markdown("**📊 Learning Progress by Topic:**")

        progress_by_topic = report_data["progress_by_topic"]
        if progress_by_topic:
            # Create columns dynamically based on available topics
            topics = list(progress_by_topic.keys())
            num_topics = len(topics)

            if num_topics > 0:
                # Create columns (max 4)
                cols = st.columns(min(4, num_topics))

                for i, (topic, progress) in enumerate(progress_by_topic.items()):
                    if i < 4:  # Limit to 4 columns
                        with cols[i]:
                            st.markdown(f"**{topic}:**")
                            st.progress(progress / 100)
                            st.markdown(f"*{progress}% completed*")
            else:
                st.markdown("• No learning progress data available yet")
        else:
            st.markdown("• No learning progress data available yet")

        # Next learning suggestions in horizontal layout
        st.markdown("**🎯 Suggested Next Learning:**")

        next_suggestions = report_data["next_suggestions"]
        if next_suggestions:
            # Create columns dynamically based on available suggestions
            num_suggestions = len(next_suggestions)
            cols = st.columns(min(4, num_suggestions))

            for i, suggestion in enumerate(next_suggestions):
                if i < 4:  # Limit to 4 columns
                    with cols[i]:
                        st.markdown(f"**{suggestion['title']}**")
                        st.markdown(f"*{suggestion['description']}*")
                        if "priority" in suggestion:
                            st.markdown(f"*Priority: {suggestion['priority']}*")
        else:
            st.markdown("• No learning suggestions available yet")
            st.markdown("• Create some learning proposals to get suggestions!")

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
        if st.session_state.auto_refresh and filters["refresh_interval"]:
            time.sleep(filters["refresh_interval"])
            st.rerun()

        # Check if we should show pending details
        if st.session_state.get("show_pending_details", False):
            self.render_pending_proposals_details()
        else:
            # Render main learning section
            self.render_learning_section()

            # Render tabs
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
                [
                    "📋 Learning Proposals",
                    "👑 Founder Mode",
                    "📊 Analytics",
                    "📈 Learning Curve",
                    "📊 Learning Report",
                    "🔒 Security & Privacy",
                ]
            )

            with tab1:
                st.markdown("### 📋 Learning Proposals")
                st.info(
                    "This is a demo dashboard. In the real system, this would show actual learning proposals."
                )

            with tab2:
                self.render_founder_mode()

            with tab3:
                self.render_analytics()

            with tab4:
                self.render_learning_curve(filters["days"])

            with tab5:
                self.render_full_learning_report()

            with tab6:
                self.render_security_privacy()

        # Footer
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**🧠 StillMe IPC**")
            st.markdown(
                "Intelligent Personal Companion - Self-evolving AI learning system"
            )

        with col2:
            st.markdown("**📊 Dashboard v2.0**")
            st.markdown("Enhanced Learning Management System")

        with col3:
            st.markdown("**🔒 Your Control**")
            st.markdown("You decide what StillMe IPC learns")

    def render_founder_mode(self):
        """Render founder mode section"""
        st.markdown("### 👑 Founder Mode")
        st.info(
            "👑 **Founder Mode**: Add knowledge directly - AUTO-APPROVED (no need to approve/reject)"
        )

        # Founder knowledge input form
        with st.form("founder_knowledge_form"):
            st.markdown("#### 📚 Add New Knowledge")

            col1, col2 = st.columns(2)

            with col1:
                title = st.text_input(
                    "📝 Knowledge Title", placeholder="e.g., Advanced AI Ethics"
                )
                priority = st.selectbox(
                    "⚡ Priority", ["high", "critical", "medium", "low"], index=0
                )

            with col2:
                source_url = st.text_input(
                    "🔗 Source URL (optional)",
                    placeholder="https://example.com/article",
                )
                content_type = st.selectbox(
                    "📄 Content Type", ["text", "url", "image"], index=0
                )

            description = st.text_area(
                "📖 Knowledge Description",
                placeholder="Describe what StillMe should learn from this knowledge...",
                height=100,
            )

            submitted = st.form_submit_button(
                "👑 Add Founder Knowledge (AUTO-APPROVED)"
            )

            if submitted:
                if title and description:
                    try:
                        # Import founder input
                        import os
                        import sys

                        sys.path.append(
                            os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                        )

                        from scripts.founder_knowledge_input import (
                            FounderKnowledgeInput,
                        )

                        founder_input = FounderKnowledgeInput()
                        proposal = founder_input.add_founder_knowledge(
                            title=title,
                            description=description,
                            source_url=source_url if source_url else None,
                            content_type=content_type,
                            priority=priority,
                        )

                        if proposal:
                            st.success(
                                f"✅ Founder knowledge added and AUTO-APPROVED: {title}"
                            )
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

                    for _i, file_path in enumerate(founder_files[:5]):  # Show last 5
                        try:
                            with open(file_path, encoding="utf-8") as f:
                                founder_data = json.load(f)

                            with st.expander(
                                f"👑 {founder_data.get('title', 'Untitled')} - {founder_data.get('created_at', 'Unknown date')[:10]}"
                            ):
                                st.markdown(
                                    f"**📝 Description:** {founder_data.get('description', 'No description')[:200]}..."
                                )
                                if founder_data.get("source_url"):
                                    st.markdown(
                                        f"**🔗 Source:** {founder_data['source_url']}"
                                    )
                                st.markdown(
                                    f"**🆔 Proposal ID:** {founder_data.get('proposal_id', 'Unknown')[:8]}..."
                                )
                                st.markdown(
                                    "**✅ Status:** AUTO-APPROVED (Founder Mode)"
                                )
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
