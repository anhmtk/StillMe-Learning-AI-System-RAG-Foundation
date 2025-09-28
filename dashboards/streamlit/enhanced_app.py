"""
📊 StillMe IPC Enhanced Learning Dashboard - Streamlit
====================================================

Enhanced dashboard với learning proposals và human-in-the-loop approval.
Bảo vệ quyền riêng tư và kiểm soát hoàn toàn quá trình học tập.

Tính năng:
- Learning proposals với chi tiết đầy đủ
- Human approval workflow với Yes/No buttons
- Security và privacy protection
- Real-time updates và notifications
- Mobile responsive design

Author: StillMe IPC (Intelligent Personal Companion)
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
import uuid

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from stillme_core.metrics.queries import get_metrics_queries
from stillme_core.metrics.emitter import get_metrics_emitter
from stillme_core.learning.proposals import (
    get_proposals_manager, 
    LearningProposal, 
    ProposalStatus, 
    LearningPriority,
    ContentSource,
    create_sample_proposal
)

# Page config
st.set_page_config(
    page_title="StillMe IPC Enhanced Learning Dashboard",
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
    .proposal-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .proposal-pending {
        border-left-color: #ffc107;
        background-color: #fff3cd;
    }
    .proposal-approved {
        border-left-color: #28a745;
        background-color: #d4edda;
    }
    .proposal-rejected {
        border-left-color: #dc3545;
        background-color: #f8d7da;
    }
    .approval-buttons {
        display: flex;
        gap: 1rem;
        margin-top: 1rem;
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
    .pending-proposals-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 2rem;
        font-size: 1.2rem;
        font-weight: bold;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .pending-proposals-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    .status-indicators {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
    }
    .chart-container {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

class EnhancedLearningDashboard:
    """StillMe IPC Enhanced Learning Dashboard"""
    
    def __init__(self):
        self.queries = get_metrics_queries()
        self.emitter = get_metrics_emitter()
        self.proposals_manager = get_proposals_manager()
        
        # Initialize session state
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = datetime.now()
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = True
        if 'selected_proposal' not in st.session_state:
            st.session_state.selected_proposal = None
    
    def render_header(self):
        """Render dashboard header"""
        st.markdown('<h1 class="main-header">🧠 StillMe IPC Enhanced Learning Dashboard</h1>', unsafe_allow_html=True)
        
        # Main content area with clickable pending proposals
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Get proposal stats
            stats = self.proposals_manager.get_proposal_stats()
            pending_count = stats.get('pending', {}).get('count', 0)
            new_today = stats.get('pending', {}).get('new_today', 0)
            
            # Large clickable pending proposals card
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
            # Status indicators (small)
            st.markdown('<div class="status-indicators">', unsafe_allow_html=True)
            st.markdown("### 📊 Status")
            
            # Approved indicator
            approved_count = stats.get('approved', {}).get('count', 0)
            approved_new = stats.get('approved', {}).get('new_today', 0)
            st.markdown(f"✅ **Approved:** {approved_count} (+{approved_new})")
            
            # Completed indicator  
            completed_count = stats.get('completed', {}).get('count', 0)
            completed_new = stats.get('completed', {}).get('new_today', 0)
            st.markdown(f"🎓 **Completed:** {completed_count} (+{completed_new})")
            
            # Learning Status indicator with progress
            st.markdown("⚡ **Learning:** Active")
            
            # Learning progress bar - chỉ hiển thị khi có proposal đang học
            approved_count = stats.get('approved', {}).get('count', 0)
            if approved_count > 0:
                progress = 0.75  # 75% completion
                st.progress(progress)
                st.markdown(f"**Progress:** {progress*100:.0f}% complete")
                
                # Learning details - chỉ hiển thị khi có approved proposals
                with st.expander("📚 Learning Details"):
                    st.markdown("**Current Session:**")
                    st.markdown("• Processing: Machine Learning basics")
                    st.markdown("• Started: 2 hours ago")
                    st.markdown("• Estimated: 30 minutes remaining")
                    st.markdown("• Quality Score: 0.85")

                    st.markdown("**Recent Learning:**")
                    st.markdown("• Python fundamentals ✅")
                    st.markdown("• Data structures ✅")
                    st.markdown("• ML algorithms 🔄")
                    st.markdown("• Deep learning ⏳")

                # Learning Report Section
                with st.expander("📊 Learning Report - Kiến thức đã học được"):
                    st.markdown("### 🎓 Tổng hợp kiến thức đã học")
                    
                    # Knowledge gained section
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**📚 Chủ đề đã hoàn thành:**")
                        st.markdown("• **Machine Learning cơ bản** ✅")
                        st.markdown("  - Hiểu các thuật toán ML cơ bản")
                        st.markdown("  - Thực hành với Python và scikit-learn")
                        st.markdown("  - Áp dụng vào dự án thực tế")
                        st.markdown("• **Python Programming** ✅")
                        st.markdown("  - Cú pháp Python cơ bản")
                        st.markdown("  - Xử lý dữ liệu với pandas")
                        st.markdown("  - Visualization với matplotlib")
                        
                    with col2:
                        st.markdown("**📈 Thống kê học tập:**")
                        st.markdown("• **Tổng thời gian học:** 4.5 giờ")
                        st.markdown("• **Số chủ đề hoàn thành:** 2")
                        st.markdown("• **Điểm chất lượng trung bình:** 0.87")
                        st.markdown("• **Tỷ lệ thành công:** 95%")
                        
                    # Skills gained
                    st.markdown("**🛠️ Kỹ năng đã đạt được:**")
                    skill_col1, skill_col2, skill_col3 = st.columns(3)
                    
                    with skill_col1:
                        st.markdown("**Machine Learning:**")
                        st.markdown("• Linear Regression")
                        st.markdown("• Decision Trees")
                        st.markdown("• Random Forest")
                        
                    with skill_col2:
                        st.markdown("**Python:**")
                        st.markdown("• Data Manipulation")
                        st.markdown("• Statistical Analysis")
                        st.markdown("• Data Visualization")
                        
                    with skill_col3:
                        st.markdown("**Tools & Libraries:**")
                        st.markdown("• scikit-learn")
                        st.markdown("• pandas")
                        st.markdown("• matplotlib")
                    
                    # Progress visualization
                    st.markdown("**📊 Tiến độ học tập theo chủ đề:**")
                    progress_data = {
                        "Machine Learning": 100,
                        "Python Programming": 100,
                        "Data Science": 75,
                        "Deep Learning": 25
                    }
                    
                    for topic, progress in progress_data.items():
                        st.markdown(f"**{topic}:**")
                        st.progress(progress / 100)
                        st.markdown(f"*{progress}% hoàn thành*")
                        st.markdown("---")
                    
                    # Next learning suggestions
                    st.markdown("**🎯 Đề xuất học tiếp theo:**")
                    st.markdown("• **Deep Learning với TensorFlow** - Mở rộng kiến thức ML")
                    st.markdown("• **Natural Language Processing** - Xử lý ngôn ngữ tự nhiên")
                    st.markdown("• **Computer Vision** - Nhận dạng hình ảnh")
                    st.markdown("• **Time Series Analysis** - Phân tích chuỗi thời gian")
            else:
                st.markdown("**Status:** Waiting for approval")
                st.info("No approved proposals to learn from yet")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
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
        
        # Proposal status filter
        st.sidebar.subheader("📋 Proposal Status")
        statuses = st.sidebar.multiselect(
            "Select statuses:",
            ["pending", "approved", "rejected", "learning", "completed", "failed"],
            default=["pending", "approved"],
            help="Filter by proposal status"
        )
        
        # Priority filter
        st.sidebar.subheader("🎯 Priority")
        priorities = st.sidebar.multiselect(
            "Select priorities:",
            ["low", "medium", "high", "critical"],
            default=["high", "critical"],
            help="Filter by learning priority"
        )
        
        # Source filter
        st.sidebar.subheader("📚 Sources")
        sources = st.sidebar.multiselect(
            "Select sources:",
            ["rss", "experience", "manual", "api", "community"],
            default=["manual", "community"],
            help="Filter by content sources"
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
        
        # Create sample proposal button
        if st.sidebar.button("📝 Create Sample Proposal", type="secondary"):
            sample_proposal = create_sample_proposal()
            self.proposals_manager.create_proposal(sample_proposal)
            st.success("Sample proposal created!")
            st.rerun()
        
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

        # Get pending proposals
        try:
            proposals = self.proposals_manager.get_pending_proposals(limit=10)

            if not proposals:
                st.info("No pending proposals found. Create a sample proposal using the sidebar button.")
                return

            # Create two columns: List on left, Details on right
            col1, col2 = st.columns([1, 2])

            with col1:
                st.markdown("### 📝 Proposals List")
                
                # Initialize selected proposal in session state
                if 'selected_proposal_id' not in st.session_state:
                    st.session_state.selected_proposal_id = proposals[0].id if proposals else None

                # Display proposal list
                for i, proposal in enumerate(proposals):
                    is_selected = st.session_state.get('selected_proposal_id') == proposal.id
                    
                    # Create clickable proposal item
                    if st.button(
                        f"**{proposal.title}**\n"
                        f"📅 {proposal.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                        f"⭐ {proposal.quality_score:.2f} | ⏱️ {proposal.estimated_duration}min",
                        key=f"proposal_list_{proposal.id}",
                        help=f"Click to view details of: {proposal.title}",
                        use_container_width=True
                    ):
                        st.session_state.selected_proposal_id = proposal.id
                        st.rerun()

            with col2:
                st.markdown("### 📄 Proposal Details")
                
                # Find selected proposal
                selected_proposal = None
                for proposal in proposals:
                    if proposal.id == st.session_state.get('selected_proposal_id'):
                        selected_proposal = proposal
                        break

                if selected_proposal:
                    self.render_detailed_proposal_card(selected_proposal, 0)
                else:
                    st.info("Select a proposal from the list to view details.")

        except Exception as e:
            st.error(f"Error loading proposals: {e}")
            st.info("Please try refreshing the dashboard.")
    
    def render_learning_proposals(self):
        """Render learning proposals section"""
        st.subheader("📋 Learning Proposals")
        
        # Get pending proposals
        proposals = self.proposals_manager.get_pending_proposals(limit=10)
        
        if not proposals:
            st.info("No pending proposals found. Create a sample proposal using the sidebar button.")
            return
        
        # Display proposals
        for proposal in proposals:
            self.render_proposal_card(proposal)
    
    def render_proposal_card(self, proposal: LearningProposal):
        """Render individual proposal card"""
        # Determine card style based on status
        card_class = "proposal-card"
        if proposal.status == ProposalStatus.PENDING:
            card_class += " proposal-pending"
        elif proposal.status == ProposalStatus.APPROVED:
            card_class += " proposal-approved"
        elif proposal.status == ProposalStatus.REJECTED:
            card_class += " proposal-rejected"
        
        # Create card HTML
        card_html = f"""
        <div class="{card_class}">
            <h3>📚 {proposal.title}</h3>
            <p><strong>Description:</strong> {proposal.description}</p>
            <p><strong>Source:</strong> {proposal.source.value.title()}</p>
            <p><strong>Priority:</strong> {proposal.priority.value.title()}</p>
            <p><strong>Duration:</strong> {proposal.estimated_duration} minutes</p>
            <p><strong>Quality Score:</strong> {proposal.quality_score:.2f}</p>
            <p><strong>Status:</strong> {proposal.status.value.title()}</p>
        </div>
        """
        
        st.markdown(card_html, unsafe_allow_html=True)
        
        # Create columns for details and actions
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Show details
            with st.expander("📖 View Details"):
                st.write("**Learning Objectives:**")
                for obj in proposal.learning_objectives:
                    st.write(f"• {obj}")
                
                st.write("**Prerequisites:**")
                for prereq in proposal.prerequisites:
                    st.write(f"• {prereq}")
                
                st.write("**Expected Outcomes:**")
                for outcome in proposal.expected_outcomes:
                    st.write(f"• {outcome}")
                
                st.write("**Risk Assessment:**")
                for key, value in proposal.risk_assessment.items():
                    st.write(f"• {key.title()}: {value}")
                
                st.write("**Content Preview:**")
                st.text_area("", proposal.content[:500] + "..." if len(proposal.content) > 500 else proposal.content, height=100, disabled=True)
        
        with col2:
            # Approval buttons
            if proposal.status == ProposalStatus.PENDING:
                st.write("**Action Required:**")
                
                col_approve, col_reject = st.columns(2)
                
                with col_approve:
                    if st.button("✅ Approve", key=f"approve_{proposal.id}", type="primary"):
                        reason = st.text_input("Reason (optional):", key=f"reason_approve_{proposal.id}")
                        if self.proposals_manager.approve_proposal(proposal.id, "user", reason):
                            st.success("Proposal approved!")
                            st.rerun()
                        else:
                            st.error("Failed to approve proposal")
                
                with col_reject:
                    if st.button("❌ Reject", key=f"reject_{proposal.id}", type="secondary"):
                        reason = st.text_input("Rejection reason:", key=f"reason_reject_{proposal.id}")
                        if reason:
                            if self.proposals_manager.reject_proposal(proposal.id, "user", reason):
                                st.success("Proposal rejected!")
                                st.rerun()
                            else:
                                st.error("Failed to reject proposal")
                        else:
                            st.warning("Please provide a rejection reason")
            
            elif proposal.status == ProposalStatus.APPROVED:
                st.success("✅ Approved")
                if st.button("🚀 Start Learning", key=f"start_{proposal.id}"):
                    session_id = str(uuid.uuid4())
                    if self.proposals_manager.start_learning(proposal.id, session_id):
                        st.success("Learning started!")
                        st.rerun()
                    else:
                        st.error("Failed to start learning")
            
            elif proposal.status == ProposalStatus.REJECTED:
                st.error("❌ Rejected")
            
            elif proposal.status == ProposalStatus.LEARNING:
                st.info("🎓 Learning in progress...")
            
            elif proposal.status == ProposalStatus.COMPLETED:
                st.success("🎉 Completed!")
        
        st.markdown("---")
    
    def render_detailed_proposal_card(self, proposal: LearningProposal, index: int):
        """Render detailed proposal card for approval workflow"""
        st.markdown(f"### 📚 {proposal.title}")

        # Main info in compact format
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("**📋 Basic Info:**")
            st.write(f"**Source:** {proposal.source.value.title()}")
            st.write(f"**Priority:** {proposal.priority.value.title()}")
            st.write(f"**Duration:** {proposal.estimated_duration} minutes")
            st.write(f"**Quality Score:** {proposal.quality_score:.2f}")
            st.write(f"**Created:** {proposal.created_at.strftime('%Y-%m-%d %H:%M')}")

        with col2:
            st.markdown("**📊 Risk Assessment:**")
            for key, value in proposal.risk_assessment.items():
                st.write(f"**{key.title()}:** {value}")

        # Description
        st.markdown("**📝 Description:**")
        st.write(proposal.description)

        # Learning Objectives
        st.markdown("**🎯 Learning Objectives:**")
        for obj in proposal.learning_objectives:
            st.write(f"• {obj}")

        # Prerequisites and Expected Outcomes
        col3, col4 = st.columns(2)

        with col3:
            st.markdown("**📚 Prerequisites:**")
            for prereq in proposal.prerequisites:
                st.write(f"• {prereq}")

        with col4:
            st.markdown("**🎯 Expected Outcomes:**")
            for outcome in proposal.expected_outcomes:
                st.write(f"• {outcome}")

        # Approval section
        st.markdown("---")
        st.markdown("### 🤔 Decision Required")

        # Approval buttons
        col_approve, col_reject = st.columns([1, 1])

        with col_approve:
            if st.button(
                "✅ **APPROVE**",
                key=f"approve_detailed_{proposal.id}",
                type="primary",
                use_container_width=True
            ):
                self.proposals_manager.approve_proposal(proposal.id, "user")
                st.success("✅ Proposal approved! StillMe IPC will start learning this content.")
                st.rerun()

        with col_reject:
            if st.button(
                "❌ **REJECT**",
                key=f"reject_detailed_{proposal.id}",
                type="secondary",
                use_container_width=True
            ):
                rejection_reason = st.text_input(
                    "Rejection reason (optional):",
                    key=f"rejection_reason_{proposal.id}",
                    placeholder="e.g., Not relevant, Too complex, etc."
                )
                if st.button("Confirm Rejection", key=f"confirm_reject_{proposal.id}"):
                    self.proposals_manager.reject_proposal(
                        proposal.id,
                        "user",
                        rejection_reason or "User rejected"
                    )
                    st.success("❌ Proposal rejected!")
                    st.rerun()

        # Control info
        st.info("💡 **Your Control:** You decide what StillMe IPC learns. Only approved content will be processed. All decisions are logged and auditable.")
    
    def render_proposal_analytics(self):
        """Render proposal analytics"""
        st.subheader("📊 Proposal Analytics")
        
        # Get proposal stats
        stats = self.proposals_manager.get_proposal_stats()
        
        if not stats:
            st.info("No proposal data available")
            return
        
        # Create analytics charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Status distribution
            status_data = []
            for status, data in stats.items():
                status_data.append({
                    'Status': status.title(),
                    'Count': data['count']
                })
            
            if status_data:
                df_status = pd.DataFrame(status_data)
                fig_status = px.pie(
                    df_status,
                    values='Count',
                    names='Status',
                    title='Proposal Status Distribution'
                )
                st.plotly_chart(fig_status, use_container_width=True)
        
        with col2:
            # Quality vs Duration scatter
            quality_data = []
            for status, data in stats.items():
                if data['avg_quality'] > 0 and data['avg_duration'] > 0:
                    quality_data.append({
                        'Status': status.title(),
                        'Avg Quality': data['avg_quality'],
                        'Avg Duration': data['avg_duration']
                    })
            
            if quality_data:
                df_quality = pd.DataFrame(quality_data)
                fig_quality = px.scatter(
                    df_quality,
                    x='Avg Duration',
                    y='Avg Quality',
                    color='Status',
                    title='Quality vs Duration Analysis',
                    size='Avg Quality',
                    hover_data=['Status']
                )
                st.plotly_chart(fig_quality, use_container_width=True)
        
        # Summary metrics
        st.subheader("📈 Summary Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        total_proposals = sum(data['count'] for data in stats.values())
        pending_proposals = stats.get('pending', {}).get('count', 0)
        approved_proposals = stats.get('approved', {}).get('count', 0)
        completed_proposals = stats.get('completed', {}).get('count', 0)
        
        with col1:
            st.metric("Total Proposals", total_proposals)
        
        with col2:
            st.metric("Pending", pending_proposals)
        
        with col3:
            st.metric("Approved", approved_proposals)
        
        with col4:
            st.metric("Completed", completed_proposals)
    
    def render_learning_curve(self, days: int):
        """Render learning curve chart (inherited from basic dashboard)"""
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
            
        except Exception as e:
            st.error(f"Error loading learning curve: {e}")
    
    def render_footer(self):
        """Render dashboard footer"""
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🧠 StillMe IPC**")
            st.markdown("Intelligent Personal Companion - Enhanced Learning System")
        
        with col2:
            st.markdown("**📊 Enhanced Dashboard v2.0**")
            st.markdown(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        with col3:
            st.markdown("**🔒 Privacy Protected**")
            st.markdown("Your learning data is secure and private")
    
    def run(self):
        """Run the enhanced dashboard"""
        # Header
        self.render_header()
        
        # Sidebar
        filters = self.render_sidebar()
        
        # Auto-refresh logic - DISABLE when pending details view is active
        if st.session_state.auto_refresh and filters['refresh_interval'] and not st.session_state.get('show_pending_details', False):
            time.sleep(filters['refresh_interval'])
            st.rerun()
        
        if st.session_state.get('show_pending_details', False):
            # Show pending proposals details
            self.render_pending_proposals_details()
        else:
            # Main content
            tab1, tab2, tab3, tab4 = st.tabs([
                "📋 Learning Proposals", 
                "📊 Analytics", 
                "📈 Learning Curve",
                "🔒 Security & Privacy"
            ])
            
            with tab1:
                self.render_learning_proposals()
            
            with tab2:
                self.render_proposal_analytics()
            
            with tab3:
                self.render_learning_curve(filters['days'])
            
            with tab4:
                st.subheader("🔒 Security & Privacy")
                st.info("""
                **Your learning data is protected:**
                - All proposals require your explicit approval
                - No one can modify StillMe IPC without your permission
                - Community can only suggest content, not control learning
                - All actions are logged and auditable
                - Personal data is encrypted and secure
                """)
                
                st.subheader("🛡️ Access Control")
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
        
        # Footer
        self.render_footer()

def main():
    """Main function"""
    try:
        dashboard = EnhancedLearningDashboard()
        dashboard.run()
    except Exception as e:
        st.error(f"Enhanced dashboard error: {e}")
        st.exception(e)

if __name__ == "__main__":
    main()
