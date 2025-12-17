"""
Decision Logging Infrastructure for Agentic RAG

This module provides structured logging of agent decisions, reasoning, and alternative paths
considered during StillMe's processing pipeline. This enables true agentic self-narrative
generation based on actual decision logs, not just LLM-generated text.

Key Features:
- Log agent decisions with reasoning
- Track alternative paths considered
- Record confidence threshold reasoning
- Store in structured format for self-narrative generation
- Support for multi-agent coordination logging

Inspired by Agentic RAG concepts: agents should log their decisions, not just execute them.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import json
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of agents in StillMe's system"""
    RAG_AGENT = "rag_agent"
    VALIDATOR_ORCHESTRATOR = "validator_orchestrator"
    SOURCE_CONSENSUS_AGENT = "source_consensus_agent"
    IDENTITY_CHECK_AGENT = "identity_check_agent"
    CONFIDENCE_AGENT = "confidence_agent"
    CITATION_AGENT = "citation_agent"
    CODEBASE_AGENT = "codebase_agent"
    HONESTY_AGENT = "honesty_agent"
    RESPONSE_AGENT = "response_agent"
    PLANNER_AGENT = "planner_agent"
    QUESTION_ANALYZER_AGENT = "question_analyzer_agent"


class DecisionType(Enum):
    """Types of decisions agents can make"""
    RETRIEVAL_DECISION = "retrieval_decision"  # Whether to retrieve, what to retrieve
    SOURCE_SELECTION = "source_selection"  # Which sources to prioritize
    VALIDATION_DECISION = "validation_decision"  # Whether to validate, which validators to use
    CONFIDENCE_THRESHOLD = "confidence_threshold"  # Why a confidence threshold was chosen
    ALTERNATIVE_PATH = "alternative_path"  # Alternative paths considered
    TOOL_SELECTION = "tool_selection"  # Which tools/agents to use
    ROUTING_DECISION = "routing_decision"  # How to route the query
    CITATION_DECISION = "citation_decision"  # Whether to add citation, which format
    FALLBACK_DECISION = "fallback_decision"  # Whether to use fallback, why


@dataclass
class AgentDecision:
    """
    Represents a single decision made by an agent
    
    This is the core data structure for decision logging.
    Each decision includes:
    - Which agent made the decision
    - What decision was made
    - Why (reasoning)
    - Alternative paths considered
    - Confidence/uncertainty level
    """
    # Core fields
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    agent_type: str = ""  # AgentType enum value
    decision_type: str = ""  # DecisionType enum value
    
    # Decision content
    decision: str = ""  # What decision was made (e.g., "Retrieve 3 documents from CRITICAL_FOUNDATION")
    reasoning: str = ""  # Why this decision was made (e.g., "Question requires StillMe foundational knowledge")
    
    # Context
    question: Optional[str] = None  # User question (truncated if too long)
    context: Optional[Dict[str, Any]] = None  # Additional context (docs retrieved, similarity scores, etc.)
    
    # Alternatives considered
    alternatives_considered: List[str] = field(default_factory=list)  # Alternative paths considered
    why_not_chosen: Optional[str] = None  # Why alternatives were not chosen
    
    # Confidence and thresholds
    confidence_level: Optional[float] = None  # Confidence in this decision (0.0-1.0)
    threshold_reasoning: Optional[str] = None  # Why a threshold was chosen (e.g., "Similarity 0.43 is sufficient because...")
    
    # Results
    outcome: Optional[str] = None  # What happened as a result of this decision
    success: Optional[bool] = None  # Whether decision was successful
    
    # Metadata
    session_id: Optional[str] = None  # Session/request ID for grouping decisions
    parent_decision_id: Optional[str] = None  # If this decision was triggered by another decision
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata


@dataclass
class DecisionSession:
    """
    Represents a complete decision session (one user query)
    
    Groups all agent decisions for a single query together.
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    question: str = ""
    detected_lang: str = "en"
    decisions: List[AgentDecision] = field(default_factory=list)
    
    # Summary
    total_decisions: int = 0
    agents_involved: List[str] = field(default_factory=list)
    final_outcome: Optional[str] = None


class DecisionLogger:
    """
    Main class for logging agent decisions
    
    Provides methods to log decisions, retrieve decision history,
    and generate self-narrative from decision logs.
    """
    
    def __init__(self, persist_to_file: bool = True, log_file: Optional[str] = None):
        """
        Initialize decision logger
        
        Args:
            persist_to_file: Whether to persist logs to file
            log_file: Path to log file (default: data/decision_logs.jsonl)
        """
        self.persist_to_file = persist_to_file
        self.log_file = log_file or "data/decision_logs.jsonl"
        
        # In-memory storage: current session
        self.current_session: Optional[DecisionSession] = None
        self._sessions: List[DecisionSession] = []
        
        # Ensure data directory exists
        if self.persist_to_file:
            Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"DecisionLogger initialized (persist={persist_to_file}, file={self.log_file})")
    
    def start_session(self, question: str, detected_lang: str = "en", session_id: Optional[str] = None) -> str:
        """
        Start a new decision session for a user query
        
        Args:
            question: User question
            detected_lang: Detected language
            session_id: Optional session ID (will generate if not provided)
            
        Returns:
            Session ID
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        self.current_session = DecisionSession(
            session_id=session_id,
            question=question[:500],  # Truncate long questions
            detected_lang=detected_lang
        )
        
        logger.debug(f"Started decision session: {session_id} for question: {question[:100]}...")
        return session_id
    
    def log_decision(
        self,
        agent_type: Union[AgentType, str],
        decision_type: Union[DecisionType, str],
        decision: str,
        reasoning: str,
        question: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        alternatives_considered: Optional[List[str]] = None,
        why_not_chosen: Optional[str] = None,
        confidence_level: Optional[float] = None,
        threshold_reasoning: Optional[str] = None,
        outcome: Optional[str] = None,
        success: Optional[bool] = None,
        parent_decision_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a decision made by an agent
        
        Args:
            agent_type: Type of agent making the decision
            decision_type: Type of decision
            decision: What decision was made
            reasoning: Why this decision was made
            question: User question (if not using current session)
            context: Additional context
            alternatives_considered: Alternative paths considered
            why_not_chosen: Why alternatives were not chosen
            confidence_level: Confidence in this decision (0.0-1.0)
            threshold_reasoning: Why a threshold was chosen
            outcome: What happened as a result
            success: Whether decision was successful
            parent_decision_id: ID of parent decision if this was triggered by another
            metadata: Additional metadata
            
        Returns:
            Decision ID
        """
        # Ensure we have a session
        if self.current_session is None:
            self.start_session(question or "unknown", "en")
        
        # Convert enums to strings
        agent_type_str = agent_type.value if isinstance(agent_type, AgentType) else agent_type
        decision_type_str = decision_type.value if isinstance(decision_type, DecisionType) else decision_type
        
        # Create decision
        agent_decision = AgentDecision(
            agent_type=agent_type_str,
            decision_type=decision_type_str,
            decision=decision,
            reasoning=reasoning,
            question=question or self.current_session.question,
            context=context,
            alternatives_considered=alternatives_considered or [],
            why_not_chosen=why_not_chosen,
            confidence_level=confidence_level,
            threshold_reasoning=threshold_reasoning,
            outcome=outcome,
            success=success,
            session_id=self.current_session.session_id,
            parent_decision_id=parent_decision_id,
            metadata=metadata or {}
        )
        
        # Add to current session
        self.current_session.decisions.append(agent_decision)
        self.current_session.total_decisions += 1
        
        # Track agents involved
        if agent_type_str not in self.current_session.agents_involved:
            self.current_session.agents_involved.append(agent_type_str)
        
        # Persist if enabled
        if self.persist_to_file:
            self._save_decision(agent_decision)
        
        logger.debug(
            f"Logged decision: {agent_type_str} -> {decision_type_str} "
            f"(decision_id={agent_decision.decision_id})"
        )
        
        return agent_decision.decision_id
    
    def end_session(self, final_outcome: Optional[str] = None) -> DecisionSession:
        """
        End current session and return it
        
        Args:
            final_outcome: Final outcome of the session
            
        Returns:
            Completed DecisionSession
        """
        if self.current_session is None:
            logger.warning("No active session to end")
            return DecisionSession()
        
        self.current_session.final_outcome = final_outcome
        self._sessions.append(self.current_session)
        
        # Persist session if enabled
        if self.persist_to_file:
            self._save_session(self.current_session)
        
        session = self.current_session
        self.current_session = None
        
        logger.debug(f"Ended decision session: {session.session_id} with {session.total_decisions} decisions")
        return session
    
    def get_session_decisions(self, session_id: Optional[str] = None) -> List[AgentDecision]:
        """
        Get all decisions for a session
        
        Args:
            session_id: Session ID (uses current session if None)
            
        Returns:
            List of decisions
        """
        if session_id is None:
            if self.current_session:
                return self.current_session.decisions
            return []
        
        # Find session in history
        for session in self._sessions:
            if session.session_id == session_id:
                return session.decisions
        
        return []
    
    def generate_agentic_narrative(self, session_id: Optional[str] = None) -> str:
        """
        Generate agentic self-narrative from decision logs
        
        This is the key method that transforms decision logs into
        a narrative that StillMe can use to explain its process.
        
        Args:
            session_id: Session ID (uses current session if None)
            
        Returns:
            Formatted narrative string
        """
        decisions = self.get_session_decisions(session_id)
        
        if not decisions:
            return "No decision logs available for this session."
        
        narrative_parts = []
        narrative_parts.append("**AGENTIC DECISION LOG:**\n")
        
        # Group by agent
        by_agent: Dict[str, List[AgentDecision]] = {}
        for decision in decisions:
            if decision.agent_type not in by_agent:
                by_agent[decision.agent_type] = []
            by_agent[decision.agent_type].append(decision)
        
        # Generate narrative for each agent
        for agent_type, agent_decisions in by_agent.items():
            narrative_parts.append(f"\n**{agent_type.upper().replace('_', ' ')}:**")
            
            for decision in agent_decisions:
                narrative_parts.append(f"\n- **Decision**: {decision.decision}")
                narrative_parts.append(f"  - **Reasoning**: {decision.reasoning}")
                
                if decision.alternatives_considered:
                    narrative_parts.append(f"  - **Alternatives considered**: {', '.join(decision.alternatives_considered)}")
                    if decision.why_not_chosen:
                        narrative_parts.append(f"  - **Why not chosen**: {decision.why_not_chosen}")
                
                if decision.threshold_reasoning:
                    narrative_parts.append(f"  - **Threshold reasoning**: {decision.threshold_reasoning}")
                
                if decision.outcome:
                    narrative_parts.append(f"  - **Outcome**: {decision.outcome}")
        
        return "\n".join(narrative_parts)
    
    def _save_decision(self, decision: AgentDecision):
        """Save a single decision to file"""
        if not self.persist_to_file:
            return
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(decision), ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"Failed to save decision to {self.log_file}: {e}")
    
    def _save_session(self, session: DecisionSession):
        """Save a complete session to file"""
        if not self.persist_to_file:
            return
        
        session_file = self.log_file.replace('.jsonl', '_sessions.jsonl')
        try:
            with open(session_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(session), ensure_ascii=False, default=str) + '\n')
        except Exception as e:
            logger.error(f"Failed to save session to {session_file}: {e}")


# Global instance
_decision_logger: Optional[DecisionLogger] = None


def get_decision_logger() -> DecisionLogger:
    """Get global decision logger instance"""
    global _decision_logger
    if _decision_logger is None:
        _decision_logger = DecisionLogger()
    return _decision_logger

