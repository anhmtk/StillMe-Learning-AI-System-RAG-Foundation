#!/usr/bin/env python3
"""
StillMe IPC Auto Proposal Creator
================================

Script để tạo learning proposal tự động một lần.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def create_auto_proposal():
    """Tạo learning proposal tự động"""
    print("📝 Creating automatic learning proposal...")

    try:
        from stillme_core.learning.proposals_manager import ProposalsManager
        manager = ProposalsManager()

        # Create an automatic proposal
        proposal_data = {
            "title": "Machine Learning Fundamentals",
            "description": "Learn the basics of machine learning including supervised and unsupervised learning, model evaluation, and practical applications",
            "learning_objectives": [
                "Understand machine learning concepts and terminology",
                "Learn about different types of ML algorithms",
                "Practice with real datasets",
                "Implement basic ML models"
            ],
            "prerequisites": [
                "Basic Python knowledge",
                "Understanding of statistics",
                "Familiarity with data analysis"
            ],
            "expected_outcomes": [
                "Build and evaluate ML models",
                "Understand model performance metrics",
                "Apply ML to real-world problems",
                "Choose appropriate algorithms"
            ],
            "estimated_duration": 180,  # 3 hours
            "quality_score": 0.91,
            "source": "ai_generated",
            "priority": "high",
            "risk_assessment": {
                "complexity": "medium",
                "time_commitment": "medium",
                "prerequisites": "medium",
                "practical_value": "high"
            }
        }

        proposal = manager.create_proposal(**proposal_data)
        print(f"✅ Auto proposal created: {proposal.title}")
        print(f"📋 Proposal ID: {proposal.id}")
        print(f"📊 Quality Score: {proposal.quality_score}")
        print(f"⏱️ Duration: {proposal.estimated_duration} minutes")

        return proposal

    except Exception as e:
        print(f"❌ Failed to create auto proposal: {e}")
        return None

def main():
    """Main function"""
    print("🧠 StillMe IPC Auto Proposal Creator")
    print("=" * 40)

    # Create proposal
    proposal = create_auto_proposal()

    if proposal:
        print("\n🎉 Proposal created successfully!")
        print(f"📋 Title: {proposal.title}")
        print(f"📝 Description: {proposal.description}")
        print(f"🎯 Quality Score: {proposal.quality_score}")
        print(f"⏱️ Estimated Duration: {proposal.estimated_duration} minutes")

        print("\n💡 Next steps:")
        print("• Check your dashboard to see the new proposal")
        print("• Review and approve/reject the proposal")
        print("• StillMe IPC will start learning if approved")

        # Save proposal info
        proposal_info = {
            "created_at": datetime.now().isoformat(),
            "proposal_id": proposal.id,
            "title": proposal.title,
            "quality_score": proposal.quality_score,
            "estimated_duration": proposal.estimated_duration
        }

        info_file = project_root / "artifacts" / "latest_proposal.json"
        info_file.parent.mkdir(parents=True, exist_ok=True)

        with open(info_file, 'w') as f:
            json.dump(proposal_info, f, indent=2)

        print(f"📄 Proposal info saved to: {info_file}")
    else:
        print("\n❌ Failed to create proposal.")
        print("Please check the error messages above and try again.")

if __name__ == "__main__":
    main()
