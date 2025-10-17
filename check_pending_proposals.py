#!/usr/bin/env python3
"""
Check Pending Proposals and Approval Workflow
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from stillme_core.env_loader import load_env_hierarchy
    load_env_hierarchy()
except ImportError:
    print("Warning: Could not import env_loader")
except Exception as e:
    print(f"Warning: Error loading environment: {e}")


def check_pending_proposals():
    """Check pending proposals and approval workflow"""
    print("⏳ Pending Proposals & Approval Workflow")
    print("=" * 50)
    
    try:
        from stillme_core.learning import get_learning_system
        ls = get_learning_system()
        pm = ls.proposals_manager
        
        # Get pending proposals
        pending = pm.get_pending_proposals()
        print(f"📋 Pending proposals: {len(pending)}")
        
        if pending:
            print("\n📝 Pending proposals details:")
            for i, p in enumerate(pending, 1):
                print(f"  {i}. {p.title}")
                print(f"     Source: {p.source}")
                print(f"     Priority: {p.priority}")
                print(f"     Status: {p.status}")
                print(f"     Created: {p.created_at}")
                print(f"     Duration: {p.estimated_duration} minutes")
                print()
        
        # Test approval workflow
        if pending:
            print("🔧 Testing approval workflow...")
            first_proposal = pending[0]
            print(f"  Approving proposal: {first_proposal.title}")
            
            # Approve the first proposal
            result = pm.approve_proposal(first_proposal.id, "admin")
            if result:
                print("  ✅ Proposal approved successfully!")
            else:
                print("  ❌ Failed to approve proposal")
        
        # Check approval system
        print("\n🔍 Checking approval system...")
        try:
            from stillme_core.learning.approval_system import ApprovalSystem
            approval_system = ApprovalSystem()
            print("  ✅ Approval system available")
        except Exception as e:
            print(f"  ❌ Approval system error: {e}")
            
    except Exception as e:
        print(f"❌ Error checking pending proposals: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_pending_proposals()
