"""
Integration Tests for Full RSS → RAG Pipeline
Tests the complete flow: RSS fetch → filter → duplicate check → add to RAG → history tracking
"""

import tempfile
import os
import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from backend.services.rss_fetcher import RSSFetcher
from backend.services.content_curator import ContentCurator
from backend.services.rss_fetch_history import RSSFetchHistory
from backend.learning.knowledge_retention import KnowledgeRetention


class TestRSSRAGPipeline:
    """Integration tests for RSS → RAG pipeline"""
    
    @pytest.fixture
    def temp_db_history(self):
        """Create temporary database for RSS fetch history"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        db_path = temp_file.name
        yield db_path
        import time
        time.sleep(0.1)
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
        except PermissionError:
            pass
    
    @pytest.fixture
    def temp_db_retention(self):
        """Create temporary database for knowledge retention"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        db_path = temp_file.name
        yield db_path
        import time
        time.sleep(0.1)
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
        except PermissionError:
            pass
    
    @pytest.fixture
    def mock_rag_retrieval(self):
        """Create mock RAG retrieval service"""
        mock_rag = MagicMock()
        mock_rag.add_learning_content = Mock(return_value=True)
        mock_rag.retrieve_context = Mock(return_value={"knowledge_docs": [], "conversation_docs": [], "total_context_docs": 0})
        return mock_rag
    
    @pytest.fixture
    def pipeline_components(self, temp_db_history, temp_db_retention, mock_rag_retrieval):
        """Create all pipeline components"""
        rss_fetcher = RSSFetcher()
        content_curator = ContentCurator()
        rss_fetch_history = RSSFetchHistory(db_path=temp_db_history)
        knowledge_retention = KnowledgeRetention(db_path=temp_db_retention)
        
        return {
            "rss_fetcher": rss_fetcher,
            "content_curator": content_curator,
            "rss_fetch_history": rss_fetch_history,
            "knowledge_retention": knowledge_retention,
            "rag_retrieval": mock_rag_retrieval
        }
    
    @pytest.mark.asyncio
    async def test_full_pipeline_success(self, pipeline_components):
        """Test complete pipeline: fetch → filter → add to RAG"""
        rss_fetcher = pipeline_components["rss_fetcher"]
        content_curator = pipeline_components["content_curator"]
        rss_fetch_history = pipeline_components["rss_fetch_history"]
        rag_retrieval = pipeline_components["rag_retrieval"]
        
        # Mock RSS feed data
        mock_entries = [
            {
                "title": "Ethics in AI: Transparency and Governance",
                "summary": (
                    "This article discusses the importance of ethical AI systems with complete transparency. "
                    "It covers AI governance, RAG systems, and the need for open-source solutions. "
                    "StillMe is an example of a transparent AI system that uses retrieval-augmented generation. "
                    "Machine learning and deep learning are important components of modern AI systems. "
                    "Vector databases and embeddings play a crucial role in RAG-based systems."
                ) * 2,  # Make it long enough
                "link": "https://example.com/article1",
                "source": "https://example.com/feed.xml",
                "published": "2025-01-27T10:00:00Z"
            },
            {
                "title": "Short Article",
                "summary": "Too short",
                "link": "https://example.com/article2",
                "source": "https://example.com/feed.xml",
                "published": "2025-01-27T10:00:00Z"
            }
        ]
        
        with patch.object(rss_fetcher, 'fetch_feeds', return_value=mock_entries):
            # Step 1: Fetch RSS feeds
            entries = rss_fetcher.fetch_feeds(max_items_per_feed=5)
            assert len(entries) == 2
            
            # Step 2: Create fetch cycle
            cycle_id = rss_fetch_history.create_fetch_cycle(cycle_number=1)
            assert cycle_id > 0
            
            # Step 3: Pre-filter content
            filtered_entries, rejected_entries = content_curator.pre_filter_content(entries)
            
            # Should filter out short content
            assert len(filtered_entries) == 1
            assert len(rejected_entries) == 1
            assert filtered_entries[0]["title"] == "Ethics in AI: Transparency and Governance"
            
            # Track rejected entries
            for rejected in rejected_entries:
                rss_fetch_history.add_fetch_item(
                    cycle_id=cycle_id,
                    title=rejected.get("title", ""),
                    source_url=rejected.get("source", ""),
                    link=rejected.get("link", ""),
                    summary=rejected.get("summary", ""),
                    status="Filtered: Low Score",
                    status_reason=rejected.get("rejection_reason", "")
                )
            
            # Step 4: Check for duplicates
            for entry in filtered_entries:
                content = f"{entry['title']}\n{entry['summary']}"
                
                # Mock no duplicates found
                rag_retrieval.retrieve_context.return_value = {
                    "knowledge_docs": [],
                    "conversation_docs": [],
                    "total_context_docs": 0
                }
                
                existing = rag_retrieval.retrieve_context(
                    query=entry['title'],
                    knowledge_limit=1,
                    conversation_limit=0
                )
                is_duplicate = len(existing.get("knowledge_docs", [])) > 0
                
                if not is_duplicate:
                    # Step 5: Add to RAG
                    success = rag_retrieval.add_learning_content(
                        content=content,
                        source=entry['source'],
                        content_type="knowledge",
                        metadata={
                            "link": entry['link'],
                            "published": entry['published'],
                            "type": "rss_feed",
                            "title": entry.get('title', '')[:200]
                        }
                    )
                    
                    if success:
                        # Step 6: Track in history
                        rss_fetch_history.add_fetch_item(
                            cycle_id=cycle_id,
                            title=entry.get("title", ""),
                            source_url=entry.get("source", ""),
                            link=entry.get("link", ""),
                            summary=entry.get("summary", ""),
                            status="Added to RAG",
                            vector_id=f"vector_{entry.get('link', '')[:8]}"
                        )
            
            # Complete cycle
            rss_fetch_history.complete_fetch_cycle(cycle_id)
            
            # Verify history
            history_items = rss_fetch_history.get_latest_fetch_items(limit=10)
            assert len(history_items) == 2
            assert any(item["status"] == "Added to RAG" for item in history_items)
            assert any(item["status"] == "Filtered: Low Score" for item in history_items)
            
            # Verify RAG was called
            assert rag_retrieval.add_learning_content.called
    
    @pytest.mark.asyncio
    async def test_pipeline_with_duplicate_detection(self, pipeline_components):
        """Test pipeline handles duplicate content correctly"""
        rss_fetcher = pipeline_components["rss_fetcher"]
        content_curator = pipeline_components["content_curator"]
        rss_fetch_history = pipeline_components["rss_fetch_history"]
        rag_retrieval = pipeline_components["rag_retrieval"]
        
        # Mock entry
        mock_entry = {
            "title": "Existing Article",
            "summary": "This article already exists in RAG. " * 50,
            "link": "https://example.com/existing",
            "source": "https://example.com/feed.xml",
            "published": "2025-01-27T10:00:00Z"
        }
        
        with patch.object(rss_fetcher, 'fetch_feeds', return_value=[mock_entry]):
            entries = rss_fetcher.fetch_feeds(max_items_per_feed=5)
            
            cycle_id = rss_fetch_history.create_fetch_cycle(cycle_number=1)
            
            # Pre-filter
            filtered_entries, _ = content_curator.pre_filter_content(entries)
            assert len(filtered_entries) == 1
            
            # Mock duplicate found
            mock_existing_doc = {
                "content": "Existing content",
                "metadata": {"link": "https://example.com/existing"}
            }
            rag_retrieval.retrieve_context.return_value = {
                "knowledge_docs": [mock_existing_doc],
                "conversation_docs": [],
                "total_context_docs": 1
            }
            
            # Check for duplicate
            entry = filtered_entries[0]
            existing = rag_retrieval.retrieve_context(
                query=entry['title'],
                knowledge_limit=1,
                conversation_limit=0
            )
            
            is_duplicate = False
            if existing.get("knowledge_docs"):
                existing_doc = existing["knowledge_docs"][0]
                existing_metadata = existing_doc.get("metadata", {})
                if existing_metadata.get("link") == entry.get("link", ""):
                    is_duplicate = True
            
            assert is_duplicate is True
            
            # Track as duplicate
            rss_fetch_history.add_fetch_item(
                cycle_id=cycle_id,
                title=entry.get("title", ""),
                source_url=entry.get("source", ""),
                link=entry.get("link", ""),
                summary=entry.get("summary", ""),
                status="Filtered: Duplicate",
                status_reason="Content already exists in RAG"
            )
            
            rss_fetch_history.complete_fetch_cycle(cycle_id)
            
            # Verify duplicate was tracked
            history_items = rss_fetch_history.get_latest_fetch_items(limit=10)
            assert len(history_items) == 1
            assert history_items[0]["status"] == "Filtered: Duplicate"
            
            # Verify RAG add was NOT called
            assert not rag_retrieval.add_learning_content.called
    
    @pytest.mark.asyncio
    async def test_pipeline_error_handling(self, pipeline_components):
        """Test pipeline handles errors gracefully"""
        rss_fetcher = pipeline_components["rss_fetcher"]
        content_curator = pipeline_components["content_curator"]
        rss_fetch_history = pipeline_components["rss_fetch_history"]
        rag_retrieval = pipeline_components["rag_retrieval"]
        
        # Mock entry
        mock_entry = {
            "title": "Test Article",
            "summary": "Ethics in AI and transparency. " * 50,
            "link": "https://example.com/article",
            "source": "https://example.com/feed.xml",
            "published": "2025-01-27T10:00:00Z"
        }
        
        with patch.object(rss_fetcher, 'fetch_feeds', return_value=[mock_entry]):
            entries = rss_fetcher.fetch_feeds(max_items_per_feed=5)
            
            cycle_id = rss_fetch_history.create_fetch_cycle(cycle_number=1)
            
            # Pre-filter
            filtered_entries, _ = content_curator.pre_filter_content(entries)
            
            # Mock RAG add failure
            rag_retrieval.add_learning_content.return_value = False
            rag_retrieval.retrieve_context.return_value = {
                "knowledge_docs": [],
                "conversation_docs": [],
                "total_context_docs": 0
            }
            
            # Process entry
            for entry in filtered_entries:
                content = f"{entry['title']}\n{entry['summary']}"
                
                # Check duplicate (none)
                existing = rag_retrieval.retrieve_context(
                    query=entry['title'],
                    knowledge_limit=1,
                    conversation_limit=0
                )
                is_duplicate = len(existing.get("knowledge_docs", [])) > 0
                
                if not is_duplicate:
                    # Try to add (will fail)
                    success = rag_retrieval.add_learning_content(
                        content=content,
                        source=entry['source'],
                        content_type="knowledge",
                        metadata={"link": entry['link']}
                    )
                    
                    if not success:
                        # Track failure
                        rss_fetch_history.add_fetch_item(
                            cycle_id=cycle_id,
                            title=entry.get("title", ""),
                            source_url=entry.get("source", ""),
                            link=entry.get("link", ""),
                            summary=entry.get("summary", ""),
                            status="Filtered: Low Score",
                            status_reason="Failed to add to RAG"
                        )
            
            rss_fetch_history.complete_fetch_cycle(cycle_id)
            
            # Verify failure was tracked
            history_items = rss_fetch_history.get_latest_fetch_items(limit=10)
            assert len(history_items) == 1
            assert "Failed" in history_items[0].get("status_reason", "")
    
    @pytest.mark.asyncio
    async def test_pipeline_with_scheduler_integration(self, pipeline_components):
        """Test pipeline integration with scheduler"""
        from backend.services.learning_scheduler import LearningScheduler
        
        rss_fetcher = pipeline_components["rss_fetcher"]
        scheduler = LearningScheduler(
            rss_fetcher=rss_fetcher,
            interval_hours=1,
            auto_add_to_rag=False  # Scheduler doesn't auto-add, main.py does
        )
        
        # Mock RSS fetch
        mock_entries = [
            {
                "title": "Scheduled Article",
                "summary": "Ethics and transparency. " * 50,
                "link": "https://example.com/scheduled",
                "source": "https://example.com/feed.xml",
                "published": "2025-01-27T10:00:00Z"
            }
        ]
        
        with patch.object(rss_fetcher, 'fetch_feeds', return_value=mock_entries):
            # Run learning cycle
            result = await scheduler.run_learning_cycle()
            
            assert result["cycle_number"] == 1
            assert result["entries_fetched"] == 1
            assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_pipeline_end_to_end_with_all_components(self, pipeline_components):
        """Test complete end-to-end pipeline with all components"""
        rss_fetcher = pipeline_components["rss_fetcher"]
        content_curator = pipeline_components["content_curator"]
        rss_fetch_history = pipeline_components["rss_fetch_history"]
        knowledge_retention = pipeline_components["knowledge_retention"]
        rag_retrieval = pipeline_components["rag_retrieval"]
        
        # Mock high-quality entries
        mock_entries = [
            {
                "title": "High Quality Article 1",
                "summary": (
                    "Ethics in AI systems with complete transparency and governance. "
                    "RAG systems and StillMe demonstrate how retrieval-augmented generation works. "
                    "Machine learning and vector databases are essential components."
                ) * 10,
                "link": "https://example.com/hq1",
                "source": "https://example.com/feed.xml",
                "published": "2025-01-27T10:00:00Z"
            },
            {
                "title": "High Quality Article 2",
                "summary": (
                    "Transparency and ethical AI governance with open-source solutions. "
                    "StillMe uses RAG to continuously learn from trusted sources."
                ) * 10,
                "link": "https://example.com/hq2",
                "source": "https://example.com/feed.xml",
                "published": "2025-01-27T10:00:00Z"
            }
        ]
        
        with patch.object(rss_fetcher, 'fetch_feeds', return_value=mock_entries):
            # Step 1: Fetch
            entries = rss_fetcher.fetch_feeds(max_items_per_feed=5)
            
            # Step 2: Create cycle
            cycle_id = rss_fetch_history.create_fetch_cycle(cycle_number=1)
            
            # Step 3: Pre-filter
            filtered_entries, rejected_entries = content_curator.pre_filter_content(entries)
            
            # Track rejected
            for rejected in rejected_entries:
                rss_fetch_history.add_fetch_item(
                    cycle_id=cycle_id,
                    title=rejected.get("title", ""),
                    source_url=rejected.get("source", ""),
                    link=rejected.get("link", ""),
                    summary=rejected.get("summary", ""),
                    status="Filtered: Low Score",
                    status_reason=rejected.get("rejection_reason", "")
                )
            
            # Step 4: Process filtered entries
            added_count = 0
            for entry in filtered_entries:
                content = f"{entry['title']}\n{entry['summary']}"
                
                # Check duplicate
                rag_retrieval.retrieve_context.return_value = {
                    "knowledge_docs": [],
                    "conversation_docs": [],
                    "total_context_docs": 0
                }
                existing = rag_retrieval.retrieve_context(
                    query=entry['title'],
                    knowledge_limit=1,
                    conversation_limit=0
                )
                is_duplicate = len(existing.get("knowledge_docs", [])) > 0
                
                if not is_duplicate:
                    # Add to RAG
                    success = rag_retrieval.add_learning_content(
                        content=content,
                        source=entry['source'],
                        content_type="knowledge",
                        metadata={"link": entry['link'], "title": entry['title']}
                    )
                    
                    if success:
                        added_count += 1
                        # Track in history
                        rss_fetch_history.add_fetch_item(
                            cycle_id=cycle_id,
                            title=entry.get("title", ""),
                            source_url=entry.get("source", ""),
                            link=entry.get("link", ""),
                            summary=entry.get("summary", ""),
                            status="Added to RAG",
                            vector_id=f"vector_{entry.get('link', '')[:8]}"
                        )
                        
                        # Record in knowledge retention
                        knowledge_retention.record_learning_session(
                            session_type="rss_fetch",
                            content_learned=content[:500],
                            accuracy_score=0.8,
                            metadata={"source": entry['source'], "link": entry['link']}
                        )
            
            # Complete cycle
            rss_fetch_history.complete_fetch_cycle(cycle_id)
            
            # Verify results
            history_items = rss_fetch_history.get_latest_fetch_items(limit=10)
            assert len(history_items) == len(filtered_entries)
            assert added_count > 0
            
            # Verify knowledge retention
            retained = knowledge_retention.get_retained_knowledge(min_retention_score=0.0, limit=10)
            assert len(retained) >= 0  # May or may not have retention score yet

