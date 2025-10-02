#!/usr/bin/env python3
"""
Test data validation script for NicheRadar v1.5
Validates test fixtures and ensures data quality
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def validate_json_schema(data, required_fields, data_type="unknown"):
    """Validate JSON data against required schema"""
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)

    if missing_fields:
        print(f"❌ {data_type}: Missing fields: {', '.join(missing_fields)}")
        return False

    print(f"✅ {data_type}: All required fields present")
    return True

def validate_timestamp(timestamp_str, data_type="unknown"):
    """Validate timestamp format"""
    try:
        datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        print(f"✅ {data_type}: Valid timestamp format")
        return True
    except ValueError:
        print(f"❌ {data_type}: Invalid timestamp format: {timestamp_str}")
        return False

def validate_url(url, data_type="unknown"):
    """Validate URL format"""
    if not url.startswith("https://"):
        print(f"❌ {data_type}: URL must use HTTPS: {url}")
        return False

    print(f"✅ {data_type}: Valid HTTPS URL")
    return True

def validate_github_trending_data():
    """Validate GitHub trending test data"""
    file_path = "tests/fixtures/github_trending_sample.json"

    if not Path(file_path).exists():
        print(f"❌ GitHub trending fixture not found: {file_path}")
        return False

    try:
        with open(file_path) as f:
            data = json.load(f)

        if not isinstance(data, list):
            print("❌ GitHub trending data should be a list")
            return False

        required_fields = ["source", "url", "title", "timestamp", "metrics", "raw"]

        for i, item in enumerate(data):
            if not validate_json_schema(item, required_fields, f"GitHub item {i}"):
                return False

            if not validate_timestamp(item["timestamp"], f"GitHub item {i}"):
                return False

            if not validate_url(item["url"], f"GitHub item {i}"):
                return False

            # Check metrics structure
            metrics_fields = ["stars", "forks", "language", "trending_score"]
            if not validate_json_schema(item["metrics"], metrics_fields, f"GitHub metrics {i}"):
                return False

        print("✅ GitHub trending data validation passed")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validating {file_path}: {e}")
        return False

def validate_hackernews_data():
    """Validate HackerNews test data"""
    file_path = "tests/fixtures/hackernews_sample.json"

    if not Path(file_path).exists():
        print(f"❌ HackerNews fixture not found: {file_path}")
        return False

    try:
        with open(file_path) as f:
            data = json.load(f)

        if not isinstance(data, list):
            print("❌ HackerNews data should be a list")
            return False

        required_fields = ["source", "url", "title", "timestamp", "metrics", "raw"]

        for i, item in enumerate(data):
            if not validate_json_schema(item, required_fields, f"HN item {i}"):
                return False

            if not validate_timestamp(item["timestamp"], f"HN item {i}"):
                return False

            if not validate_url(item["url"], f"HN item {i}"):
                return False

            # Check metrics structure
            metrics_fields = ["score", "comments", "heat_score"]
            if not validate_json_schema(item["metrics"], metrics_fields, f"HN metrics {i}"):
                return False

        print("✅ HackerNews data validation passed")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validating {file_path}: {e}")
        return False

def validate_news_data():
    """Validate news test data"""
    file_path = "tests/fixtures/news_sample.json"

    if not Path(file_path).exists():
        print(f"❌ News fixture not found: {file_path}")
        return False

    try:
        with open(file_path) as f:
            data = json.load(f)

        if not isinstance(data, list):
            print("❌ News data should be a list")
            return False

        required_fields = ["source", "url", "title", "timestamp", "metrics", "raw"]

        for i, item in enumerate(data):
            if not validate_json_schema(item, required_fields, f"News item {i}"):
                return False

            if not validate_timestamp(item["timestamp"], f"News item {i}"):
                return False

            if not validate_url(item["url"], f"News item {i}"):
                return False

            # Check metrics structure
            metrics_fields = ["relevance_score", "sentiment", "engagement"]
            if not validate_json_schema(item["metrics"], metrics_fields, f"News metrics {i}"):
                return False

        print("✅ News data validation passed")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validating {file_path}: {e}")
        return False

def validate_google_trends_data():
    """Validate Google Trends test data"""
    file_path = "tests/fixtures/google_trends_sample.json"

    if not Path(file_path).exists():
        print(f"❌ Google Trends fixture not found: {file_path}")
        return False

    try:
        with open(file_path) as f:
            data = json.load(f)

        if not isinstance(data, list):
            print("❌ Google Trends data should be a list")
            return False

        required_fields = ["source", "url", "title", "timestamp", "metrics", "raw"]

        for i, item in enumerate(data):
            if not validate_json_schema(item, required_fields, f"Trends item {i}"):
                return False

            if not validate_timestamp(item["timestamp"], f"Trends item {i}"):
                return False

            if not validate_url(item["url"], f"Trends item {i}"):
                return False

            # Check metrics structure
            metrics_fields = ["trend_score", "search_volume", "growth_rate"]
            if not validate_json_schema(item["metrics"], metrics_fields, f"Trends metrics {i}"):
                return False

        print("✅ Google Trends data validation passed")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validating {file_path}: {e}")
        return False

def validate_reddit_data():
    """Validate Reddit test data"""
    file_path = "tests/fixtures/reddit_sample.json"

    if not Path(file_path).exists():
        print(f"❌ Reddit fixture not found: {file_path}")
        return False

    try:
        with open(file_path) as f:
            data = json.load(f)

        if not isinstance(data, list):
            print("❌ Reddit data should be a list")
            return False

        required_fields = ["source", "url", "title", "timestamp", "metrics", "raw"]

        for i, item in enumerate(data):
            if not validate_json_schema(item, required_fields, f"Reddit item {i}"):
                return False

            if not validate_timestamp(item["timestamp"], f"Reddit item {i}"):
                return False

            if not validate_url(item["url"], f"Reddit item {i}"):
                return False

            # Check metrics structure
            metrics_fields = ["upvotes", "comments", "engagement_score"]
            if not validate_json_schema(item["metrics"], metrics_fields, f"Reddit metrics {i}"):
                return False

        print("✅ Reddit data validation passed")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validating {file_path}: {e}")
        return False

def check_fixtures_directory():
    """Check if fixtures directory exists and has required files"""
    fixtures_dir = Path("tests/fixtures")

    if not fixtures_dir.exists():
        print("❌ Fixtures directory not found: tests/fixtures")
        return False

    required_files = [
        "github_trending_sample.json",
        "hackernews_sample.json",
        "news_sample.json",
        "google_trends_sample.json",
        "reddit_sample.json"
    ]

    missing_files = []
    for file_name in required_files:
        file_path = fixtures_dir / file_name
        if not file_path.exists():
            missing_files.append(file_name)

    if missing_files:
        print(f"❌ Missing fixture files: {', '.join(missing_files)}")
        return False

    print("✅ All required fixture files exist")
    return True

def main():
    """Main validation function"""
    print("🔍 Validating test data...")

    checks = [
        ("Fixtures Directory", check_fixtures_directory),
        ("GitHub Trending Data", validate_github_trending_data),
        ("HackerNews Data", validate_hackernews_data),
        ("News Data", validate_news_data),
        ("Google Trends Data", validate_google_trends_data),
        ("Reddit Data", validate_reddit_data)
    ]

    all_passed = True
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}:")
        if not check_func():
            all_passed = False

    if all_passed:
        print("\n✅ All test data validation checks passed!")
        return 0
    else:
        print("\n❌ Some test data validation checks failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
