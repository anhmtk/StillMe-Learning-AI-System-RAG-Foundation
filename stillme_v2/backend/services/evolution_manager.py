# Evolution Manager Service
"""
Evolution Manager Service
Manages daily learning sessions and evolution tracking
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from ..core.learning_engine import EvolutionaryLearningEngine, EvolutionStage
from ..database.schema import LearningSession as DBLearningSession, Proposal, KnowledgeBase
from .rss_pipeline import RSSLearningPipeline, ContentProposal
from .notification_service import notification_service
from .trust_score_manager import trust_score_manager
from .knowledge_consolidation_service import knowledge_consolidation_service

logger = logging.getLogger(__name__)


class EvolutionManager:
    """
    Evolution Manager
    Orchestrates daily learning sessions and evolution tracking
    """
    
    # Configuration constants
    MAX_PROPOSALS_PER_SESSION: int = 50
    AUTO_APPROVAL_THRESHOLD: float = 0.8
    SESSION_TIMEOUT_MINUTES: int = 30
    LEARNING_HISTORY_DAYS: int = 30
    
    def __init__(self, db_session: Session) -> None:
        """
        Initialize Evolution Manager
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
        self.learning_engine = EvolutionaryLearningEngine()
        self.rss_pipeline = RSSLearningPipeline()
        
    def run_daily_learning_session(self) -> Dict[str, Any]:
        """
        Run complete daily learning session
        
        Returns:
            Dict containing session results and metrics
            
        Raises:
            Exception: If learning session fails
        """
        logger.info("🚀 Starting daily evolution session...")
        
        try:
            # 1. Fetch RSS content
            content = self.rss_pipeline.fetch_daily_content()
            logger.info(f"Fetched {len(content)} content items")
            
            # 2. Generate proposals
            proposals = self.rss_pipeline.generate_proposals(content)
            logger.info(f"Generated {len(proposals)} proposals")
            
            # 3. Auto-approve safe proposals
            auto_approved, needs_review = self.rss_pipeline.filter_proposals_for_auto_approval(
                proposals, 
                threshold=self.AUTO_APPROVAL_THRESHOLD
            )
            logger.info(f"Auto-approved: {len(auto_approved)}, Needs review: {len(needs_review)}")
            
            # Limit proposals to prevent overload
            if len(auto_approved) > self.MAX_PROPOSALS_PER_SESSION:
                auto_approved = auto_approved[:self.MAX_PROPOSALS_PER_SESSION]
                logger.warning(f"Limited proposals to {self.MAX_PROPOSALS_PER_SESSION}")
            
            # 4. Learn from approved proposals
            session = self.learning_engine.start_daily_learning_session([
                {
                    "title": p.title,
                    "content": p.content,
                    "quality_score": p.quality_score
                } for p in auto_approved
            ])
            
            # 5. Save to database
            self._save_learning_session(session)
            self._save_learned_knowledge(auto_approved)
            
            # 6. Self-assessment
            assessment = self.learning_engine.self_assess_performance()
            
            # 7. Adjust parameters
            self.learning_engine.adjust_learning_parameters(assessment)
            
            result = {
                "session": session,
                "assessment": assessment,
                "proposals_processed": len(proposals),
                "auto_approved": len(auto_approved),
                "needs_review": len(needs_review),
                "success": True,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(
                f"Daily session completed successfully. "
                f"Session: {session.session_id}, "
                f"Learned: {session.proposals_learned}, "
                f"Stage: {session.evolution_stage.value}"
            )
            
            # Update trust scores based on learning outcomes
            self._update_trust_scores_from_session(auto_approved, session)
            
            # Consolidate knowledge from learned proposals
            consolidation_result = self._consolidate_learned_knowledge(auto_approved)
            result["consolidation_result"] = consolidation_result
            
            # Send notification about learning session
            try:
                notification_service.notify_learning_session({
                    "session_id": session.session_id,
                    "evolution_stage": session.evolution_stage.value,
                    "proposals_learned": session.proposals_learned,
                    "success_rate": 0.8 if assessment.get("overall_health") == "healthy" else 0.5,
                    "duration_minutes": 30  # Estimated
                })
            except Exception as notify_error:
                logger.warning(f"Failed to send notification: {notify_error}")
            
            return result
            
        except Exception as e:
            logger.error(f"Daily learning session failed: {str(e)}", exc_info=True)
            raise
    
    def _update_trust_scores_from_session(self, proposals: List[ContentProposal], session: Any):
        """Update trust scores based on learning session outcomes"""
        try:
            # Determine learning success based on session metrics
            learning_success = session.success and session.proposals_learned > 0
            
            # Group proposals by source
            source_proposals = {}
            for proposal in proposals:
                source_name = proposal.source_name
                if source_name not in source_proposals:
                    source_proposals[source_name] = []
                source_proposals[source_name].append(proposal)
            
            # Update trust scores for each source
            for source_name, source_props in source_proposals.items():
                # Calculate average quality score for this source
                avg_quality = sum(prop.quality_score for prop in source_props) / len(source_props)
                
                # Update performance metrics
                trust_score_manager.update_performance(
                    source_name=source_name,
                    learning_outcome=learning_success,
                    quality_score=avg_quality
                )
                
                logger.debug(f"Updated trust score for {source_name}: success={learning_success}, quality={avg_quality:.3f}")
                
        except Exception as e:
            logger.error(f"Failed to update trust scores: {e}")
    
    def _consolidate_learned_knowledge(self, proposals: List[ContentProposal]) -> Dict[str, Any]:
        """Consolidate knowledge from learned proposals"""
        try:
            logger.info("Starting knowledge consolidation from learned proposals...")
            
            # Add proposals to knowledge base
            added_items = 0
            for proposal in proposals:
                if proposal.status == "approved":
                    item_id = knowledge_consolidation_service.add_knowledge_item(
                        title=proposal.title,
                        content=proposal.content,
                        source=proposal.source_name,
                        category=proposal.category,
                        quality_score=proposal.quality_score,
                        trust_score=proposal.quality_score  # Use quality as trust for now
                    )
                    
                    if item_id:
                        added_items += 1
            
            logger.info(f"Added {added_items} knowledge items to consolidation service")
            
            # Run consolidation if we have enough items
            consolidation_result = {"items_added": added_items}
            
            if added_items > 0:
                # Check if we should run consolidation
                total_items = len(knowledge_consolidation_service.knowledge_items)
                if total_items >= 10:  # Run consolidation every 10 items
                    consolidation_result.update(
                        knowledge_consolidation_service.consolidate_knowledge()
                    )
                    logger.info(f"Knowledge consolidation completed: {consolidation_result}")
            
            return consolidation_result
            
        except Exception as e:
            logger.error(f"Failed to consolidate learned knowledge: {e}")
            return {"error": str(e)}
    
    def _save_learning_session(self, session: Any) -> None:
        """
        Save learning session to database
        
        Args:
            session: Learning session object
            
        Raises:
            Exception: If database operation fails
        """
        try:
            db_session = DBLearningSession(
                session_id=session.session_id,
                date=session.date,
                proposals_learned=session.proposals_learned,
                accuracy_delta=session.accuracy_delta,
                evolution_stage=session.evolution_stage.value,
                duration_minutes=session.duration_minutes,
                success=session.success,
                notes="\n".join(session.notes)
            )
            
            self.db.add(db_session)
            self.db.commit()
            logger.debug(f"Saved learning session: {session.session_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save learning session {session.session_id}: {str(e)}")
            raise
    
    def _save_learned_knowledge(self, proposals: List[ContentProposal]) -> None:
        """
        Save learned knowledge to database
        
        Args:
            proposals: List of approved content proposals
            
        Raises:
            Exception: If database operation fails
        """
        try:
            for proposal in proposals:
                knowledge = KnowledgeBase(
                    knowledge_id=f"KNOW_{proposal.proposal_id}",
                    title=proposal.title,
                    content=proposal.content,
                    source=proposal.source_name,
                    category=proposal.category,
                    confidence=proposal.quality_score,
                    learned_at=datetime.now()
                )
                self.db.add(knowledge)
            
            self.db.commit()
            logger.debug(f"Saved {len(proposals)} knowledge items")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save knowledge: {str(e)}")
            raise
    
    def get_evolution_status(self) -> Dict[str, Any]:
        """
        Get current evolution status
        
        Returns:
            Dict containing evolution status and recent sessions
        """
        try:
            stats = self.learning_engine.get_learning_stats()
            
            # Get recent sessions from DB
            recent_sessions = self.db.query(DBLearningSession).order_by(
                DBLearningSession.created_at.desc()
            ).limit(7).all()
            
            status = {
                **stats,
                "recent_sessions": [
                    {
                        "date": s.date,
                        "proposals_learned": s.proposals_learned,
                        "evolution_stage": s.evolution_stage,
                        "success": s.success
                    } for s in recent_sessions
                ],
                "total_sessions": self.db.query(DBLearningSession).count(),
                "success_rate": self._calculate_success_rate()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get evolution status: {str(e)}")
            return {"error": str(e)}
    
    def get_learning_history(self, days: int = LEARNING_HISTORY_DAYS) -> List[Dict[str, Any]]:
        """
        Get learning history for specified number of days
        
        Args:
            days: Number of days of history to retrieve
            
        Returns:
            List of learning session records
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            sessions = self.db.query(DBLearningSession).filter(
                DBLearningSession.created_at >= cutoff_date
            ).order_by(DBLearningSession.created_at.desc()).all()
            
            history = [
                {
                    "session_id": s.session_id,
                    "date": s.date,
                    "proposals_learned": s.proposals_learned,
                    "evolution_stage": s.evolution_stage,
                    "accuracy_delta": s.accuracy_delta,
                    "duration_minutes": s.duration_minutes,
                    "success": s.success,
                    "created_at": s.created_at
                }
                for s in sessions
            ]
            
            logger.info(f"Retrieved {len(history)} learning sessions from last {days} days")
            return history
            
        except Exception as e:
            logger.error(f"Failed to get learning history: {str(e)}")
            return []
    
    def get_evolution_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive evolution metrics
        
        Returns:
            Dict containing various evolution metrics
        """
        try:
            # Basic session metrics
            total_sessions = self.db.query(DBLearningSession).count()
            successful_sessions = self.db.query(DBLearningSession).filter(
                DBLearningSession.success == True
            ).count()
            
            # Knowledge metrics
            total_knowledge = self.db.query(KnowledgeBase).count()
            recent_knowledge = self.db.query(KnowledgeBase).filter(
                KnowledgeBase.learned_at >= datetime.now() - timedelta(days=7)
            ).count()
            
            # Stage progression - FIXED: Use current_stage property instead of get_current_stage()
            current_stage = self.learning_engine.current_stage  # ✅ ĐÃ SỬA
            stage_sessions = {}
            for stage in EvolutionStage:
                count = self.db.query(DBLearningSession).filter(
                    DBLearningSession.evolution_stage == stage.value
                ).count()
                stage_sessions[stage.value] = count
            
            metrics = {
                "total_sessions": total_sessions,
                "successful_sessions": successful_sessions,
                "success_rate": (successful_sessions / total_sessions * 100) if total_sessions > 0 else 0,
                "total_knowledge_items": total_knowledge,
                "recent_knowledge_items": recent_knowledge,
                "current_stage": current_stage.value,  # ✅ ĐÃ SỬA
                "stage_distribution": stage_sessions,
                "average_proposals_per_session": self._calculate_avg_proposals(),
                "learning_trend": self._calculate_learning_trend()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get evolution metrics: {str(e)}")
            return {"error": str(e)}
    
    def trigger_manual_learning(self, proposal_ids: List[str]) -> Dict[str, Any]:
        """
        Trigger manual learning for specific proposals
        
        Args:
            proposal_ids: List of proposal IDs to learn
            
        Returns:
            Dict containing learning results
        """
        try:
            # In a real implementation, you would fetch these proposals from database
            # For now, we'll simulate this
            logger.info(f"Triggering manual learning for {len(proposal_ids)} proposals")
            
            # This would be replaced with actual proposal fetching logic
            manual_proposals = [
                ContentProposal(
                    proposal_id=pid,
                    title=f"Manual Proposal {pid}",
                    content="Manual learning content",
                    source_name="manual",
                    category="manual",
                    quality_score=0.9
                )
                for pid in proposal_ids
            ]
            
            # Learn from manual proposals
            session = self.learning_engine.start_daily_learning_session([
                {
                    "title": p.title,
                    "content": p.content,
                    "quality_score": p.quality_score
                } for p in manual_proposals
            ])
            
            # Save results
            self._save_learning_session(session)
            self._save_learned_knowledge(manual_proposals)
            
            result = {
                "session_id": session.session_id,
                "proposals_learned": len(manual_proposals),
                "evolution_stage": session.evolution_stage.value,
                "success": True,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Manual learning completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Manual learning failed: {str(e)}")
            return {"error": str(e), "success": False}
    
    def get_pending_review_proposals(self) -> List[Dict[str, Any]]:
        """
        Get proposals that need manual review
        
        Returns:
            List of proposals pending review
        """
        try:
            # This would integrate with your actual review system
            # For now, return empty list as placeholder
            pending_proposals = []
            
            # In real implementation:
            # pending_proposals = self.db.query(Proposal).filter(
            #     Proposal.status == "pending_review"
            # ).all()
            
            logger.info(f"Found {len(pending_proposals)} proposals pending review")
            return [
                {
                    "proposal_id": p.proposal_id,
                    "title": p.title,
                    "category": p.category,
                    "confidence": getattr(p, 'quality_score', 0.5)
                }
                for p in pending_proposals
            ]
            
        except Exception as e:
            logger.error(f"Failed to get pending review proposals: {str(e)}")
            return []
    
    def _calculate_success_rate(self) -> float:
        """Calculate overall success rate of learning sessions"""
        try:
            total = self.db.query(DBLearningSession).count()
            if total == 0:
                return 0.0
                
            successful = self.db.query(DBLearningSession).filter(
                DBLearningSession.success == True
            ).count()
            
            return (successful / total) * 100
            
        except Exception as e:
            logger.error(f"Failed to calculate success rate: {str(e)}")
            return 0.0
    
    def _calculate_avg_proposals(self) -> float:
        """Calculate average proposals per session"""
        try:
            sessions = self.db.query(DBLearningSession).all()
            if not sessions:
                return 0.0
                
            total_proposals = sum(s.proposals_learned for s in sessions)
            return total_proposals / len(sessions)
            
        except Exception as e:
            logger.error(f"Failed to calculate average proposals: {str(e)}")
            return 0.0
    
    def _calculate_learning_trend(self) -> str:
        """
        Calculate learning trend (improving/stable/declining)
        
        Returns:
            Trend indicator string
        """
        try:
            recent_sessions = self.db.query(DBLearningSession).order_by(
                DBLearningSession.created_at.desc()
            ).limit(5).all()
            
            if len(recent_sessions) < 2:
                return "insufficient_data"
            
            # Compare last two sessions
            last_session = recent_sessions[0]
            previous_session = recent_sessions[1]
            
            if last_session.proposals_learned > previous_session.proposals_learned:
                return "improving"
            elif last_session.proposals_learned == previous_session.proposals_learned:
                return "stable"
            else:
                return "declining"
                
        except Exception as e:
            logger.error(f"Failed to calculate learning trend: {str(e)}")
            return "unknown"