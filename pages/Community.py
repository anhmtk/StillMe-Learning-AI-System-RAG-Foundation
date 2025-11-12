"""
StillMe Community - Standalone Community Page
Community-driven learning proposals and voting system
"""

import os
import time
import requests
import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configure page
st.set_page_config(
    page_title="StillMe Community",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

API_BASE = os.getenv("STILLME_API_BASE", "http://localhost:8000")

# Custom CSS for attractive design
st.markdown("""
<style>
    .community-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    .stat-card {
        background: #1e3a5f;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #46b3ff;
        margin-bottom: 1rem;
    }
    .proposal-card {
        background: #262730;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #3a3f4b;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    .proposal-card:hover {
        border-color: #46b3ff;
        box-shadow: 0 4px 12px rgba(70, 179, 255, 0.2);
    }
    .vote-button {
        background: linear-gradient(135deg, #46b3ff 0%, #667eea 100%);
        border: none;
        color: white;
        padding: 0.5rem 1.5rem;
        border-radius: 5px;
        cursor: pointer;
        font-weight: bold;
    }
    .vote-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(70, 179, 255, 0.4);
    }
    .progress-bar {
        background: #3a3f4b;
        height: 8px;
        border-radius: 4px;
        overflow: hidden;
        margin: 0.5rem 0;
    }
    .progress-fill {
        background: linear-gradient(90deg, #46b3ff 0%, #667eea 100%);
        height: 100%;
        transition: width 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)


def get_daily_stats() -> Optional[Dict[str, Any]]:
    """Get daily community statistics"""
    try:
        response = requests.get(f"{API_BASE}/api/community/stats", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching stats: {e}")
        return None


def get_proposals(limit: int = 20) -> List[Dict[str, Any]]:
    """Get pending proposals"""
    try:
        response = requests.get(f"{API_BASE}/api/community/proposals?limit={limit}", timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get("proposals", [])
    except Exception as e:
        st.error(f"Error fetching proposals: {e}")
        return []


def get_learning_queue() -> Optional[Dict[str, Any]]:
    """Get learning queue"""
    try:
        response = requests.get(f"{API_BASE}/api/community/queue", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching learning queue: {e}")
        return None


def vote_on_proposal(proposal_id: str, user_id: str, vote_type: str) -> Optional[Dict[str, Any]]:
    """Vote on a proposal"""
    try:
        response = requests.post(
            f"{API_BASE}/api/community/proposals/{proposal_id}/vote",
            json={
                "proposal_id": proposal_id,
                "user_id": user_id,
                "vote_type": vote_type
            },
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error voting: {e}")
        return None


def create_proposal(proposal_type: str, source_url: str, description: str, proposer_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Create a new proposal"""
    try:
        response = requests.post(
            f"{API_BASE}/api/community/proposals",
            json={
                "proposal_type": proposal_type,
                "source_url": source_url,
                "description": description,
                "proposer_id": proposer_id
            },
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error creating proposal: {e}")
        return None


def main():
    # Header
    st.markdown("""
    <div class="community-header">
        <h1>🤝 StillMe Community</h1>
        <p style="font-size: 1.2rem; margin-top: 1rem;">
            Together, we shape StillMe's learning journey. Your voice matters.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get user ID (simple session-based)
    if "user_id" not in st.session_state:
        st.session_state.user_id = f"user_{int(time.time())}"
    
    # Daily Stats Section
    stats = get_daily_stats()
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <h3 style="color: #46b3ff; margin: 0;">{stats.get('votes_today', 0)}</h3>
                <p style="color: #aaa; margin: 0.5rem 0 0 0;">Votes Today</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <h3 style="color: #46b3ff; margin: 0;">{stats.get('proposals_today', 0)}</h3>
                <p style="color: #aaa; margin: 0.5rem 0 0 0;">New Proposals</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <h3 style="color: #46b3ff; margin: 0;">{stats.get('approved_today', 0)}</h3>
                <p style="color: #aaa; margin: 0.5rem 0 0 0;">Approved Today</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            votes_needed = stats.get('total_votes_needed', 0)
            st.markdown(f"""
            <div class="stat-card">
                <h3 style="color: #46b3ff; margin: 0;">{votes_needed}</h3>
                <p style="color: #aaa; margin: 0.5rem 0 0 0;">Votes Needed</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Daily notification
        if votes_needed > 0:
            st.info(f"📢 **Today's Progress:** StillMe has received {stats.get('votes_today', 0)} votes today. {votes_needed} more votes needed to reach the learning threshold!")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📋 Pending Proposals", "📚 Learning Queue", "💡 Submit Proposal"])
    
    with tab1:
        st.markdown("### 🗳️ Vote on Proposals")
        st.markdown("Help StillMe learn by voting on community proposals. Each proposal needs 10 votes to be approved.")
        
        proposals = get_proposals(limit=20)
        
        if not proposals:
            st.info("No pending proposals. Be the first to submit one!")
        else:
            for proposal in proposals:
                with st.container():
                    st.markdown(f"""
                    <div class="proposal-card">
                        <h4 style="color: #46b3ff; margin-bottom: 0.5rem;">{proposal.get('proposal_type', 'Unknown')}</h4>
                        <p style="color: #aaa; margin: 0.5rem 0;"><strong>Source:</strong> {proposal.get('source_url', 'N/A')}</p>
                        <p style="color: #fff; margin: 0.5rem 0;">{proposal.get('description', 'No description')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        votes_for = proposal.get('votes_for', 0)
                        votes_needed = proposal.get('votes_needed', 10)
                        progress = min(100, (votes_for / 10) * 100) if votes_needed > 0 else 100
                        
                        st.markdown(f"""
                        <div style="margin: 1rem 0;">
                            <div style="display: flex; justify-content: space-between; color: #fff; margin-bottom: 0.5rem;">
                                <span>📊 {votes_for}/10 votes</span>
                                <span>{votes_needed} more needed</span>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {progress}%;"></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        if st.button("✅ Vote For", key=f"vote_for_{proposal.get('proposal_id')}", use_container_width=True):
                            result = vote_on_proposal(
                                proposal_id=proposal.get('proposal_id'),
                                user_id=st.session_state.user_id,
                                vote_type="for"
                            )
                            if result:
                                st.success(result.get('message', 'Vote recorded!'))
                                time.sleep(1)
                                st.rerun()
                    
                    with col3:
                        if st.button("❌ Vote Against", key=f"vote_against_{proposal.get('proposal_id')}", use_container_width=True):
                            result = vote_on_proposal(
                                proposal_id=proposal.get('proposal_id'),
                                user_id=st.session_state.user_id,
                                vote_type="against"
                            )
                            if result:
                                st.info(result.get('message', 'Vote recorded!'))
                                time.sleep(1)
                                st.rerun()
                    
                    st.markdown("---")
    
    with tab2:
        st.markdown("### 📚 Learning Queue")
        st.markdown("See what StillMe has learned and what's coming next!")
        
        queue = get_learning_queue()
        
        if queue:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### ✅ Recently Learned")
                learned = queue.get('learned', [])
                if learned:
                    for item in learned:
                        st.markdown(f"""
                        <div style="background: #1e3a5f; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;">
                            <p style="color: #46b3ff; margin: 0; font-weight: bold;">{item.get('title', 'Unknown')}</p>
                            <p style="color: #aaa; margin: 0.3rem 0 0 0; font-size: 0.9rem;">{item.get('source', 'N/A')}</p>
                            <p style="color: #666; margin: 0.3rem 0 0 0; font-size: 0.8rem;">Learned: {item.get('learned_at', 'N/A')[:10] if item.get('learned_at') else 'N/A'}</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No items learned yet. Vote on proposals to help StillMe learn!")
            
            with col2:
                st.markdown("#### ⏳ Coming Soon")
                pending = queue.get('pending', [])
                if pending:
                    for item in pending:
                        votes_received = item.get('votes_received', 0)
                        votes_needed = item.get('votes_needed', 10)
                        progress = min(100, (votes_received / votes_needed) * 100) if votes_needed > 0 else 100
                        
                        st.markdown(f"""
                        <div style="background: #262730; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem; border-left: 4px solid #46b3ff;">
                            <p style="color: #fff; margin: 0; font-weight: bold;">{item.get('title', 'Unknown')}</p>
                            <p style="color: #aaa; margin: 0.3rem 0 0 0; font-size: 0.9rem;">{item.get('source', 'N/A')}</p>
                            <div style="margin: 0.5rem 0;">
                                <div style="display: flex; justify-content: space-between; color: #46b3ff; font-size: 0.9rem; margin-bottom: 0.3rem;">
                                    <span>{votes_received}/{votes_needed} votes</span>
                                </div>
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: {progress}%;"></div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No pending items. Submit proposals to get started!")
        else:
            st.info("Learning queue is empty. Submit proposals to help StillMe learn!")
    
    with tab3:
        st.markdown("### 💡 Submit a Learning Proposal")
        st.markdown("Help StillMe learn by proposing new sources of knowledge!")
        
        with st.form("proposal_form", clear_on_submit=True):
            proposal_type = st.selectbox(
                "Proposal Type",
                ["RSS Feed", "Article", "Research Paper", "Documentation", "Other"],
                help="Select the type of content you're proposing"
            )
            
            source_url = st.text_input(
                "Source URL",
                placeholder="https://example.com/feed.xml or https://example.com/article",
                help="URL of the RSS feed, article, or other content source"
            )
            
            description = st.text_area(
                "Description",
                placeholder="Describe why this source would be valuable for StillMe to learn from...",
                height=150,
                help="Explain why this source is valuable and what StillMe can learn from it"
            )
            
            submitted = st.form_submit_button("💡 Submit Proposal", type="primary", use_container_width=True)
            
            if submitted:
                if not source_url or not description:
                    st.error("Please fill in all required fields.")
                else:
                    result = create_proposal(
                        proposal_type=proposal_type,
                        source_url=source_url,
                        description=description,
                        proposer_id=st.session_state.user_id
                    )
                    
                    if result:
                        st.success(f"✅ Proposal submitted! ID: {result.get('proposal_id', 'N/A')}")
                        st.info("Your proposal will appear in the voting section. Share it with the community to get votes!")
                        time.sleep(2)
                        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #aaa; padding: 2rem 0;">
        <p>StillMe Community - Together we learn, together we grow 🌱</p>
        <p style="font-size: 0.9rem;">Every vote matters. Every proposal counts.</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

