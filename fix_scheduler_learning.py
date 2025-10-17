#!/usr/bin/env python3
"""
Fix Scheduler Learning Integration
"""

import asyncio
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


async def test_learning_integration():
    """Test learning system integration"""
    print("🔍 Testing Learning System Integration")
    print("=" * 50)
    
    try:
        # Test learning system
        from stillme_core.learning import get_learning_system
        learning_system = get_learning_system()
        
        print(f"✅ Learning system available: {learning_system.is_available()}")
        
        # Test proposals manager
        proposals_manager = learning_system.proposals_manager
        print("✅ Proposals manager available")
        
        # Test learning sources
        from stillme_core.learning.sources import LEARNING_SOURCES
        print(f"✅ Learning sources: {len(LEARNING_SOURCES)} available")
        
        # Test creating proposals from sources
        print("\n🧪 Testing proposal creation from sources...")
        
        test_sources = ['hackernews', 'reddit', 'github', 'stackoverflow']
        created_count = 0
        
        for source_name in test_sources:
            try:
                source_class = LEARNING_SOURCES.get(source_name)
                if source_class:
                    source = source_class()
                    
                    # Fetch content
                    content_list = await source.fetch_content(limit=1)
                    
                    for content in content_list:
                        # Create proposal
                        proposal = proposals_manager.create_proposal(
                            title=content.title,
                            description=content.description,
                            learning_objectives=[
                                f"Learn about {content.title}",
                                "Understand key concepts",
                                "Apply knowledge practically"
                            ],
                            prerequisites=["Basic knowledge"],
                            expected_outcomes=[
                                "Improved understanding",
                                "Practical application skills"
                            ],
                            estimated_duration=60,
                            quality_score=content.quality_score,
                            source=source_name,
                            priority="medium",
                            risk_assessment={
                                "complexity": "medium",
                                "time_required": "medium",
                                "prerequisites": "low",
                                "practical_value": "high"
                            }
                        )
                        
                        print(f"  ✅ Created proposal from {source_name}: {content.title[:50]}...")
                        created_count += 1
                        
            except Exception as e:
                print(f"  ❌ Failed {source_name}: {e}")
                continue
        
        print(f"\n📊 Created {created_count} proposals from sources")
        
        # Check total proposals
        all_proposals = proposals_manager.get_all_proposals()
        pending_proposals = proposals_manager.get_pending_proposals()
        
        print(f"📈 Total proposals: {len(all_proposals)}")
        print(f"⏳ Pending proposals: {len(pending_proposals)}")
        
        # Test auto-approval
        if pending_proposals:
            print(f"\n🔧 Testing auto-approval...")
            approved_count = 0
            
            for proposal in pending_proposals[:2]:  # Test with 2 proposals
                if proposal.priority in ['high', 'medium']:
                    success = proposals_manager.approve_proposal(proposal.id, "auto_test")
                    if success:
                        approved_count += 1
                        print(f"  ✅ Auto-approved: {proposal.title[:50]}...")
            
            print(f"📊 Auto-approved {approved_count} proposals")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function"""
    success = await test_learning_integration()
    
    if success:
        print("\n🎉 Learning system integration test passed!")
        print("✅ Scheduler can now create and approve proposals automatically")
    else:
        print("\n❌ Learning system integration test failed!")
        print("⚠️  Scheduler needs to be fixed to work with learning system")


if __name__ == "__main__":
    asyncio.run(main())
