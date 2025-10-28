#!/usr/bin/env python3
"""
Test Creating Learning Proposals
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


def test_create_proposals():
    """Test creating different types of learning proposals"""
    print("🧪 Testing Learning Proposal Creation")
    print("=" * 50)
    
    try:
        from stillme_core.learning import get_learning_system
        ls = get_learning_system()
        pm = ls.proposals_manager
        
        # Test 1: Create manual text proposal
        print("📝 Test 1: Creating manual text proposal...")
        proposal1 = pm.create_proposal(
            title="Học về Python Web Development",
            description="Nghiên cứu Flask và Django để phát triển web applications",
            learning_objectives=[
                "Hiểu Flask framework cơ bản",
                "Học Django ORM và models",
                "Thực hành tạo REST API",
                "Deploy ứng dụng web"
            ],
            prerequisites=["Python cơ bản", "HTML/CSS", "Database basics"],
            expected_outcomes=[
                "Có thể tạo web app với Flask",
                "Hiểu Django architecture",
                "Có thể tạo REST API",
                "Biết deploy lên cloud"
            ],
            estimated_duration=180,  # 3 hours
            quality_score=0.9,
            source="manual",
            priority="high",
            risk_assessment={
                "complexity": "medium",
                "time_required": "high",
                "prerequisites": "medium",
                "practical_value": "high"
            }
        )
        print(f"  ✅ Created proposal: {proposal1.id}")
        
        # Test 2: Create API-based proposal
        print("\n🔗 Test 2: Creating API-based proposal...")
        proposal2 = pm.create_proposal(
            title="Học về OpenAI API Integration",
            description="Tích hợp OpenAI API vào ứng dụng Python",
            learning_objectives=[
                "Hiểu OpenAI API endpoints",
                "Implement text generation",
                "Handle API rate limits",
                "Error handling và retry logic"
            ],
            prerequisites=["Python", "HTTP requests", "JSON handling"],
            expected_outcomes=[
                "Có thể gọi OpenAI API",
                "Implement text generation features",
                "Handle errors gracefully",
                "Optimize API usage"
            ],
            estimated_duration=120,  # 2 hours
            quality_score=0.85,
            source="api",
            priority="medium",
            risk_assessment={
                "complexity": "low",
                "time_required": "medium",
                "prerequisites": "low",
                "practical_value": "high"
            }
        )
        print(f"  ✅ Created proposal: {proposal2.id}")
        
        # Test 3: Create experience-based proposal
        print("\n💡 Test 3: Creating experience-based proposal...")
        proposal3 = pm.create_proposal(
            title="Học từ kinh nghiệm debugging",
            description="Phân tích và học từ các lỗi đã gặp trong dự án",
            learning_objectives=[
                "Phân tích root cause của bugs",
                "Học debugging techniques",
                "Prevent similar issues",
                "Improve code quality"
            ],
            prerequisites=["Programming experience", "Debugging tools"],
            expected_outcomes=[
                "Better debugging skills",
                "Prevention strategies",
                "Code quality improvement",
                "Faster issue resolution"
            ],
            estimated_duration=90,  # 1.5 hours
            quality_score=0.8,
            source="experience",
            priority="medium",
            risk_assessment={
                "complexity": "low",
                "time_required": "low",
                "prerequisites": "low",
                "practical_value": "high"
            }
        )
        print(f"  ✅ Created proposal: {proposal3.id}")
        
        # Check total proposals now
        all_proposals = pm.get_all_proposals()
        print(f"\n📊 Total proposals now: {len(all_proposals)}")
        
        # Check pending proposals
        pending = pm.get_pending_proposals()
        print(f"⏳ Pending proposals: {len(pending)}")
        
        print("\n✅ All proposal creation tests passed!")
        
    except Exception as e:
        print(f"❌ Error creating proposals: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_create_proposals()
