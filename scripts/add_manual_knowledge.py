#!/usr/bin/env python3
"""
StillMe IPC Manual Knowledge Input
Cho phép bạn gửi kiến thức mới cho StillMe học
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from stillme_core.learning.proposals_manager import ProposalsManager
from stillme_core.alerting.alerting_system import AlertingSystem

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ManualKnowledgeInput:
    def __init__(self):
        self.proposals_manager = ProposalsManager()
        self.alerting_system = AlertingSystem()
    
    def add_knowledge(self, title, description, source_url=None, priority="medium"):
        """Thêm kiến thức mới cho StillMe học"""
        logger.info("📚 StillMe IPC Manual Knowledge Input")
        logger.info("==========================================")
        logger.info(f"📝 Adding new knowledge: {title}")
        
        try:
            # Tạo learning proposal từ kiến thức manual
            proposal = self.proposals_manager.create_proposal(
                title=title,
                description=description,
                learning_objectives=[
                    f"Understand {title} concepts",
                    "Apply knowledge in practical scenarios",
                    "Integrate with existing knowledge base"
                ],
                prerequisites=["Basic understanding of the topic"],
                expected_outcomes=[
                    f"Mastery of {title}",
                    "Practical application skills",
                    "Enhanced knowledge base"
                ],
                estimated_duration=120,  # 2 hours default
                quality_score=0.90,  # High quality for manual input
                source="manual",
                priority=priority,
                risk_assessment={
                    "complexity": "medium",
                    "time_commitment": "medium", 
                    "prerequisites": "low",
                    "practical_value": "high"
                },
                created_by="manual_input"
            )
            
            logger.info(f"✅ Knowledge proposal created: {proposal.title}")
            logger.info(f"📋 Proposal ID: {proposal.id}")
            logger.info(f"📊 Quality Score: {proposal.quality_score}")
            
            # Gửi thông báo
            self.alerting_system.send_alert(
                "New Manual Knowledge Added",
                f"New knowledge has been added for StillMe IPC to learn:\n\n"
                f"📚 **Title:** {title}\n"
                f"📝 **Description:** {description}\n"
                f"📊 **Quality Score:** {proposal.quality_score}\n"
                f"⚡ **Priority:** {priority}\n"
                f"🆔 **Proposal ID:** {proposal.id[:8]}...\n\n"
                f"Please review and approve in the dashboard!",
                "info"
            )
            
            # Lưu thông tin vào file
            self._save_knowledge_info(proposal, source_url)
            
            print(f"\n🎉 Knowledge added successfully!")
            print(f"📚 Title: {title}")
            print(f"📝 Description: {description}")
            print(f"📊 Quality Score: {proposal.quality_score}")
            print(f"🆔 Proposal ID: {proposal.id}")
            print(f"\n💡 Next steps:")
            print(f"• Check dashboard to see the new proposal")
            print(f"• Review and approve the proposal")
            print(f"• StillMe IPC will start learning if approved")
            
            return proposal
            
        except Exception as e:
            logger.error(f"❌ Failed to add knowledge: {e}")
            print(f"\n❌ Failed to add knowledge: {e}")
            return None
    
    def _save_knowledge_info(self, proposal, source_url=None):
        """Lưu thông tin kiến thức vào file"""
        try:
            knowledge_info = {
                "proposal_id": proposal.id,
                "title": proposal.title,
                "description": proposal.description,
                "source_url": source_url,
                "created_at": datetime.now().isoformat(),
                "created_by": "manual_input"
            }
            
            # Lưu vào artifacts
            artifacts_dir = project_root / "artifacts" / "manual_knowledge"
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"knowledge_{proposal.id[:8]}.json"
            filepath = artifacts_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(knowledge_info, f, indent=4, ensure_ascii=False)
            
            logger.info(f"📄 Knowledge info saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save knowledge info: {e}")

def main():
    """Main function - Interactive mode"""
    print("🧠 StillMe IPC Manual Knowledge Input")
    print("==========================================")
    print("📚 Add new knowledge for StillMe to learn")
    print()
    
    # Get input from user
    title = input("📝 Enter knowledge title: ").strip()
    if not title:
        print("❌ Title cannot be empty!")
        return
    
    print("\n📖 Enter knowledge description (press Enter twice to finish):")
    description_lines = []
    while True:
        line = input()
        if line == "" and description_lines and description_lines[-1] == "":
            break
        description_lines.append(line)
    
    description = "\n".join(description_lines).strip()
    if not description:
        print("❌ Description cannot be empty!")
        return
    
    source_url = input("\n🔗 Enter source URL (optional): ").strip() or None
    
    print("\n⚡ Select priority:")
    print("1. Low")
    print("2. Medium (default)")
    print("3. High")
    print("4. Critical")
    
    priority_choice = input("Enter choice (1-4): ").strip()
    priority_map = {"1": "low", "2": "medium", "3": "high", "4": "critical"}
    priority = priority_map.get(priority_choice, "medium")
    
    # Add knowledge
    knowledge_input = ManualKnowledgeInput()
    proposal = knowledge_input.add_knowledge(title, description, source_url, priority)
    
    if proposal:
        print(f"\n✅ Knowledge added successfully!")
        print(f"🆔 Proposal ID: {proposal.id}")
        print(f"📊 Check dashboard to approve: http://localhost:8506")
    else:
        print(f"\n❌ Failed to add knowledge. Please try again.")

if __name__ == "__main__":
    main()
