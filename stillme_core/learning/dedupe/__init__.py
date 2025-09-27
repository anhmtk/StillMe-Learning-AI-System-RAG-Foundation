"""
StillMe Learning Deduplication
Content novelty detection and deduplication.
"""

from .novelty import check_content_novelty, add_content_to_index, get_deduplicator

__all__ = ['check_content_novelty', 'add_content_to_index', 'get_deduplicator']
