#!/usr/bin/env python3
"""
Test Fixed Learning Sources
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


async def test_fixed_sources():
    """Test the fixed learning sources"""
    print("🔧 Testing Fixed Learning Sources")
    print("=" * 50)
    
    try:
        from stillme_core.learning.sources import LEARNING_SOURCES
        
        # Test ArXiv and Medium
        test_sources = ['arxiv', 'medium']
        
        for source_name in test_sources:
            print(f"\n🧪 Testing {source_name}...")
            
            try:
                source_class = LEARNING_SOURCES.get(source_name)
                if source_class:
                    source = source_class()
                    
                    # Test health check
                    print(f"  🔍 Health check...")
                    health = await source.health_check()
                    print(f"  Health: {'✅' if health else '❌'}")
                    
                    if health:
                        # Test fetch content
                        print(f"  📥 Fetching content...")
                        content = await source.fetch_content(limit=2)
                        print(f"  Content: {len(content)} items")
                        
                        if content:
                            for i, item in enumerate(content, 1):
                                print(f"    {i}. {item.title[:60]}...")
                    else:
                        print(f"  ⚠️  Health check failed, skipping content fetch")
                        
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        print(f"\n✅ Fixed sources test completed!")
        
    except Exception as e:
        print(f"❌ Error testing fixed sources: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_fixed_sources())
