#!/usr/bin/env python3
"""
Simple test script to verify NicheRadar functionality without pytest
"""

import sys
import os
import json
from pathlib import Path

def test_basic_imports():
    """Test basic imports"""
    print("🧪 Testing basic imports...")
    
    try:
        import yaml
        print("✅ PyYAML imported successfully")
    except ImportError as e:
        print(f"❌ PyYAML import failed: {e}")
        return False
    
    try:
        import vcr
        print("✅ VCR imported successfully")
    except ImportError as e:
        print(f"❌ VCR import failed: {e}")
        return False
    
    return True

def test_config_files():
    """Test configuration files exist"""
    print("\n🧪 Testing configuration files...")
    
    config_files = [
        "config/staging.yaml",
        "policies/network_allowlist.yaml", 
        "policies/niche_weights.yaml"
    ]
    
    all_exist = True
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"✅ {config_file} exists")
        else:
            print(f"❌ {config_file} missing")
            all_exist = False
    
    return all_exist

def test_fixture_files():
    """Test fixture files exist"""
    print("\n🧪 Testing fixture files...")
    
    fixture_files = [
        "tests/fixtures/github_trending_sample.json",
        "tests/fixtures/hackernews_sample.json",
        "tests/fixtures/news_sample.json",
        "tests/fixtures/google_trends_sample.json",
        "tests/fixtures/reddit_sample.json"
    ]
    
    all_exist = True
    for fixture_file in fixture_files:
        if Path(fixture_file).exists():
            print(f"✅ {fixture_file} exists")
            # Test JSON validity
            try:
                with open(fixture_file, 'r', encoding='utf-8') as f:
                    json.load(f)
                print(f"  ✅ JSON is valid")
            except json.JSONDecodeError as e:
                print(f"  ❌ Invalid JSON: {e}")
                all_exist = False
        else:
            print(f"❌ {fixture_file} missing")
            all_exist = False
    
    return all_exist

def test_directories():
    """Test required directories exist"""
    print("\n🧪 Testing directories...")
    
    directories = [
        "tests/",
        "tests/fixtures/",
        "tests/cassettes/",
        "reports/",
        "reports/coverage/",
        "logs/"
    ]
    
    all_exist = True
    for directory in directories:
        if Path(directory).exists():
            print(f"✅ {directory} exists")
        else:
            print(f"❌ {directory} missing")
            all_exist = False
    
    return all_exist

def test_backend_connection():
    """Test backend connection"""
    print("\n🧪 Testing backend connection...")
    
    try:
        import requests
        response = requests.get("http://127.0.0.1:1216/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is responding")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 NicheRadar v1.5 - Simple Test Suite")
    print("=" * 50)
    
    tests = [
        test_basic_imports,
        test_config_files,
        test_fixture_files,
        test_directories,
        test_backend_connection
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! NicheRadar v1.5 is ready for testing.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
