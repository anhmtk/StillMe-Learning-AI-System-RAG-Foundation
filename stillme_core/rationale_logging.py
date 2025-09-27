"""
StillMe Rationale Logging System
Standardized logging of AI decision-making processes with citations and traceability.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

log = logging.getLogger(__name__)

class RationaleSignal:
    """Represents a signal used in decision making."""
    
    def __init__(self, name: str, value: Any, weight: float = 1.0, 
                 source: Optional[str] = None, confidence: float = 1.0):
        self.name = name
        self.value = value
        self.weight = weight
        self.source = source
        self.confidence = confidence
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "value": self.value,
            "weight": self.weight,
            "source": self.source,
            "confidence": self.confidence
        }

class RationaleExplanation:
    """Represents an explanation for a decision."""
    
    def __init__(self, type: str, content: str, confidence: float = 1.0):
        self.type = type  # e.g., "reasoning", "rule", "precedent", "intuition"
        self.content = content
        self.confidence = confidence
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type,
            "content": self.content,
            "confidence": self.confidence
        }

class RationaleCitation:
    """Represents a citation or source for information."""
    
    def __init__(self, source: str, url: Optional[str] = None, 
                 date: Optional[str] = None, confidence: float = 1.0,
                 excerpt: Optional[str] = None):
        self.source = source
        self.url = url
        self.date = date
        self.confidence = confidence
        self.excerpt = excerpt
    
    def to_dict(self) -> Dict:
        return {
            "source": self.source,
            "url": self.url,
            "date": self.date,
            "confidence": self.confidence,
            "excerpt": self.excerpt
        }

class RationaleEntry:
    """Complete rationale entry for a decision."""
    
    def __init__(self, decision_id: str, policy: str, 
                 signals: List[RationaleSignal],
                 final_action: Any,
                 explanations: List[RationaleExplanation],
                 citations: List[RationaleCitation],
                 trace_id: str,
                 timestamp: Optional[str] = None,
                 context: Optional[Dict] = None,
                 metadata: Optional[Dict] = None):
        self.decision_id = decision_id
        self.policy = policy
        self.signals = signals
        self.final_action = final_action
        self.explanations = explanations
        self.citations = citations
        self.trace_id = trace_id
        self.timestamp = timestamp or datetime.now().isoformat()
        self.context = context or {}
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict:
        return {
            "decision_id": self.decision_id,
            "policy": self.policy,
            "signals": [s.to_dict() for s in self.signals],
            "final_action": self.final_action,
            "explanations": [e.to_dict() for e in self.explanations],
            "citations": [c.to_dict() for c in self.citations],
            "trace_id": self.trace_id,
            "timestamp": self.timestamp,
            "context": self.context,
            "metadata": self.metadata
        }

class RationaleLogger:
    """Logger for rationale entries."""
    
    def __init__(self, log_dir: str = "logs/rationales"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger("rationale")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Add daily rotating file handler
        self._setup_daily_handler()
        
        # Prevent propagation
        self.logger.propagate = False
    
    def _setup_daily_handler(self):
        """Setup daily rotating file handler."""
        today = datetime.now().strftime("%Y%m%d")
        log_file = self.log_dir / f"{today}.jsonl"
        
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_decision(self, entry: RationaleEntry):
        """Log a rationale entry."""
        try:
            # Convert to JSON
            log_data = entry.to_dict()
            json_line = json.dumps(log_data, ensure_ascii=False)
            
            # Log to file
            self.logger.info(json_line)
            
            # Also log to main logger for visibility
            log.info(f"Decision logged: {entry.decision_id} (policy: {entry.policy})")
            
        except Exception as e:
            log.error(f"Failed to log rationale: {e}")
    
    def get_decisions(self, date: Optional[str] = None, 
                     policy: Optional[str] = None,
                     trace_id: Optional[str] = None) -> List[Dict]:
        """Retrieve rationale entries."""
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        
        log_file = self.log_dir / f"{date}.jsonl"
        
        if not log_file.exists():
            return []
        
        entries = []
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        
                        # Filter by policy if specified
                        if policy and entry.get("policy") != policy:
                            continue
                        
                        # Filter by trace_id if specified
                        if trace_id and entry.get("trace_id") != trace_id:
                            continue
                        
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            log.error(f"Failed to read rationale log: {e}")
        
        return entries

# Global rationale logger instance
_rationale_logger = None

def get_rationale_logger() -> RationaleLogger:
    """Get global rationale logger instance."""
    global _rationale_logger
    if _rationale_logger is None:
        _rationale_logger = RationaleLogger()
    return _rationale_logger

def log_decision_rationale(
    policy: str,
    signals: List[RationaleSignal],
    final_action: Any,
    explanations: List[RationaleExplanation],
    citations: List[RationaleCitation],
    trace_id: Optional[str] = None,
    context: Optional[Dict] = None,
    metadata: Optional[Dict] = None
) -> str:
    """Log a decision with rationale and return decision ID."""
    
    # Generate decision ID
    decision_id = str(uuid.uuid4())
    
    # Use provided trace_id or generate new one
    if trace_id is None:
        trace_id = str(uuid.uuid4())
    
    # Create rationale entry
    entry = RationaleEntry(
        decision_id=decision_id,
        policy=policy,
        signals=signals,
        final_action=final_action,
        explanations=explanations,
        citations=citations,
        trace_id=trace_id,
        context=context,
        metadata=metadata
    )
    
    # Log the entry
    logger = get_rationale_logger()
    logger.log_decision(entry)
    
    return decision_id

# Decorator for automatic rationale logging
def with_rationale(policy: str, enable_in_careful_mode: bool = True):
    """Decorator to automatically log rationale for function calls."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Check if we should log rationale
            should_log = True
            if enable_in_careful_mode:
                # Check if we're in careful mode
                # This could be from environment variable or config
                careful_mode = os.getenv("STILLME_CAREFUL_MODE", "false").lower() == "true"
                should_log = careful_mode
            
            if not should_log:
                return func(*args, **kwargs)
            
            # Generate trace ID
            trace_id = str(uuid.uuid4())
            
            # Prepare signals
            signals = [
                RationaleSignal("function_name", func.__name__, 1.0, "decorator"),
                RationaleSignal("args_count", len(args), 1.0, "decorator"),
                RationaleSignal("kwargs_count", len(kwargs), 1.0, "decorator")
            ]
            
            # Add input signals if they're simple types
            for i, arg in enumerate(args[:3]):  # Limit to first 3 args
                if isinstance(arg, (str, int, float, bool)):
                    signals.append(RationaleSignal(f"arg_{i}", str(arg)[:100], 0.8, "input"))
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Create explanations
                explanations = [
                    RationaleExplanation(
                        "reasoning",
                        f"Function {func.__name__} executed successfully",
                        1.0
                    )
                ]
                
                # Create citations
                citations = [
                    RationaleCitation(
                        source="function_call",
                        confidence=1.0
                    )
                ]
                
                # Log rationale
                log_decision_rationale(
                    policy=policy,
                    signals=signals,
                    final_action=result,
                    explanations=explanations,
                    citations=citations,
                    trace_id=trace_id,
                    context={"function": func.__name__},
                    metadata={"decorated": True}
                )
                
                return result
                
            except Exception as e:
                # Log error rationale
                explanations = [
                    RationaleExplanation(
                        "reasoning",
                        f"Function {func.__name__} failed with error: {str(e)}",
                        1.0
                    )
                ]
                
                log_decision_rationale(
                    policy=policy,
                    signals=signals,
                    final_action=None,
                    explanations=explanations,
                    citations=[],
                    trace_id=trace_id,
                    context={"function": func.__name__, "error": str(e)},
                    metadata={"decorated": True, "error": True}
                )
                
                raise
        
        return wrapper
    return decorator

# Utility functions for common rationale patterns
def create_signal(name: str, value: Any, weight: float = 1.0, 
                 source: Optional[str] = None, confidence: float = 1.0) -> RationaleSignal:
    """Create a rationale signal."""
    return RationaleSignal(name, value, weight, source, confidence)

def create_explanation(type: str, content: str, confidence: float = 1.0) -> RationaleExplanation:
    """Create a rationale explanation."""
    return RationaleExplanation(type, content, confidence)

def create_citation(source: str, url: Optional[str] = None, 
                   date: Optional[str] = None, confidence: float = 1.0,
                   excerpt: Optional[str] = None) -> RationaleCitation:
    """Create a rationale citation."""
    return RationaleCitation(source, url, date, confidence, excerpt)

# Import os for environment variable check
import os
