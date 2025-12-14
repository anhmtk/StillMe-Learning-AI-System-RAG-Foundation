"""
StepDetector - Detects and parses multi-step reasoning from responses
Inspired by SSR (Socratic Self-Refine) for step-level validation
"""

import re
import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Step:
    """Represents a single step in a multi-step response"""
    step_number: int
    content: str
    original_text: str  # Full text including "Bước 1:" prefix
    start_pos: int      # Position in original response
    end_pos: int


class StepDetector:
    """Detects and parses multi-step reasoning from responses"""
    
    def __init__(self):
        """Initialize step detector"""
        logger.info("StepDetector initialized")
    
    def is_multi_step(self, response: str) -> bool:
        """
        Quick check if response contains multi-step reasoning
        
        Args:
            response: The response text to check
            
        Returns:
            True if response likely contains steps, False otherwise
        """
        if not response or len(response.strip()) < 20:
            return False
        
        # Quick pattern matching for common step indicators
        # PHASE 2 FIX: Add more patterns to detect numbered lists with dashes/bullets
        step_indicators = [
            r"Bước\s+\d+",      # Vietnamese: "Bước 1", "Bước 2"
            r"Step\s+\d+",      # English: "Step 1", "Step 2"
            r"(?:^|\n)\s*\d+\.\s+",  # Numbered: "1.", "2." (at start of line or after newline)
            r"(?:^|\n)\s*-\s+.*?:\s*",  # Bullet with colon: "- Tính Chính Xác:", "- Tính Tốc Độ:"
            r"(?:^|\n)\s*\*\*.*?\*\*:\s*",  # Bold header with colon: "**Tính Chính Xác:**"
        ]
        
        for pattern in step_indicators:
            matches = re.findall(pattern, response, re.MULTILINE | re.IGNORECASE)
            if len(matches) >= 2:  # At least 2 steps
                logger.info(f"✅ Multi-step detected via pattern '{pattern}': {len(matches)} matches")
                return True
        
        logger.info(f"❌ Not detected as multi-step (response length: {len(response)}, checked {len(step_indicators)} patterns)")
        return False
    
    def detect_steps(self, response: str) -> List[Step]:
        """
        Detect and parse steps from response
        
        Supports multiple formats:
        - Vietnamese: "Bước 1:", "Bước 2:"
        - English: "Step 1:", "Step 2:"
        - Numbered lists: "1.", "2."
        
        Args:
            response: The response text to parse
            
        Returns:
            List of Step objects, sorted by step number
        """
        if not response:
            return []
        
        steps = []
        
        # Pattern 1: Vietnamese "Bước N:" or "Bước N."
        pattern_vi = r"Bước\s+(\d+)[:\.]\s*(.+?)(?=Bước\s+\d+|$)"
        matches_vi = re.finditer(pattern_vi, response, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        for match in matches_vi:
            step_num = int(match.group(1))
            content = match.group(2).strip()
            steps.append(Step(
                step_number=step_num,
                content=content,
                original_text=match.group(0).strip(),
                start_pos=match.start(),
                end_pos=match.end()
            ))
        
        # Pattern 2: English "Step N:" or "Step N."
        pattern_en = r"Step\s+(\d+)[:\.]\s*(.+?)(?=Step\s+\d+|$)"
        matches_en = re.finditer(pattern_en, response, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        for match in matches_en:
            step_num = int(match.group(1))
            content = match.group(2).strip()
            steps.append(Step(
                step_number=step_num,
                content=content,
                original_text=match.group(0).strip(),
                start_pos=match.start(),
                end_pos=match.end()
            ))
        
        # Pattern 3: Numbered list "1.", "2." (with optional leading whitespace)
        # Only if no other patterns matched (avoid double detection)
        if len(steps) == 0:
            # Pattern: optional whitespace, number, dot, space, then content until next number or end
            pattern_numbered = r"(?:^|\n)\s*(\d+)\.\s+(.+?)(?=\n\s*\d+\.|$)"
            matches_num = re.finditer(pattern_numbered, response, re.MULTILINE | re.DOTALL)
            numbered_steps = []
            for match in matches_num:
                step_num = int(match.group(1))
                content = match.group(2).strip()
                numbered_steps.append(Step(
                    step_number=step_num,
                    content=content,
                    original_text=match.group(0).strip(),
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
            # Use numbered steps if we found at least 2
            if len(numbered_steps) >= 2:
                steps.extend(numbered_steps)
        
        # Pattern 4: Bullet points with bold headers "- **Header:**" or "- Header:"
        # PHASE 2 FIX: Add support for bullet + bold format
        if len(steps) == 0:
            # Pattern: "- **Header:**" or "- Header:" followed by content
            pattern_bullet = r"(?:^|\n)\s*-\s+(?:\*\*)?([^:]+?)(?:\*\*)?:\s*(.+?)(?=\n\s*-|$)"
            matches_bullet = re.finditer(pattern_bullet, response, re.MULTILINE | re.DOTALL)
            bullet_steps = []
            step_num = 1
            for match in matches_bullet:
                header = match.group(1).strip()
                content = match.group(2).strip()
                bullet_steps.append(Step(
                    step_number=step_num,
                    content=f"{header}: {content}",
                    original_text=match.group(0).strip(),
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
                step_num += 1
            # Use bullet steps if we found at least 2
            if len(bullet_steps) >= 2:
                steps.extend(bullet_steps)
        
        # Remove duplicates (same step number) - keep first occurrence
        seen_numbers = set()
        unique_steps = []
        for step in steps:
            if step.step_number not in seen_numbers:
                seen_numbers.add(step.step_number)
                unique_steps.append(step)
        
        # Sort by step number
        unique_steps.sort(key=lambda x: x.step_number)
        
        logger.debug(f"Detected {len(unique_steps)} steps from response")
        return unique_steps

