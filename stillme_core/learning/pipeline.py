"""
StillMe Learning Pipeline
Main pipeline for content discovery, scoring, approval, and ingestion.
"""

import logging
import argparse
import sys
from typing import List, Optional, Dict, Any
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from stillme_core.learning.fetcher.rss_fetch import fetch_content_from_sources
from stillme_core.learning.parser.normalize import normalize_content_batch
from stillme_core.learning.gates.license_gate import validate_content_licenses
from stillme_core.learning.risk.injection_scan import assess_content_risks
from stillme_core.learning.score.quality import score_content_quality_batch
from stillme_core.learning.dedupe.novelty import check_content_novelty, add_content_to_index
from stillme_core.learning.approve.queue import add_to_approval_queue, get_approval_queue
from stillme_core.learning.ingest.vector_store import add_content_to_vector_store
from stillme_core.learning.ingest.claims_store import ingest_content_claims
from stillme_core.learning.reports.digest import save_daily_reports

log = logging.getLogger(__name__)

class LearningPipeline:
    """Main learning pipeline orchestrator."""
    
    def __init__(self):
        self.approval_queue = get_approval_queue()
        log.info("Learning pipeline initialized")
    
    def scan_content(self, sources: Optional[List[str]] = None, 
                    category: Optional[str] = None) -> Dict[str, Any]:
        """Scan content from sources and process through pipeline."""
        log.info("Starting content scan...")
        
        # Step 1: Fetch content
        log.info("Fetching content from sources...")
        raw_content = fetch_content_from_sources(sources, category)
        log.info(f"Fetched {len(raw_content)} raw content items")
        
        if not raw_content:
            log.warning("No content fetched from sources")
            return {
                'status': 'success',
                'message': 'No content found to process',
                'stats': {
                    'fetched': 0,
                    'normalized': 0,
                    'license_passed': 0,
                    'risk_passed': 0,
                    'quality_scored': 0,
                    'novelty_checked': 0,
                    'queued': 0
                }
            }
        
        # Step 2: Normalize content
        log.info("Normalizing content...")
        normalized_content = normalize_content_batch(raw_content)
        log.info(f"Normalized {len(normalized_content)} content items")
        
        # Step 3: License validation
        log.info("Validating licenses...")
        license_decisions = validate_content_licenses(normalized_content)
        license_passed = [content for content, decision in zip(normalized_content, license_decisions) 
                         if decision.allowed]
        log.info(f"License validation: {len(license_passed)}/{len(normalized_content)} passed")
        
        # Step 4: Risk assessment
        log.info("Assessing risks...")
        risk_assessments = assess_content_risks(license_passed)
        risk_passed = [content for content, assessment in zip(license_passed, risk_assessments) 
                      if assessment.safe]
        log.info(f"Risk assessment: {len(risk_passed)}/{len(license_passed)} passed")
        
        # Step 5: Quality scoring
        log.info("Scoring content quality...")
        quality_scores = score_content_quality_batch(risk_passed)
        log.info(f"Quality scored for {len(quality_scores)} items")
        
        # Step 6: Novelty checking
        log.info("Checking content novelty...")
        queued_items = []
        
        for content, quality_score in zip(risk_passed, quality_scores):
            # Check novelty
            novelty_result = check_content_novelty(content)
            
            # Add to approval queue
            item_id = add_to_approval_queue(
                content=content,
                quality_score=quality_score,
                license_decision=license_decisions[normalized_content.index(content)],
                risk_assessment=risk_assessments[license_passed.index(content)],
                novelty_score=novelty_result.novelty_score
            )
            
            queued_items.append({
                'id': item_id,
                'title': content.title,
                'quality_score': quality_score.overall_score,
                'novelty_score': novelty_result.novelty_score,
                'is_novel': novelty_result.is_novel
            })
        
        log.info(f"Added {len(queued_items)} items to approval queue")
        
        # Step 7: Generate reports
        log.info("Generating daily reports...")
        digest_file, metrics_file = save_daily_reports()
        
        return {
            'status': 'success',
            'message': f'Content scan completed successfully',
            'stats': {
                'fetched': len(raw_content),
                'normalized': len(normalized_content),
                'license_passed': len(license_passed),
                'risk_passed': len(risk_passed),
                'quality_scored': len(quality_scores),
                'novelty_checked': len(queued_items),
                'queued': len(queued_items)
            },
            'queued_items': queued_items,
            'reports': {
                'digest': digest_file,
                'metrics': metrics_file
            }
        }
    
    def approve_item(self, item_id: str, approved_by: str = "cli-user") -> Dict[str, Any]:
        """Approve an item for ingestion."""
        log.info(f"Approving item: {item_id}")
        
        success = self.approval_queue.approve_item(item_id, approved_by)
        
        if success:
            # Get the approved item
            item = self.approval_queue.get_item(item_id)
            if item:
                # Ingest the content
                log.info(f"Ingesting approved content: {item.content.title}")
                
                # Add to vector store
                vector_ids = add_content_to_vector_store(item.content)
                
                # Add to claims store
                total_claims, added_claims = ingest_content_claims(item.content)
                
                return {
                    'status': 'success',
                    'message': f'Item approved and ingested successfully',
                    'item_id': item_id,
                    'title': item.content.title,
                    'vector_chunks': len(vector_ids),
                    'claims_extracted': total_claims,
                    'claims_added': added_claims
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Approved item not found'
                }
        else:
            return {
                'status': 'error',
                'message': f'Failed to approve item: {item_id}'
            }
    
    def reject_item(self, item_id: str, reason: str, rejected_by: str = "cli-user") -> Dict[str, Any]:
        """Reject an item."""
        log.info(f"Rejecting item: {item_id} - {reason}")
        
        success = self.approval_queue.reject_item(item_id, rejected_by, reason)
        
        if success:
            return {
                'status': 'success',
                'message': f'Item rejected successfully',
                'item_id': item_id,
                'reason': reason
            }
        else:
            return {
                'status': 'error',
                'message': f'Failed to reject item: {item_id}'
            }
    
    def ingest_item(self, item_id: str) -> Dict[str, Any]:
        """Ingest an approved item."""
        log.info(f"Ingesting item: {item_id}")
        
        item = self.approval_queue.get_item(item_id)
        if not item:
            return {
                'status': 'error',
                'message': f'Item not found: {item_id}'
            }
        
        if item.status != 'approved':
            return {
                'status': 'error',
                'message': f'Item not approved: {item.status}'
            }
        
        # Add to vector store
        vector_ids = add_content_to_vector_store(item.content)
        
        # Add to claims store
        total_claims, added_claims = ingest_content_claims(item.content)
        
        return {
            'status': 'success',
            'message': f'Item ingested successfully',
            'item_id': item_id,
            'title': item.content.title,
            'vector_chunks': len(vector_ids),
            'claims_extracted': total_claims,
            'claims_added': added_claims
        }
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get approval queue status."""
        stats = self.approval_queue.get_statistics()
        pending_items = self.approval_queue.get_pending_items(limit=10)
        top_recommendations = self.approval_queue.get_top_recommendations(limit=5)
        
        return {
            'status': 'success',
            'queue_stats': stats,
            'pending_items': [
                {
                    'id': item.id,
                    'title': item.content.title,
                    'quality_score': item.quality_score.overall_score,
                    'novelty_score': item.novelty_score,
                    'recommendation': item.recommendation
                }
                for item in pending_items
            ],
            'top_recommendations': [
                {
                    'id': item.id,
                    'title': item.content.title,
                    'quality_score': item.quality_score.overall_score,
                    'novelty_score': item.novelty_score,
                    'recommendation': item.recommendation
                }
                for item in top_recommendations
            ]
        }

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="StillMe Learning Pipeline CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --scan                           # Scan all sources
  %(prog)s --scan --sources "arXiv AI Papers"  # Scan specific source
  %(prog)s --scan --category academic       # Scan by category
  %(prog)s --approve <item_id>              # Approve item
  %(prog)s --reject <item_id> --reason "Low quality"  # Reject item
  %(prog)s --ingest <item_id>               # Ingest approved item
  %(prog)s --status                         # Show queue status
        """
    )
    
    # Action arguments (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument("--scan", action="store_true", 
                             help="Scan content from sources")
    action_group.add_argument("--approve", metavar="ITEM_ID", 
                             help="Approve item for ingestion")
    action_group.add_argument("--reject", metavar="ITEM_ID", 
                             help="Reject item")
    action_group.add_argument("--ingest", metavar="ITEM_ID", 
                             help="Ingest approved item")
    action_group.add_argument("--status", action="store_true", 
                             help="Show approval queue status")
    
    # Scan options
    parser.add_argument("--sources", nargs="+", 
                       help="Specific sources to scan")
    parser.add_argument("--category", 
                       help="Category to scan (academic, industry, technical, ethics)")
    parser.add_argument("--actor", default="cli-user", 
                       help="Actor performing the action")
    parser.add_argument("--reason", 
                       help="Reason for rejection")
    parser.add_argument("--json", action="store_true", 
                       help="Output in JSON format")
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = LearningPipeline()
    
    try:
        if args.scan:
            result = pipeline.scan_content(args.sources, args.category)
            
        elif args.approve:
            result = pipeline.approve_item(args.approve, args.actor)
            
        elif args.reject:
            if not args.reason:
                print("❌ Error: --reason required for rejection")
                sys.exit(1)
            result = pipeline.reject_item(args.reject, args.reason, args.actor)
            
        elif args.ingest:
            result = pipeline.ingest_item(args.ingest)
            
        elif args.status:
            result = pipeline.get_queue_status()
        
        # Output result
        if args.json:
            import json
            print(json.dumps(result, indent=2))
        else:
            if result['status'] == 'success':
                print(f"✅ {result['message']}")
                
                if 'stats' in result:
                    stats = result['stats']
                    print(f"📊 Stats: {stats['fetched']} fetched, {stats['queued']} queued")
                
                if 'queued_items' in result:
                    print(f"📋 Queued items:")
                    for item in result['queued_items'][:5]:  # Show top 5
                        print(f"  - {item['title'][:50]}... (Q:{item['quality_score']:.2f}, N:{item['novelty_score']:.2f})")
                
                if 'reports' in result:
                    print(f"📄 Reports generated:")
                    print(f"  - {result['reports']['digest']}")
                    print(f"  - {result['reports']['metrics']}")
                
                if 'queue_stats' in result:
                    stats = result['queue_stats']
                    print(f"📊 Queue: {stats['pending_items']} pending, {stats['approved_items']} approved")
                
                if 'pending_items' in result:
                    print(f"📋 Pending items:")
                    for item in result['pending_items'][:5]:
                        print(f"  - {item['title'][:50]}... (Q:{item['quality_score']:.2f})")
                
                if 'top_recommendations' in result:
                    print(f"⭐ Top recommendations:")
                    for item in result['top_recommendations']:
                        print(f"  - {item['title'][:50]}... (Q:{item['quality_score']:.2f})")
            else:
                print(f"❌ {result['message']}")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.json:
            import json
            print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
