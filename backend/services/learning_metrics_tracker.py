"""
Learning Metrics Tracker - Phase 2
Tracks learning metrics with timestamps for transparency and self-awareness

This service tracks:
- Entries fetched per learning cycle
- Entries added to RAG
- Entries filtered/rejected
- Filter reasons
- Learning cycle timestamps
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class LearningCycleMetrics:
    """Metrics for a single learning cycle"""
    cycle_number: int
    timestamp: str  # ISO format
    entries_fetched: int
    entries_added: int
    entries_filtered: int
    filter_reasons: Dict[str, int]  # reason -> count
    sources: Dict[str, int]  # source -> entries_fetched
    duration_seconds: Optional[float] = None
    error: Optional[str] = None


@dataclass
class DailyMetrics:
    """Aggregated metrics for a single day"""
    date: str  # YYYY-MM-DD
    total_cycles: int
    total_entries_fetched: int
    total_entries_added: int
    total_entries_filtered: int
    filter_reasons: Dict[str, int]
    sources: Dict[str, int]
    cycles: List[LearningCycleMetrics]


class LearningMetricsTracker:
    """
    Tracks learning metrics with timestamps for transparency
    
    Stores metrics in-memory and optionally persists to file.
    Can be upgraded to database later if needed.
    """
    
    def __init__(self, persist_to_file: bool = True, metrics_file: Optional[str] = None):
        """
        Initialize metrics tracker
        
        Args:
            persist_to_file: Whether to persist metrics to file
            metrics_file: Path to metrics file (default: data/learning_metrics.jsonl)
        """
        self.persist_to_file = persist_to_file
        self.metrics_file = metrics_file or "data/learning_metrics.jsonl"
        
        # In-memory storage: list of LearningCycleMetrics
        self._cycles: List[LearningCycleMetrics] = []
        
        # Ensure data directory exists
        if self.persist_to_file:
            Path(self.metrics_file).parent.mkdir(parents=True, exist_ok=True)
            self._load_metrics()
        
        logger.info(f"LearningMetricsTracker initialized (persist={persist_to_file}, file={self.metrics_file})")
    
    def _load_metrics(self):
        """Load metrics from file"""
        try:
            if Path(self.metrics_file).exists():
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            cycle = LearningCycleMetrics(**data)
                            self._cycles.append(cycle)
                logger.info(f"Loaded {len(self._cycles)} learning cycles from {self.metrics_file}")
        except Exception as e:
            logger.warning(f"Failed to load metrics from {self.metrics_file}: {e}")
    
    def _save_cycle(self, cycle: LearningCycleMetrics):
        """Save a single cycle to file"""
        if self.persist_to_file:
            try:
                with open(self.metrics_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(asdict(cycle), ensure_ascii=False) + '\n')
            except Exception as e:
                logger.error(f"Failed to save cycle to {self.metrics_file}: {e}")
    
    def record_learning_cycle(
        self,
        cycle_number: int,
        entries_fetched: int,
        entries_added: int,
        entries_filtered: int,
        filter_reasons: Optional[Dict[str, int]] = None,
        sources: Optional[Dict[str, int]] = None,
        duration_seconds: Optional[float] = None,
        error: Optional[str] = None
    ) -> LearningCycleMetrics:
        """
        Record a learning cycle with metrics
        
        Args:
            cycle_number: Learning cycle number
            entries_fetched: Total entries fetched
            entries_added: Entries successfully added to RAG
            entries_filtered: Entries filtered/rejected
            filter_reasons: Dict of filter reason -> count
            sources: Dict of source -> entries_fetched
            duration_seconds: Duration of learning cycle in seconds
            error: Error message if cycle failed
            
        Returns:
            LearningCycleMetrics object
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        cycle = LearningCycleMetrics(
            cycle_number=cycle_number,
            timestamp=timestamp,
            entries_fetched=entries_fetched,
            entries_added=entries_added,
            entries_filtered=entries_filtered,
            filter_reasons=filter_reasons or {},
            sources=sources or {},
            duration_seconds=duration_seconds,
            error=error
        )
        
        self._cycles.append(cycle)
        self._save_cycle(cycle)
        
        logger.info(f"Recorded learning cycle #{cycle_number}: fetched={entries_fetched}, added={entries_added}, filtered={entries_filtered}")
        
        return cycle
    
    def get_metrics_for_date(self, date: str) -> Optional[DailyMetrics]:
        """
        Get aggregated metrics for a specific date (YYYY-MM-DD)
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            DailyMetrics or None if no data for that date
        """
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        cycles_for_date = [
            cycle for cycle in self._cycles
            if datetime.fromisoformat(cycle.timestamp.replace('Z', '+00:00')).date() == date_obj
        ]
        
        if not cycles_for_date:
            return None
        
        # Aggregate metrics
        total_cycles = len(cycles_for_date)
        total_entries_fetched = sum(c.entries_fetched for c in cycles_for_date)
        total_entries_added = sum(c.entries_added for c in cycles_for_date)
        total_entries_filtered = sum(c.entries_filtered for c in cycles_for_date)
        
        # Aggregate filter reasons
        filter_reasons = {}
        for cycle in cycles_for_date:
            for reason, count in cycle.filter_reasons.items():
                filter_reasons[reason] = filter_reasons.get(reason, 0) + count
        
        # Aggregate sources
        sources = {}
        for cycle in cycles_for_date:
            for source, count in cycle.sources.items():
                sources[source] = sources.get(source, 0) + count
        
        return DailyMetrics(
            date=date,
            total_cycles=total_cycles,
            total_entries_fetched=total_entries_fetched,
            total_entries_added=total_entries_added,
            total_entries_filtered=total_entries_filtered,
            filter_reasons=filter_reasons,
            sources=sources,
            cycles=cycles_for_date
        )
    
    def get_metrics_for_today(self) -> Optional[DailyMetrics]:
        """Get metrics for today"""
        today = datetime.now(timezone.utc).date().isoformat()
        return self.get_metrics_for_date(today)
    
    def get_metrics_range(self, start_date: str, end_date: str) -> List[DailyMetrics]:
        """
        Get metrics for a date range
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            List of DailyMetrics for each day in range
        """
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        results = []
        current = start
        while current <= end:
            date_str = current.isoformat()
            metrics = self.get_metrics_for_date(date_str)
            if metrics:
                results.append(metrics)
            current += timedelta(days=1)
        
        return results
    
    def get_latest_cycle(self) -> Optional[LearningCycleMetrics]:
        """Get the latest learning cycle"""
        if not self._cycles:
            return None
        return self._cycles[-1]
    
    def get_recent_cycles(self, count: int = 10) -> List[LearningCycleMetrics]:
        """Get the most recent N cycles"""
        return self._cycles[-count:] if len(self._cycles) > count else self._cycles
    
    def get_all_cycles(self) -> List[LearningCycleMetrics]:
        """Get all learning cycles"""
        return self._cycles.copy()
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics
        
        Returns:
            Dict with summary metrics
        """
        if not self._cycles:
            return {
                "total_cycles": 0,
                "total_entries_fetched": 0,
                "total_entries_added": 0,
                "total_entries_filtered": 0,
                "filter_rate": 0.0,
                "add_rate": 0.0,
                "latest_cycle": None
            }
        
        total_cycles = len(self._cycles)
        total_entries_fetched = sum(c.entries_fetched for c in self._cycles)
        total_entries_added = sum(c.entries_added for c in self._cycles)
        total_entries_filtered = sum(c.entries_filtered for c in self._cycles)
        
        filter_rate = (total_entries_filtered / total_entries_fetched * 100) if total_entries_fetched > 0 else 0.0
        add_rate = (total_entries_added / total_entries_fetched * 100) if total_entries_fetched > 0 else 0.0
        
        return {
            "total_cycles": total_cycles,
            "total_entries_fetched": total_entries_fetched,
            "total_entries_added": total_entries_added,
            "total_entries_filtered": total_entries_filtered,
            "filter_rate": round(filter_rate, 2),
            "add_rate": round(add_rate, 2),
            "latest_cycle": asdict(self._cycles[-1]) if self._cycles else None
        }


# Global instance (singleton pattern)
_metrics_tracker: Optional[LearningMetricsTracker] = None


def get_learning_metrics_tracker() -> LearningMetricsTracker:
    """Get or create global LearningMetricsTracker instance"""
    global _metrics_tracker
    if _metrics_tracker is None:
        _metrics_tracker = LearningMetricsTracker()
    return _metrics_tracker

