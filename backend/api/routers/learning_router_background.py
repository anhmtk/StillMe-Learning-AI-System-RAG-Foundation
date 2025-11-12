"""
Background task implementation for non-blocking learning cycles
Extracted from learning_router.py for better organization
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any
from backend.api.job_queue import get_job_queue, JobStatus

logger = logging.getLogger(__name__)

# Feature flag check
ENABLE_CONTINUUM_MEMORY = os.getenv("ENABLE_CONTINUUM_MEMORY", "false").lower() == "true"


async def run_learning_cycle_background(job_id: str):
    """
    Background task to run learning cycle.
    Updates job status and progress as it runs.
    """
    job_queue = get_job_queue()
    job = job_queue.get_job(job_id)
    
    if not job:
        logger.error(f"Job {job_id} not found")
        return
    
    try:
        job.started_at = datetime.now()
        job.update_progress("fetching", entries_fetched=0)
        job.add_log("Starting learning cycle...")
        
        # Import from main module to avoid circular imports
        import backend.api.main as main_module
        
        learning_scheduler = main_module.learning_scheduler
        rss_fetch_history = main_module.rss_fetch_history
        rag_retrieval = main_module.rag_retrieval
        source_integration = main_module.source_integration
        content_curator = main_module.content_curator
        self_diagnosis = main_module.self_diagnosis
        
        if not learning_scheduler:
            raise Exception("Scheduler not available")
        
        # Phase 1: Fetching
        job.update_progress("fetching", entries_fetched=0)
        job.add_log("Fetching entries from all sources...")
        result = await learning_scheduler.run_learning_cycle()
        cycle_number = result.get("cycle_number", 0)
        
        # Initialize Tiered Update Isolation for Nested Learning
        update_isolation = None
        promotion_manager = None
        if ENABLE_CONTINUUM_MEMORY:
            try:
                from backend.learning.continuum_memory import TieredUpdateIsolation
                from backend.learning.promotion_manager import PromotionManager
                from backend.api.metrics_collector import get_metrics_collector
                update_isolation = TieredUpdateIsolation()
                promotion_manager = PromotionManager()
                metrics = get_metrics_collector()
                metrics.set_cycle_count(cycle_number)
                job.add_log(f"Nested Learning: Update isolation enabled (cycle #{cycle_number})")
            except Exception as e:
                logger.warning(f"Failed to initialize Nested Learning components: {e}")
                job.add_log(f"Warning: Update isolation not available: {e}")
        
        job.update_progress("fetching", entries_fetched=result.get("entries_fetched", 0))
        job.add_log(f"Fetched {result.get('entries_fetched', 0)} entries")
        
        # Create fetch cycle for tracking
        cycle_id = None
        if rss_fetch_history:
            cycle_id = rss_fetch_history.create_fetch_cycle(cycle_number=cycle_number)
        
        # Phase 2: Pre-filter
        if learning_scheduler.auto_add_to_rag and rag_retrieval:
            job.update_progress("prefilter", entries_filtered=0)
            job.add_log("Applying pre-filter to reduce costs...")
            
            entries_to_add = []
            filtered_count = 0
            
            try:
                if source_integration:
                    all_entries = source_integration.fetch_all_sources(
                        max_items_per_source=5,
                        use_pre_filter=False
                    )
                    job.add_log(f"Fetched {len(all_entries)} entries from all sources")
                    
                    # Count entries by source for detailed breakdown
                    source_counts = {}
                    for entry in all_entries:
                        source = entry.get("source", "unknown")
                        if "rss" in source.lower() or "feed" in source.lower():
                            source_counts["RSS"] = source_counts.get("RSS", 0) + 1
                        elif "arxiv" in source.lower():
                            source_counts["arXiv"] = source_counts.get("arXiv", 0) + 1
                        elif "crossref" in source.lower():
                            source_counts["CrossRef"] = source_counts.get("CrossRef", 0) + 1
                        elif "wikipedia" in source.lower():
                            source_counts["Wikipedia"] = source_counts.get("Wikipedia", 0) + 1
                        else:
                            source_counts[source] = source_counts.get(source, 0) + 1
                    
                    # Log breakdown by source
                    if source_counts:
                        breakdown = ", ".join([f"{source}: {count}" for source, count in source_counts.items()])
                        job.add_log(f"Source breakdown: {breakdown}")
                else:
                    all_entries = learning_scheduler.rss_fetcher.fetch_feeds(max_items_per_feed=5)
                    job.add_log(f"Fetched {len(all_entries)} entries from RSS")
                
                # Pre-filter
                if content_curator:
                    filtered_entries, rejected_entries = content_curator.pre_filter_content(all_entries)
                    filtered_count = len(rejected_entries)
                    job.update_progress("prefilter", entries_filtered=filtered_count)
                    job.add_log(f"Pre-filter: {len(filtered_entries)}/{len(all_entries)} passed. Rejected {filtered_count} items")
                    
                    # Log filter reasons breakdown
                    if rejected_entries:
                        reason_counts = {}
                        for rejected in rejected_entries:
                            reason = rejected.get("rejection_reason", "Unknown")
                            reason_counts[reason] = reason_counts.get(reason, 0) + 1
                        
                        if reason_counts:
                            reason_breakdown = ", ".join([f"{reason}: {count}" for reason, count in reason_counts.items()])
                            job.add_log(f"Filter reasons: {reason_breakdown}")
                    
                    all_entries = filtered_entries
                
                # Prioritize
                if content_curator and self_diagnosis:
                    recent_gaps = []
                    prioritized = content_curator.prioritize_learning_content(all_entries, knowledge_gaps=recent_gaps)
                    entries_to_add = prioritized[:min(5, len(prioritized))]
                else:
                    entries_to_add = all_entries[:min(10, len(all_entries))]
                
            except Exception as e:
                logger.error(f"Error preparing entries for RAG: {e}")
                job.add_log(f"Error preparing entries: {str(e)}")
                entries_to_add = []
            
            # Phase 3: Embedding and adding to RAG (with Nested Learning tiered update isolation)
            added_count = 0
            skipped_count = 0
            total_entries = len(entries_to_add)
            
            # Get PromotionManager for surprise score calculation
            promotion_manager = None
            if ENABLE_CONTINUUM_MEMORY:
                try:
                    from backend.learning.promotion_manager import PromotionManager
                    promotion_manager = PromotionManager()
                except Exception as e:
                    logger.warning(f"PromotionManager not available: {e}")
            
            for idx, entry in enumerate(entries_to_add):
                try:
                    job.update_progress(
                        "embedding",
                        entries_added=added_count,
                        current_item=entry.get('title', '')[:50]
                    )
                    job.add_log(f"Processing entry {idx + 1}/{total_entries}: {entry.get('title', '')[:50]}")
                    
                    content = f"{entry.get('title', '')}\n{entry.get('summary', '')}"
                    if not content.strip():
                        continue
                    
                    # Check duplicates
                    is_duplicate = False
                    try:
                        existing = rag_retrieval.retrieve_context(
                            query=entry.get('title', ''),
                            knowledge_limit=1,
                            conversation_limit=0
                        )
                        if existing.get("knowledge_docs"):
                            existing_doc = existing["knowledge_docs"][0]
                            existing_metadata = existing_doc.get("metadata", {})
                            if existing_metadata.get("link", "") == entry.get("link", ""):
                                is_duplicate = True
                    except Exception:
                        pass
                    
                    if is_duplicate:
                        continue
                    
                    # Nested Learning: Calculate surprise score and route to tier
                    tier = "L0"  # Default tier
                    surprise_score = 0.0
                    should_update = True
                    
                    if update_isolation and promotion_manager:
                        try:
                            # Generate item_id for this entry
                            import hashlib
                            item_id = hashlib.md5(content.encode()).hexdigest()
                            
                            # Calculate surprise score
                            surprise_score = promotion_manager.calculate_surprise_score(
                                item_id=item_id,
                                content=content,
                                existing_keywords=None,
                                centroid_embeddings=None
                            )
                            
                            # Route to tier based on surprise score
                            tier = update_isolation.get_tier_for_knowledge(item_id, surprise_score)
                            
                            # Check if tier should update at this cycle
                            should_update = update_isolation.should_update_tier(tier, cycle_number)
                            
                            if not should_update:
                                skipped_count += 1
                                # Track skipped metrics
                                from backend.api.metrics_collector import get_metrics_collector
                                metrics = get_metrics_collector()
                                metrics.increment_tier_skipped(tier)
                                job.add_log(
                                    f"Skipped entry (tier {tier}, cycle {cycle_number}, "
                                    f"surprise={surprise_score:.2f}): {entry.get('title', '')[:50]}"
                                )
                                continue
                            
                            job.add_log(
                                f"Entry routed to tier {tier} (surprise={surprise_score:.2f}): "
                                f"{entry.get('title', '')[:50]}"
                            )
                        except Exception as e:
                            logger.warning(f"Error in tiered routing: {e}")
                            # Fallback: continue with default behavior
                            should_update = True
                    
                    # Add to RAG
                    job.update_progress("adding_to_rag", entries_added=added_count)
                    importance_score = 0.5
                    if content_curator:
                        importance_score = content_curator.calculate_importance_score(entry)
                    
                    # Add tier and surprise score to metadata
                    metadata = {
                        "link": entry.get('link', ''),
                        "published": entry.get('published', ''),
                        "type": "rss_feed",
                        "scheduler_cycle": cycle_number,
                        "priority_score": entry.get("priority_score", 0.5),
                        "importance_score": importance_score,
                        "title": entry.get('title', '')[:200]
                    }
                    
                    if ENABLE_CONTINUUM_MEMORY:
                        metadata["tier"] = tier
                        metadata["surprise_score"] = surprise_score
                    
                    success = rag_retrieval.add_learning_content(
                        content=content,
                        source=entry.get('source', 'rss'),
                        content_type="knowledge",
                        metadata=metadata
                    )
                    
                    if success:
                        added_count += 1
                        job.update_progress("adding_to_rag", entries_added=added_count)
                        
                        # Update tier cycle tracking
                        if update_isolation and ENABLE_CONTINUUM_MEMORY:
                            try:
                                import hashlib
                                item_id = hashlib.md5(content.encode()).hexdigest()
                                update_isolation.update_tier_cycle(item_id, tier, cycle_number)
                                
                                # Track metrics for Nested Learning
                                from backend.api.metrics_collector import get_metrics_collector
                                metrics = get_metrics_collector()
                                metrics.increment_tier_update(tier)
                                metrics.increment_embedding_operation(tier)
                                metrics.add_surprise_score(surprise_score)
                            except Exception as e:
                                logger.debug(f"Error updating tier cycle: {e}")
                        else:
                            # Track embedding operation even without Nested Learning
                            from backend.api.metrics_collector import get_metrics_collector
                            metrics = get_metrics_collector()
                            metrics.increment_embedding_operation()
                    
                except Exception as e:
                    logger.error(f"Error adding entry to RAG: {e}")
                    job.add_log(f"Error adding entry: {str(e)[:100]}")
                    continue
            
            result["entries_added_to_rag"] = added_count
            result["entries_filtered"] = filtered_count
            if ENABLE_CONTINUUM_MEMORY:
                result["entries_skipped_tiered"] = skipped_count
                job.add_log(f"Nested Learning: Added {added_count} entries, skipped {skipped_count} (tiered update isolation)")
            
            # Add filter reasons if available from pre-filter
            if content_curator and hasattr(content_curator, 'last_filter_reasons'):
                result["filter_reasons"] = content_curator.last_filter_reasons
            
            if rss_fetch_history and cycle_id:
                rss_fetch_history.complete_fetch_cycle(cycle_id)
            
            job.add_log(f"Completed: Added {added_count} entries to RAG")
        
        # Mark as done
        job.status = JobStatus.DONE
        job.completed_at = datetime.now()
        job.result = result
        job.update_progress("done", entries_added=result.get("entries_added_to_rag", 0))
        job.add_log("Learning cycle completed successfully")
        
    except Exception as e:
        logger.error(f"Background learning cycle error: {e}", exc_info=True)
        job.status = JobStatus.ERROR
        job.completed_at = datetime.now()
        job.error = str(e)
        job.add_log(f"Error: {str(e)}")

