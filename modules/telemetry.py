"""
Telemetry system for StillMe AI
Logs performance metrics and routing information to JSONL file
"""
import json
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Thread-safe logging
_lock = threading.Lock()
_log_file = Path("reports/telemetry.jsonl")

def _ensure_log_dir():
    """Ensure reports directory exists"""
    _log_file.parent.mkdir(parents=True, exist_ok=True)

def log_event(event: Dict[str, Any]) -> None:
    """
    Log an event to telemetry.jsonl
    
    Args:
        event: Dictionary containing event data
    """
    with _lock:
        _ensure_log_dir()
        
        # Add timestamp if not present
        if "ts" not in event:
            event["ts"] = time.time()
        
        # Write to JSONL file
        with open(_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

def reset_log() -> None:
    """Reset telemetry log file"""
    with _lock:
        _ensure_log_dir()
        if _log_file.exists():
            _log_file.unlink()

def get_log_path() -> Path:
    """Get path to telemetry log file"""
    return _log_file

def read_events() -> list[Dict[str, Any]]:
    """
    Read all events from telemetry log
    
    Returns:
        List of event dictionaries
    """
    if not _log_file.exists():
        return []
    
    events = []
    with open(_log_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    return events

def get_stats() -> Dict[str, Any]:
    """
    Get basic statistics from telemetry log
    
    Returns:
        Dictionary with statistics
    """
    events = read_events()
    if not events:
        return {"total_events": 0}
    
    stats = {
        "total_events": len(events),
        "routes": {},
        "models": {},
        "fast_lane_count": 0,
        "stream_count": 0,
    }
    
    # Count routes and models
    for event in events:
        route = event.get("route", "unknown")
        model = event.get("model", "unknown")
        fast_lane = event.get("fast_lane", False)
        stream = event.get("stream", False)
        
        stats["routes"][route] = stats["routes"].get(route, 0) + 1
        stats["models"][model] = stats["models"].get(model, 0) + 1
        
        if fast_lane:
            stats["fast_lane_count"] += 1
        if stream:
            stats["stream_count"] += 1
    
    return stats
