"""
System Self-Awareness Monitor
Provides real-time system status for StillMe to inject into prompts
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SystemMonitor:
    """Monitors system status and provides self-awareness context"""
    
    def __init__(self):
        self._rss_fetcher = None
        self._source_integration = None
        self._last_status = None
        self._last_update = None
    
    def set_components(self, rss_fetcher=None, source_integration=None):
        """Set component references for monitoring"""
        self._rss_fetcher = rss_fetcher
        self._source_integration = source_integration
    
    def get_system_status_note(self) -> str:
        """
        Get a concise system status note to inject into prompts
        
        Returns:
            String like: "[System: 22 sources, 3 errors (RSS: 3 failed), Latency: 120ms]"
        """
        try:
            status_parts = []
            
            # Get RSS feed status
            if self._rss_fetcher:
                try:
                    rss_stats = self._rss_fetcher.get_stats()
                    total_feeds = rss_stats.get("feeds_count", 0)
                    failed_feeds = rss_stats.get("failed_feeds", 0)
                    successful_feeds = rss_stats.get("successful_feeds", 0)
                    
                    if total_feeds > 0:
                        if failed_feeds > 0:
                            status_parts.append(f"RSS: {total_feeds} feeds ({failed_feeds} failed, {successful_feeds} ok)")
                        else:
                            status_parts.append(f"RSS: {total_feeds} feeds (all ok)")
                except Exception as e:
                    logger.debug(f"Could not get RSS stats: {e}")
            
            # Get source integration status
            if self._source_integration:
                try:
                    source_stats = self._source_integration.get_source_stats()
                    enabled_sources = []
                    for name, info in source_stats.items():
                        if info.get("enabled"):
                            enabled_sources.append(name.upper())
                    
                    if enabled_sources:
                        status_parts.append(f"Sources: {len(enabled_sources)} ({', '.join(enabled_sources)})")
                except Exception as e:
                    logger.debug(f"Could not get source stats: {e}")
            
            if status_parts:
                status_note = f"[System: {', '.join(status_parts)}]"
                self._last_status = status_note
                self._last_update = datetime.now()
                return status_note
            
            return "[System: Status unavailable]"
            
        except Exception as e:
            logger.warning(f"Error generating system status note: {e}")
            return "[System: Status error]"
    
    def get_detailed_status(self) -> Dict[str, Any]:
        """
        Get detailed system status for learning sources queries
        
        Returns:
            Dictionary with detailed status information
        """
        status = {
            "rss": {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "failure_rate": 0.0,
                "errors": []
            },
            "sources": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Get RSS feed details
        if self._rss_fetcher:
            try:
                rss_stats = self._rss_fetcher.get_stats()
                logger.info(f"🔍 DEBUG: rss_fetcher.get_stats() returned: {rss_stats}")
                status["rss"]["total"] = rss_stats.get("feeds_count", 0)
                status["rss"]["successful"] = rss_stats.get("successful_feeds", 0)
                status["rss"]["failed"] = rss_stats.get("failed_feeds", 0)
                status["rss"]["failure_rate"] = rss_stats.get("failure_rate", 0.0)
                status["rss"]["last_error"] = rss_stats.get("last_error")
                logger.info(f"🔍 DEBUG: Parsed RSS status - total={status['rss']['total']}, failed={status['rss']['failed']}, successful={status['rss']['successful']}")
            except Exception as e:
                logger.warning(f"⚠️ Could not get RSS stats from rss_fetcher: {e}")
        else:
            logger.warning(f"⚠️ rss_fetcher is None in system_monitor.get_detailed_status()")
        
        # Get source integration details
        if self._source_integration:
            try:
                source_stats = self._source_integration.get_source_stats()
                for name, info in source_stats.items():
                    status["sources"][name] = {
                        "enabled": info.get("enabled", False),
                        "status": info.get("stats", {}).get("status", "unknown") if info.get("stats") else "unknown"
                    }
            except Exception as e:
                logger.debug(f"Could not get source stats: {e}")
        
        return status


# Global singleton instance
_system_monitor_instance: Optional[SystemMonitor] = None

def get_system_monitor() -> SystemMonitor:
    """Get global SystemMonitor instance"""
    global _system_monitor_instance
    if _system_monitor_instance is None:
        _system_monitor_instance = SystemMonitor()
    return _system_monitor_instance

