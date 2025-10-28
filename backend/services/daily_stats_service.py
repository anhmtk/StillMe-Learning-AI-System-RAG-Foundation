"""
Daily Learning Statistics Service for StillMe V2
Manages historical learning data for analytics and comparison
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from ..database.schema import DailyLearningStats, LearningSession, Proposal
from ..services.rss_pipeline import get_pipeline_instance

logger = logging.getLogger(__name__)


class DailyLearningStatsService:
    """Service for managing daily learning statistics"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def update_today_stats(self) -> Dict[str, Any]:
        """Update today's learning statistics"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Get current pipeline stats
            pipeline = get_pipeline_instance()
            pipeline_stats = pipeline.get_pipeline_stats()
            
            # Get today's proposals
            today_proposals = self.db.query(Proposal).filter(
                func.date(Proposal.created_at) == today
            ).all()
            
            # Get today's learning sessions
            today_sessions = self.db.query(LearningSession).filter(
                LearningSession.date == today
            ).all()
            
            # Calculate metrics
            proposals_generated = len(today_proposals)
            proposals_approved = len([p for p in today_proposals if p.status == "approved"])
            proposals_pending = len([p for p in today_proposals if p.status == "pending"])
            
            # Calculate average scores
            if today_proposals:
                avg_quality = sum(p.quality_score for p in today_proposals) / len(today_proposals)
                avg_relevance = sum(p.relevance_score for p in today_proposals) / len(today_proposals)
                avg_novelty = sum(p.novelty_score for p in today_proposals) / len(today_proposals)
            else:
                avg_quality = avg_relevance = avg_novelty = 0.0
            
            # Calculate learning efficiency
            content_fetched = pipeline_stats.get("fetched_content_count", 0)
            learning_efficiency = (proposals_generated / content_fetched * 100) if content_fetched > 0 else 0.0
            
            # Get evolution stage (from latest session)
            evolution_stage = "infant"
            if today_sessions:
                latest_session = max(today_sessions, key=lambda s: s.created_at)
                evolution_stage = latest_session.evolution_stage
            
            # Calculate session metrics
            successful_sessions = len([s for s in today_sessions if s.success])
            total_duration = sum(s.duration_minutes for s in today_sessions)
            
            # Create or update daily stats
            daily_stats = self.db.query(DailyLearningStats).filter(
                DailyLearningStats.date == today
            ).first()
            
            if daily_stats:
                # Update existing record
                daily_stats.content_fetched = content_fetched
                daily_stats.content_sources = pipeline_stats.get("enabled_sources", 0)
                daily_stats.proposals_generated = proposals_generated
                daily_stats.proposals_approved = proposals_approved
                daily_stats.proposals_pending = proposals_pending
                daily_stats.avg_quality_score = avg_quality
                daily_stats.avg_relevance_score = avg_relevance
                daily_stats.avg_novelty_score = avg_novelty
                daily_stats.learning_efficiency = learning_efficiency
                daily_stats.evolution_stage = evolution_stage
                daily_stats.learning_sessions_count = len(today_sessions)
                daily_stats.successful_sessions = successful_sessions
                daily_stats.total_duration_minutes = total_duration
                daily_stats.updated_at = datetime.utcnow()
            else:
                # Create new record
                daily_stats = DailyLearningStats(
                    date=today,
                    content_fetched=content_fetched,
                    content_sources=pipeline_stats.get("enabled_sources", 0),
                    proposals_generated=proposals_generated,
                    proposals_approved=proposals_approved,
                    proposals_pending=proposals_pending,
                    avg_quality_score=avg_quality,
                    avg_relevance_score=avg_relevance,
                    avg_novelty_score=avg_novelty,
                    learning_efficiency=learning_efficiency,
                    evolution_stage=evolution_stage,
                    learning_sessions_count=len(today_sessions),
                    successful_sessions=successful_sessions,
                    total_duration_minutes=total_duration
                )
                self.db.add(daily_stats)
            
            self.db.commit()
            
            logger.info(f"✅ Updated daily learning stats for {today}")
            
            return {
                "date": today,
                "content_fetched": content_fetched,
                "proposals_generated": proposals_generated,
                "proposals_approved": proposals_approved,
                "learning_efficiency": learning_efficiency,
                "evolution_stage": evolution_stage,
                "successful_sessions": successful_sessions
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to update daily stats: {e}")
            self.db.rollback()
            raise e
    
    def get_historical_stats(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get learning statistics for a date range"""
        try:
            stats = self.db.query(DailyLearningStats).filter(
                DailyLearningStats.date >= start_date,
                DailyLearningStats.date <= end_date
            ).order_by(DailyLearningStats.date.desc()).all()
            
            result = []
            for stat in stats:
                result.append({
                    "date": stat.date,
                    "content_fetched": stat.content_fetched,
                    "content_sources": stat.content_sources,
                    "proposals_generated": stat.proposals_generated,
                    "proposals_approved": stat.proposals_approved,
                    "proposals_pending": stat.proposals_pending,
                    "avg_quality_score": stat.avg_quality_score,
                    "avg_relevance_score": stat.avg_relevance_score,
                    "avg_novelty_score": stat.avg_novelty_score,
                    "learning_efficiency": stat.learning_efficiency,
                    "evolution_stage": stat.evolution_stage,
                    "learning_sessions_count": stat.learning_sessions_count,
                    "successful_sessions": stat.successful_sessions,
                    "total_duration_minutes": stat.total_duration_minutes,
                    "created_at": stat.created_at.isoformat() if stat.created_at else None,
                    "updated_at": stat.updated_at.isoformat() if stat.updated_at else None
                })
            
            logger.info(f"📊 Retrieved {len(result)} historical stats from {start_date} to {end_date}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to get historical stats: {e}")
            raise e
    
    def get_comparison_stats(self, current_date: str, compare_date: str) -> Dict[str, Any]:
        """Get comparison between two dates"""
        try:
            current_stats = self.db.query(DailyLearningStats).filter(
                DailyLearningStats.date == current_date
            ).first()
            
            compare_stats = self.db.query(DailyLearningStats).filter(
                DailyLearningStats.date == compare_date
            ).first()
            
            if not current_stats:
                return {"error": f"No stats found for {current_date}"}
            
            if not compare_stats:
                return {"error": f"No stats found for {compare_date}"}
            
            # Calculate differences
            comparison = {
                "current_date": current_date,
                "compare_date": compare_date,
                "content_fetched": {
                    "current": current_stats.content_fetched,
                    "compare": compare_stats.content_fetched,
                    "delta": current_stats.content_fetched - compare_stats.content_fetched,
                    "delta_percent": ((current_stats.content_fetched - compare_stats.content_fetched) / compare_stats.content_fetched * 100) if compare_stats.content_fetched > 0 else 0
                },
                "proposals_generated": {
                    "current": current_stats.proposals_generated,
                    "compare": compare_stats.proposals_generated,
                    "delta": current_stats.proposals_generated - compare_stats.proposals_generated,
                    "delta_percent": ((current_stats.proposals_generated - compare_stats.proposals_generated) / compare_stats.proposals_generated * 100) if compare_stats.proposals_generated > 0 else 0
                },
                "learning_efficiency": {
                    "current": current_stats.learning_efficiency,
                    "compare": compare_stats.learning_efficiency,
                    "delta": current_stats.learning_efficiency - compare_stats.learning_efficiency,
                    "delta_percent": ((current_stats.learning_efficiency - compare_stats.learning_efficiency) / compare_stats.learning_efficiency * 100) if compare_stats.learning_efficiency > 0 else 0
                },
                "avg_quality_score": {
                    "current": current_stats.avg_quality_score,
                    "compare": compare_stats.avg_quality_score,
                    "delta": current_stats.avg_quality_score - compare_stats.avg_quality_score,
                    "delta_percent": ((current_stats.avg_quality_score - compare_stats.avg_quality_score) / compare_stats.avg_quality_score * 100) if compare_stats.avg_quality_score > 0 else 0
                },
                "successful_sessions": {
                    "current": current_stats.successful_sessions,
                    "compare": compare_stats.successful_sessions,
                    "delta": current_stats.successful_sessions - compare_stats.successful_sessions,
                    "delta_percent": ((current_stats.successful_sessions - compare_stats.successful_sessions) / compare_stats.successful_sessions * 100) if compare_stats.successful_sessions > 0 else 0
                }
            }
            
            logger.info(f"📈 Generated comparison between {current_date} and {compare_date}")
            return comparison
            
        except Exception as e:
            logger.error(f"❌ Failed to get comparison stats: {e}")
            raise e
    
    def get_learning_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get learning trends over the last N days"""
        try:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            stats = self.get_historical_stats(start_date, end_date)
            
            if not stats:
                return {"error": "No historical data available"}
            
            # Calculate trends
            total_content = sum(s["content_fetched"] for s in stats)
            total_proposals = sum(s["proposals_generated"] for s in stats)
            avg_efficiency = sum(s["learning_efficiency"] for s in stats) / len(stats) if stats else 0
            avg_quality = sum(s["avg_quality_score"] for s in stats) / len(stats) if stats else 0
            
            # Calculate growth rates
            if len(stats) >= 2:
                first_week = stats[-7:] if len(stats) >= 7 else stats[-len(stats)//2:]
                last_week = stats[:7] if len(stats) >= 7 else stats[:len(stats)//2]
                
                first_week_avg = sum(s["content_fetched"] for s in first_week) / len(first_week)
                last_week_avg = sum(s["content_fetched"] for s in last_week) / len(last_week)
                
                growth_rate = ((last_week_avg - first_week_avg) / first_week_avg * 100) if first_week_avg > 0 else 0
            else:
                growth_rate = 0
            
            trends = {
                "period": f"{days} days",
                "start_date": start_date,
                "end_date": end_date,
                "total_days": len(stats),
                "total_content_fetched": total_content,
                "total_proposals_generated": total_proposals,
                "average_learning_efficiency": avg_efficiency,
                "average_quality_score": avg_quality,
                "growth_rate_percent": growth_rate,
                "daily_averages": {
                    "content_per_day": total_content / len(stats) if stats else 0,
                    "proposals_per_day": total_proposals / len(stats) if stats else 0,
                    "efficiency_per_day": avg_efficiency
                },
                "evolution_stages": list(set(s["evolution_stage"] for s in stats)),
                "best_day": max(stats, key=lambda s: s["content_fetched"]) if stats else None,
                "most_efficient_day": max(stats, key=lambda s: s["learning_efficiency"]) if stats else None
            }
            
            logger.info(f"📊 Generated learning trends for {days} days")
            return trends
            
        except Exception as e:
            logger.error(f"❌ Failed to get learning trends: {e}")
            raise e


# Global instance
daily_stats_service = None

def get_daily_stats_service(db_session: Session) -> DailyLearningStatsService:
    """Get or create daily stats service instance"""
    global daily_stats_service
    if daily_stats_service is None:
        daily_stats_service = DailyLearningStatsService(db_session)
    return daily_stats_service
