"""
Learning Sources - 12 Nguồn Học Tập
===================================

Hệ thống 12 nguồn học tập tự động cho StillMe AI:
1. Hacker News (HN)
2. Reddit
3. GitHub
4. TechCrunch
5. The Verge
6. ArXiv
7. News
8. Stack Overflow
9. Medium
10. Academic (Nature, Science, IEEE)
11. YouTube
12. Subreddits

Author: StillMe AI Framework
Version: 2.0.0
"""

from .hackernews import HackerNewsSource
from .reddit import RedditSource
from .github import GitHubSource
from .techcrunch import TechCrunchSource
from .theverge import TheVergeSource
from .arxiv import ArXivSource
from .news import NewsSource
from .stackoverflow import StackOverflowSource
from .medium import MediumSource
from .academic import AcademicSource
from .youtube import YouTubeSource
from .subreddits import SubredditsSource

__all__ = [
    "HackerNewsSource",
    "RedditSource", 
    "GitHubSource",
    "TechCrunchSource",
    "TheVergeSource",
    "ArXivSource",
    "NewsSource",
    "StackOverflowSource",
    "MediumSource",
    "AcademicSource",
    "YouTubeSource",
    "SubredditsSource",
]

# Registry of all learning sources
LEARNING_SOURCES = {
    "hackernews": HackerNewsSource,
    "reddit": RedditSource,
    "github": GitHubSource,
    "techcrunch": TechCrunchSource,
    "theverge": TheVergeSource,
    "arxiv": ArXivSource,
    "news": NewsSource,
    "stackoverflow": StackOverflowSource,
    "medium": MediumSource,
    "academic": AcademicSource,
    "youtube": YouTubeSource,
    "subreddits": SubredditsSource,
}
