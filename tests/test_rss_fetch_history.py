"""
Tests for RSS Fetch History Service
Tests fetch cycle creation, item tracking, retrieval, and cycle statistics
"""

import pytest
import tempfile
import os
from backend.services.rss_fetch_history import RSSFetchHistory
from datetime import datetime


class TestRSSFetchHistory:
    """Test suite for RSSFetchHistory"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        db_path = temp_file.name
        
        yield db_path
        
        # Cleanup - wait a bit for connections to close
        import time
        time.sleep(0.1)
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
        except PermissionError:
            # On Windows, file might still be locked - ignore for now
            pass
    
    @pytest.fixture
    def history(self, temp_db):
        """Create RSSFetchHistory instance with temp database"""
        return RSSFetchHistory(db_path=temp_db)
    
    def test_create_fetch_cycle_success(self, history):
        """Test successful fetch cycle creation"""
        cycle_id = history.create_fetch_cycle(cycle_number=1)
        
        assert cycle_id > 0
        assert isinstance(cycle_id, int)
    
    def test_create_fetch_cycle_multiple_cycles(self, history):
        """Test creating multiple fetch cycles"""
        cycle_id1 = history.create_fetch_cycle(cycle_number=1)
        cycle_id2 = history.create_fetch_cycle(cycle_number=2)
        cycle_id3 = history.create_fetch_cycle(cycle_number=3)
        
        assert cycle_id1 > 0
        assert cycle_id2 > cycle_id1
        assert cycle_id3 > cycle_id2
    
    def test_add_fetch_item_success(self, history):
        """Test successful fetch item addition"""
        cycle_id = history.create_fetch_cycle(cycle_number=1)
        
        item_id = history.add_fetch_item(
            cycle_id=cycle_id,
            title="Test Article",
            source_url="https://example.com/feed.xml",
            link="https://example.com/article",
            summary="Test article summary",
            status="Added to RAG",
            status_reason="Successfully added",
            vector_id="vector_123",
            added_to_rag_at=datetime.now().isoformat()
        )
        
        assert item_id > 0
        assert isinstance(item_id, int)
    
    def test_add_fetch_item_different_statuses(self, history):
        """Test adding items with different statuses"""
        cycle_id = history.create_fetch_cycle(cycle_number=1)
        
        # Add item with "Added to RAG" status
        item_id1 = history.add_fetch_item(
            cycle_id=cycle_id,
            title="Article 1",
            source_url="https://example.com/feed.xml",
            link="https://example.com/article1",
            summary="Summary 1",
            status="Added to RAG"
        )
        
        # Add item with "Filtered: Duplicate" status
        item_id2 = history.add_fetch_item(
            cycle_id=cycle_id,
            title="Article 2",
            source_url="https://example.com/feed.xml",
            link="https://example.com/article2",
            summary="Summary 2",
            status="Filtered: Duplicate",
            status_reason="Duplicate link found"
        )
        
        # Add item with "Filtered: Low Score" status
        item_id3 = history.add_fetch_item(
            cycle_id=cycle_id,
            title="Article 3",
            source_url="https://example.com/feed.xml",
            link="https://example.com/article3",
            summary="Summary 3",
            status="Filtered: Low Score",
            status_reason="Keyword score too low"
        )
        
        assert item_id1 > 0
        assert item_id2 > 0
        assert item_id3 > 0
    
    def test_get_latest_fetch_items(self, history):
        """Test retrieving latest fetch items"""
        cycle_id = history.create_fetch_cycle(cycle_number=1)
        
        # Add multiple items
        for i in range(5):
            history.add_fetch_item(
                cycle_id=cycle_id,
                title=f"Article {i}",
                source_url="https://example.com/feed.xml",
                link=f"https://example.com/article{i}",
                summary=f"Summary {i}",
                status="Added to RAG"
            )
        
        # Complete the cycle (no parameters needed - stats are auto-updated)
        history.complete_fetch_cycle(cycle_id=cycle_id)
        
        # Get latest items
        items = history.get_latest_fetch_items(limit=10)
        
        assert len(items) == 5
        assert items[0]["title"] == "Article 4"  # Most recent first
        assert items[0]["status"] == "Added to RAG"
    
    def test_get_latest_fetch_items_limit(self, history):
        """Test limit parameter in get_latest_fetch_items"""
        cycle_id = history.create_fetch_cycle(cycle_number=1)
        
        # Add 10 items
        for i in range(10):
            history.add_fetch_item(
                cycle_id=cycle_id,
                title=f"Article {i}",
                source_url="https://example.com/feed.xml",
                link=f"https://example.com/article{i}",
                summary=f"Summary {i}",
                status="Added to RAG"
            )
        
        history.complete_fetch_cycle(cycle_id=cycle_id)
        
        # Get with limit
        items = history.get_latest_fetch_items(limit=5)
        
        assert len(items) == 5
    
    def test_get_latest_fetch_items_empty(self, history):
        """Test retrieval when no items exist"""
        items = history.get_latest_fetch_items(limit=10)
        
        assert isinstance(items, list)
        assert len(items) == 0
    
    def test_complete_fetch_cycle(self, history):
        """Test completing a fetch cycle"""
        cycle_id = history.create_fetch_cycle(cycle_number=1)
        
        # Add some items
        history.add_fetch_item(
            cycle_id=cycle_id,
            title="Article 1",
            source_url="https://example.com/feed.xml",
            link="https://example.com/article1",
            summary="Summary 1",
            status="Added to RAG"
        )
        
        # Complete cycle (stats are auto-updated when items are added)
        history.complete_fetch_cycle(cycle_id=cycle_id)
        
        # Verify cycle is completed (check via get_latest_fetch_items)
        items = history.get_latest_fetch_items(limit=10)
        assert len(items) >= 1
    
    def test_complete_fetch_cycle_statistics(self, history):
        """Test cycle completion with detailed statistics"""
        cycle_id = history.create_fetch_cycle(cycle_number=1)
        
        # Add items with different statuses
        history.add_fetch_item(cycle_id=cycle_id, title="A1", source_url="feed1", link="link1", summary="S1", status="Added to RAG")
        history.add_fetch_item(cycle_id=cycle_id, title="A2", source_url="feed1", link="link2", summary="S2", status="Filtered: Duplicate")
        history.add_fetch_item(cycle_id=cycle_id, title="A3", source_url="feed1", link="link3", summary="S3", status="Filtered: Low Score")
        
        # Complete cycle (stats are auto-updated when items are added)
        history.complete_fetch_cycle(cycle_id=cycle_id)
        
        # Statistics should be stored
        items = history.get_latest_fetch_items(limit=10)
        assert len(items) == 3
    
    def test_get_latest_fetch_items_from_most_recent_cycle(self, history):
        """Test that get_latest_fetch_items returns items from most recent cycle"""
        # Create first cycle
        cycle_id1 = history.create_fetch_cycle(cycle_number=1)
        history.add_fetch_item(cycle_id=cycle_id1, title="Cycle 1 Article", source_url="feed1", link="link1", summary="S1", status="Added to RAG")
        history.complete_fetch_cycle(cycle_id=cycle_id1)
        
        # Create second cycle
        cycle_id2 = history.create_fetch_cycle(cycle_number=2)
        history.add_fetch_item(cycle_id=cycle_id2, title="Cycle 2 Article", source_url="feed1", link="link2", summary="S2", status="Added to RAG")
        history.complete_fetch_cycle(cycle_id=cycle_id2)
        
        # Get latest items (should be from cycle 2)
        items = history.get_latest_fetch_items(limit=10)
        
        assert len(items) == 1
        assert items[0]["title"] == "Cycle 2 Article"
    
    def test_add_fetch_item_with_vector_id(self, history):
        """Test adding item with vector ID"""
        cycle_id = history.create_fetch_cycle(cycle_number=1)
        
        item_id = history.add_fetch_item(
            cycle_id=cycle_id,
            title="Article with Vector ID",
            source_url="https://example.com/feed.xml",
            link="https://example.com/article",
            summary="Summary",
            status="Added to RAG",
            vector_id="vector_abc123",
            added_to_rag_at=datetime.now().isoformat()
        )
        
        assert item_id > 0
        
        # Verify vector_id is stored
        items = history.get_latest_fetch_items(limit=1)
        assert len(items) == 1
        assert items[0]["vector_id"] == "vector_abc123"
    
    def test_add_fetch_item_with_status_reason(self, history):
        """Test adding item with status reason"""
        cycle_id = history.create_fetch_cycle(cycle_number=1)
        
        item_id = history.add_fetch_item(
            cycle_id=cycle_id,
            title="Filtered Article",
            source_url="https://example.com/feed.xml",
            link="https://example.com/article",
            summary="Summary",
            status="Filtered: Low Score",
            status_reason="Content length too short: 200 chars < 500 minimum"
        )
        
        assert item_id > 0
        
        # Verify status_reason is stored
        items = history.get_latest_fetch_items(limit=1)
        assert len(items) == 1
        assert items[0]["status_reason"] == "Content length too short: 200 chars < 500 minimum"
    
    def test_fetch_item_timestamps(self, history):
        """Test that fetch timestamps are properly stored"""
        cycle_id = history.create_fetch_cycle(cycle_number=1)
        
        item_id = history.add_fetch_item(
            cycle_id=cycle_id,
            title="Article",
            source_url="https://example.com/feed.xml",
            link="https://example.com/article",
            summary="Summary",
            status="Added to RAG"
        )
        
        assert item_id > 0
        
        # Verify timestamp exists
        items = history.get_latest_fetch_items(limit=1)
        assert len(items) == 1
        assert "fetch_timestamp" in items[0]
        assert items[0]["fetch_timestamp"] is not None
    
    def test_multiple_items_same_cycle(self, history):
        """Test adding multiple items to same cycle"""
        cycle_id = history.create_fetch_cycle(cycle_number=1)
        
        # Add multiple items
        item_ids = []
        for i in range(10):
            item_id = history.add_fetch_item(
                cycle_id=cycle_id,
                title=f"Article {i}",
                source_url="https://example.com/feed.xml",
                link=f"https://example.com/article{i}",
                summary=f"Summary {i}",
                status="Added to RAG"
            )
            item_ids.append(item_id)
        
        # All should have different IDs
        assert len(set(item_ids)) == 10
        
        # All should be retrievable
        items = history.get_latest_fetch_items(limit=20)
        assert len(items) == 10
    
    def test_database_initialization(self, history):
        """Test database is properly initialized"""
        # Database should be created and tables should exist
        # This is tested implicitly by being able to create cycles and items
        cycle_id = history.create_fetch_cycle(cycle_number=1)
        assert cycle_id > 0

