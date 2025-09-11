#!/usr/bin/env python3
"""
Test script để kiểm tra framework startup
"""

import sys
import asyncio
import logging
import time
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test import các modules"""
    logger.info("🔍 Testing module imports...")
    
    try:
        from framework import StillMeFramework
        logger.info("✅ StillMeFramework imported successfully")
    except Exception as e:
        logger.error(f"❌ Failed to import StillMeFramework: {e}")
        return False
    
    try:
        from modules.layered_memory_v1 import LayeredMemoryV1
        logger.info("✅ LayeredMemoryV1 imported successfully")
    except Exception as e:
        logger.error(f"❌ Failed to import LayeredMemoryV1: {e}")
        return False
    
    try:
        from modules.ethical_core_system_v1 import EthicalCoreSystem
        logger.info("✅ EthicalCoreSystem imported successfully")
    except Exception as e:
        logger.error(f"❌ Failed to import EthicalCoreSystem: {e}")
        return False
    
    return True

def test_framework_init():
    """Test khởi tạo framework"""
    logger.info("🔍 Testing framework initialization...")
    
    try:
        from framework import StillMeFramework
        
        # Khởi tạo framework với config đơn giản
        config = {
            "modules_dir": "modules",
            "strict_mode": False,
            "security_level": "high"
        }
        
        framework = StillMeFramework(config)
        logger.info("✅ Framework initialized successfully")
        return framework
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize framework: {e}")
        return None

async def test_framework_run():
    """Test chạy framework với timeout"""
    logger.info("🔍 Testing framework run with timeout...")
    
    try:
        from framework import StillMeFramework
        
        config = {
            "modules_dir": "modules",
            "strict_mode": False,
            "security_level": "high"
        }
        
        framework = StillMeFramework(config)
        
        # Chạy framework với timeout 10 giây
        logger.info("🚀 Starting framework with 10s timeout...")
        
        try:
            await asyncio.wait_for(framework.run(), timeout=10.0)
        except asyncio.TimeoutError:
            logger.warning("⏰ Framework run timed out after 10s (this is expected for testing)")
            return True
        except Exception as e:
            logger.error(f"❌ Framework run failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to test framework run: {e}")
        return False

def main():
    """Main test function"""
    logger.info("🚀 Starting StillMe Framework startup test...")
    
    # Test 1: Import modules
    if not test_imports():
        logger.error("❌ Import test failed")
        return False
    
    # Test 2: Initialize framework
    framework = test_framework_init()
    if not framework:
        logger.error("❌ Framework initialization test failed")
        return False
    
    # Test 3: Run framework with timeout
    try:
        result = asyncio.run(test_framework_run())
        if result:
            logger.info("✅ All tests passed!")
            return True
        else:
            logger.error("❌ Framework run test failed")
            return False
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
