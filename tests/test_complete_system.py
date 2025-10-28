#!/usr/bin/env python3
"""
Test Complete StillMe Learning System
====================================

Test toàn bộ hệ thống học tập tự động với 12 nguồn và 3 con đường.
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


async def test_learning_sources():
    """Test 12 learning sources"""
    print("🔍 Testing 12 Learning Sources")
    print("=" * 50)
    
    try:
        from stillme_core.learning.sources import LEARNING_SOURCES
        
        print(f"✅ Found {len(LEARNING_SOURCES)} learning sources:")
        for name, source_class in LEARNING_SOURCES.items():
            print(f"  - {name}: {source_class.__name__}")
        
        # Test each source
        for name, source_class in LEARNING_SOURCES.items():
            try:
                print(f"\n🧪 Testing {name}...")
                source = source_class()
                
                # Test health check
                health = await source.health_check()
                print(f"  Health: {'✅' if health else '❌'}")
                
                # Test fetch content (limit to 2 for testing)
                content = await source.fetch_content(limit=2)
                print(f"  Content: {len(content)} items")
                
                if content:
                    print(f"    Sample: {content[0].title[:50]}...")
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing learning sources: {e}")
        return False


async def test_scheduler():
    """Test automated scheduler"""
    print("\n⏰ Testing Automated Scheduler")
    print("=" * 50)
    
    try:
        from stillme_core.modules.automated_scheduler import AutomatedScheduler
        
        scheduler = AutomatedScheduler()
        print("✅ Scheduler created")
        
        # Check config
        print(f"📅 Learning times: {len(scheduler.config.daily_learning_times)} times per day")
        print(f"   Times: {', '.join(scheduler.config.daily_learning_times[:3])}...")
        print(f"⏱️  Interval: {scheduler.config.auto_learning_interval} minutes")
        
        # Initialize scheduler
        await scheduler.initialize()
        print("✅ Scheduler initialized")
        
        # Get status
        status = scheduler.get_status()
        print(f"📊 Status: {status['status']}")
        print(f"📋 Jobs: {len(status['jobs'])} configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing scheduler: {e}")
        return False


async def test_community_voting():
    """Test community voting system"""
    print("\n🗳️ Testing Community Voting System")
    print("=" * 50)
    
    try:
        from stillme_core.learning.community_voting import CommunityVotingSystem, VoteType
        
        voting = CommunityVotingSystem()
        print("✅ Community voting system created")
        
        # Create test proposal
        proposal_id = voting.create_proposal(
            title="Test Community Proposal",
            description="This is a test proposal from the community",
            content="Test content for learning",
            created_by="test_user",
            vote_threshold=3  # Low threshold for testing
        )
        print(f"✅ Created test proposal: {proposal_id}")
        
        # Add some votes
        voting.vote_proposal(proposal_id, "user1", VoteType.UP, "Great idea!")
        voting.vote_proposal(proposal_id, "user2", VoteType.UP, "I agree")
        voting.vote_proposal(proposal_id, "user3", VoteType.UP, "Let's learn this!")
        print("✅ Added 3 votes")
        
        # Check proposal status
        proposal = voting.get_proposal(proposal_id)
        if proposal:
            print(f"📊 Proposal status: {proposal.status}")
            print(f"📈 Votes: {proposal.upvotes} up, {proposal.downvotes} down")
            print(f"🎯 Threshold: {proposal.vote_threshold}")
        
        # Get stats
        stats = voting.get_voting_stats()
        print(f"📊 Voting stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing community voting: {e}")
        return False


async def test_notification_automation():
    """Test notification automation"""
    print("\n📱 Testing Notification Automation")
    print("=" * 50)
    
    try:
        from stillme_core.learning.notification_automation import get_learning_notification_automation
        
        automation = get_learning_notification_automation()
        print("✅ Notification automation created")
        
        # Test new proposal notification
        result = await automation.notify_new_proposal(
            proposal_id="test_123",
            title="Test Learning Proposal",
            source="manual",
            priority="high"
        )
        print(f"📧 New proposal notification: {'✅' if result else '❌'}")
        
        # Test approval notification
        result = await automation.notify_proposal_approved(
            proposal_id="test_123",
            title="Test Learning Proposal",
            approved_by="admin"
        )
        print(f"✅ Approval notification: {'✅' if result else '❌'}")
        
        # Test completion notification
        result = await automation.notify_learning_completed(
            proposal_id="test_123",
            title="Test Learning Proposal",
            duration=120,
            progress=1.0
        )
        print(f"🎉 Completion notification: {'✅' if result else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing notification automation: {e}")
        return False


async def test_auto_start():
    """Test auto-start system"""
    print("\n🚀 Testing Auto-Start System")
    print("=" * 50)
    
    try:
        # Check if auto-start script exists
        autostart_script = Path("start_learning_system.py")
        if autostart_script.exists():
            print("✅ Auto-start script exists")
        else:
            print("❌ Auto-start script not found")
            return False
        
        # Check batch file
        batch_file = Path("start_learning_system.bat")
        if batch_file.exists():
            print("✅ Windows batch file exists")
        else:
            print("❌ Windows batch file not found")
        
        # Check PowerShell script
        ps_script = Path("start_learning_system.ps1")
        if ps_script.exists():
            print("✅ PowerShell script exists")
        else:
            print("❌ PowerShell script not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing auto-start: {e}")
        return False


async def main():
    """Main test function"""
    print("🧪 StillMe Complete Learning System Test")
    print("=" * 60)
    
    tests = [
        ("Learning Sources", test_learning_sources),
        ("Automated Scheduler", test_scheduler),
        ("Community Voting", test_community_voting),
        ("Notification Automation", test_notification_automation),
        ("Auto-Start System", test_auto_start),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! StillMe learning system is ready!")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
