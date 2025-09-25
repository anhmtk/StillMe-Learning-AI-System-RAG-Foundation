#!/usr/bin/env python3
"""
Clarification Core - StillMe
Phase 1: Basic Clarification Handler
Phase 2: Intelligent Clarification with Learning
Phase 3: Advanced Multi-Modal & Enterprise Features

This module provides the core functionality for detecting ambiguous prompts
and generating clarification questions to improve user interaction quality.
"""

import re
import json
import time
import logging
import yaml
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# Phase 3 imports
try:
    from .multi_modal_clarification import MultiModalClarifier, MultiModalResult
    from .proactive_suggestion import ProactiveSuggestion, SuggestionResult
    from .audit_logger import AuditLogger
    PHASE3_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Phase 3 modules not available: {e}")
    PHASE3_AVAILABLE = False

class CircuitBreaker:
    """Circuit breaker for clarification safety"""
    
    def __init__(self, max_failures: int = 5, reset_seconds: int = 60):
        self.max_failures = max_failures
        self.reset_seconds = reset_seconds
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.reset_seconds:
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.max_failures:
                self.state = "open"
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
            
            raise e
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open"""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.reset_seconds:
                self.state = "half-open"
                return False
            return True
        return False

@dataclass
class ClarificationResult:
    """Result of clarification analysis"""
    needs_clarification: bool
    confidence: float
    question: Optional[str]
    category: Optional[str]
    reasoning: str
    options: Optional[List[str]] = None
    domain: Optional[str] = None
    round_number: int = 1
    max_rounds: int = 2
    trace_id: Optional[str] = None
    # Phase 3 additions
    input_type: Optional[str] = None  # "text", "code", "image", "mixed"
    suggestions: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class ClarificationHandler:
    """
    Core clarification handler for StillMe
    
    Detects ambiguous prompts and generates clarification questions
    to improve user interaction quality and reduce token waste.
    
    Phase 2 Features:
    - Context-aware clarification
    - Learning from user feedback
    - Quick/Careful modes
    - Circuit breaker protection
    
    Phase 3 Features:
    - Multi-modal input support (text, code, image)
    - Proactive suggestions
    - Enterprise audit logging
    - Advanced observability
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.ambiguity_patterns = self._load_ambiguity_patterns()
        self.clarification_templates = self._load_clarification_templates()
        
        # Phase 2 components
        self.context_aware_clarifier = None
        self.learner = None
        self.circuit_breaker = CircuitBreaker()
        
        # Phase 3 components
        self.multi_modal_clarifier = None
        self.proactive_suggestion = None
        self.audit_logger = None
        
        # Initialize Phase 2 components if available
        self._initialize_phase2_components()
        
        # Initialize Phase 3 components if available
        self._initialize_phase3_components()
        
        # Configuration
        self.confidence_threshold = self.config.get("confidence_thresholds", {}).get("ask_clarify", 0.25)  # Keep Phase 1 threshold
        self.proceed_threshold = self.config.get("confidence_thresholds", {}).get("proceed", 0.80)
        self.max_rounds = self.config.get("max_rounds", 2)
        self.default_mode = self.config.get("default_mode", "careful")
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "clarifications_asked": 0,
            "successful_clarifications": 0,
            "failed_clarifications": 0,
            "circuit_breaker_trips": 0,
            # Phase 3 statistics
            "multi_modal_requests": 0,
            "proactive_suggestions_used": 0,
            "audit_events_logged": 0
        }
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        default_config = {
            "enabled": True,
            "default_mode": "careful",
            "max_rounds": 2,
            "confidence_thresholds": {
                "ask_clarify": 0.55,
                "proceed": 0.80
            },
            "caching": {
                "enabled": True,
                "max_entries": 1024,
                "ttl_seconds": 3600
            },
            "learning": {
                "enabled": True,
                "min_samples_to_apply": 3,
                "decay": 0.90
            },
            "telemetry": {
                "log_level": "info",
                "sample_rate": 1.0
            },
            "safety": {
                "circuit_breaker": {
                    "max_failures": 5,
                    "reset_seconds": 60
                }
            }
        }
        
        if not config_path:
            config_path = "config/clarification.yaml"
        
        try:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f)
                    # Merge with defaults
                    clarification_config = loaded_config.get("clarification", {})
                    default_config.update(clarification_config)
                    logger.info(f"Loaded clarification config from {config_path}")
            else:
                logger.warning(f"Config file {config_path} not found, using defaults")
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
        
        return default_config
    
    def _initialize_phase2_components(self):
        """Initialize Phase 2 components if available"""
        try:
            # Import Phase 2 components
            from .clarification_learning import ClarificationLearner, ClarificationPatternStore
            from .contextual_clarification import ContextAwareClarifier
            
            # Initialize pattern store and learner
            pattern_store = ClarificationPatternStore(
                decay=self.config.get("learning", {}).get("decay", 0.90)
            )
            self.learner = ClarificationLearner(pattern_store)
            
            # Initialize context-aware clarifier
            self.context_aware_clarifier = ContextAwareClarifier(
                context_analyzer=None,  # Will be injected later
                semantic_search=None,   # Will be injected later
                learner=self.learner
            )
            
            logger.info("Phase 2 components initialized successfully")
        except ImportError as e:
            logger.warning(f"Phase 2 components not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to initialize Phase 2 components: {e}")
    
    def _initialize_phase3_components(self):
        """Initialize Phase 3 components if available"""
        if not PHASE3_AVAILABLE:
            logger.info("Phase 3 modules not available, skipping initialization")
            return
        
        try:
            # Initialize multi-modal clarifier
            multi_modal_config = self.config.get("multi_modal", {})
            if multi_modal_config.get("enabled", False):
                self.multi_modal_clarifier = MultiModalClarifier(
                    multi_modal_config, 
                    self.context_aware_clarifier
                )
                logger.info("Multi-modal clarifier initialized")
            
            # Initialize proactive suggestion
            proactive_config = self.config.get("proactive", {})
            if proactive_config.get("enabled", False):
                self.proactive_suggestion = ProactiveSuggestion(proactive_config)
                logger.info("Proactive suggestion initialized")
            
            # Initialize audit logger
            audit_config = self.config.get("enterprise_audit", {})
            if audit_config.get("enabled", False):
                self.audit_logger = AuditLogger(audit_config)
                logger.info("Audit logger initialized")
            
            logger.info("Phase 3 components initialized successfully")
        except Exception as e:
            logger.warning(f"Phase 3 components initialization failed: {e}")
    
    def _load_ambiguity_patterns(self) -> Dict[str, List[str]]:
        """Load ambiguity detection patterns"""
        return {
            "vague_instruction": [
                r"\b(write|make|create|build|do|fix|help)\s+(code|app|something|it|this|that)\b",
                r"\b(improve|optimize|enhance|upgrade|better)\s+(it|this|that)\b",
                r"\b(set|configure|adjust|tune|refactor)\s+(it|this|that)\b",
                r"\b(change|modify|update|restructure|reorganize|simplify|complexify|downgrade|upgrade)\s+(it|this|that)\b",
                r"\b(help)\s+(me|you|us|them)\b"
            ],
            "missing_context": [
                r"\b(build|create|make|develop|design)\s+(an?\s+)?(app|website|program|system|tool|database|report|script|api|dashboard|form|chatbot|game|plugin|widget|component|module|service|library|framework|platform|toolchain|solution|ui|interface)\b",
                r"\b(write|create|make)\s+(documentation|code|program|script|function|class|method|query|filter|view|trigger|constraint|index|relationship|join|union|subquery|procedure|transaction|backup|restore|migration|rollback|deployment|release|build|an?\s+index)\b",
                r"\b(write|create|make)\s+(a\s+)?(program|script|function|class|method|query|filter|view|trigger|constraint|index|relationship|join|union|subquery|procedure|transaction|backup|restore|migration|rollback|deployment|release|build)\b"
            ],
            "ambiguous_reference": [
                r"\b(do|fix|change|update|delete|move|copy|paste|save|load|run|stop|start|restart|close|open|hide|show|enable|disable|activate|deactivate|turn\s+on|turn\s+off|switch)\s+(it|this|that)\b",
                r"\b(do|fix|change|update|delete|move|copy|paste|save|load|run|stop|start|restart|close|open|hide|show|enable|disable|activate|deactivate|turn\s+on|turn\s+off|switch)\s+(it|this|that)\s+(thing|stuff|something|stuff|now|immediately|quickly|right\s+away)\b"
            ],
            "single_word_vague": [
                r"^(optimize|improve|enhance|fix|help|make|do|create|build|develop|design|write|generate|analyze|review|check|test|debug|refactor|restructure|upgrade|update|modify|change|adjust|tune|configure|setup|install|deploy|run|execute|start|stop|restart|close|open|hide|show|enable|disable|activate|deactivate)$"
            ],
            "code_ambiguity": [
                r"def\s+\w+\s*\([^)]*:\s*$",  # Function definition with syntax error
                r"def\s+\w+\s*\([^)]*\):\s*$.*def\s+\w+\s*\([^)]*\):\s*$",  # Multiple function definitions
                r"def.*def",  # Multiple functions in code block (very simple)
            ],
            "unicode_chaos": [
                r"[\U0001F600-\U0001F64F]",  # Emoticons
                r"[\U0001F300-\U0001F5FF]",  # Misc Symbols and Pictographs
                r"[\U0001F680-\U0001F6FF]",  # Transport and Map
                r"[\U0001F1E0-\U0001F1FF]",  # Regional indicator symbols
                r"[\u2600-\u26FF]",    # Miscellaneous symbols
                r"[\u2700-\u27BF]",    # Dingbats
                r"[\U0001F900-\U0001F9FF]",  # Supplemental Symbols and Pictographs
                r"[\U0001FA70-\U0001FAFF]",  # Symbols and Pictographs Extended-A
                r"[\u4E00-\u9FFF]",    # CJK Unified Ideographs
                r"[\u0600-\u06FF]",    # Arabic
                r"[\u0400-\u04FF]",    # Cyrillic
                r"[\u0370-\u03FF]",    # Greek and Coptic
                r"[\u2200-\u22FF]",    # Mathematical Operators
            ],
            "nested_vague": [
                r"\b(make|do|create|build|develop|design|write|generate|analyze|review|check|test|debug|refactor|restructure|upgrade|update|modify|change|adjust|tune|configure|setup|install|deploy|run|execute|start|stop|restart|close|open|hide|show|enable|disable|activate|deactivate)\s+(it|this|that)\s+(better|faster|slower|smaller|bigger|cleaner|simpler|more\s+complex|worse|easier|harder|cheaper|more\s+expensive|more\s+secure|more\s+reliable|more\s+scalable|more\s+maintainable|more\s+testable|more\s+readable|more\s+efficient|more\s+flexible|more\s+robust|more\s+portable|more\s+compatible|more\s+accessible|more\s+user-friendly)\b",
                r"\b(but|and|maybe|perhaps|possibly|probably|likely|unlikely|definitely|certainly|absolutely|totally|completely|entirely|partially|somewhat|quite|rather|very|extremely|incredibly|amazingly|surprisingly|unexpectedly|obviously|clearly|apparently|seemingly|supposedly|allegedly|reportedly|apparently|obviously|clearly|definitely|certainly|absolutely|totally|completely|entirely|partially|somewhat|quite|rather|very|extremely|incredibly|amazingly|surprisingly|unexpectedly)\b.*\b(but|and|maybe|perhaps|possibly|probably|likely|unlikely|definitely|certainly|absolutely|totally|completely|entirely|partially|somewhat|quite|rather|very|extremely|incredibly|amazingly|surprisingly|unexpectedly|obviously|clearly|apparently|seemingly|supposedly|allegedly|reportedly|apparently|obviously|clearly|definitely|certainly|absolutely|totally|completely|entirely|partially|somewhat|quite|rather|very|extremely|incredibly|amazingly|surprisingly|unexpectedly)\b",
                r"\b(like|similar\s+to|as\s+good\s+as|better\s+than|worse\s+than|same\s+as|different\s+from|compared\s+to|in\s+comparison\s+to|unlike|instead\s+of|rather\s+than|other\s+than|except\s+for|apart\s+from|besides|in\s+addition\s+to|along\s+with|together\s+with|combined\s+with|mixed\s+with|blended\s+with|integrated\s+with|merged\s+with|fused\s+with|joined\s+with|connected\s+with|linked\s+with|associated\s+with|related\s+to|connected\s+to|linked\s+to|associated\s+to|related\s+with)\s+(the\s+)?(other|another|different|similar|same|previous|next|last|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\b",
            ],
            "ambiguous_pronouns": [
                r"\b(it|this|that|they|them|their|these|those)\s+(is|are|was|were|will\s+be|should\s+be|could\s+be|might\s+be|must\s+be|can\s+be|may\s+be|would\s+be|has\s+been|have\s+been|had\s+been|will\s+have\s+been|should\s+have\s+been|could\s+have\s+been|might\s+have\s+been|must\s+have\s+been|can\s+have\s+been|may\s+have\s+been|would\s+have\s+been)\b",
                r"\b(do|does|did|will|should|could|might|must|can|may|would|has|have|had|will\s+have|should\s+have|could\s+have|might\s+have|must\s+have|can\s+have|may\s+have|would\s+have)\s+(it|this|that|they|them|their|these|those)\b",
                r"\b(it|this|that|they|them|their|these|those)\s+(work|works|worked|working|function|functions|functioned|functioning|operate|operates|operated|operating|run|runs|ran|running|execute|executes|executed|executing|perform|performs|performed|performing|behave|behaves|behaved|behaving|act|acts|acted|acting|respond|responds|responded|responding|react|reacts|reacted|reacting|handle|handles|handled|handling|process|processes|processed|processing|manage|manages|managed|managing|control|controls|controlled|controlling|monitor|monitors|monitored|monitoring|track|tracks|tracked|tracking|measure|measures|measured|measuring|calculate|calculates|calculated|calculating|compute|computes|computed|computing|solve|solves|solved|solving|resolve|resolves|resolved|resolving|address|addresses|addressed|addressing|tackle|tackles|tackled|tackling|approach|approaches|approached|approaching|deal\s+with|deals\s+with|dealt\s+with|dealing\s+with|work\s+on|works\s+on|worked\s+on|working\s+on|focus\s+on|focuses\s+on|focused\s+on|focusing\s+on|concentrate\s+on|concentrates\s+on|concentrated\s+on|concentrating\s+on|emphasize|emphasizes|emphasized|emphasizing|highlight|highlights|highlighted|highlighting|spotlight|spotlights|spotlighted|spotlighting|feature|features|featured|featuring|showcase|showcases|showcased|showcasing|present|presents|presented|presenting)\b",
                r"\b(update|updates|updated|updating|modify|modifies|modified|modifying|change|changes|changed|changing|edit|edits|edited|editing|fix|fixes|fixed|fixing|improve|improves|improved|improving|enhance|enhances|enhanced|enhancing|optimize|optimizes|optimized|optimizing|refactor|refactors|refactored|refactoring|restructure|restructures|restructured|restructuring|upgrade|upgrades|upgraded|upgrading|adjust|adjusts|adjusted|adjusting|tune|tunes|tuned|tuning|configure|configures|configured|configuring|setup|setups|set\s+up|setting\s+up|install|installs|installed|installing|deploy|deploys|deployed|deploying|run|runs|ran|running|execute|executes|executed|executing|start|starts|started|starting|stop|stops|stopped|stopping|restart|restarts|restarted|restarting|close|closes|closed|closing|open|opens|opened|opening|hide|hides|hid|hidden|hiding|show|shows|showed|shown|showing|enable|enables|enabled|enabling|disable|disables|disabled|disabling|activate|activates|activated|activating|deactivate|deactivates|deactivated|deactivating|turn\s+on|turns\s+on|turned\s+on|turning\s+on|turn\s+off|turns\s+off|turned\s+off|turning\s+off|switch|switches|switched|switching|delete|deletes|deleted|deleting|remove|removes|removed|removing|replace|replaces|replaced|replacing|move|moves|moved|moving|copy|copies|copied|copying|paste|pastes|pasted|pasting|cut|cuts|cutting|save|saves|saved|saving|load|loads|loaded|loading|open|opens|opened|opening|close|closes|closed|closing|create|creates|created|creating|make|makes|made|making|build|builds|built|building|generate|generates|generated|generating|write|writes|wrote|written|writing|read|reads|reading|find|finds|found|finding|search|searches|searched|searching|select|selects|selected|selecting|choose|chooses|chose|chosen|choosing|pick|picks|picked|picking|grab|grabs|grabbed|grabbing|take|takes|took|taken|taking|get|gets|got|gotten|getting|put|puts|putting|place|places|placed|placing|set|sets|setting|add|adds|added|adding|subtract|subtracts|subtracted|subtracting|multiply|multiplies|multiplied|multiplying|divide|divides|divided|dividing|calculate|calculates|calculated|calculating|compute|computes|computed|computing|solve|solves|solved|solving|resolve|resolves|resolved|resolving|address|addresses|addressed|addressing|tackle|tackles|tackled|tackling|approach|approaches|approached|approaching|deal\s+with|deals\s+with|dealt\s+with|dealing\s+with|work\s+on|works\s+on|worked\s+on|working\s+on|focus\s+on|focuses\s+on|focused\s+on|focusing\s+on|concentrate\s+on|concentrates\s+on|concentrated\s+on|concentrating\s+on|emphasize|emphasizes|emphasized|emphasizing|highlight|highlights|highlighted|highlighting|spotlight|spotlights|spotlighted|spotlighting|feature|features|featured|featuring|showcase|showcases|showcased|showcasing|present|presents|presented|presenting)\s+(it|this|that|they|them|their|these|those)\b",
            ],
            "context_switching": [
                r"\b(now|then|next|after|before|later|earlier|previously|subsequently|meanwhile|simultaneously|concurrently|parallel|alternatively|instead|rather|however|nevertheless|nonetheless|moreover|furthermore|additionally|besides|also|too|as\s+well|in\s+addition|on\s+the\s+other\s+hand|on\s+the\s+contrary|in\s+contrast|by\s+contrast|conversely|oppositely|differently|similarly|likewise|correspondingly|analogously|equivalently|identically|exactly|precisely|specifically|particularly|especially|notably|remarkably|surprisingly|interestingly|curiously|strangely|oddly|unexpectedly|unfortunately|fortunately|luckily|unluckily|sadly|happily|ironically|paradoxically|contradictorily|confusingly|mysteriously|puzzlingly|bewilderingly|perplexingly|bafflingly|enigmatically|cryptically|obscurely|vaguely|ambiguously|unclearly|indistinctly|fuzzily|blurrily|hazily|dimly|faintly|weakly|softly|quietly|loudly|strongly|powerfully|forcefully|vigorously|energetically|actively|passively|aggressively|defensively|offensively|constructively|destructively|positively|negatively|optimistically|pessimistically|realistically|idealistically|pragmatically|theoretically|practically|technically|scientifically|mathematically|logically|rationally|emotionally|intuitively|instinctively|subconsciously|consciously|deliberately|intentionally|accidentally|unintentionally|purposely|aimlessly|randomly|systematically|methodically|carefully|carelessly|thoughtfully|thoughtlessly|mindfully|mindlessly|attentively|inattentively|concentratedly|distractedly|focused|unfocused|organized|disorganized|structured|unstructured|planned|unplanned|prepared|unprepared|ready|unready|set|unset|fixed|unfixed|stable|unstable|steady|unsteady|consistent|inconsistent|reliable|unreliable|dependable|undependable|trustworthy|untrustworthy|honest|dishonest|truthful|untruthful|accurate|inaccurate|precise|imprecise|exact|inexact|correct|incorrect|right|wrong|true|false|valid|invalid|legitimate|illegitimate|legal|illegal|lawful|unlawful|ethical|unethical|moral|immoral|good|bad|positive|negative|beneficial|harmful|helpful|unhelpful|useful|useless|valuable|worthless|important|unimportant|significant|insignificant|relevant|irrelevant|applicable|inapplicable|suitable|unsuitable|appropriate|inappropriate|proper|improper|correct|incorrect|right|wrong|true|false|valid|invalid|legitimate|illegitimate|legal|illegal|lawful|unlawful|ethical|unethical|moral|immoral|good|bad|positive|negative|beneficial|harmful|helpful|unhelpful|useful|useless|valuable|worthless|important|unimportant|significant|insignificant|relevant|irrelevant|applicable|inapplicable|suitable|unsuitable|appropriate|inappropriate|proper|improper)\b.*\b(but|however|nevertheless|nonetheless|moreover|furthermore|additionally|besides|also|too|as\s+well|in\s+addition|on\s+the\s+other\s+hand|on\s+the\s+contrary|in\s+contrast|by\s+contrast|conversely|oppositely|differently|similarly|likewise|correspondingly|analogously|equivalently|identically|exactly|precisely|specifically|particularly|especially|notably|remarkably|surprisingly|interestingly|curiously|strangely|oddly|unexpectedly|unfortunately|fortunately|luckily|unluckily|sadly|happily|ironically|paradoxically|contradictorily|confusingly|mysteriously|puzzlingly|bewilderingly|perplexingly|bafflingly|enigmatically|cryptically|obscurely|vaguely|ambiguously|unclearly|indistinctly|fuzzily|blurrily|hazily|dimly|faintly|weakly|softly|quietly|loudly|strongly|powerfully|forcefully|vigorously|energetically|actively|passively|aggressively|defensively|offensively|constructively|destructively|positively|negatively|optimistically|pessimistically|realistically|idealistically|pragmatically|theoretically|practically|technically|scientifically|mathematically|logically|rationally|emotionally|intuitively|instinctively|subconsciously|consciously|deliberately|intentionally|accidentally|unintentionally|purposely|aimlessly|randomly|systematically|methodically|carefully|carelessly|thoughtfully|thoughtlessly|mindfully|mindlessly|attentively|inattentively|concentratedly|distractedly|focused|unfocused|organized|disorganized|structured|unstructured|planned|unplanned|prepared|unprepared|ready|unready|set|unset|fixed|unfixed|stable|unstable|steady|unsteady|consistent|inconsistent|reliable|unreliable|dependable|undependable|trustworthy|untrustworthy|honest|dishonest|truthful|untruthful|accurate|inaccurate|precise|imprecise|exact|inexact|correct|incorrect|right|wrong|true|false|valid|invalid|legitimate|illegitimate|legal|illegal|lawful|unlawful|ethical|unethical|moral|immoral|good|bad|positive|negative|beneficial|harmful|helpful|unhelpful|useful|useless|valuable|worthless|important|unimportant|significant|insignificant|relevant|irrelevant|applicable|inapplicable|suitable|unsuitable|appropriate|inappropriate|proper|improper)\b",
            ],
            "fuzzy_goal": [
                r"\b(make|do)\s+(it|this|that)\s+(faster|slower|smaller|bigger|cleaner|simpler|more\s+complex|better|worse|easier|harder|cheaper|more\s+expensive|more\s+secure|more\s+reliable|more\s+scalable|more\s+maintainable|more\s+testable|more\s+readable|more\s+efficient|more\s+flexible|more\s+robust|more\s+portable|more\s+compatible|more\s+accessible|more\s+user-friendly)\b"
            ],
            "missing_parameter": [
                r"\b(write|create|make|build|design)\s+(a\s+)?(function|class|variable|method|schema|table|query|filter|view|trigger|constraint|index|relationship|join|union|subquery|procedure|transaction|backup|restore|migration|rollback|deployment|release|build)\b"
            ],
            "slang_informal": [
                r"\b(gimme|hook\s+me\s+up|sort\s+this\s+out|fix\s+this\s+mess|make\s+it\s+pop|jazz\s+it\s+up|spice\s+it\s+up|beef\s+it\s+up|tweak\s+it|fiddle\s+with\s+it|mess\s+around\s+with\s+it|play\s+with\s+it|toy\s+with\s+it|fool\s+around\s+with\s+it|mess\s+with\s+it|tinker\s+with\s+it|futz\s+with\s+it|screw\s+with\s+it|mess\s+it\s+up|break\s+it|fix\s+it\s+up|patch\s+it\s+up|clean\s+it\s+up|tidy\s+it\s+up|straighten\s+it\s+out)\b"
            ],
            "contextual_dependency": [
                r"\b(do\s+the\s+same\s+thing|like\s+before|as\s+usual|the\s+usual\s+way|like\s+last\s+time|same\s+as\s+before|like\s+the\s+other\s+one|similar\s+to\s+that|like\s+that\s+thing|same\s+as\s+that|like\s+the\s+previous|as\s+we\s+did|like\s+we\s+discussed|as\s+planned|according\s+to\s+plan|per\s+the\s+spec|as\s+specified|per\s+requirements|as\s+required|per\s+standard|as\s+standard|per\s+protocol|as\s+protocol|per\s+procedure|as\s+procedure)\b"
            ],
            "cross_domain": [
                r"\b(analyze|process|handle|manage|control|monitor|track|measure|calculate|compute|solve|resolve|address|tackle|approach|deal\s+with|work\s+on|focus\s+on|concentrate\s+on|emphasize|highlight|spotlight|feature|showcase|present)\s+(this|it|that)\b"
            ]
        }
    
    def _load_clarification_templates(self) -> Dict[str, List[str]]:
        """Load clarification question templates"""
        return {
            "vague_instruction": [
                "What exactly would you like me to {action}?",
                "Could you be more specific about what needs to be {action}?",
                "What should I {action} for you?",
                "I'd be happy to help! What specifically do you need me to {action}?"
            ],
            "missing_context": [
                "What type of {item} would you like me to create?",
                "Could you tell me more about the {item} you need?",
                "What should this {item} do or contain?",
                "What are the requirements for this {item}?"
            ],
            "ambiguous_reference": [
                "What does '{reference}' refer to?",
                "Could you clarify what you mean by '{reference}'?",
                "What should I {action}?",
                "I'm not sure what you're referring to. Could you be more specific?"
            ],
            "single_word_vague": [
                "What would you like me to {action}?",
                "Could you specify what you want me to {action}?",
                "What should I {action} for you?",
                "I need more details about what to {action}."
            ],
            "code_ambiguity": [
                "I see code in your input. What would you like me to do with it?",
                "Do you want me to fix the syntax errors first?",
                "Which function should I focus on?",
                "What specific changes do you need in this code?"
            ],
            "nested_vague": [
                "I see multiple requirements. Which one should I prioritize?",
                "You mentioned several aspects. What's the most important?",
                "There are many conditions here. What's the main goal?",
                "I need to understand the primary objective from all these requirements."
            ],
            "ambiguous_pronouns": [
                "What does 'it' refer to in this context?",
                "Could you clarify what you mean by 'this'?",
                "I need to know what 'that' refers to.",
                "What specific item are you talking about?"
            ],
            "context_switching": [
                "I notice you're switching topics. What should I focus on?",
                "You mentioned multiple things. Which one is the priority?",
                "There are several directions here. What's the main goal?",
                "I need to understand what you want me to focus on."
            ],
            "fuzzy_goal": [
                "What aspect should be {goal}?",
                "How would you like me to make it {goal}?",
                "What specifically needs to be {goal}?",
                "Could you clarify what should be {goal}?"
            ],
            "missing_parameter": [
                "What should this {item} do?",
                "What functionality do you need for this {item}?",
                "What are the requirements for this {item}?",
                "Could you specify what this {item} should accomplish?"
            ],
            "slang_informal": [
                "I'd be happy to help! Could you clarify what you need?",
                "What would you like me to do for you?",
                "Could you be more specific about what you need help with?",
                "I'm here to help! What can I do for you?"
            ],
            "contextual_dependency": [
                "I don't have the previous context. Could you provide more details?",
                "What was done before that I should reference?",
                "Could you clarify what you're referring to?",
                "What should I base this on?"
            ],
            "cross_domain": [
                "What type of {action} do you need?",
                "Could you specify what kind of {action} you're looking for?",
                "What should I {action} for you?",
                "What are you trying to {action}?"
            ]
        }
    
    def detect_ambiguity(self, prompt: str, context: Optional[Dict[str, Any]] = None, 
                        mode: Optional[str] = None, round_number: int = 1, trace_id: Optional[str] = None) -> ClarificationResult:
        """
        Detect if a prompt is ambiguous and needs clarification
        
        Args:
            prompt: User input prompt
            context: Conversation context (optional)
            mode: Clarification mode ("quick" or "careful")
            round_number: Current clarification round (1-based)
            trace_id: Trace ID for observability
            
        Returns:
            ClarificationResult with detection results
        """
        # Update statistics
        self.stats["total_requests"] += 1
        
        # Check circuit breaker
        if self.circuit_breaker.is_open():
            self.stats["circuit_breaker_trips"] += 1
            logger.warning("Circuit breaker is open, skipping clarification")
            return ClarificationResult(
                needs_clarification=False,
                confidence=0.0,
                question=None,
                category="circuit_breaker_open",
                reasoning="Circuit breaker is open due to repeated failures",
                round_number=round_number,
                max_rounds=self.max_rounds,
                trace_id=trace_id
            )
        
        # Use provided mode or default
        if mode is None:
            mode = self.default_mode
        
        # Check if we've exceeded max rounds
        if round_number > self.max_rounds:
            logger.warning(f"Exceeded max rounds ({self.max_rounds}), proceeding with best effort")
            return ClarificationResult(
                needs_clarification=False,
                confidence=0.0,
                question=None,
                category="max_rounds_exceeded",
                reasoning=f"Exceeded maximum clarification rounds ({self.max_rounds})",
                round_number=round_number,
                max_rounds=self.max_rounds,
                trace_id=trace_id
            )
        
        # Phase 3: Log audit event for clarification request
        if self.audit_logger and trace_id:
            user_id = context.get("user_id", "unknown") if context else "unknown"
            session_id = context.get("session_id") if context else None
            input_type = "text"  # Default, will be updated by multi-modal analysis
            
            audit_trace_id = self.audit_logger.log_clarification_request(
                user_id=user_id,
                session_id=session_id,
                input_text=prompt,
                input_type=input_type,
                domain=context.get("domain_hint") if context else None,
                mode=mode or "careful",
                context=context or {}
            )
            
            if audit_trace_id and audit_trace_id != "audit_disabled":
                trace_id = audit_trace_id
        
        if not prompt or not prompt.strip():
            return ClarificationResult(
                needs_clarification=True,
                confidence=1.0,
                question="Could you please provide your request?",
                category="empty_prompt",
                reasoning="Empty or whitespace-only prompt",
                round_number=round_number,
                max_rounds=self.max_rounds,
                trace_id=trace_id
            )
        
        # Phase 1: Basic ambiguity detection
        basic_result = self._detect_basic_ambiguity(prompt)
        
        # Phase 2: Context-aware clarification if available
        if self.context_aware_clarifier and context:
            try:
                enhanced_result = self._detect_context_aware_ambiguity(
                    prompt, context, basic_result, mode or "careful", round_number, trace_id
                )
                return enhanced_result
            except Exception as e:
                logger.warning(f"Context-aware clarification failed: {e}")
                # Fall back to basic result
        
        # Use basic result with Phase 2 enhancements
        return ClarificationResult(
            needs_clarification=basic_result.needs_clarification,
            confidence=basic_result.confidence,
            question=basic_result.question,
            category=basic_result.category,
            reasoning=basic_result.reasoning,
            round_number=round_number,
            max_rounds=self.max_rounds,
            trace_id=trace_id
        )
    
    def _detect_basic_ambiguity(self, prompt: str) -> ClarificationResult:
        """Phase 1 basic ambiguity detection"""
        prompt_lower = prompt.lower().strip()
        max_confidence = 0.0
        best_category = None
        best_reasoning = ""
        
        # Check each category of ambiguity
        for category, patterns in self.ambiguity_patterns.items():
            for pattern in patterns:
                if re.search(pattern, prompt_lower, re.IGNORECASE | re.MULTILINE):
                    confidence = self._calculate_confidence(prompt, pattern, category)
                    logger.debug(f"Pattern '{pattern}' matched for category '{category}' with confidence {confidence}")
                    if confidence > max_confidence:
                        max_confidence = confidence
                        best_category = category
                        best_reasoning = f"Matched pattern '{pattern}' for category '{category}'"
                else:
                    logger.debug(f"Pattern '{pattern}' did not match for category '{category}'")
        
        
        logger.debug(f"Final result: max_confidence={max_confidence}, best_category={best_category}, needs_clarification={max_confidence >= self.confidence_threshold}")
        logger.debug(f"Prompt: {repr(prompt)}")
        logger.debug(f"Prompt lower: {repr(prompt_lower)}")
        
        # Determine if clarification is needed
        needs_clarification = max_confidence >= self.confidence_threshold
        
        if needs_clarification:
            question = self._generate_clarification_question(prompt, best_category or "unknown", {})
        else:
            question = None
        
        return ClarificationResult(
            needs_clarification=needs_clarification,
            confidence=max_confidence,
            question=question,
            category=best_category,
            reasoning=best_reasoning
        )
    
    def _detect_context_aware_ambiguity(self, prompt: str, context: Dict[str, Any], 
                                      basic_result: ClarificationResult, mode: str, 
                                      round_number: int, trace_id: Optional[str]) -> ClarificationResult:
        """Phase 2 context-aware ambiguity detection"""
        # Extract context information
        conversation_history = context.get("conversation_history", [])
        project_context = context.get("project_context", {})
        
        # Get context-aware clarification question
        if self.context_aware_clarifier:
            clarification_question = self.context_aware_clarifier.make_question(
                prompt, conversation_history, project_context
            )
        else:
            clarification_question = {"question": "Could you provide more details?", "options": [], "confidence": 0.5}
        
        # Adjust confidence based on mode
        if mode == "quick":
            # Only ask if very confident
            needs_clarification = basic_result.confidence >= self.proceed_threshold
        else:  # careful mode
            # Ask if not completely confident
            needs_clarification = basic_result.confidence < self.proceed_threshold
        
        # Update statistics
        if needs_clarification:
            self.stats["clarifications_asked"] += 1
        
        # Handle both dict and object types
        if isinstance(clarification_question, dict):
            confidence = clarification_question.get("confidence", 0.5)
            question = clarification_question.get("question", "Could you provide more details?")
            options = clarification_question.get("options", [])
            reasoning = clarification_question.get("reasoning", "Context-aware analysis")
            domain = clarification_question.get("domain")
        else:
            confidence = getattr(clarification_question, "confidence", 0.5)
            question = getattr(clarification_question, "question", "Could you provide more details?")
            options = getattr(clarification_question, "options", [])
            reasoning = getattr(clarification_question, "reasoning", "Context-aware analysis")
            domain = getattr(clarification_question, "domain", None)
        
        return ClarificationResult(
            needs_clarification=needs_clarification,
            confidence=basic_result.confidence,  # Use basic result confidence, not context-aware confidence
            question=question,
            options=options,
            category=basic_result.category,
            reasoning=f"{basic_result.reasoning} | {reasoning}",
            domain=domain,
            round_number=round_number,
            max_rounds=self.max_rounds,
            trace_id=trace_id
        )
    
    def _calculate_confidence(self, prompt: str, pattern: str, category: str) -> float:
        """Calculate confidence score for ambiguity detection"""
        base_confidence = 0.5
        
        # Adjust based on prompt length (shorter = more ambiguous, but don't penalize too much)
        # Special handling for nested vague - don't penalize long text
        if category == "nested_vague":
            length_factor = 1.0  # No penalty for nested vague
        else:
            length_factor = max(0.3, 1.0 - (len(prompt) / 200))  # Reduced penalty for long text
        
        # Adjust based on category
        category_weights = {
                    "vague_instruction": 2.0,  # Increased from 0.9 to 2.0 for better detection
                    "missing_context": 0.8,
                    "ambiguous_reference": 1.5,  # Increased from 0.95 to 1.5 for better detection
                    "single_word_vague": 1.3,    # High weight for single-word vague instructions
                    "code_ambiguity": 2.1,        # High weight for code ambiguity detection
                    "unicode_chaos": 1.8,         # High weight for unicode/emoji chaos
                    "nested_vague": 2.5,          # Very high weight for nested vague phrases
                    "ambiguous_pronouns": 1.8,    # High weight for ambiguous pronouns
                    "context_switching": 1.9,     # High weight for context switching
                    "fuzzy_goal": 0.85,
                    "missing_parameter": 0.8,
                    "slang_informal": 0.7,
                    "contextual_dependency": 0.9,
                    "cross_domain": 0.75
                }
        
        category_weight = category_weights.get(category, 0.5)
        
        return min(1.0, base_confidence * length_factor * category_weight)
    
    def _generate_clarification_question(self, prompt: str, category: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate appropriate clarification question"""
        if not category or category not in self.clarification_templates:
            return "Could you please clarify what you need help with?"
        
        templates = self.clarification_templates[category]
        
        # Select appropriate template based on category
        if category == "vague_instruction":
            # Extract action from prompt
            action_match = re.search(r"\b(write|make|create|build|do|fix|help|improve|optimize|enhance|upgrade|set|configure|adjust|tune|refactor|change|modify|update|restructure)\b", prompt.lower())
            action = action_match.group(1) if action_match else "do"
            template = templates[0].format(action=action)
        
        elif category == "missing_context":
            # Extract item from prompt
            item_match = re.search(r"\b(app|website|program|system|tool|database|report|script|api|dashboard|form|chatbot|game|plugin|widget|component|module|service|library|framework|platform|toolchain|function|class|method|query|filter|view|trigger|constraint|index|relationship|join|union|subquery|procedure|transaction|backup|restore|migration|rollback|deployment|release|build)\b", prompt.lower())
            item = item_match.group(1) if item_match else "item"
            template = templates[0].format(item=item)
        
        elif category == "ambiguous_reference":
            # Extract reference from prompt
            reference_match = re.search(r"\b(it|this|that)\b", prompt.lower())
            reference = reference_match.group(1) if reference_match else "this"
            action_match = re.search(r"\b(do|fix|change|update|delete|move|copy|paste|save|load|run|stop|start|restart|close|open|hide|show|enable|disable|activate|deactivate|turn\s+on|turn\s+off|switch)\b", prompt.lower())
            action = action_match.group(1) if action_match else "do"
            template = templates[0].format(reference=reference, action=action)
        
        elif category == "single_word_vague":
            # Extract action from prompt (single word)
            action = prompt.lower().strip()
            template = templates[0].format(action=action)
        
        elif category == "code_ambiguity":
            # Use first template for code ambiguity
            template = templates[0]
        
        elif category == "nested_vague":
            # Use first template for nested vague
            template = templates[0]
        
        elif category == "ambiguous_pronouns":
            # Use first template for ambiguous pronouns
            template = templates[0]
        
        elif category == "context_switching":
            # Use first template for context switching
            template = templates[0]
        
        elif category == "fuzzy_goal":
            # Extract goal from prompt
            goal_match = re.search(r"\b(faster|slower|smaller|bigger|cleaner|simpler|more\s+complex|better|worse|easier|harder|cheaper|more\s+expensive|more\s+secure|more\s+reliable|more\s+scalable|more\s+maintainable|more\s+testable|more\s+readable|more\s+efficient|more\s+flexible|more\s+robust|more\s+portable|more\s+compatible|more\s+accessible|more\s+user-friendly)\b", prompt.lower())
            goal = goal_match.group(1) if goal_match else "better"
            template = templates[0].format(goal=goal)
        
        elif category == "missing_parameter":
            # Extract item from prompt
            item_match = re.search(r"\b(function|class|variable|method|schema|table|query|filter|view|trigger|constraint|index|relationship|join|union|subquery|procedure|transaction|backup|restore|migration|rollback|deployment|release|build)\b", prompt.lower())
            item = item_match.group(1) if item_match else "item"
            template = templates[0].format(item=item)
        
        elif category == "cross_domain":
            # Extract action from prompt
            action_match = re.search(r"\b(analyze|process|handle|manage|control|monitor|track|measure|calculate|compute|solve|resolve|address|tackle|approach|deal\s+with|work\s+on|focus\s+on|concentrate\s+on|emphasize|highlight|spotlight|feature|showcase|present)\b", prompt.lower())
            action = action_match.group(1) if action_match else "help with"
            template = templates[0].format(action=action)
        
        else:
            template = templates[0]
        
        return template or "Could you please clarify what you need help with?"
    
    def generate_clarification(self, prompt: str, context: Optional[Dict[str, Any]] = None, 
                             mode: Optional[str] = None, round_number: int = 1, trace_id: Optional[str] = None) -> Optional[str]:
        """
        Generate clarification question for ambiguous prompt
        
        Args:
            prompt: User input prompt
            context: Conversation context (optional)
            mode: Clarification mode ("quick" or "careful")
            round_number: Current clarification round (1-based)
            trace_id: Trace ID for observability
            
        Returns:
            Clarification question or None if not needed
        """
        result = self.detect_ambiguity(prompt, context, mode, round_number, trace_id)
        return result.question if result.needs_clarification else None
    
    async def record_clarification_feedback(self, prompt: str, question: str, user_reply: Optional[str], 
                                          success: bool, context: Optional[Dict[str, Any]] = None, 
                                          trace_id: Optional[str] = None):
        """
        Record feedback from clarification attempt
        
        Args:
            prompt: Original user prompt
            question: Clarification question asked
            user_reply: User's response (None if skipped)
            success: Whether the clarification led to successful outcome
            context: Additional context
            trace_id: Trace ID for observability
        """
        if not self.learner:
            logger.warning("Learner not available, cannot record feedback")
            return
        
        try:
            await self.learner.record_attempt(
                prompt=prompt,
                question=question,
                user_reply=user_reply,
                success=success,
                context=context or {},
                trace_id=trace_id
            )
            
            # Update statistics
            if success:
                self.stats["successful_clarifications"] += 1
            else:
                self.stats["failed_clarifications"] += 1
                
            logger.info(f"Recorded clarification feedback: success={success}, trace_id={trace_id}")
        except Exception as e:
            logger.error(f"Failed to record clarification feedback: {e}")
    
    def get_clarification_stats(self) -> Dict[str, Any]:
        """Get clarification handler statistics"""
        base_stats = {
            "patterns_loaded": sum(len(patterns) for patterns in self.ambiguity_patterns.values()),
            "categories": list(self.ambiguity_patterns.keys()),
            "templates_loaded": sum(len(templates) for templates in self.clarification_templates.values()),
            "confidence_threshold": self.confidence_threshold,
            "proceed_threshold": self.proceed_threshold,
            "max_rounds": self.max_rounds,
            "default_mode": self.default_mode,
            "phase2_enabled": self.context_aware_clarifier is not None and self.learner is not None
        }
        
        # Add Phase 2 statistics
        base_stats.update(self.stats)
        
        # Add learning statistics if available
        if self.learner:
            try:
                learning_stats = self.learner.get_learning_stats()
                base_stats["learning"] = learning_stats
            except Exception as e:
                logger.warning(f"Failed to get learning stats: {e}")
        
        # Add circuit breaker status
        base_stats["circuit_breaker"] = {
            "is_open": self.circuit_breaker.is_open(),
            "failure_count": self.circuit_breaker.failure_count,
            "state": self.circuit_breaker.state
        }
        
        return base_stats
    
    def set_mode(self, mode: str):
        """Set clarification mode"""
        if mode in ["quick", "careful"]:
            self.default_mode = mode
            logger.info(f"Clarification mode set to: {mode}")
        else:
            logger.warning(f"Invalid mode: {mode}, must be 'quick' or 'careful'")
    
    def reset_circuit_breaker(self):
        """Reset circuit breaker"""
        self.circuit_breaker.failure_count = 0
        self.circuit_breaker.state = "closed"
        self.circuit_breaker.last_failure_time = 0
        logger.info("Circuit breaker reset")
    
    def clear_learning_data(self):
        """Clear all learning data (for testing)"""
        if self.learner:
            self.learner.clear_learning_data()
            logger.info("Learning data cleared")

# Example usage and testing
if __name__ == "__main__":
    handler = ClarificationHandler()
    
    # Test cases
    test_prompts = [
        "Write code for this",
        "Build an app", 
        "Do it now",
        "Make it better",
        "Create a function",
        "gimme some code",
        "do the same thing",
        "analyze this"
    ]
    
    print("Clarification Handler Test Results:")
    print("=" * 50)
    
    for prompt in test_prompts:
        result = handler.detect_ambiguity(prompt)
        print(f"Prompt: '{prompt}'")
        print(f"Needs clarification: {result.needs_clarification}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Category: {result.category}")
        print(f"Question: {result.question}")
        print("-" * 30)
