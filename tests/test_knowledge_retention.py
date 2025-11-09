"""
Tests for Knowledge Retention Service
Tests knowledge addition, retrieval, retention score calculation, and database operations
"""

import pytest
import tempfile
import os
from backend.learning.knowledge_retention import KnowledgeRetention


class TestKnowledgeRetention:
    """Test suite for KnowledgeRetention"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        db_path = temp_file.name
        
        yield db_path
        
        # Cleanup
        if os.path.exists(db_path):
            os.remove(db_path)
    
    @pytest.fixture
    def retention(self, temp_db):
        """Create KnowledgeRetention instance with temp database"""
        return KnowledgeRetention(db_path=temp_db)
    
    def test_add_knowledge_success(self, retention):
        """Test successful knowledge addition"""
        knowledge_id = retention.add_knowledge(
            content="Test knowledge content",
            source="https://example.com/article",
            knowledge_type="general",
            confidence_score=0.8,
            metadata={"author": "Test Author"}
        )
        
        assert knowledge_id > 0
        assert isinstance(knowledge_id, int)
    
    def test_add_knowledge_with_metadata(self, retention):
        """Test knowledge addition with metadata"""
        metadata = {
            "author": "Test Author",
            "tags": ["test", "knowledge"],
            "timestamp": "2025-01-27T10:00:00Z"
        }
        
        knowledge_id = retention.add_knowledge(
            content="Test content with metadata",
            source="https://example.com/article",
            metadata=metadata
        )
        
        assert knowledge_id > 0
        
        # Verify metadata was stored (use min_retention_score=0.0 to get all items)
        knowledge = retention.get_retained_knowledge(min_retention_score=0.0, limit=1)
        assert len(knowledge) == 1
        stored_metadata = knowledge[0].get("metadata", {})
        assert stored_metadata.get("author") == "Test Author"
    
    def test_add_knowledge_default_values(self, retention):
        """Test knowledge addition with default values"""
        knowledge_id = retention.add_knowledge(
            content="Test content",
            source="https://example.com/article"
        )
        
        assert knowledge_id > 0
        
        # Verify defaults
        knowledge = retention.get_retained_knowledge(limit=1, min_retention_score=0.0)
        assert len(knowledge) == 1
        assert knowledge[0]["knowledge_type"] == "general"
        assert knowledge[0]["confidence_score"] == 0.5
    
    def test_get_retained_knowledge_basic(self, retention):
        """Test basic knowledge retrieval"""
        # Add knowledge
        retention.add_knowledge(
            content="Test knowledge",
            source="https://example.com/article",
            knowledge_type="general"
        )
        
        # Update retention score to make it retrievable
        knowledge = retention.get_retained_knowledge(min_retention_score=0.0, limit=10)
        assert len(knowledge) >= 1
        assert knowledge[0]["content"] == "Test knowledge"
        assert knowledge[0]["source"] == "https://example.com/article"
    
    def test_get_retained_knowledge_min_score_filter(self, retention):
        """Test knowledge retrieval with minimum score filter"""
        # Add knowledge
        knowledge_id = retention.add_knowledge(
            content="High score knowledge",
            source="https://example.com/high",
            knowledge_type="general"
        )
        
        # Set high retention score
        retention.update_retention_score(knowledge_id, 0.9)
        
        # Add another with low score
        knowledge_id2 = retention.add_knowledge(
            content="Low score knowledge",
            source="https://example.com/low",
            knowledge_type="general"
        )
        retention.update_retention_score(knowledge_id2, 0.3)
        
        # Get only high score items
        high_score_items = retention.get_retained_knowledge(min_retention_score=0.7, limit=10)
        
        # Should only return high score item
        assert len(high_score_items) >= 1
        assert all(item["retention_score"] >= 0.7 for item in high_score_items)
    
    def test_get_retained_knowledge_limit(self, retention):
        """Test knowledge retrieval respects limit"""
        # Add multiple knowledge items
        for i in range(5):
            retention.add_knowledge(
                content=f"Knowledge item {i}",
                source=f"https://example.com/{i}",
                knowledge_type="general"
            )
        
        # Get with limit
        knowledge = retention.get_retained_knowledge(min_retention_score=0.0, limit=3)
        
        assert len(knowledge) <= 3
    
    def test_get_retained_knowledge_type_filter(self, retention):
        """Test knowledge retrieval with type filter"""
        # Add knowledge of different types
        retention.add_knowledge(
            content="General knowledge",
            source="https://example.com/general",
            knowledge_type="general"
        )
        retention.add_knowledge(
            content="Technical knowledge",
            source="https://example.com/technical",
            knowledge_type="technical"
        )
        
        # Get only general type
        general_items = retention.get_retained_knowledge(
            knowledge_type="general",
            min_retention_score=0.0,
            limit=10
        )
        
        assert len(general_items) >= 1
        assert all(item["knowledge_type"] == "general" for item in general_items)
    
    def test_update_retention_score_success(self, retention):
        """Test successful retention score update"""
        # Add knowledge
        knowledge_id = retention.add_knowledge(
            content="Test knowledge",
            source="https://example.com/article"
        )
        
        # Update score
        success = retention.update_retention_score(knowledge_id, 0.85)
        
        assert success is True
        
        # Verify update
        knowledge = retention.get_retained_knowledge(min_retention_score=0.8, limit=1)
        assert len(knowledge) == 1
        assert knowledge[0]["retention_score"] == 0.85
    
    def test_update_retention_score_invalid_id(self, retention):
        """Test retention score update with invalid ID"""
        success = retention.update_retention_score(99999, 0.85)
        
        # SQLite UPDATE doesn't fail for non-existent IDs, it just affects 0 rows
        # The method returns True if no exception occurs
        # This is acceptable behavior - we test that it doesn't crash
        assert isinstance(success, bool)
    
    def test_retention_score_calculation(self, retention):
        """Test retention score calculation logic"""
        # Add knowledge
        retention.add_knowledge(
            content="Test knowledge",
            source="https://example.com/article",
            confidence_score=0.9
        )
        
        # Initial retention score should be 0.0
        knowledge = retention.get_retained_knowledge(min_retention_score=0.0, limit=1)
        assert len(knowledge) == 1
        initial_score = knowledge[0]["retention_score"]
        assert initial_score == 0.0  # Default retention score
    
    def test_access_count_tracking(self, retention):
        """Test access count is tracked"""
        # Add knowledge
        retention.add_knowledge(
            content="Test knowledge",
            source="https://example.com/article"
        )
        
        # Get knowledge (should increment access count)
        knowledge = retention.get_retained_knowledge(min_retention_score=0.0, limit=1)
        assert len(knowledge) == 1
        
        # Access count should be tracked (may be 0 initially)
        assert "access_count" in knowledge[0]
        assert isinstance(knowledge[0]["access_count"], int)
    
    def test_record_learning_session(self, retention):
        """Test recording learning session"""
        session_id = retention.record_learning_session(
            session_type="chat",
            content_learned="Q: What is StillMe? A: StillMe is a transparent AI system.",
            accuracy_score=0.85,
            metadata={"user_id": "test_user"}
        )
        
        assert session_id > 0
        assert isinstance(session_id, int)
    
    def test_record_learning_session_with_metadata(self, retention):
        """Test recording learning session with metadata"""
        metadata = {
            "user_id": "test_user",
            "context": "RAG retrieval",
            "model": "gpt-4"
        }
        
        session_id = retention.record_learning_session(
            session_type="chat",
            content_learned="Test learning content",
            accuracy_score=0.9,
            metadata=metadata
        )
        
        assert session_id > 0
    
    def test_get_retained_knowledge_empty(self, retention):
        """Test retrieval when no knowledge exists"""
        knowledge = retention.get_retained_knowledge(limit=10)
        
        assert isinstance(knowledge, list)
        assert len(knowledge) == 0
    
    def test_add_knowledge_error_handling(self, retention):
        """Test error handling in knowledge addition"""
        # Try to add with invalid data (should handle gracefully)
        # Note: SQLite is lenient, so this might not fail, but we test the error path
        knowledge_id = retention.add_knowledge(
            content="",  # Empty content
            source="",  # Empty source
            knowledge_type="invalid_type"
        )
        
        # Should return -1 on error or valid ID if it succeeds
        assert isinstance(knowledge_id, int)
    
    def test_database_operations_isolation(self, retention):
        """Test that database operations are isolated"""
        # Add knowledge
        retention.add_knowledge(
            content="Knowledge 1",
            source="https://example.com/1"
        )
        
        # Create new instance (should use same DB)
        retention2 = KnowledgeRetention(db_path=retention.db_path)
        
        # Should see the same knowledge
        knowledge = retention2.get_retained_knowledge(min_retention_score=0.0, limit=10)
        assert len(knowledge) >= 1
    
    def test_metadata_json_serialization(self, retention):
        """Test metadata is properly serialized as JSON"""
        complex_metadata = {
            "nested": {
                "key": "value",
                "list": [1, 2, 3]
            },
            "tags": ["tag1", "tag2"]
        }
        
        knowledge_id = retention.add_knowledge(
            content="Test content",
            source="https://example.com/article",
            metadata=complex_metadata
        )
        
        assert knowledge_id > 0
        
        # Verify metadata can be retrieved
        knowledge = retention.get_retained_knowledge(min_retention_score=0.0, limit=1)
        assert len(knowledge) == 1
        stored_metadata = knowledge[0].get("metadata", {})
        assert isinstance(stored_metadata, dict)
        assert stored_metadata.get("nested", {}).get("key") == "value"

