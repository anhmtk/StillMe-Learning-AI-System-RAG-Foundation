#!/usr/bin/env python3
"""
🎯 NicheRadar v1.5 - StillMe Intelligent Personal Companion
==========================================================

NicheRadar là module săn niche và thực thi có feedback loop, bảo mật, minh bạch, dễ kiểm chứng.

Mục tiêu: Biến StillMe thành cỗ máy phát hiện và thực thi cơ hội niche với:
- Data collection từ multiple sources
- Intelligent scoring với NicheScore formula
- Time-to-First-Dollar playbook generation
- Feedback loop learning weights
- Security & compliance đầy đủ

Author: StillMe Framework Team
Version: 1.5.0
Phase: NicheRadar Core
"""

from .collectors import (
    GitHubTrendingCollector,
    HackerNewsCollector,
    NewsDeltaCollector,
    GoogleTrendsCollector,
    RedditEngagementCollector
)

from .scoring import (
    NicheScorer,
    NicheScore
)

from .playbook import (
    PlaybookGenerator,
    ProductBrief,
    MVPSpec,
    PricingSuggestion,
    ExecutionPack
)

# from .feedback import (
#     FeedbackTracker,
#     LearningWeights,
#     update_weights_suggestion
# )

__version__ = "1.5.0"
__author__ = "StillMe Framework Team"

# Export main classes
__all__ = [
    "GitHubTrendingCollector",
    "HackerNewsCollector",
    "NewsDeltaCollector",
    "GoogleTrendsCollector",
    "RedditEngagementCollector",
    "NicheScorer",
    "NicheScore",
    "PlaybookGenerator",
    "ProductBrief",
    "MVPSpec",
    "PricingSuggestion",
    "ExecutionPack",
    # "FeedbackTracker",
    # "LearningWeights"
]
