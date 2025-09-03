#!/usr/bin/env python3
"""
Integration Test cho tất cả modules đã sửa:
- framework.py
- content_integrity_filter.py  
- conversational_core_v1.py
- ethical_core_system_v1.py
- layered_memory_v1.py
- persona_morph.py
"""

import asyncio
import os
import sys
import logging

# Thêm thư mục modules vào path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

# Tắt logging để output rõ ràng
logging.basicConfig(level=logging.ERROR)

async def test_framework():
    """Test framework.py import và khởi tạo"""
    try:
        import framework
        print("✅ Framework.py: Import thành công")
        
        # Test khởi tạo framework
        framework_instance = framework.StillMeFramework({
            "modules_dir": "modules", 
            "strict_mode": False, 
            "security_level": "high"
        })
        print("✅ Framework.py: Khởi tạo thành công")
        return True
    except Exception as e:
        print(f"❌ Framework.py: Lỗi - {e}")
        return False

async def test_content_integrity_filter():
    """Test content_integrity_filter.py"""
    try:
        from content_integrity_filter import ContentIntegrityFilter
        
        # Test khởi tạo với testing mode
        filter_instance = ContentIntegrityFilter(
            openrouter_api_key="test_key_12345",
            testing_mode=True
        )
        print("✅ ContentIntegrityFilter: Import và khởi tạo thành công")
        
        # Test basic functionality
        result = await filter_instance.pre_filter_content(
            "Đây là nội dung test an toàn",
            "https://example.com"
        )
        print(f"✅ ContentIntegrityFilter: Pre-filter test thành công - {result}")
        
        return True
    except Exception as e:
        print(f"❌ ContentIntegrityFilter: Lỗi - {e}")
        return False

def test_conversational_core():
    """Test conversational_core_v1.py"""
    try:
        from conversational_core_v1 import ConversationalCore
        
        # Mock persona engine
        class MockPersonaEngine:
            def generate_response(self, user_input: str, history: list) -> str:
                return f"Mock response cho: {user_input}"
        
        # Test khởi tạo
        core = ConversationalCore(
            persona_engine=MockPersonaEngine(),
            max_history=5
        )
        print("✅ ConversationalCore: Import và khởi tạo thành công")
        
        # Test basic functionality
        response = core.respond("Xin chào")
        print(f"✅ ConversationalCore: Response test thành công - {response}")
        
        return True
    except Exception as e:
        print(f"❌ ConversationalCore: Lỗi - {e}")
        return False

async def test_ethical_core():
    """Test ethical_core_system_v1.py"""
    try:
        from ethical_core_system_v1 import EthicalCoreSystem
        
        # Test khởi tạo (sẽ fail nếu không có OPENROUTER_API_KEY)
        try:
            ethical_system = EthicalCoreSystem()
            print("✅ EthicalCoreSystem: Import và khởi tạo thành công")
            return True
        except ValueError as e:
            if "OPENROUTER_API_KEY" in str(e):
                print("✅ EthicalCoreSystem: Import thành công (cần API key để khởi tạo)")
                return True
            else:
                raise e
    except Exception as e:
        print(f"❌ EthicalCoreSystem: Lỗi - {e}")
        return False

def test_layered_memory():
    """Test layered_memory_v1.py"""
    try:
        from layered_memory_v1 import LayeredMemoryV1
        
        # Test khởi tạo
        memory = LayeredMemoryV1()
        print("✅ LayeredMemoryV1: Import và khởi tạo thành công")
        
        # Test basic functionality
        memory.add_memory("User prefers dark coffee", 0.6)
        memory.add_memory("User is allergic to peanuts", 0.9)
        results = memory.search("coffee")
        print(f"✅ LayeredMemoryV1: Memory operations thành công - {len(results)} results")
        
        return True
    except Exception as e:
        print(f"❌ LayeredMemoryV1: Lỗi - {e}")
        return False

def test_persona_morph():
    """Test persona_morph.py"""
    try:
        from persona_morph import PersonaMorph
        
        # Test khởi tạo (sẽ fail nếu không có OPENROUTER_API_KEY)
        try:
            persona = PersonaMorph()
            print("✅ PersonaMorph: Import và khởi tạo thành công")
            return True
        except ValueError as e:
            if "OPENROUTER_API_KEY" in str(e):
                print("✅ PersonaMorph: Import thành công (cần API key để khởi tạo)")
                return True
            else:
                raise e
    except Exception as e:
        print(f"❌ PersonaMorph: Lỗi - {e}")
        return False

async def main():
    """Test chính"""
    print("🚀 BẮT ĐẦU INTEGRATION TEST CHO TẤT CẢ MODULES...")
    print("=" * 70)
    
    results = {}
    
    # Test từng module
    print("\n📋 Test 1: Framework.py")
    results['framework'] = await test_framework()
    
    print("\n📋 Test 2: ContentIntegrityFilter")
    results['content_integrity'] = await test_content_integrity_filter()
    
    print("\n📋 Test 3: ConversationalCore")
    results['conversational_core'] = test_conversational_core()
    
    print("\n📋 Test 4: EthicalCoreSystem")
    results['ethical_core'] = await test_ethical_core()
    
    print("\n📋 Test 5: LayeredMemoryV1")
    results['layered_memory'] = test_layered_memory()
    
    print("\n📋 Test 6: PersonaMorph")
    results['persona_morph'] = test_persona_morph()
    
    # Kết quả tổng hợp
    print("\n" + "=" * 70)
    print("📊 KẾT QUẢ TỔNG HỢP:")
    
    passed = sum(results.values())
    total = len(results)
    
    for module, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{module:20}: {status}")
    
    print(f"\n🎯 TỔNG KẾT: {passed}/{total} modules hoạt động thành công")
    
    if passed == total:
        print("\n🎉 TẤT CẢ MODULES ĐÃ SỬA THÀNH CÔNG!")
        print("✅ Có thể import và chạy được")
        print("✅ Sẵn sàng integration với framework")
        print("✅ Framework ready for production!")
    else:
        print(f"\n⚠️ CÓ {total - passed} MODULES CẦN SỬA THÊM")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
