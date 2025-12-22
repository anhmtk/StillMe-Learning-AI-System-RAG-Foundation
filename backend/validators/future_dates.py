"""
Future Dates Validator - Blocks responses containing future dates/timestamps
"""

import re
import logging
from datetime import datetime
from typing import Optional, List, Any, Dict
from .base import Validator, ValidationResult

logger = logging.getLogger(__name__)


class FutureDatesValidator(Validator):
    """
    Validator that detects and blocks responses containing future dates/timestamps.
    
    This prevents StillMe from hallucinating dates in the future (e.g., "2026", "2025-12-23" when current date is 2025-12-22).
    """
    
    def __init__(self):
        super().__init__()
        self.name = "FutureDatesValidator"
        self.priority = 3  # High priority - should run early to catch hallucinations
        
    def run(self, answer: str, ctx_docs: List[str] = None, 
                 user_question: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Validate that answer does not contain future dates/timestamps.
        
        Args:
            answer: The answer to validate
            ctx_docs: Context documents (not used for this validator)
            user_question: User's question (optional)
            context: Additional context (optional)
            
        Returns:
            ValidationResult indicating if future dates were detected
        """
        if not answer:
            return ValidationResult(
                passed=True,
                reasons=["empty_answer"]
            )
        
        # Get current date/time
        current_time = datetime.now()
        current_year = current_time.year
        current_month = current_time.month
        current_day = current_time.day
        
        # Patterns to detect dates
        date_patterns = [
            # YYYY-MM-DD format
            r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b',
            # DD/MM/YYYY or MM/DD/YYYY format
            r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',
            # DD-MM-YYYY format
            r'\b(\d{1,2})-(\d{1,2})-(\d{4})\b',
            # YYYY/MM/DD format
            r'\b(\d{4})/(\d{1,2})/(\d{1,2})\b',
            # Year only (4 digits)
            r'\b(20\d{2})\b',  # Matches 2000-2099
        ]
        
        future_dates_found = []
        answer_lower = answer.lower()
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, answer)
            for match in matches:
                try:
                    # Try to parse the date
                    date_str = match.group(0)
                    
                    # Handle different formats
                    if '-' in date_str and len(date_str.split('-')) == 3:
                        # YYYY-MM-DD or DD-MM-YYYY
                        parts = date_str.split('-')
                        if len(parts[0]) == 4:  # YYYY-MM-DD
                            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                        else:  # DD-MM-YYYY
                            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                    elif '/' in date_str and len(date_str.split('/')) == 3:
                        # YYYY/MM/DD or DD/MM/YYYY or MM/DD/YYYY
                        parts = date_str.split('/')
                        if len(parts[0]) == 4:  # YYYY/MM/DD
                            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                        elif len(parts[2]) == 4:  # DD/MM/YYYY or MM/DD/YYYY
                            # Try DD/MM/YYYY first (more common internationally)
                            try:
                                day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                                # Validate: if day > 12, it's definitely DD/MM/YYYY
                                if day > 12:
                                    pass  # Already correct
                                elif month > 12:
                                    # Swap: it's MM/DD/YYYY
                                    month, day = day, month
                            except:
                                # Fallback: assume DD/MM/YYYY
                                day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                        else:
                            continue  # Skip if can't determine format
                    elif re.match(r'^\d{4}$', date_str):
                        # Year only
                        year = int(date_str)
                        month = 1
                        day = 1
                    else:
                        continue
                    
                    # Validate date
                    if month < 1 or month > 12 or day < 1 or day > 31:
                        continue
                    
                    # Check if date is in the future
                    try:
                        parsed_date = datetime(year, month, day)
                        if parsed_date > current_time:
                            future_dates_found.append({
                                "date": date_str,
                                "parsed": parsed_date.strftime("%Y-%m-%d"),
                                "current": current_time.strftime("%Y-%m-%d"),
                                "position": match.start()
                            })
                    except ValueError:
                        # Invalid date (e.g., Feb 30) - skip
                        continue
                        
                except (ValueError, IndexError) as e:
                    # Failed to parse date - skip
                    logger.debug(f"Failed to parse date '{match.group(0)}': {e}")
                    continue
        
        if future_dates_found:
            # CRITICAL: Future dates detected - this is a hallucination
            logger.warning(
                f"🚨 FutureDatesValidator: Detected {len(future_dates_found)} future date(s) in response: "
                f"{[fd['date'] for fd in future_dates_found]}"
            )
            
            # Build patched answer by removing or correcting future dates
            patched_answer = answer
            # Sort by position (descending) to replace from end to start
            for fd in sorted(future_dates_found, key=lambda x: x['position'], reverse=True):
                # Replace future date with current date or remove it
                # For now, we'll mark it for removal in post-processing
                # The actual patching should be done by the LLM rewrite
                pass
            
            return ValidationResult(
                passed=False,
                reasons=["future_dates_detected"],
                warnings=[f"Future date detected: {fd['date']} (current: {fd['current']})" for fd in future_dates_found],
                patched_answer=None,  # Let LLM rewrite handle this
                requires_rewrite=True
            )
        
        return ValidationResult(
            passed=True,
            reasons=["no_future_dates"]
        )

