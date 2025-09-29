#!/usr/bin/env python3
"""
StillMe IPC Founder Knowledge Input
Chế độ đặc biệt cho founder - tự động approve, không cần duyệt
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

class FounderKnowledgeInput:
    def __init__(self):
        self.proposals_manager = ProposalsManager()
        self.alerting_system = AlertingSystem()
        
    def add_founder_knowledge(self, title, description, source_url=None, content_type="text", priority="high"):
        """Thêm kiến thức founder - tự động approve"""
        logger.info("👑 StillMe IPC Founder Knowledge Input")
        logger.info("==========================================")
        logger.info(f"📝 Adding founder knowledge: {title}")
        
        try:
            # Tạo proposal với founder source
            proposal = self.proposals_manager.create_proposal(
                title=title,
                description=description,
                learning_objectives=[
                    f"Master {title} concepts",
                    "Apply knowledge in practical scenarios",
                    "Integrate with existing knowledge base"
                ],
                prerequisites=["Basic understanding of the topic"],
                expected_outcomes=[
                    f"Expertise in {title}",
                    "Practical application skills",
                    "Enhanced knowledge base"
                ],
                estimated_duration=180,  # 3 hours default
                quality_score=0.98,  # Very high quality for founder input
                source="founder",
                priority=priority,
                risk_assessment={
                    "complexity": "medium",
                    "time_commitment": "medium",
                    "prerequisites": "low",
                    "practical_value": "very_high"
                },
                created_by="founder"
            )
            
            # TỰ ĐỘNG APPROVE - Không cần duyệt
            self.proposals_manager.approve_proposal(proposal.id, "founder")
            
            logger.info(f"✅ Founder knowledge added and AUTO-APPROVED: {proposal.title}")
            logger.info(f"📋 Proposal ID: {proposal.id}")
            logger.info(f"📊 Quality Score: {proposal.quality_score}")
            
            # Gửi thông báo
            self.alerting_system.send_alert(
                "Founder Knowledge Added",
                f"New founder knowledge has been added and AUTO-APPROVED:\n\n"
                f"👑 **Title:** {title}\n"
                f"📝 **Description:** {description}\n"
                f"📊 **Quality Score:** {proposal.quality_score}\n"
                f"⚡ **Priority:** {priority}\n"
                f"🆔 **Proposal ID:** {proposal.id[:8]}...\n"
                f"✅ **Status:** AUTO-APPROVED (Founder Mode)\n\n"
                f"StillMe IPC will start learning this knowledge immediately!",
                "info"
            )
            
            # Lưu thông tin founder knowledge
            self._save_founder_knowledge(proposal, source_url, content_type)
            
            print(f"\n🎉 Founder knowledge added and AUTO-APPROVED!")
            print(f"👑 Title: {title}")
            print(f"📝 Description: {description}")
            print(f"📊 Quality Score: {proposal.quality_score}")
            print(f"🆔 Proposal ID: {proposal.id}")
            print(f"✅ Status: AUTO-APPROVED (Founder Mode)")
            print(f"\n💡 StillMe IPC will start learning this knowledge immediately!")
            
            return proposal
            
        except Exception as e:
            logger.error(f"❌ Failed to add founder knowledge: {e}")
            print(f"\n❌ Failed to add founder knowledge: {e}")
            return None
    
    def add_from_url(self, url, title=None, priority="high"):
        """Thêm kiến thức từ URL"""
        logger.info(f"🔗 Adding knowledge from URL: {url}")
        
        try:
            import requests
            from bs4 import BeautifulSoup
            
            # Fetch content from URL
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title if not provided
            if not title:
                title = soup.find('title')
                title = title.get_text().strip() if title else "Knowledge from URL"
            
            # Extract description
            description = ""
            for tag in soup.find_all(['p', 'div', 'article']):
                text = tag.get_text().strip()
                if len(text) > 100:  # Get meaningful content
                    description = text[:500] + "..." if len(text) > 500 else text
                    break
            
            if not description:
                description = f"Knowledge extracted from: {url}"
            
            # Add as founder knowledge
            return self.add_founder_knowledge(
                title=title,
                description=description,
                source_url=url,
                content_type="url",
                priority=priority
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to add knowledge from URL: {e}")
            print(f"\n❌ Failed to add knowledge from URL: {e}")
            return None
    
    def add_from_text(self, text_content, title, priority="high"):
        """Thêm kiến thức từ text content"""
        logger.info(f"📄 Adding knowledge from text content: {title}")
        
        return self.add_founder_knowledge(
            title=title,
            description=text_content,
            content_type="text",
            priority=priority
        )
    
    def _save_founder_knowledge(self, proposal, source_url=None, content_type="text"):
        """Lưu thông tin founder knowledge"""
        try:
            founder_info = {
                "proposal_id": proposal.id,
                "title": proposal.title,
                "description": proposal.description,
                "source_url": source_url,
                "content_type": content_type,
                "created_at": datetime.now().isoformat(),
                "created_by": "founder",
                "auto_approved": True,
                "founder_mode": True
            }
            
            # Lưu vào artifacts
            artifacts_dir = project_root / "artifacts" / "founder_knowledge"
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"founder_{proposal.id[:8]}.json"
            filepath = artifacts_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(founder_info, f, indent=4, ensure_ascii=False)
            
            logger.info(f"📄 Founder knowledge info saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save founder knowledge info: {e}")

def main():
    """Main function - Interactive mode"""
    import sys
    
    # Check if command line arguments provided
    if len(sys.argv) > 1:
        # Command line mode
        title = sys.argv[1] if len(sys.argv) > 1 else "Founder Knowledge"
        description = sys.argv[2] if len(sys.argv) > 2 else "Knowledge added by founder"
        priority = sys.argv[3] if len(sys.argv) > 3 else "high"
        
        founder_input = FounderKnowledgeInput()
        proposal = founder_input.add_founder_knowledge(title, description, priority=priority)
        
        if proposal:
            print(f"\n✅ Founder knowledge added and AUTO-APPROVED!")
            print(f"🆔 Proposal ID: {proposal.id}")
            print(f"📊 StillMe IPC will start learning immediately!")
        else:
            print(f"\n❌ Failed to add founder knowledge. Please try again.")
        return
    
    # Interactive mode
    print("👑 StillMe IPC Founder Knowledge Input")
    print("==========================================")
    print("📚 Add knowledge as founder (AUTO-APPROVED)")
    print()
    
    # Get input from user
    print("📝 Select input method:")
    print("1. Text content")
    print("2. URL")
    print("3. Quick text")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        # Text content
        title = input("📝 Enter knowledge title: ").strip()
        if not title:
            print("❌ Title cannot be empty!")
            return
        
        print("\n📖 Enter knowledge content (press Enter twice to finish):")
        content_lines = []
        while True:
            line = input()
            if line == "" and content_lines and content_lines[-1] == "":
                break
            content_lines.append(line)
        
        content = "\n".join(content_lines).strip()
        if not content:
            print("❌ Content cannot be empty!")
            return
        
        priority = input("\n⚡ Enter priority (low/medium/high/critical): ").strip() or "high"
        
        # Add knowledge
        founder_input = FounderKnowledgeInput()
        proposal = founder_input.add_from_text(content, title, priority)
        
    elif choice == "2":
        # URL
        url = input("🔗 Enter URL: ").strip()
        if not url:
            print("❌ URL cannot be empty!")
            return
        
        title = input("📝 Enter title (optional): ").strip() or None
        priority = input("⚡ Enter priority (low/medium/high/critical): ").strip() or "high"
        
        # Add knowledge
        founder_input = FounderKnowledgeInput()
        proposal = founder_input.add_from_url(url, title, priority)
        
    elif choice == "3":
        # Quick text
        title = input("📝 Enter knowledge title: ").strip()
        if not title:
            print("❌ Title cannot be empty!")
            return
        
        description = input("📖 Enter knowledge description: ").strip()
        if not description:
            print("❌ Description cannot be empty!")
            return
        
        priority = input("⚡ Enter priority (low/medium/high/critical): ").strip() or "high"
        
        # Add knowledge
        founder_input = FounderKnowledgeInput()
        proposal = founder_input.add_founder_knowledge(title, description, priority=priority)
        
    else:
        print("❌ Invalid choice!")
        return
    
    if proposal:
        print(f"\n✅ Founder knowledge added and AUTO-APPROVED!")
        print(f"🆔 Proposal ID: {proposal.id}")
        print(f"📊 StillMe IPC will start learning immediately!")
    else:
        print(f"\n❌ Failed to add founder knowledge. Please try again.")

if __name__ == "__main__":
    main()
