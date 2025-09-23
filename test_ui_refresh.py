#!/usr/bin/env python3
"""
Test script for StillMe UI Refresh
Tests all new components and integrations
"""
import sys
import os

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'libs'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'runtime'))

def test_imports():
    """Test all new imports"""
    print("🧪 Testing imports...")
    
    try:
        from system_prompt import system_prompt_manager
        print("✅ System prompt manager imported")
    except Exception as e:
        print(f"❌ System prompt manager import failed: {e}")
        return False
    
    try:
        from performance_tracker import performance_tracker, PerformanceMetrics
        print("✅ Performance tracker imported")
    except Exception as e:
        print(f"❌ Performance tracker import failed: {e}")
        return False
    
    try:
        from design_tokens import design_tokens
        print("✅ Design tokens imported")
    except Exception as e:
        print(f"❌ Design tokens import failed: {e}")
        return False
    
    try:
        from brand import get_window_title, get_header_text, get_about_text
        print("✅ Brand config imported")
    except Exception as e:
        print(f"❌ Brand config import failed: {e}")
        return False
    
    try:
        from policy_loader import load_policies
        print("✅ Policy loader imported")
    except Exception as e:
        print(f"❌ Policy loader import failed: {e}")
        return False
    
    return True

def test_system_prompt():
    """Test system prompt manager"""
    print("\n🧪 Testing system prompt manager...")
    
    try:
        from system_prompt import system_prompt_manager
        
        # Test first message (should include intro)
        prompt1 = system_prompt_manager.get_system_prompt(
            language_name="Vietnamese",
            locale="vi-VN",
            session_id="test_session",
            is_first_message=True
        )
        
        assert "introduce yourself" in prompt1.lower()
        assert "stillme" in prompt1.lower()
        print("✅ First message prompt includes introduction")
        
        # Test subsequent message (should not include intro)
        prompt2 = system_prompt_manager.get_system_prompt(
            language_name="Vietnamese",
            locale="vi-VN",
            session_id="test_session",
            is_first_message=False
        )
        
        assert "do not repeat" in prompt2.lower()
        print("✅ Subsequent message prompt excludes introduction")
        
        return True
    except Exception as e:
        print(f"❌ System prompt test failed: {e}")
        return False

def test_performance_tracker():
    """Test performance tracker"""
    print("\n🧪 Testing performance tracker...")
    
    try:
        from performance_tracker import performance_tracker, PerformanceMetrics
        
        # Test metrics creation
        metrics = performance_tracker.create_metrics(
            model="gemma2:2b",
            engine="ollama",
            input_text="Hello, how are you?",
            output_text="I'm doing well, thank you for asking!",
            latency_ms=1500.5,
            session_id="test_session"
        )
        
        assert metrics.model == "gemma2:2b"
        assert metrics.engine == "ollama"
        assert metrics.latency_ms == 1500.5
        print("✅ Performance metrics created successfully")
        
        # Test display text
        display_text = metrics.get_display_text()
        assert "gemma2:2b" in display_text
        assert "1500.5" in display_text
        print("✅ Performance metrics display text generated")
        
        # Test session summary
        summary = performance_tracker.get_session_summary("test_session")
        assert summary["total_requests"] == 1
        assert summary["models_used"] == ["gemma2:2b"]
        print("✅ Session summary generated")
        
        return True
    except Exception as e:
        print(f"❌ Performance tracker test failed: {e}")
        return False

def test_design_tokens():
    """Test design tokens"""
    print("\n🧪 Testing design tokens...")
    
    try:
        from design_tokens import design_tokens
        
        # Test color retrieval
        primary_bg = design_tokens.get_tkinter_color("backgroundPrimary")
        assert primary_bg == "#0F0C29"
        print("✅ Design token color retrieval works")
        
        # Test gradient CSS
        gradient = design_tokens.get_gradient_css("background")
        assert "linear-gradient" in gradient
        print("✅ Design token gradient generation works")
        
        # Test component style
        button_style = design_tokens.get_component_style("button", "primary")
        assert "background" in button_style
        print("✅ Design token component style retrieval works")
        
        return True
    except Exception as e:
        print(f"❌ Design tokens test failed: {e}")
        return False

def test_branding():
    """Test branding configuration"""
    print("\n🧪 Testing branding configuration...")
    
    try:
        from brand import get_window_title, get_header_text, get_about_text
        
        # Test window title
        title = get_window_title()
        assert "StillMe" in title
        assert "Intelligent Personal Companion" in title
        assert "IPC" in title
        print("✅ Window title includes IPC branding")
        
        # Test header text
        header = get_header_text()
        assert header["title"] == "StillMe"
        assert "Intelligent Personal Companion" in header["subtitle"]
        print("✅ Header text includes IPC branding")
        
        # Test about text
        about = get_about_text()
        assert "Intelligent Personal Companion" in about["title"]
        assert "IPC" in about["description"]
        print("✅ About text includes IPC branding")
        
        return True
    except Exception as e:
        print(f"❌ Branding test failed: {e}")
        return False

def test_policy_loading():
    """Test policy loading"""
    print("\n🧪 Testing policy loading...")
    
    try:
        from policy_loader import load_policies
        
        # This should not raise an exception
        load_policies()
        print("✅ Policies loaded successfully")
        
        return True
    except Exception as e:
        print(f"❌ Policy loading test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 StillMe UI Refresh Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_system_prompt,
        test_performance_tracker,
        test_design_tokens,
        test_branding,
        test_policy_loading
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! UI refresh is ready.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
