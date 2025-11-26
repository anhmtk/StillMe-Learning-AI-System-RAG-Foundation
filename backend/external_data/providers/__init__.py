"""
External Data Providers

Each provider implements ExternalDataProvider protocol to fetch data from specific APIs.
"""

from .base import ExternalDataProvider, ExternalDataResult
from .weather import WeatherProvider
from .news import NewsProvider

__all__ = [
    "ExternalDataProvider",
    "ExternalDataResult",
    "WeatherProvider",
    "NewsProvider",
]

