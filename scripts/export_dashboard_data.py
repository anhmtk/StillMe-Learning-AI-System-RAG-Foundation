"""
📊 StillMe IPC Dashboard Data Export
===================================

Exports learning data to JSON/CSV files for GitHub Pages dashboard.
Runs automatically to keep public dashboard updated.

Features:
- Export proposals data to JSON
- Export metrics to CSV
- Update evolution timeline
- Generate learning statistics
- Auto-commit to GitHub

Author: StillMe AI Framework
Version: 1.0.0
Date: 2025-09-29
"""

import os
import sys
import json
import csv
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from stillme_core.learning.proposals_manager import ProposalsManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DashboardDataExporter:
    """Export learning data for public dashboard"""

    def __init__(self):
        self.proposals_manager = ProposalsManager()
        self.docs_dir = project_root / "docs"
        self.docs_dir.mkdir(exist_ok=True)

    def export_proposals_data(self):
        """Export proposals data to JSON"""
        try:
            logger.info("📊 Exporting proposals data...")

            # Get all proposals
            proposals = self.proposals_manager.get_all_proposals()

            # Convert to JSON-serializable format
            proposals_data = []
            for proposal in proposals:
                proposal_dict = {
                    "id": proposal.id,
                    "title": proposal.title,
                    "description": proposal.description,
                    "status": proposal.status,
                    "priority": proposal.priority.value if hasattr(proposal.priority, 'value') else str(proposal.priority),
                    "source": proposal.source.value if hasattr(proposal.source, 'value') else str(proposal.source),
                    "quality_score": proposal.quality_score,
                    "estimated_duration": proposal.estimated_duration,
                    "created_at": proposal.created_at.isoformat() if proposal.created_at else None,
                    "approved_at": getattr(proposal, 'approved_at', None).isoformat() if getattr(proposal, 'approved_at', None) else None,
                    "created_by": getattr(proposal, 'created_by', 'system')
                }
                proposals_data.append(proposal_dict)

            # Save to JSON file
            proposals_file = self.docs_dir / "proposals_data.json"
            with open(proposals_file, 'w', encoding='utf-8') as f:
                json.dump(proposals_data, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Exported {len(proposals_data)} proposals to {proposals_file}")
            return proposals_data

        except Exception as e:
            logger.error(f"❌ Failed to export proposals data: {e}")
            return []

    def export_metrics_data(self):
        """Export learning metrics to CSV"""
        try:
            logger.info("📈 Exporting metrics data...")

            # Get proposals for metrics calculation
            proposals = self.proposals_manager.get_all_proposals()

            # Calculate daily metrics for last 30 days
            metrics_data = []
            today = datetime.now().date()

            for i in range(30):
                date = today - timedelta(days=i)
                date_str = date.isoformat()

                # Filter proposals for this date
                daily_proposals = [
                    p for p in proposals
                    if p.created_at and p.created_at.date() == date
                ]

                # Calculate metrics
                total_proposals = len(daily_proposals)
                approved_proposals = len([p for p in daily_proposals if p.status == 'approved'])
                completed_proposals = len([p for p in daily_proposals if p.status == 'completed'])
                pending_proposals = len([p for p in daily_proposals if p.status == 'pending'])

                # Calculate quality score average
                quality_scores = [p.quality_score for p in daily_proposals if p.quality_score]
                avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

                metrics_data.append({
                    "date": date_str,
                    "total": total_proposals,
                    "approved": approved_proposals,
                    "completed": completed_proposals,
                    "pending": pending_proposals,
                    "avg_quality": round(avg_quality, 2)
                })

            # Save to CSV file
            metrics_file = self.docs_dir / "learning_metrics.csv"
            with open(metrics_file, 'w', newline='', encoding='utf-8') as f:
                if metrics_data:
                    writer = csv.DictWriter(f, fieldnames=metrics_data[0].keys())
                    writer.writeheader()
                    writer.writerows(metrics_data)

            logger.info(f"✅ Exported metrics data to {metrics_file}")
            return metrics_data

        except Exception as e:
            logger.error(f"❌ Failed to export metrics data: {e}")
            return []

    def update_evolution_timeline(self):
        """Update evolution timeline with current stats"""
        try:
            logger.info("🚀 Updating evolution timeline...")

            timeline_file = self.docs_dir / "evolution_timeline.json"

            # Load existing timeline
            if timeline_file.exists():
                with open(timeline_file, 'r', encoding='utf-8') as f:
                    timeline_data = json.load(f)
            else:
                timeline_data = {
                    "events": [],
                    "milestones": [],
                    "learning_sources": [],
                    "current_stats": {}
                }

            # Update current stats
            proposals = self.proposals_manager.get_all_proposals()
            timeline_data["current_stats"] = {
                "total_proposals": len(proposals),
                "approved_proposals": len([p for p in proposals if p.status == 'approved']),
                "completed_learning": len([p for p in proposals if p.status == 'completed']),
                "knowledge_sources": len(set(p.source.value if hasattr(p.source, 'value') else str(p.source) for p in proposals)),
                "learning_sessions_today": len([p for p in proposals if p.created_at and p.created_at.date() == datetime.now().date()]),
                "last_discovery": datetime.now().isoformat()
            }

            # Save updated timeline
            with open(timeline_file, 'w', encoding='utf-8') as f:
                json.dump(timeline_data, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Updated evolution timeline: {timeline_data['current_stats']}")
            return timeline_data

        except Exception as e:
            logger.error(f"❌ Failed to update evolution timeline: {e}")
            return {}

    def export_all_data(self):
        """Export all dashboard data"""
        try:
            logger.info("📊 Starting dashboard data export...")

            # Export all data
            proposals_data = self.export_proposals_data()
            metrics_data = self.export_metrics_data()
            timeline_data = self.update_evolution_timeline()

            # Create summary
            summary = {
                "export_timestamp": datetime.now().isoformat(),
                "proposals_count": len(proposals_data),
                "metrics_days": len(metrics_data),
                "current_stats": timeline_data.get("current_stats", {})
            }

            # Save summary
            summary_file = self.docs_dir / "export_summary.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)

            logger.info("🎉 Dashboard data export completed!")
            logger.info(f"📊 Summary: {summary}")

            return summary

        except Exception as e:
            logger.error(f"❌ Failed to export dashboard data: {e}")
            return {}

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Export StillMe IPC dashboard data")
    parser.add_argument("--type", choices=["all", "proposals", "metrics", "timeline"],
                       default="all", help="Type of data to export")

    args = parser.parse_args()

    exporter = DashboardDataExporter()

    if args.type == "all":
        exporter.export_all_data()
    elif args.type == "proposals":
        exporter.export_proposals_data()
    elif args.type == "metrics":
        exporter.export_metrics_data()
    elif args.type == "timeline":
        exporter.update_evolution_timeline()

if __name__ == "__main__":
    main()
