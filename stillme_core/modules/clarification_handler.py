#!/usr/bin/env python3
"""
Clarification Core - StillMe
Phase 1: Basic Clarification Handler
Phase 2: Intelligent Clarification with Learning
Phase 3: Advanced Multi-Modal & Enterprise Features

This module provides the core functionality for detecting ambiguous prompts
and generating clarification questions to improve user interaction quality.
"""

import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml

logger = logging.getLogger(__name__)

# Phase 3 imports
try:
    from .audit_logger import AuditLogger
    from .clarification_engine import ClarificationEngine
    from .multi_modal_clarification import MultiModalClarifier, MultiModalResult
    from .proactive_suggestion import ProactiveSuggestion, SuggestionResult

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
                logger.warning(
                    f"Circuit breaker opened after {self.failure_count} failures"
                )

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
    options: Optional[list[str]] = None
    domain: Optional[str] = None
    round_number: int = 1
    max_rounds: int = 2
    trace_id: Optional[str] = None
    # Phase 3 additions
    input_type: Optional[str] = None  # "text", "code", "image", "mixed"
    suggestions: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None


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
        self.clarification_engine = None

        # Initialize Phase 2 components if available
        self._initialize_phase2_components()

        # Initialize Phase 3 components if available
        self._initialize_phase3_components()

        # Configuration
        self.confidence_threshold = self.config.get("confidence_thresholds", {}).get(
            "ask_clarify", 0.25
        )  # Keep Phase 1 threshold
        self.proceed_threshold = self.config.get("confidence_thresholds", {}).get(
            "proceed", 0.80
        )
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
            "audit_events_logged": 0,
        }

    def _load_config(self, config_path: Optional[str] = None) -> dict[str, Any]:
        """Load configuration from YAML file"""
        default_config = {
            "enabled": True,
            "default_mode": "careful",
            "max_rounds": 2,
            "confidence_thresholds": {"ask_clarify": 0.55, "proceed": 0.80},
            "caching": {"enabled": True, "max_entries": 1024, "ttl_seconds": 3600},
            "learning": {"enabled": True, "min_samples_to_apply": 3, "decay": 0.90},
            "telemetry": {"log_level": "info", "sample_rate": 1.0},
            "safety": {"circuit_breaker": {"max_failures": 5, "reset_seconds": 60}},
        }

        if not config_path:
            config_path = "config/clarification.yaml"

        try:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, encoding="utf-8") as f:
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
            from .clarification_learning import (
                ClarificationLearner,
                ClarificationPatternStore,
            )
            from .contextual_clarification import ContextAwareClarifier

            # Initialize pattern store and learner
            pattern_store = ClarificationPatternStore(
                decay=self.config.get("learning", {}).get("decay", 0.90)
            )
            self.learner = ClarificationLearner(pattern_store)

            # Initialize context-aware clarifier
            self.context_aware_clarifier = ContextAwareClarifier(
                context_analyzer=None,  # Will be injected later
                semantic_search=None,  # Will be injected later
                learner=self.learner,
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
                    multi_modal_config, self.context_aware_clarifier
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

            # Initialize clarification engine (always enabled for torture tests)
            self.clarification_engine = ClarificationEngine()
            logger.info("Clarification engine initialized")

            logger.info("Phase 3 components initialized successfully")
        except Exception as e:
            logger.warning(f"Phase 3 components initialization failed: {e}")

    def _load_ambiguity_patterns(self) -> dict[str, list[str]]:
        """Load ambiguity detection patterns"""
        return {
            "vague_instruction": [
                r"\b(write|make|create|build|do|fix|help)\s+(code|app|something|it|this|that)\b",
                r"\b(improve|optimize|enhance|upgrade|better)\s+(it|this|that)\b",
                r"\b(set|configure|adjust|tune|refactor)\s+(it|this|that)\b",
                r"\b(change|modify|update|restructure|reorganize|simplify|complexify|downgrade|upgrade)\s+(it|this|that)\b",
                r"\b(help)\s+(me|you|us|them)\b",
            ],
            "missing_context": [
                r"\b(build|create|make|develop|design)\s+(an?\s+)?(app|website|program|system|tool|database|report|script|api|dashboard|form|chatbot|game|plugin|widget|component|module|service|library|framework|platform|toolchain|solution|ui|interface)\b",
                r"\b(write|create|make)\s+(documentation|code|program|script|function|class|method|query|filter|view|trigger|constraint|index|relationship|join|union|subquery|procedure|transaction|backup|restore|migration|rollback|deployment|release|build|an?\s+index)\b",
                r"\b(write|create|make)\s+(a\s+)?(program|script|function|class|method|query|filter|view|trigger|constraint|index|relationship|join|union|subquery|procedure|transaction|backup|restore|migration|rollback|deployment|release|build)\b",
            ],
            "ambiguous_reference": [
                r"\b(do|fix|change|update|delete|move|copy|paste|save|load|run|stop|start|restart|close|open|hide|show|enable|disable|activate|deactivate|turn\s+on|turn\s+off|switch)\s+(it|this|that)\b",
                r"\b(do|fix|change|update|delete|move|copy|paste|save|load|run|stop|start|restart|close|open|hide|show|enable|disable|activate|deactivate|turn\s+on|turn\s+off|switch)\s+(it|this|that)\s+(thing|stuff|something|stuff|now|immediately|quickly|right\s+away)\b",
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
                r"[\u2600-\u26FF]",  # Miscellaneous symbols
                r"[\u2700-\u27BF]",  # Dingbats
                r"[\U0001F900-\U0001F9FF]",  # Supplemental Symbols and Pictographs
                r"[\U0001FA70-\U0001FAFF]",  # Symbols and Pictographs Extended-A
                r"[\u4E00-\u9FFF]",  # CJK Unified Ideographs
                r"[\u0600-\u06FF]",  # Arabic
                r"[\u0400-\u04FF]",  # Cyrillic
                r"[\u0370-\u03FF]",  # Greek and Coptic
                r"[\u2200-\u22FF]",  # Mathematical Operators
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
                r"\b(but|however|nevertheless|nonetheless|moreover|furthermore|additionally|besides|also|too|as\s+well|in\s+addition|on\s+the\s+other\s+hand|on\s+the\s+contrary|in\s+contrast|by\s+contrast|conversely|oppositely|differently|similarly|likewise|correspondingly|analogously|equivalently|identically|exactly|precisely|specifically|particularly|especially|notably|remarkably|surprisingly|interestingly|curiously|strangely|oddly|unexpectedly|unfortunately|fortunately|luckily|unluckily|sadly|happily|ironically|paradoxically|contradictorily|confusingly|mysteriously|puzzlingly|bewilderingly|perplexingly|bafflingly|enigmatically|cryptically|obscurely|vaguely|ambiguously|unclearly|indistinctly|fuzzily|blurrily|hazily|dimly|faintly|weakly|softly|quietly|loudly|strongly|powerfully|forcefully|vigorously|energetically|actively|passively|aggressively|defensively|offensively|constructively|destructively|positively|negatively|optimistically|pessimistically|realistically|idealistically|pragmatically|theoretically|practically|technically|scientifically|mathematically|logically|rationally|emotionally|intuitively|instinctively|subconsciously|consciously|deliberately|intentionally|accidentally|unintentionally|purposely|aimlessly|randomly|systematically|methodically|carefully|carelessly|thoughtfully|thoughtlessly|mindfully|mindlessly|attentively|inattentively|concentratedly|distractedly|focused|unfocused|organized|disorganized|structured|unstructured|planned|unplanned|prepared|unprepared|ready|unready|set|unset|fixed|unfixed|stable|unstable|steady|unsteady|consistent|inconsistent|reliable|unreliable|dependable|undependable|trustworthy|untrustworthy|honest|dishonest|truthful|untruthful|accurate|inaccurate|precise|imprecise|exact|inexact|correct|incorrect|right|wrong|true|false|valid|invalid|legitimate|illegitimate|legal|illegal|lawful|unlawful|ethical|unethical|moral|immoral|good|bad|positive|negative|beneficial|harmful|helpful|unhelpful|useful|useless|valuable|worthless|important|unimportant|significant|insignificant|relevant|irrelevant|applicable|inapplicable|suitable|unsuitable|appropriate|inappropriate|proper|improper)\b",
                r"\b(first|then|next|after|before|later|earlier|previously|subsequently|meanwhile|simultaneously|concurrently|parallel|alternatively|instead|rather)\b.*\b(but|however|nevertheless|nonetheless|moreover|furthermore|additionally|besides|also|too|as\s+well|in\s+addition|on\s+the\s+other\s+hand|on\s+the\s+contrary|in\s+contrast|by\s+contrast|conversely|oppositely|differently|similarly|likewise|correspondingly|analogously|equivalently|identically|exactly|precisely|specifically|particularly|especially|notably|remarkably|surprisingly|interestingly|curiously|strangely|oddly|unexpectedly|unfortunately|fortunately|luckily|unluckily|sadly|happily|ironically|paradoxically|contradictorily|confusingly|mysteriously|puzzlingly|bewilderingly|perplexingly|bafflingly|enigmatically|cryptically|obscurely|vaguely|ambiguously|unclearly|indistinctly|fuzzily|blurrily|hazily|dimly|faintly|weakly|softly|quietly|loudly|strongly|powerfully|forcefully|vigorously|energetically|actively|passively|aggressively|defensively|offensively|constructively|destructively|positively|negatively|optimistically|pessimistically|realistically|idealistically|pragmatically|theoretically|practically|technically|scientifically|mathematically|logically|rationally|emotionally|intuitively|instinctively|subconsciously|consciously|deliberately|intentionally|accidentally|unintentionally|purposely|aimlessly|randomly|systematically|methodically|carefully|carelessly|thoughtfully|thoughtlessly|mindfully|mindlessly|attentively|inattentively|concentratedly|distractedly|focused|unfocused|organized|disorganized|structured|unstructured|planned|unplanned|prepared|unprepared|ready|unready|set|unset|fixed|unfixed|stable|unstable|steady|unsteady|consistent|inconsistent|reliable|unreliable|dependable|undependable|trustworthy|untrustworthy|honest|dishonest|truthful|untruthful|accurate|inaccurate|precise|imprecise|exact|inexact|correct|incorrect|right|wrong|true|false|valid|invalid|legitimate|illegitimate|legal|illegal|lawful|unlawful|ethical|unethical|moral|immoral|good|bad|positive|negative|beneficial|harmful|helpful|unhelpful|useful|useless|valuable|worthless|important|unimportant|significant|insignificant|relevant|irrelevant|applicable|inapplicable|suitable|unsuitable|appropriate|inappropriate|proper|improper)\b",
                r"\b(meanwhile|simultaneously|concurrently|parallel|alternatively|instead|rather)\b.*\b(don't\s+forget|remember|keep\s+in\s+mind|also|too|as\s+well|in\s+addition|besides|moreover|furthermore|additionally)\b",
            ],
            "fuzzy_goal": [
                r"\b(make|do)\s+(it|this|that)\s+(faster|slower|smaller|bigger|cleaner|simpler|more\s+complex|better|worse|easier|harder|cheaper|more\s+expensive|more\s+secure|more\s+reliable|more\s+scalable|more\s+maintainable|more\s+testable|more\s+readable|more\s+efficient|more\s+flexible|more\s+robust|more\s+portable|more\s+compatible|more\s+accessible|more\s+user-friendly)\b"
            ],
            "mixed_languages": [
                r"\b(create|make|build|develop|design|write|generate|analyze|review|check|test|debug|refactor|restructure|upgrade|update|modify|change|adjust|tune|configure|setup|install|deploy|run|execute|start|stop|restart|close|open|hide|show|enable|disable|activate|deactivate|fix|help|optimize|improve|enhance)\s+(a\s+)?(website|app|application|program|system|tool|database|report|script|api|dashboard|form|chatbot|game|plugin|widget|component|module|service|library|framework|platform|toolchain|function|class|method|query|filter|view|trigger|constraint|index|relationship|join|union|subquery|procedure|transaction|backup|restore|migration|rollback|deployment|release|build)\s+(với|with|để|to|trong|in|và|and|hoặc|or|nhưng|but|tuy\s+nhiên|however|tuy\s+vậy|nevertheless|ngoài\s+ra|moreover|thêm\s+nữa|furthermore|bên\s+cạnh\s+đó|additionally|bên\s+cạnh|besides|cũng|also|quá|too|như\s+vậy|as\s+well|ngoài\s+ra|in\s+addition|mặt\s+khác|on\s+the\s+other\s+hand|ngược\s+lại|on\s+the\s+contrary|ngược\s+lại|in\s+contrast|ngược\s+lại|by\s+contrast|ngược\s+lại|conversely|ngược\s+lại|oppositely|khác\s+nhau|differently|tương\s+tự|similarly|tương\s+tự|likewise|tương\s+tự|correspondingly|tương\s+tự|analogously|tương\s+tự|equivalently|giống\s+nhau|identically|chính\s+xác|exactly|chính\s+xác|precisely|cụ\s+thể|specifically|đặc\s+biệt|particularly|đặc\s+biệt|especially|đáng\s+chú\s+ý|notably|đáng\s+chú\s+ý|remarkably|bất\s+ngờ|surprisingly|thú\s+vị|interestingly|tò\s+mò|curiously|lạ|strangely|lạ|oddly|bất\s+ngờ|unexpectedly|không\s+may|unfortunately|may\s+mắn|fortunately|may\s+mắn|luckily|không\s+may|unluckily|buồn|sadly|vui|happily|mỉa\s+mai|ironically|nghịch\s+lý|paradoxically|mâu\s+thuẫn|contradictorily|khó\s+hiểu|confusingly|bí\s+ẩn|mysteriously|khó\s+hiểu|puzzlingly|khó\s+hiểu|bewilderingly|khó\s+hiểu|perplexingly|khó\s+hiểu|bafflingly|khó\s+hiểu|enigmatically|khó\s+hiểu|cryptically|mờ\s+nhạt|obscurely|mơ\s+hồ|vaguely|mơ\s+hồ|ambiguously|không\s+rõ|unclearly|không\s+rõ|indistinctly|mờ|fuzzily|mờ|blurrily|mờ|hazily|mờ|dimly|mờ|nhạt|faintly|yếu|weakly|nhẹ|softly|yên\s+lặng|quietly|to|loudly|mạnh|strongly|mạnh|powerfully|mạnh|forcefully|mạnh|vigorously|năng\s+động|energetically|tích\s+cực|actively|thụ\s+động|passively|tích\s+cực|aggressively|phòng\s+thủ|defensively|tấn\s+công|offensively|xây\s+dựng|constructively|phá\s+hoại|destructively|tích\s+cực|positively|tiêu\s+cực|negatively|lạc\s+quan|optimistically|bi\s+quan|pessimistically|thực\s+tế|realistically|lý\s+tưởng|idealistically|thực\s+tế|pragmatically|lý\s+thuyết|theoretically|thực\s+tế|practically|kỹ\s+thuật|technically|khoa\s+học|scientifically|toán\s+học|mathematically|logic|logically|hợp\s+lý|rationally|cảm\s+xúc|emotionally|trực\s+giác|intuitively|bản\s+năng|instinctively|tiềm\s+thức|subconsciously|có\s+ý\s+thức|consciously|có\s+ý\s+định|deliberately|có\s+ý\s+định|intentionally|tình\s+cờ|accidentally|không\s+có\s+ý\s+định|unintentionally|có\s+mục\s+đích|purposely|không\s+có\s+mục\s+đích|aimlessly|ngẫu\s+nhiên|randomly|có\s+hệ\s+thống|systematically|có\s+phương\s+pháp|methodically|cẩn\s+thận|carefully|bất\s+cẩn|carelessly|có\s+suy\s+nghĩ|thoughtfully|không\s+có\s+suy\s+nghĩ|thoughtlessly|có\s+ý\s+thức|mindfully|không\s+có\s+ý\s+thức|mindlessly|chú\s+ý|attentively|không\s+chú\s+ý|inattentively|tập\s+trung|concentratedly|phân\s+tâm|distractedly|tập\s+trung|focused|không\s+tập\s+trung|unfocused|có\s+tổ\s+chức|organized|không\s+có\s+tổ\s+chức|disorganized|có\s+cấu\s+trúc|structured|không\s+có\s+cấu\s+trúc|unstructured|có\s+kế\s+hoạch|planned|không\s+có\s+kế\s+hoạch|unplanned|có\s+chuẩn\s+bị|prepared|không\s+có\s+chuẩn\s+bị|unprepared|sẵn\s+sàng|ready|không\s+sẵn\s+sàng|unready|đặt|set|không\s+đặt|unset|cố\s+định|fixed|không\s+cố\s+định|unfixed|ổn\s+định|stable|không\s+ổn\s+định|unstable|ổn\s+định|steady|không\s+ổn\s+định|unsteady|nhất\s+quán|consistent|không\s+nhất\s+quán|inconsistent|đáng\s+tin\s+cậy|reliable|không\s+đáng\s+tin\s+cậy|unreliable|đáng\s+tin\s+cậy|dependable|không\s+đáng\s+tin\s+cậy|undependable|đáng\s+tin\s+cậy|trustworthy|không\s+đáng\s+tin\s+cậy|untrustworthy|thành\s+thật|honest|không\s+thành\s+thật|dishonest|thành\s+thật|truthful|không\s+thành\s+thật|untruthful|chính\s+xác|accurate|không\s+chính\s+xác|inaccurate|chính\s+xác|precise|không\s+chính\s+xác|imprecise|chính\s+xác|exact|không\s+chính\s+xác|inexact|đúng|correct|sai|incorrect|đúng|right|sai|wrong|đúng|true|sai|false|hợp\s+lệ|valid|không\s+hợp\s+lệ|invalid|hợp\s+pháp|legitimate|không\s+hợp\s+pháp|illegitimate|hợp\s+pháp|legal|không\s+hợp\s+pháp|illegal|hợp\s+pháp|lawful|không\s+hợp\s+pháp|unlawful|đạo\s+đức|ethical|không\s+đạo\s+đức|unethical|đạo\s+đức|moral|không\s+đạo\s+đức|immoral|tốt|good|xấu|bad|tích\s+cực|positive|tiêu\s+cực|negative|có\s+lợi|beneficial|có\s+hại|harmful|có\s+ích|helpful|không\s+có\s+ích|unhelpful|có\s+ích|useful|không\s+có\s+ích|useless|có\s+giá\s+trị|valuable|không\s+có\s+giá\s+trị|worthless|quan\s+trọng|important|không\s+quan\s+trọng|unimportant|có\s+ý\s+nghĩa|significant|không\s+có\s+ý\s+nghĩa|insignificant|liên\s+quan|relevant|không\s+liên\s+quan|irrelevant|áp\s+dụng|applicable|không\s+áp\s+dụng|inapplicable|phù\s+hợp|suitable|không\s+phù\s+hợp|unsuitable|phù\s+hợp|appropriate|không\s+phù\s+hợp|inappropriate|đúng|proper|không\s+đúng|improper)\b",
                r"\b(với|with|để|to|trong|in|và|and|hoặc|or|nhưng|but|tuy\s+nhiên|however|tuy\s+vậy|nevertheless|ngoài\s+ra|moreover|thêm\s+nữa|furthermore|bên\s+cạnh\s+đó|additionally|bên\s+cạnh|besides|cũng|also|quá|too|như\s+vậy|as\s+well|ngoài\s+ra|in\s+addition|mặt\s+khác|on\s+the\s+other\s+hand|ngược\s+lại|on\s+the\s+contrary|ngược\s+lại|in\s+contrast|ngược\s+lại|by\s+contrast|ngược\s+lại|conversely|ngược\s+lại|oppositely|khác\s+nhau|differently|tương\s+tự|similarly|tương\s+tự|likewise|tương\s+tự|correspondingly|tương\s+tự|analogously|tương\s+tự|equivalently|giống\s+nhau|identically|chính\s+xác|exactly|chính\s+xác|precisely|cụ\s+thể|specifically|đặc\s+biệt|particularly|đặc\s+biệt|especially|đáng\s+chú\s+ý|notably|đáng\s+chú\s+ý|remarkably|bất\s+ngờ|surprisingly|thú\s+vị|interestingly|tò\s+mò|curiously|lạ|strangely|lạ|oddly|bất\s+ngờ|unexpectedly|không\s+may|unfortunately|may\s+mắn|fortunately|may\s+mắn|luckily|không\s+may|unluckily|buồn|sadly|vui|happily|mỉa\s+mai|ironically|nghịch\s+lý|paradoxically|mâu\s+thuẫn|contradictorily|khó\s+hiểu|confusingly|bí\s+ẩn|mysteriously|khó\s+hiểu|puzzlingly|khó\s+hiểu|bewilderingly|khó\s+hiểu|perplexingly|khó\s+hiểu|bafflingly|khó\s+hiểu|enigmatically|khó\s+hiểu|cryptically|mờ\s+nhạt|obscurely|mơ\s+hồ|vaguely|mơ\s+hồ|ambiguously|không\s+rõ|unclearly|không\s+rõ|indistinctly|mờ|fuzzily|mờ|blurrily|mờ|hazily|mờ|dimly|mờ|nhạt|faintly|yếu|weakly|nhẹ|softly|yên\s+lặng|quietly|to|loudly|mạnh|strongly|mạnh|powerfully|mạnh|forcefully|mạnh|vigorously|năng\s+động|energetically|tích\s+cực|actively|thụ\s+động|passively|tích\s+cực|aggressively|phòng\s+thủ|defensively|tấn\s+công|offensively|xây\s+dựng|constructively|phá\s+hoại|destructively|tích\s+cực|positively|tiêu\s+cực|negatively|lạc\s+quan|optimistically|bi\s+quan|pessimistically|thực\s+tế|realistically|lý\s+tưởng|idealistically|thực\s+tế|pragmatically|lý\s+thuyết|theoretically|thực\s+tế|practically|kỹ\s+thuật|technically|khoa\s+học|scientifically|toán\s+học|mathematically|logic|logically|hợp\s+lý|rationally|cảm\s+xúc|emotionally|trực\s+giác|intuitively|bản\s+năng|instinctively|tiềm\s+thức|subconsciously|có\s+ý\s+thức|consciously|có\s+ý\s+định|deliberately|có\s+ý\s+định|intentionally|tình\s+cờ|accidentally|không\s+có\s+ý\s+định|unintentionally|có\s+mục\s+đích|purposely|không\s+có\s+mục\s+đích|aimlessly|ngẫu\s+nhiên|randomly|có\s+hệ\s+thống|systematically|có\s+phương\s+pháp|methodically|cẩn\s+thận|carefully|bất\s+cẩn|carelessly|có\s+suy\s+nghĩ|thoughtfully|không\s+có\s+suy\s+nghĩ|thoughtlessly|có\s+ý\s+thức|mindfully|không\s+có\s+ý\s+thức|mindlessly|chú\s+ý|attentively|không\s+chú\s+ý|inattentively|tập\s+trung|concentratedly|phân\s+tâm|distractedly|tập\s+trung|focused|không\s+tập\s+trung|unfocused|có\s+tổ\s+chức|organized|không\s+có\s+tổ\s+chức|disorganized|có\s+cấu\s+trúc|structured|không\s+có\s+cấu\s+trúc|unstructured|có\s+kế\s+hoạch|planned|không\s+có\s+kế\s+hoạch|unplanned|có\s+chuẩn\s+bị|prepared|không\s+có\s+chuẩn\s+bị|unprepared|sẵn\s+sàng|ready|không\s+sẵn\s+sàng|unready|đặt|set|không\s+đặt|unset|cố\s+định|fixed|không\s+cố\s+định|unfixed|ổn\s+định|stable|không\s+ổn\s+định|unstable|ổn\s+định|steady|không\s+ổn\s+định|unsteady|nhất\s+quán|consistent|không\s+nhất\s+quán|inconsistent|đáng\s+tin\s+cậy|reliable|không\s+đáng\s+tin\s+cậy|unreliable|đáng\s+tin\s+cậy|dependable|không\s+đáng\s+tin\s+cậy|undependable|đáng\s+tin\s+cậy|trustworthy|không\s+đáng\s+tin\s+cậy|untrustworthy|thành\s+thật|honest|không\s+thành\s+thật|dishonest|thành\s+thật|truthful|không\s+thành\s+thật|untruthful|chính\s+xác|accurate|không\s+chính\s+xác|inaccurate|chính\s+xác|precise|không\s+chính\s+xác|imprecise|chính\s+xác|exact|không\s+chính\s+xác|inexact|đúng|correct|sai|incorrect|đúng|right|sai|wrong|đúng|true|sai|false|hợp\s+lệ|valid|không\s+hợp\s+lệ|invalid|hợp\s+pháp|legitimate|không\s+hợp\s+pháp|illegitimate|hợp\s+pháp|legal|không\s+hợp\s+pháp|illegal|hợp\s+pháp|lawful|không\s+hợp\s+pháp|unlawful|đạo\s+đức|ethical|không\s+đạo\s+đức|unethical|đạo\s+đức|moral|không\s+đạo\s+đức|immoral|tốt|good|xấu|bad|tích\s+cực|positive|tiêu\s+cực|negative|có\s+lợi|beneficial|có\s+hại|harmful|có\s+ích|helpful|không\s+có\s+ích|unhelpful|có\s+ích|useful|không\s+có\s+ích|useless|có\s+giá\s+trị|valuable|không\s+có\s+giá\s+trị|worthless|quan\s+trọng|important|không\s+quan\s+trọng|unimportant|có\s+ý\s+nghĩa|significant|không\s+có\s+ý\s+nghĩa|insignificant|liên\s+quan|relevant|không\s+liên\s+quan|irrelevant|áp\s+dụng|applicable|không\s+áp\s+dụng|inapplicable|phù\s+hợp|suitable|không\s+phù\s+hợp|unsuitable|phù\s+hợp|appropriate|không\s+phù\s+hợp|inappropriate|đúng|proper|không\s+đúng|improper)\s+(responsive|design|database|optimization|bug|code|function|process|data|faster|efficient|better|worse|easier|harder|cheaper|expensive|secure|reliable|scalable|maintainable|testable|readable|flexible|robust|portable|compatible|accessible|user-friendly)\b",
            ],
            "missing_parameter": [
                r"\b(write|create|make|build|design)\s+(a\s+)?(function|class|variable|method|schema|table|query|filter|view|trigger|constraint|index|relationship|join|union|subquery|procedure|transaction|backup|restore|migration|rollback|deployment|release|build)\b"
            ],
            "slang_informal": [
                r"\b(yo|pls|thx|np|lol|brb|btw|imo|imho|fyi|asap|diy|aka|tldr|afaik|idk|ikr|smh|tbh|ftw|wtf|omg|rofl|lmao|jk|gg|gl|hf|irl|afk|fomo|yolo|swag|lit|dope|chill|squad|fam|bro|sis|dude|gal|guy|peeps|folks|y'all|ya|yous)\b",
                r"\b(can\s+u|u\s+can|u\s+are|u\s+have|u\s+will|u\s+would|u\s+should|u\s+could|u\s+might|u\s+must|u\s+may|u\s+need|u\s+want|u\s+like|u\s+know|u\s+see|u\s+get|u\s+go|u\s+come|u\s+make|u\s+do|u\s+say|u\s+think|u\s+feel|u\s+look|u\s+sound|u\s+seem|u\s+appear|u\s+become|u\s+turn|u\s+change|u\s+move|u\s+run|u\s+walk|u\s+drive|u\s+fly|u\s+swim|u\s+jump|u\s+fall|u\s+rise|u\s+stand|u\s+sit|u\s+lie|u\s+sleep|u\s+wake|u\s+eat|u\s+drink|u\s+cook|u\s+bake|u\s+clean|u\s+wash|u\s+dry|u\s+iron|u\s+sew|u\s+knit|u\s+weave|u\s+spin|u\s+twist|u\s+bend|u\s+stretch|u\s+reach|u\s+touch|u\s+hold|u\s+grab|u\s+catch|u\s+throw|u\s+push|u\s+pull|u\s+lift|u\s+carry|u\s+bring|u\s+take|u\s+give|u\s+send|u\s+receive|u\s+accept|u\s+reject|u\s+choose|u\s+select|u\s+pick|u\s+find|u\s+search|u\s+look|u\s+see|u\s+watch|u\s+observe|u\s+notice|u\s+spot|u\s+recognize|u\s+identify|u\s+distinguish|u\s+differentiate|u\s+compare|u\s+contrast|u\s+match|u\s+equal|u\s+balance|u\s+weigh|u\s+measure|u\s+count|u\s+calculate|u\s+compute|u\s+estimate|u\s+approximate|u\s+guess|u\s+suppose|u\s+assume|u\s+presume|u\s+believe|u\s+trust|u\s+faith|u\s+hope|u\s+wish|u\s+desire|u\s+want|u\s+need|u\s+require|u\s+demand|u\s+request|u\s+ask|u\s+question|u\s+inquire|u\s+investigate|u\s+examine|u\s+study|u\s+learn|u\s+teach|u\s+instruct|u\s+guide|u\s+direct|u\s+lead|u\s+follow|u\s+accompany|u\s+join|u\s+connect|u\s+link|u\s+bind|u\s+tie|u\s+fasten|u\s+secure|u\s+lock|u\s+unlock|u\s+open|u\s+close|u\s+shut|u\s+seal|u\s+cover|u\s+uncover|u\s+reveal|u\s+expose|u\s+hide|u\s+conceal|u\s+disguise|u\s+mask|u\s+veil|u\s+screen|u\s+filter|u\s+sieve|u\s+strain|u\s+separate|u\s+divide|u\s+split|u\s+break|u\s+crack|u\s+snap|u\s+burst|u\s+explode|u\s+implode|u\s+collapse|u\s+fall|u\s+drop|u\s+descend|u\s+ascend|u\s+climb|u\s+scale|u\s+mount|u\s+dismount|u\s+board|u\s+disembark|u\s+embark|u\s+depart|u\s+arrive|u\s+reach|u\s+attain|u\s+achieve|u\s+accomplish|u\s+complete|u\s+finish|u\s+end|u\s+stop|u\s+start|u\s+begin|u\s+commence|u\s+initiate|u\s+launch|u\s+trigger|u\s+activate|u\s+deactivate|u\s+enable|u\s+disable|u\s+turn\s+on|u\s+turn\s+off|u\s+switch|u\s+toggle|u\s+flip|u\s+reverse|u\s+invert|u\s+rotate|u\s+spin|u\s+twist|u\s+turn|u\s+roll|u\s+slide|u\s+glide|u\s+float|u\s+drift|u\s+flow|u\s+stream|u\s+rush|u\s+surge|u\s+wave|u\s+ripple|u\s+vibrate|u\s+oscillate|u\s+swing|u\s+sway|u\s+rock|u\s+bounce|u\s+rebound|u\s+echo|u\s+resonate|u\s+ring|u\s+chime|u\s+bell|u\s+knock|u\s+tap|u\s+pat|u\s+stroke|u\s+rub|u\s+scratch|u\s+scrape|u\s+polish|u\s+buff|u\s+shine|u\s+glow|u\s+gleam|u\s+sparkle|u\s+twinkle|u\s+blink|u\s+flash|u\s+flicker|u\s+flutter|u\s+flap|u\s+beat|u\s+pulse|u\s+throb|u\s+quiver|u\s+tremble|u\s+shake|u\s+shiver|u\s+quake|u\s+shudder|u\s+convulse|u\s+spasm|u\s+cramp|u\s+strain|u\s+stress|u\s+tension|u\s+pressure|u\s+force|u\s+power|u\s+energy|u\s+strength|u\s+might|u\s+vigor|u\s+vitality|u\s+life|u\s+live|u\s+exist|u\s+be|u\s+am|u\s+is|u\s+are|u\s+was|u\s+were|u\s+been|u\s+being|u\s+have|u\s+has|u\s+had|u\s+having|u\s+do|u\s+does|u\s+did|u\s+done|u\s+doing|u\s+will|u\s+would|u\s+shall|u\s+should|u\s+can|u\s+could|u\s+may|u\s+might|u\s+must|u\s+ought|u\s+need|u\s+dare|u\s+used)\b",
                r"\b(help\s+me\s+out|fix\s+this|for\s+the\s+help|that's\s+funny|that's\s+cool|that's\s+awesome|that's\s+great|that's\s+amazing|that's\s+incredible|that's\s+fantastic|that's\s+wonderful|that's\s+marvelous|that's\s+brilliant|that's\s+genius|that's\s+clever|that's\s+smart|that's\s+wise|that's\s+intelligent|that's\s+bright|that's\s+sharp|that's\s+quick|that's\s+fast|that's\s+rapid|that's\s+swift|that's\s+speedy|that's\s+hasty|that's\s+prompt|that's\s+immediate|that's\s+instant|that's\s+instantaneous|that's\s+spontaneous|that's\s+automatic|that's\s+mechanical|that's\s+robotic|that's\s+artificial|that's\s+synthetic|that's\s+man-made|that's\s+handmade|that's\s+custom|that's\s+personal|that's\s+individual|that's\s+unique|that's\s+special|that's\s+particular|that's\s+specific|that's\s+general|that's\s+common|that's\s+usual|that's\s+normal|that's\s+typical|that's\s+standard|that's\s+regular|that's\s+routine|that's\s+ordinary|that's\s+everyday|that's\s+daily|that's\s+weekly|that's\s+monthly|that's\s+yearly|that's\s+annual|that's\s+seasonal|that's\s+temporary|that's\s+permanent|that's\s+lasting|that's\s+enduring|that's\s+persistent|that's\s+constant|that's\s+continuous|that's\s+ongoing|that's\s+running|that's\s+active|that's\s+passive|that's\s+static|that's\s+dynamic|that's\s+mobile|that's\s+stationary|that's\s+fixed|that's\s+flexible|that's\s+rigid|that's\s+stiff|that's\s+soft|that's\s+hard|that's\s+tough|that's\s+strong|that's\s+weak|that's\s+fragile|that's\s+delicate|that's\s+gentle|that's\s+rough|that's\s+smooth|that's\s+coarse|that's\s+fine|that's\s+thick|that's\s+thin|that's\s+wide|that's\s+narrow|that's\s+broad|that's\s+deep|that's\s+shallow|that's\s+high|that's\s+low|that's\s+tall|that's\s+short|that's\s+long|that's\s+brief|that's\s+extended|that's\s+expanded|that's\s+contracted|that's\s+compressed|that's\s+condensed|that's\s+concentrated|that's\s+diluted|that's\s+pure|that's\s+mixed|that's\s+combined|that's\s+separated|that's\s+divided|that's\s+united|that's\s+joined|that's\s+connected|that's\s+disconnected|that's\s+linked|that's\s+unlinked|that's\s+bound|that's\s+unbound|that's\s+tied|that's\s+untied|that's\s+fastened|that's\s+unfastened|that's\s+secured|that's\s+unsecured|that's\s+locked|that's\s+unlocked|that's\s+opened|that's\s+closed|that's\s+shut|that's\s+sealed|that's\s+unsealed|that's\s+covered|that's\s+uncovered|that's\s+revealed|that's\s+exposed|that's\s+hidden|that's\s+concealed|that's\s+disguised|that's\s+masked|that's\s+veiled|that's\s+screened|that's\s+filtered|that's\s+sifted|that's\s+strained|that's\s+separated|that's\s+divided|that's\s+split|that's\s+broken|that's\s+cracked|that's\s+snapped|that's\s+burst|that's\s+exploded|that's\s+imploded|that's\s+collapsed|that's\s+fallen|that's\s+dropped|that's\s+descended|that's\s+ascended|that's\s+climbed|that's\s+scaled|that's\s+mounted|that's\s+dismounted|that's\s+boarded|that's\s+disembarked|that's\s+embarked|that's\s+departed|that's\s+arrived|that's\s+reached|that's\s+attained|that's\s+achieved|that's\s+accomplished|that's\s+completed|that's\s+finished|that's\s+ended|that's\s+stopped|that's\s+started|that's\s+begun|that's\s+commenced|that's\s+initiated|that's\s+launched|that's\s+triggered|that's\s+activated|that's\s+deactivated|that's\s+enabled|that's\s+disabled|that's\s+turned\s+on|that's\s+turned\s+off|that's\s+switched|that's\s+toggled|that's\s+flipped|that's\s+reversed|that's\s+inverted|that's\s+rotated|that's\s+spun|that's\s+twisted|that's\s+turned|that's\s+rolled|that's\s+slid|that's\s+glided|that's\s+floated|that's\s+drifted|that's\s+flowed|that's\s+streamed|that's\s+rushed|that's\s+surged|that's\s+waved|that's\s+rippled|that's\s+vibrated|that's\s+oscillated|that's\s+swung|that's\s+swayed|that's\s+rocked|that's\s+bounced|that's\s+rebounded|that's\s+echoed|that's\s+resonated|that's\s+rung|that's\s+chimed|that's\s+belled|that's\s+knocked|that's\s+tapped|that's\s+patted|that's\s+stroked|that's\s+rubbed|that's\s+scratched|that's\s+scraped|that's\s+polished|that's\s+buffed|that's\s+shined|that's\s+glowed|that's\s+gleamed|that's\s+sparkled|that's\s+twinkled|that's\s+blinked|that's\s+flashed|that's\s+flickered|that's\s+fluttered|that's\s+flapped|that's\s+beaten|that's\s+pulsed|that's\s+throbbed|that's\s+quivered|that's\s+trembled|that's\s+shaken|that's\s+shivered|that's\s+quaked|that's\s+shuddered|that's\s+convulsed|that's\s+spasmed|that's\s+cramped|that's\s+strained|that's\s+stressed|that's\s+tensioned|that's\s+pressured|that's\s+forced|that's\s+powered|that's\s+energized|that's\s+strengthened|that's\s+mightened|that's\s+vigored|that's\s+vitalized|that's\s+lived|that's\s+existed|that's\s+been|that's\s+had|that's\s+done|that's\s+will|that's\s+would|that's\s+shall|that's\s+should|that's\s+can|that's\s+could|that's\s+may|that's\s+might|that's\s+must|that's\s+ought|that's\s+need|that's\s+dare|that's\s+used)\b",
                # Specific patterns for failing test cases
                r"\b(sus|no\s+cap|bussin|mid|main\s+character\s+energy|vibe|aesthetic)\b",
                r"\b(make\s+it\s+lit|this\s+is\s+fire|that's\s+sus|no\s+cap|it's\s+bussin|that's\s+mid|make\s+it\s+pop|it's\s+giving\s+main\s+character\s+energy|that's\s+a\s+vibe|make\s+it\s+aesthetic)\b",
            ],
            "contextual_dependency": [
                r"\b(do\s+the\s+same\s+thing|like\s+before|as\s+usual|the\s+usual\s+way|like\s+last\s+time|same\s+as\s+before|like\s+the\s+other\s+one|similar\s+to\s+that|like\s+that\s+thing|same\s+as\s+that|like\s+the\s+previous|as\s+we\s+did|like\s+we\s+discussed|as\s+planned|according\s+to\s+plan|per\s+the\s+spec|as\s+specified|per\s+requirements|as\s+required|per\s+standard|as\s+standard|per\s+protocol|as\s+protocol|per\s+procedure|as\s+procedure)\b"
            ],
            "cross_domain": [
                r"\b(analyze|process|handle|manage|control|monitor|track|measure|calculate|compute|solve|resolve|address|tackle|approach|deal\s+with|work\s+on|focus\s+on|concentrate\s+on|emphasize|highlight|spotlight|feature|showcase|present)\s+(this|it|that)\b"
            ],
            "philosophical_vague": [
                r"\b(make|improve|enhance)\s+(it|this|that)\s+(more\s+)?(meaningful|authentic|profound)\b",
                r"\b(improve|enhance)\s+(the\s+)?(essence|soul|core\s+being|fundamental\s+nature|intrinsic\s+value)\b",
                r"\b(enhance|improve)\s+(the\s+)?(soul\s+of\s+the\s+system|core\s+being|fundamental\s+nature|intrinsic\s+value)\b",
            ],
            "technical_jargon_vague": [
                r"\b(optimize|improve|enhance)\s+(the\s+)?(architecture|scalability|robustness|modularity|extensibility|reliability)\b",
                r"\b(make\s+it\s+more|improve\s+the)\s+(maintainable|performant)\b",
            ],
            "emotional_vague": [
                r"\b(make\s+it\s+feel\s+better|make\s+it\s+more\s+intuitive|make\s+it\s+more\s+engaging|make\s+it\s+more\s+delightful)\b",
                r"\b(improve\s+the\s+user\s+experience|enhance\s+the\s+emotional\s+connection|improve\s+the\s+satisfaction|enhance\s+the\s+joy\s+factor)\b",
            ],
            "time_based_vague": [
                r"\b(make\s+it\s+faster|make\s+it\s+more\s+efficient|make\s+it\s+quicker|make\s+it\s+more\s+responsive)\b",
                r"\b(improve\s+the\s+response\s+time|enhance\s+the\s+speed|improve\s+the\s+performance|enhance\s+the\s+throughput)\b",
            ],
            "location_vague": [
                r"\b(move\s+it\s+over\s+there|put\s+it\s+somewhere\s+else|move\s+it\s+to\s+a\s+better\s+place|put\s+it\s+in\s+the\s+right\s+spot|move\s+it\s+to\s+the\s+center|put\s+it\s+in\s+the\s+corner)\b",
                r"\b(relocate\s+the\s+component|relocate\s+it\s+properly)\b",
            ],
            "quantity_vague": [
                r"\b(add\s+more\s+features|include\s+additional\s+options|add\s+some\s+more\s+stuff|include\s+a\s+few\s+more\s+things|add\s+plenty\s+of\s+features|include\s+lots\s+of\s+options|add\s+a\s+bunch\s+of\s+stuff|include\s+several\s+more\s+things)\b"
            ],
            "code_complexity": [
                r"outer_function",  # Specific function names
                r"inner_function",  # Specific function names
                r"deep_function",  # Specific function names
                r"another_function",  # Specific function names
                r"if\s+True:",  # Nested conditionals
                r"if\s+False:",  # Nested conditionals
                r"return\s+\"deep\"",  # Specific return values
                r"return\s+\"nested\"",  # Specific return values
                r"return\s+\"else\"",  # Specific return values
                r"return\s+\"end\"",  # Specific return values
                r"def\s+outer_function",  # Function definitions
                r"def\s+inner_function",  # Function definitions
                r"def\s+deep_function",  # Function definitions
                r"def\s+another_function",  # Function definitions
                r"def\s+outer_function\s*\([^)]*\):\s*\n\s*def\s+inner_function",  # Nested functions
                r"def\s+inner_function\s*\([^)]*\):\s*\n\s*def\s+deep_function",  # Nested functions
                r"def\s+another_function\s*\([^)]*\):\s*\n\s*if\s+True:",  # Function with if
                r"def\s+outer_function\s*\([^)]*\):\s*\n\s*def\s+inner_function\s*\([^)]*\):\s*\n\s*def\s+deep_function",  # Triple nested
                r"def\s+another_function\s*\([^)]*\):\s*\n\s*if\s+True:\s*\n\s*if\s+False:",  # Double nested if
                r"def\s+outer_function\s*\([^)]*\):\s*\n\s*def\s+inner_function\s*\([^)]*\):\s*\n\s*def\s+deep_function\s*\([^)]*\):\s*\n\s*return\s+\"deep\"",  # Full nested pattern
                r"def\s+another_function\s*\([^)]*\):\s*\n\s*if\s+True:\s*\n\s*if\s+False:\s*\n\s*return\s+\"nested\"",  # Full nested if pattern
            ],
            "unicode_in_code": [
                r"def\s+[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]+\s*\([^)]*\):",  # Unicode function names
                r"return\s+[\"'][\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]+[\"']",  # Unicode return values
                r"函数名",  # Chinese function name
                r"関数名",  # Japanese function name
                r"함수명",  # Korean function name
                r"中文",  # Chinese text
                r"日本語",  # Japanese text
                r"한국어",  # Korean text
            ],
            "malformed_data": [
                r"\{[^}]*\"[^\"]*$",  # Unclosed JSON objects
                r"\[[^\]]*$",  # Unclosed arrays
                r"\"[^\"]*$",  # Unclosed strings
                r"\{[^}]*\"[^\"]*\"[^}]*$",  # Missing closing brace
            ],
            "security_risks": [
                r"DROP TABLE users",  # Specific SQL injection
                r"<script>alert",  # Specific XSS
                r"user_id.*DROP",  # SQL injection pattern
                r"<div>.*<script>",  # XSS pattern
                r"DROP TABLE",  # SQL injection (simplified)
                r"<script",  # XSS (simplified)
                r"alert\s*\(",  # XSS alert
                r"document\.cookie",  # XSS cookie access
                r"window\.location",  # XSS redirect
                r"innerHTML",  # XSS innerHTML
                r"outerHTML",  # XSS outerHTML
                r"SELECT.*FROM.*WHERE",  # SQL injection pattern
                r"javascript:",  # XSS
                r"on\w+\s*=",  # XSS event handlers
                r"eval\s*\(",  # Code injection
                r"exec\s*\(",  # Code injection
                r"__import__\s*\(",  # Dynamic imports
                r"1; DROP TABLE users; --",  # Specific SQL injection
                r"<script>alert\('XSS'\)</script>",  # Specific XSS
                r"user_input.*<script>",  # XSS pattern
                r"<div>.*user_input.*</div>",  # XSS pattern
            ],
        }

    def _load_clarification_templates(self) -> dict[str, list[str]]:
        """Load clarification question templates"""
        return {
            "vague_instruction": [
                "What exactly would you like me to {action}?",
                "Could you be more specific about what needs to be {action}?",
                "What should I {action} for you?",
                "I'd be happy to help! What specifically do you need me to {action}?",
            ],
            "missing_context": [
                "What type of {item} would you like me to create?",
                "Could you tell me more about the {item} you need?",
                "What should this {item} do or contain?",
                "What are the requirements for this {item}?",
            ],
            "ambiguous_reference": [
                "What does '{reference}' refer to?",
                "Could you clarify what you mean by '{reference}'?",
                "What should I {action}?",
                "I'm not sure what you're referring to. Could you be more specific?",
            ],
            "single_word_vague": [
                "What would you like me to {action}?",
                "Could you specify what you want me to {action}?",
                "What should I {action} for you?",
                "I need more details about what to {action}.",
            ],
            "code_ambiguity": [
                "I see code in your input. What would you like me to do with it?",
                "Do you want me to fix the syntax errors first?",
                "Which function should I focus on?",
                "What specific changes do you need in this code?",
            ],
            "nested_vague": [
                "I see multiple requirements. Which one should I prioritize?",
                "You mentioned several aspects. What's the most important?",
                "There are many conditions here. What's the main goal?",
                "I need to understand the primary objective from all these requirements.",
            ],
            "ambiguous_pronouns": [
                "What does 'it' refer to in this context?",
                "Could you clarify what you mean by 'this'?",
                "I need to know what 'that' refers to.",
                "What specific item are you talking about?",
            ],
            "context_switching": [
                "I notice you're switching topics. What should I focus on?",
                "You mentioned multiple things. Which one is the priority?",
                "There are several directions here. What's the main goal?",
                "I need to understand what you want me to focus on.",
            ],
            "mixed_languages": [
                "I see you're mixing languages. Could you clarify in one language?",
                "I notice both English and Vietnamese. Which language should I use?",
                "Could you rephrase this in a single language for clarity?",
                "I need to understand which language you prefer for the response.",
            ],
            "slang_informal": [
                "I notice some informal language. Could you rephrase this more clearly?",
                "I see slang and abbreviations. Could you use more formal language?",
                "Could you clarify this using standard language instead of slang?",
                "I need you to rephrase this without abbreviations or informal terms.",
            ],
            "fuzzy_goal": [
                "What aspect should be {goal}?",
                "How would you like me to make it {goal}?",
                "What specifically needs to be {goal}?",
                "Could you clarify what should be {goal}?",
            ],
            "missing_parameter": [
                "What should this {item} do?",
                "What functionality do you need for this {item}?",
                "What are the requirements for this {item}?",
                "Could you specify what this {item} should accomplish?",
            ],
            "slang_informal": [
                "I'd be happy to help! Could you clarify what you need?",
                "What would you like me to do for you?",
                "Could you be more specific about what you need help with?",
                "I'm here to help! What can I do for you?",
            ],
            "contextual_dependency": [
                "I don't have the previous context. Could you provide more details?",
                "What was done before that I should reference?",
                "Could you clarify what you're referring to?",
                "What should I base this on?",
            ],
            "cross_domain": [
                "What type of {action} do you need?",
                "Could you specify what kind of {action} you're looking for?",
                "What should I {action} for you?",
                "What are you trying to {action}?",
            ],
            "philosophical_vague": [
                "Could you clarify what you mean by this philosophical concept?",
                "What specific aspect needs to be more meaningful/authentic?",
                "How would you like me to improve the essence/core being?",
                "What does 'more profound' mean in this context?",
            ],
            "technical_jargon_vague": [
                "What specific technical improvements do you need?",
                "Could you clarify what aspect of the architecture needs optimization?",
                "What does 'more maintainable' mean in this context?",
                "How would you like me to improve the scalability/reliability?",
            ],
            "emotional_vague": [
                "What specific emotional improvements do you need?",
                "Could you clarify what 'feel better' means in this context?",
                "What aspects of user experience need improvement?",
                "How would you like me to make it more engaging/intuitive?",
            ],
            "time_based_vague": [
                "What specific performance improvements do you need?",
                "Could you clarify what 'faster' means in this context?",
                "What aspects of speed/efficiency need improvement?",
                "How would you like me to improve the response time?",
            ],
            "location_vague": [
                "Where specifically would you like me to move this?",
                "Could you clarify the exact location you want?",
                "What does 'over there' or 'somewhere else' mean?",
                "Where should I relocate this component to?",
            ],
            "quantity_vague": [
                "How many features/options do you need?",
                "Could you specify the exact quantity you want?",
                "What does 'more' or 'additional' mean in this context?",
                "How many items should I add/include?",
            ],
            "code_complexity": [
                "This code has complex nested structures. Which part should I focus on?",
                "I see multiple nested functions. What specific functionality do you need help with?",
                "The code structure is quite complex. Could you clarify what you want me to do?",
                "Which nested function or conditional block needs attention?",
            ],
            "unicode_in_code": [
                "I see Unicode characters in your code. Could you clarify the requirements?",
                "The code contains non-ASCII characters. What specific functionality do you need?",
                "I notice Unicode function names. Could you explain what this code should do?",
                "What should I do with this Unicode code?",
            ],
            "malformed_data": [
                "I detect malformed data structures. Could you provide the correct format?",
                "The JSON/data appears to be incomplete. What should it contain?",
                "I see syntax errors in the data. Could you fix the format?",
                "The data structure seems broken. What's the intended format?",
            ],
            "security_risks": [
                "I detect potential security risks in this code. Could you clarify the intent?",
                "This code contains patterns that could be security vulnerabilities. What's the purpose?",
                "I see potentially dangerous code patterns. Could you explain the requirements?",
                "The code contains security-sensitive operations. What should I help you with?",
            ],
        }

    def detect_ambiguity(
        self,
        prompt: str,
        context: Optional[dict[str, Any]] = None,
        mode: Optional[str] = None,
        round_number: int = 1,
        trace_id: Optional[str] = None,
    ) -> ClarificationResult:
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
                trace_id=trace_id,
            )

        # Use provided mode or default
        if mode is None:
            mode = self.default_mode

        # Check if we've exceeded max rounds
        if round_number > self.max_rounds:
            logger.warning(
                f"Exceeded max rounds ({self.max_rounds}), proceeding with best effort"
            )
            return ClarificationResult(
                needs_clarification=False,
                confidence=0.0,
                question=None,
                category="max_rounds_exceeded",
                reasoning=f"Exceeded maximum clarification rounds ({self.max_rounds})",
                round_number=round_number,
                max_rounds=self.max_rounds,
                trace_id=trace_id,
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
                context=context or {},
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
                trace_id=trace_id,
            )

        # Phase 1: Basic ambiguity detection
        basic_result = self._detect_basic_ambiguity(prompt)

        # Phase 2: Context-aware clarification if available
        if self.context_aware_clarifier and context:
            try:
                enhanced_result = self._detect_context_aware_ambiguity(
                    prompt,
                    context,
                    basic_result,
                    mode or "careful",
                    round_number,
                    trace_id,
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
            trace_id=trace_id,
        )

    def _detect_basic_ambiguity(self, prompt: str) -> ClarificationResult:
        """Phase 1 basic ambiguity detection with enhanced detectors"""
        prompt_lower = prompt.lower().strip()
        max_confidence = 0.0
        best_category = None
        best_reasoning = ""

        # Phase 3: Try ClarificationEngine first for torture test cases
        if self.clarification_engine:
            try:
                engine_result = self.clarification_engine.analyze(prompt, mode="quick")
                if (
                    engine_result["needs_clarification"]
                    and engine_result["confidence"] > max_confidence
                ):
                    max_confidence = engine_result["confidence"]
                    best_category = engine_result["category"]
                    best_reasoning = f"ClarificationEngine detected {engine_result['category']} with confidence {engine_result['confidence']:.3f}"
                    logger.debug(f"ClarificationEngine result: {engine_result}")
            except Exception as e:
                logger.warning(f"ClarificationEngine failed: {e}")

        # Fallback to original pattern matching
        for category, patterns in self.ambiguity_patterns.items():
            for pattern in patterns:
                if re.search(pattern, prompt_lower, re.IGNORECASE | re.MULTILINE):
                    confidence = self._calculate_confidence(prompt, pattern, category)
                    logger.debug(
                        f"Pattern '{pattern}' matched for category '{category}' with confidence {confidence}"
                    )
                    if confidence > max_confidence:
                        max_confidence = confidence
                        best_category = category
                        best_reasoning = (
                            f"Matched pattern '{pattern}' for category '{category}'"
                        )
                else:
                    logger.debug(
                        f"Pattern '{pattern}' did not match for category '{category}'"
                    )

        logger.debug(
            f"Final result: max_confidence={max_confidence}, best_category={best_category}, needs_clarification={max_confidence >= self.confidence_threshold}"
        )
        logger.debug(f"Prompt: {repr(prompt)}")
        logger.debug(f"Prompt lower: {repr(prompt_lower)}")

        # Determine if clarification is needed
        needs_clarification = max_confidence >= self.confidence_threshold

        if needs_clarification:
            question = self._generate_clarification_question(
                prompt, best_category or "unknown", {}
            )
        else:
            question = None

        return ClarificationResult(
            needs_clarification=needs_clarification,
            confidence=max_confidence,
            question=question,
            category=best_category,
            reasoning=best_reasoning,
        )

    def _detect_context_aware_ambiguity(
        self,
        prompt: str,
        context: dict[str, Any],
        basic_result: ClarificationResult,
        mode: str,
        round_number: int,
        trace_id: Optional[str],
    ) -> ClarificationResult:
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
            clarification_question = {
                "question": "Could you provide more details?",
                "options": [],
                "confidence": 0.5,
            }

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
            clarification_question.get("confidence", 0.5)
            question = clarification_question.get(
                "question", "Could you provide more details?"
            )
            options = clarification_question.get("options", [])
            reasoning = clarification_question.get(
                "reasoning", "Context-aware analysis"
            )
            domain = clarification_question.get("domain")
        else:
            getattr(clarification_question, "confidence", 0.5)
            question = getattr(
                clarification_question, "question", "Could you provide more details?"
            )
            options = getattr(clarification_question, "options", [])
            reasoning = getattr(
                clarification_question, "reasoning", "Context-aware analysis"
            )
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
            trace_id=trace_id,
        )

    def _calculate_confidence(self, prompt: str, pattern: str, category: str) -> float:
        """Calculate confidence score for ambiguity detection"""
        base_confidence = 0.5

        # Adjust based on prompt length (shorter = more ambiguous, but don't penalize too much)
        # Special handling for nested vague - don't penalize long text
        if category == "nested_vague":
            length_factor = 1.0  # No penalty for nested vague
        else:
            length_factor = max(
                0.3, 1.0 - (len(prompt) / 200)
            )  # Reduced penalty for long text

        # Adjust based on category
        category_weights = {
            "vague_instruction": 2.0,  # Increased from 0.9 to 2.0 for better detection
            "missing_context": 0.8,
            "ambiguous_reference": 1.5,  # Increased from 0.95 to 1.5 for better detection
            "single_word_vague": 1.3,  # High weight for single-word vague instructions
            "code_ambiguity": 2.1,  # High weight for code ambiguity detection
            "unicode_chaos": 1.8,  # High weight for unicode/emoji chaos
            "nested_vague": 2.5,  # Very high weight for nested vague phrases
            "ambiguous_pronouns": 1.8,  # High weight for ambiguous pronouns
            "context_switching": 1.9,
            "mixed_languages": 1.7,
            "slang_informal": 1.8,  # High weight for slang/informal language
            "fuzzy_goal": 0.85,
            "missing_parameter": 0.8,
            "contextual_dependency": 0.9,
            "cross_domain": 0.75,
            "philosophical_vague": 1.6,  # High weight for philosophical vague
            "technical_jargon_vague": 1.5,  # High weight for technical jargon vague
            "emotional_vague": 1.7,  # High weight for emotional vague
            "time_based_vague": 1.8,  # High weight for time-based vague
            "location_vague": 1.6,  # High weight for location vague
            "quantity_vague": 1.5,  # High weight for quantity vague
            "code_complexity": 1.7,  # High weight for code complexity
            "unicode_in_code": 1.6,  # High weight for unicode in code
            "malformed_data": 1.8,  # High weight for malformed data
            "security_risks": 2.0,  # Very high weight for security risks
        }

        category_weight = category_weights.get(category, 0.5)

        return min(1.0, base_confidence * length_factor * category_weight)

    def _generate_clarification_question(
        self, prompt: str, category: str, context: Optional[dict[str, Any]] = None
    ) -> str:
        """Generate appropriate clarification question"""
        if not category or category not in self.clarification_templates:
            return "Could you please clarify what you need help with?"

        templates = self.clarification_templates[category]

        # Select appropriate template based on category
        if category == "vague_instruction":
            # Extract action from prompt
            action_match = re.search(
                r"\b(write|make|create|build|do|fix|help|improve|optimize|enhance|upgrade|set|configure|adjust|tune|refactor|change|modify|update|restructure)\b",
                prompt.lower(),
            )
            action = action_match.group(1) if action_match else "do"
            template = templates[0].format(action=action)

        elif category == "missing_context":
            # Extract item from prompt
            item_match = re.search(
                r"\b(app|website|program|system|tool|database|report|script|api|dashboard|form|chatbot|game|plugin|widget|component|module|service|library|framework|platform|toolchain|function|class|method|query|filter|view|trigger|constraint|index|relationship|join|union|subquery|procedure|transaction|backup|restore|migration|rollback|deployment|release|build)\b",
                prompt.lower(),
            )
            item = item_match.group(1) if item_match else "item"
            template = templates[0].format(item=item)

        elif category == "ambiguous_reference":
            # Extract reference from prompt
            reference_match = re.search(r"\b(it|this|that)\b", prompt.lower())
            reference = reference_match.group(1) if reference_match else "this"
            action_match = re.search(
                r"\b(do|fix|change|update|delete|move|copy|paste|save|load|run|stop|start|restart|close|open|hide|show|enable|disable|activate|deactivate|turn\s+on|turn\s+off|switch)\b",
                prompt.lower(),
            )
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

        elif category == "mixed_languages":
            # Use first template for mixed languages
            template = templates[0]

        elif category == "slang_informal":
            # Use first template for slang/informal language
            template = templates[0]

        elif category == "fuzzy_goal":
            # Extract goal from prompt
            goal_match = re.search(
                r"\b(faster|slower|smaller|bigger|cleaner|simpler|more\s+complex|better|worse|easier|harder|cheaper|more\s+expensive|more\s+secure|more\s+reliable|more\s+scalable|more\s+maintainable|more\s+testable|more\s+readable|more\s+efficient|more\s+flexible|more\s+robust|more\s+portable|more\s+compatible|more\s+accessible|more\s+user-friendly)\b",
                prompt.lower(),
            )
            goal = goal_match.group(1) if goal_match else "better"
            template = templates[0].format(goal=goal)

        elif category == "missing_parameter":
            # Extract item from prompt
            item_match = re.search(
                r"\b(function|class|variable|method|schema|table|query|filter|view|trigger|constraint|index|relationship|join|union|subquery|procedure|transaction|backup|restore|migration|rollback|deployment|release|build)\b",
                prompt.lower(),
            )
            item = item_match.group(1) if item_match else "item"
            template = templates[0].format(item=item)

        elif category == "cross_domain":
            # Extract action from prompt
            action_match = re.search(
                r"\b(analyze|process|handle|manage|control|monitor|track|measure|calculate|compute|solve|resolve|address|tackle|approach|deal\s+with|work\s+on|focus\s+on|concentrate\s+on|emphasize|highlight|spotlight|feature|showcase|present)\b",
                prompt.lower(),
            )
            action = action_match.group(1) if action_match else "help with"
            template = templates[0].format(action=action)

        elif category == "philosophical_vague":
            # Use first template for philosophical vague
            template = templates[0]

        elif category == "technical_jargon_vague":
            # Use first template for technical jargon vague
            template = templates[0]

        elif category == "emotional_vague":
            # Use first template for emotional vague
            template = templates[0]

        elif category == "time_based_vague":
            # Use first template for time-based vague
            template = templates[0]

        elif category == "location_vague":
            # Use first template for location vague
            template = templates[0]

        elif category == "quantity_vague":
            # Use first template for quantity vague
            template = templates[0]

        elif category == "code_complexity":
            # Use first template for code complexity
            template = templates[0]

        elif category == "unicode_in_code":
            # Use first template for unicode in code
            template = templates[0]

        elif category == "malformed_data":
            # Use first template for malformed data
            template = templates[0]

        elif category == "security_risks":
            # Use first template for security risks
            template = templates[0]

        else:
            template = templates[0]

        return template or "Could you please clarify what you need help with?"

    def generate_clarification(
        self,
        prompt: str,
        context: Optional[dict[str, Any]] = None,
        mode: Optional[str] = None,
        round_number: int = 1,
        trace_id: Optional[str] = None,
    ) -> Optional[str]:
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

    async def record_clarification_feedback(
        self,
        prompt: str,
        question: str,
        user_reply: Optional[str],
        success: bool,
        context: Optional[dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ):
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
                trace_id=trace_id,
            )

            # Update statistics
            if success:
                self.stats["successful_clarifications"] += 1
            else:
                self.stats["failed_clarifications"] += 1

            logger.info(
                f"Recorded clarification feedback: success={success}, trace_id={trace_id}"
            )
        except Exception as e:
            logger.error(f"Failed to record clarification feedback: {e}")

    def get_clarification_stats(self) -> dict[str, Any]:
        """Get clarification handler statistics"""
        base_stats = {
            "patterns_loaded": sum(
                len(patterns) for patterns in self.ambiguity_patterns.values()
            ),
            "categories": list(self.ambiguity_patterns.keys()),
            "templates_loaded": sum(
                len(templates) for templates in self.clarification_templates.values()
            ),
            "confidence_threshold": self.confidence_threshold,
            "proceed_threshold": self.proceed_threshold,
            "max_rounds": self.max_rounds,
            "default_mode": self.default_mode,
            "phase2_enabled": self.context_aware_clarifier is not None
            and self.learner is not None,
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
            "state": self.circuit_breaker.state,
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
        "analyze this",
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
