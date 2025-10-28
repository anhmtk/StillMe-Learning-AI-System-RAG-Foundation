#!/usr/bin/env python3
"""
Test Create Session
"""

from stillme_core.learning.evolutionary_learning_system import EvolutionaryLearningSystem
from stillme_core.learning.proposals_manager import ProposalsManager

def test_create_session():
    print("🧪 Testing Session Creation...")
    
    # Create proposal first
    proposals_manager = ProposalsManager()
    proposal = proposals_manager.create_proposal(
        title="Test Session Creation",
        description="Testing session creation and notifications",
        learning_objectives=["Test objective"],
        prerequisites=[],
        expected_outcomes=["Test outcome"],
        estimated_duration=30,
        quality_score=0.8,
        source="test",
        priority="medium",
        risk_assessment={"level": "low", "notes": "Test session"}
    )
    
    print(f"✅ Created proposal: {proposal.id}")
    
    # Approve proposal
    proposals_manager.approve_proposal(proposal.id, "test")
    print(f"✅ Approved proposal: {proposal.id}")
    
    # Start learning session
    learning_system = EvolutionaryLearningSystem()
    session_id = learning_system.start_learning_session(
        proposal_id=proposal.id,
        title=proposal.title
    )
    
    print(f"✅ Started session: {session_id}")
    
    # Check active sessions
    sessions = learning_system.get_active_sessions()
    print(f"📊 Active sessions: {len(sessions)}")
    
    for session_id, data in sessions.items():
        print(f"  Session: {session_id[:8]}... - {data.get('title', 'Unknown')}")
        print(f"    Status: {data.get('status', 'Unknown')}")
        print(f"    Progress: {data.get('progress', 0)}%")
        print(f"    Started: {data.get('started_at', 'Unknown')}")

if __name__ == "__main__":
    test_create_session()
