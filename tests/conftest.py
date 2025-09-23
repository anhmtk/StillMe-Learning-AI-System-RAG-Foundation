"""
Pytest configuration and fixtures for NicheRadar v1.5 testing
Includes VCR setup, test data fixtures, and file quarantine protection
"""

import pytest
import json
import os
import yaml
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# VCR configuration
try:
    import vcr
    
    # Configure VCR for HTTP recording
    vcr_config = vcr.VCR(
        cassette_library_dir='tests/cassettes',
        record_mode='once',  # Record once, then use cassettes
        match_on=['method', 'scheme', 'host', 'port', 'path', 'query'],
        filter_headers=['authorization', 'x-api-key'],
        filter_query_parameters=['api_key', 'token'],
        serializer='json',
        decode_compressed_response=True,
        before_record_response=lambda response: {
            'status': response['status'],
            'headers': dict(response['headers']),
            'body': response['body'].decode('utf-8') if response['body'] else None
        }
    )
except ImportError:
    vcr_config = None

def is_file_quarantined(file_path):
    """Check if file is quarantined (has .quarantined extension)"""
    return str(file_path).endswith('.quarantined')

def is_file_clean(file_path):
    """Check if file can be read as UTF-8 without issues"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read()
        return True
    except (UnicodeDecodeError, Exception):
        return False

def pytest_collect_file(file_path, parent):
    """Hook to filter out problematic files during collection"""
    # Only apply to files in tests/ directory
    if not str(file_path).startswith('tests/'):
        return None
    
    # Skip quarantined files
    if is_file_quarantined(file_path):
        print(f"⚠️  Skipping quarantined file: {file_path}")
        return None
    
    # Skip files that can't be read as UTF-8
    if not is_file_clean(file_path):
        print(f"⚠️  Skipping file with encoding issues: {file_path}")
        return None
    
    # Let pytest handle the file normally
    return None

@pytest.fixture(scope="session")
def staging_config():
    """Load staging configuration"""
    config_path = Path("config/staging.yaml")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}

@pytest.fixture(scope="session")
def test_fixtures():
    """Load test fixtures from JSON files"""
    fixtures = {}
    fixtures_dir = Path("tests/fixtures")
    
    if fixtures_dir.exists():
        for json_file in fixtures_dir.glob("*.json"):
            with open(json_file, 'r', encoding='utf-8') as f:
                fixtures[json_file.stem] = json.load(f)
    
    return fixtures

@pytest.fixture(scope="session")
def network_allowlist():
    """Load network allowlist configuration"""
    allowlist_path = Path("policies/network_allowlist.yaml")
    if allowlist_path.exists():
        with open(allowlist_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {"allowed_domains": []}

@pytest.fixture(scope="session")
def niche_weights():
    """Load niche weights configuration"""
    weights_path = Path("policies/niche_weights.yaml")
    if weights_path.exists():
        with open(weights_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {"weights": {}}

@pytest.fixture
def mock_github_trending():
    """Mock GitHub trending data"""
    return [
        {
            "source": "github_trending",
            "url": "https://github.com/microsoft/vscode",
            "title": "Visual Studio Code",
            "timestamp": "2024-09-22T10:00:00Z",
            "metrics": {
                "stars": 150000,
                "forks": 26000,
                "language": "TypeScript",
                "trending_score": 0.95
            },
            "raw": {
                "id": 1,
                "name": "vscode",
                "full_name": "microsoft/vscode",
                "html_url": "https://github.com/microsoft/vscode",
                "description": "Visual Studio Code",
                "stargazers_count": 150000,
                "forks_count": 26000,
                "language": "TypeScript"
            }
        }
    ]

@pytest.fixture
def mock_hackernews():
    """Mock HackerNews data"""
    return [
        {
            "source": "hackernews",
            "url": "https://news.ycombinator.com/item?id=12345678",
            "title": "New AI Framework for Developers",
            "timestamp": "2024-09-22T10:00:00Z",
            "metrics": {
                "score": 245,
                "comments": 89,
                "heat_score": 0.82
            },
            "raw": {
                "objectID": "12345678",
                "title": "New AI Framework for Developers",
                "url": "https://example.com/ai-framework",
                "points": 245,
                "num_comments": 89,
                "created_at": "2024-09-22T09:30:00Z",
                "author": "techdev"
            }
        }
    ]

@pytest.fixture
def mock_news_data():
    """Mock news data"""
    return [
        {
            "source": "newsapi",
            "url": "https://example.com/ai-breakthrough",
            "title": "AI Breakthrough in Natural Language Processing",
            "timestamp": "2024-09-22T10:00:00Z",
            "metrics": {
                "relevance_score": 0.92,
                "sentiment": 0.8,
                "engagement": 0.75
            },
            "raw": {
                "source": {"id": "tech-crunch", "name": "TechCrunch"},
                "author": "John Doe",
                "title": "AI Breakthrough in Natural Language Processing",
                "description": "New research shows significant improvements in NLP models...",
                "url": "https://example.com/ai-breakthrough",
                "publishedAt": "2024-09-22T09:30:00Z"
            }
        }
    ]

@pytest.fixture
def mock_google_trends():
    """Mock Google Trends data"""
    return [
        {
            "source": "google_trends",
            "url": "https://trends.google.com/trends/explore?q=artificial+intelligence",
            "title": "Artificial Intelligence Trends",
            "timestamp": "2024-09-22T10:00:00Z",
            "metrics": {
                "trend_score": 0.85,
                "search_volume": 95000,
                "growth_rate": 0.15
            },
            "raw": {
                "keyword": "artificial intelligence",
                "region": "US",
                "timeframe": "7d",
                "interest_over_time": [
                    {"date": "2024-09-15", "value": 80},
                    {"date": "2024-09-16", "value": 85},
                    {"date": "2024-09-17", "value": 90},
                    {"date": "2024-09-18", "value": 88},
                    {"date": "2024-09-19", "value": 92},
                    {"date": "2024-09-20", "value": 95},
                    {"date": "2024-09-21", "value": 98}
                ]
            }
        }
    ]

@pytest.fixture
def mock_reddit_data():
    """Mock Reddit data"""
    return [
        {
            "source": "reddit",
            "url": "https://reddit.com/r/MachineLearning/comments/123456",
            "title": "New ML Framework Discussion",
            "timestamp": "2024-09-22T10:00:00Z",
            "metrics": {
                "upvotes": 1250,
                "comments": 89,
                "engagement_score": 0.88
            },
            "raw": {
                "id": "123456",
                "title": "New ML Framework Discussion",
                "selftext": "Discussion about the new machine learning framework...",
                "score": 1250,
                "num_comments": 89,
                "created_utc": 1726992000,
                "subreddit": "MachineLearning",
                "author": "ml_enthusiast"
            }
        }
    ]

@pytest.fixture
def sample_niche_score():
    """Sample niche score for testing"""
    return {
        "topic": "AI Chatbot Development",
        "total_score": 8.5,
        "confidence": 0.9,
        "signals": {
            "trend_momentum": 0.8,
            "github_velocity": 0.9,
            "hackernews_heat": 0.7,
            "news_delta": 0.8,
            "reddit_engagement": 0.6,
            "competition_proxy": 0.3,
            "feasibility_fit": 0.9
        },
        "sources": [
            {
                "source_name": "GitHub Trending",
                "url": "https://github.com/trending",
                "timestamp": "2024-09-22T10:00:00Z",
                "domain": "github.com"
            }
        ]
    }

@pytest.fixture
def vcr_cassette():
    """VCR cassette for HTTP recording"""
    return vcr_config

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test"""
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    os.makedirs("reports/coverage", exist_ok=True)
    os.makedirs("reports/playbooks", exist_ok=True)
    os.makedirs("tests/cassettes", exist_ok=True)
    
    # Set test environment variables
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    yield
    
    # Cleanup after test
    # Remove temporary files if needed
    pass

@pytest.fixture
def mock_web_response():
    """Mock web response for testing"""
    return {
        "success": True,
        "data": "Test web content",
        "attribution": {
            "source_name": "Test Source",
            "url": "https://example.com/test",
            "retrieved_at": "2024-09-22T10:00:00Z",
            "domain": "example.com"
        },
        "cache_hit": False,
        "latency_ms": 150
    }

@pytest.fixture
def mock_tool_gate_decision():
    """Mock tool gate decision for testing"""
    return {
        "allowed": True,
        "reason": "Tool request approved",
        "sanitized_params": {
            "query": "test query",
            "window": "24h"
        }
    }

# Pytest markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "web: Tests requiring web access")

# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Add markers based on test file names
    for item in items:
        if "test_niche_units" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "test_niche_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "test_niche_ui" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
        
        # Add web marker for tests that require web access
        if any(keyword in item.nodeid for keyword in ["web", "http", "api"]):
            item.add_marker(pytest.mark.web)
