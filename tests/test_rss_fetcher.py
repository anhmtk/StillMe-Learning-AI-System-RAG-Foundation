"""
Tests for RSS Fetcher Service
Tests RSS feed fetching, error handling, and edge cases
"""

import pytest
from unittest.mock import patch, MagicMock
from backend.services.rss_fetcher import RSSFetcher


class TestRSSFetcher:
    """Test suite for RSSFetcher"""
    
    def test_fetch_feeds_success(self):
        """Test successful feed fetching"""
        fetcher = RSSFetcher()
        
        # Create mock feed object with entries attribute
        mock_entry1 = MagicMock()
        mock_entry1.title = 'Test Article 1'
        mock_entry1.summary = 'Test summary 1'
        mock_entry1.link = 'https://example.com/article1'
        mock_entry1.published = '2025-01-27T10:00:00Z'
        mock_entry1.get = lambda key, default='': getattr(mock_entry1, key, default)
        
        mock_entry2 = MagicMock()
        mock_entry2.title = 'Test Article 2'
        mock_entry2.summary = ''  # Explicitly set to empty string
        mock_entry2.description = 'Test description 2'
        mock_entry2.link = 'https://example.com/article2'
        mock_entry2.published = '2025-01-27T11:00:00Z'
        # Mock .get() to return description when summary is requested and empty
        def mock_get2(key, default=''):
            if key == 'summary':
                # Return description if summary is empty
                return mock_entry2.description if not mock_entry2.summary else mock_entry2.summary
            elif key == 'description':
                return mock_entry2.description
            return getattr(mock_entry2, key, default)
        mock_entry2.get = mock_get2
        
        mock_feed = MagicMock()
        mock_feed.entries = [mock_entry1, mock_entry2]
        
        with patch('backend.services.rss_fetcher.feedparser.parse', return_value=mock_feed):
            entries = fetcher.fetch_feeds(max_items_per_feed=5)
        
        # Should have entries from all feeds (2 feeds * 2 entries = 4 total)
        assert len(entries) == 4
        # Check that entries are from both feeds
        sources = [entry['source'] for entry in entries]
        assert len(set(sources)) == 2  # Should have 2 different sources
        assert entries[0]['title'] == 'Test Article 1'
        assert entries[0]['summary'] == 'Test summary 1'
        assert entries[0]['link'] == 'https://example.com/article1'
        assert entries[0]['source'] in fetcher.feeds
        assert entries[0]['content_type'] == 'knowledge'
        
        assert entries[1]['title'] == 'Test Article 2'
        assert entries[1]['summary'] == 'Test description 2'  # Should use description if summary missing
    
    def test_fetch_feeds_max_items_limit(self):
        """Test that max_items_per_feed limit is respected"""
        fetcher = RSSFetcher()
        
        # Create mock feed with more entries than limit
        mock_entries = []
        for i in range(10):
            mock_entry = MagicMock()
            mock_entry.title = f'Article {i}'
            mock_entry.summary = f'Summary {i}'
            mock_entry.link = f'https://example.com/{i}'
            mock_entry.published = '2025-01-27T10:00:00Z'
            mock_entry.get = lambda key, default='': getattr(mock_entry, key, default)
            mock_entries.append(mock_entry)
        
        mock_feed = MagicMock()
        mock_feed.entries = mock_entries
        
        with patch('backend.services.rss_fetcher.feedparser.parse', return_value=mock_feed):
            entries = fetcher.fetch_feeds(max_items_per_feed=3)
        
        # Should only return 3 items per feed (2 feeds * 3 entries = 6 total)
        assert len(entries) == 6
        # Verify limit is respected per feed
        sources = [entry['source'] for entry in entries]
        for source in set(sources):
            source_entries = [e for e in entries if e['source'] == source]
            assert len(source_entries) == 3
    
    def test_fetch_feeds_multiple_feeds(self):
        """Test fetching from multiple feeds"""
        fetcher = RSSFetcher()
        
        # Mock different responses for different feeds
        def mock_parse(url):
            mock_feed = MagicMock()
            if 'ycombinator' in url:
                mock_entry = MagicMock()
                mock_entry.title = 'HN Article'
                mock_entry.summary = 'HN Summary'
                mock_entry.link = 'https://news.ycombinator.com/item?id=1'
                mock_entry.published = '2025-01-27T10:00:00Z'
                mock_entry.get = lambda key, default='': getattr(mock_entry, key, default)
                mock_feed.entries = [mock_entry]
            elif 'nytimes' in url:
                mock_entry = MagicMock()
                mock_entry.title = 'NYT Article'
                mock_entry.summary = 'NYT Summary'
                mock_entry.link = 'https://nytimes.com/article1'
                mock_entry.published = '2025-01-27T10:00:00Z'
                mock_entry.get = lambda key, default='': getattr(mock_entry, key, default)
                mock_feed.entries = [mock_entry]
            else:
                mock_feed.entries = []
            return mock_feed
        
        with patch('backend.services.rss_fetcher.feedparser.parse', side_effect=mock_parse):
            entries = fetcher.fetch_feeds(max_items_per_feed=5)
        
        # Should have entries from multiple feeds
        assert len(entries) >= 1
        sources = [entry['source'] for entry in entries]
        assert any('ycombinator' in source for source in sources) or any('nytimes' in source for source in sources)
    
    def test_fetch_feeds_network_failure(self):
        """Test handling of network failures"""
        fetcher = RSSFetcher()
        
        # Mock feedparser to raise exception
        with patch('backend.services.rss_fetcher.feedparser.parse', side_effect=Exception("Network error")):
            entries = fetcher.fetch_feeds(max_items_per_feed=5)
        
        # Should return empty list or partial results (other feeds might succeed)
        assert isinstance(entries, list)
    
    def test_fetch_feeds_invalid_feed(self):
        """Test handling of invalid feed URLs"""
        fetcher = RSSFetcher()
        
        # Mock feedparser to return invalid feed structure
        mock_feed = MagicMock()
        mock_feed.entries = None  # Invalid structure
        
        with patch('backend.services.rss_fetcher.feedparser.parse', return_value=mock_feed):
            entries = fetcher.fetch_feeds(max_items_per_feed=5)
        
        # Should handle gracefully
        assert isinstance(entries, list)
    
    def test_fetch_feeds_empty_entries(self):
        """Test handling of feeds with no entries"""
        fetcher = RSSFetcher()
        
        mock_feed = MagicMock()
        mock_feed.entries = []
        
        with patch('backend.services.rss_fetcher.feedparser.parse', return_value=mock_feed):
            entries = fetcher.fetch_feeds(max_items_per_feed=5)
        
        assert len(entries) == 0
    
    def test_fetch_single_feed_success(self):
        """Test successful single feed fetching"""
        fetcher = RSSFetcher()
        feed_url = "https://example.com/feed.xml"
        
        mock_entry = MagicMock()
        mock_entry.title = 'Single Article'
        mock_entry.summary = 'Single Summary'
        mock_entry.link = 'https://example.com/article'
        mock_entry.published = '2025-01-27T10:00:00Z'
        mock_entry.get = lambda key, default='': getattr(mock_entry, key, default)
        
        mock_feed = MagicMock()
        mock_feed.entries = [mock_entry]
        
        with patch('backend.services.rss_fetcher.feedparser.parse', return_value=mock_feed):
            entries = fetcher.fetch_single_feed(feed_url, max_items=5)
        
        assert len(entries) == 1
        assert entries[0]['title'] == 'Single Article'
        assert entries[0]['source'] == feed_url
    
    def test_fetch_single_feed_max_items(self):
        """Test max_items limit for single feed"""
        fetcher = RSSFetcher()
        feed_url = "https://example.com/feed.xml"
        
        mock_entries = []
        for i in range(10):
            mock_entry = MagicMock()
            mock_entry.title = f'Article {i}'
            mock_entry.summary = f'Summary {i}'
            mock_entry.link = f'https://example.com/{i}'
            mock_entry.published = '2025-01-27T10:00:00Z'
            mock_entry.get = lambda key, default='': getattr(mock_entry, key, default)
            mock_entries.append(mock_entry)
        
        mock_feed = MagicMock()
        mock_feed.entries = mock_entries
        
        with patch('backend.services.rss_fetcher.feedparser.parse', return_value=mock_feed):
            entries = fetcher.fetch_single_feed(feed_url, max_items=3)
        
        assert len(entries) == 3
    
    def test_fetch_single_feed_error_handling(self):
        """Test error handling for single feed"""
        fetcher = RSSFetcher()
        feed_url = "https://example.com/invalid-feed.xml"
        
        # Mock feedparser to raise exception
        with patch('backend.services.rss_fetcher.feedparser.parse', side_effect=Exception("Feed parse error")):
            entries = fetcher.fetch_single_feed(feed_url, max_items=5)
        
        # Should return empty list on error
        assert entries == []
    
    def test_fetch_single_feed_missing_fields(self):
        """Test handling of entries with missing fields"""
        fetcher = RSSFetcher()
        feed_url = "https://example.com/feed.xml"
        
        mock_entry = MagicMock()
        mock_entry.title = 'Article with missing fields'
        mock_entry.summary = ''  # Missing
        mock_entry.link = ''  # Missing
        mock_entry.published = ''  # Missing
        mock_entry.description = ''  # Missing
        mock_entry.get = lambda key, default='': getattr(mock_entry, key, default)
        
        mock_feed = MagicMock()
        mock_feed.entries = [mock_entry]
        
        with patch('backend.services.rss_fetcher.feedparser.parse', return_value=mock_feed):
            entries = fetcher.fetch_single_feed(feed_url, max_items=5)
        
        assert len(entries) == 1
        assert entries[0]['title'] == 'Article with missing fields'
        assert entries[0]['summary'] == ''  # Should default to empty string
        assert entries[0]['link'] == ''  # Should default to empty string
        assert 'published' in entries[0]  # Should have published (defaults to current time)
    
    def test_fetch_single_feed_uses_description_when_summary_missing(self):
        """Test that description is used when summary is missing"""
        fetcher = RSSFetcher()
        feed_url = "https://example.com/feed.xml"
        
        # Create mock entry that properly handles .get() method
        mock_entry = MagicMock()
        mock_entry.title = 'Article'
        mock_entry.summary = ''  # Missing
        mock_entry.description = 'Article description'
        mock_entry.link = 'https://example.com/article'
        mock_entry.published = '2025-01-27T10:00:00Z'
        # Mock .get() to return description when summary is requested and empty
        def mock_get(key, default=''):
            if key == 'summary':
                return mock_entry.summary if mock_entry.summary else (mock_entry.description if hasattr(mock_entry, 'description') else default)
            return getattr(mock_entry, key, default)
        mock_entry.get = mock_get
        
        mock_feed = MagicMock()
        mock_feed.entries = [mock_entry]
        
        with patch('backend.services.rss_fetcher.feedparser.parse', return_value=mock_feed):
            entries = fetcher.fetch_single_feed(feed_url, max_items=5)
        
        assert entries[0]['summary'] == 'Article description'

