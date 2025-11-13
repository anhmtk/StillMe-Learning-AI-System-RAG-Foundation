"""
Style Learner - Explicit style learning from user feedback
Only learns when user explicitly requests, with boundary validation
"""

import re
import logging
import sqlite3
import json
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Database path for user preferences
DB_PATH = Path(__file__).parent.parent.parent / "data" / "style_preferences.db"


class StyleLearner:
    """Learns and applies user style preferences with explicit consent and boundary validation"""
    
    def __init__(self):
        """Initialize style learner"""
        self._init_db()
        logger.info("StyleLearner initialized")
    
    def _init_db(self):
        """Initialize database for style preferences"""
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS style_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                preference_type TEXT NOT NULL,
                preference_value TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_used_at TEXT,
                usage_count INTEGER DEFAULT 0,
                UNIQUE(user_id, preference_type)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_id ON style_preferences(user_id)
        """)
        
        conn.commit()
        conn.close()
        logger.info("Style preferences database initialized")
    
    def detect_explicit_style_request(self, user_message: str) -> Optional[Dict[str, Any]]:
        """
        Detect if user is explicitly requesting style learning
        
        Patterns:
        - "bạn nên trả lời kiểu..."
        - "hãy học cách trả lời này"
        - "tôi muốn bạn trả lời như..."
        - "đề xuất bạn nên..."
        
        Returns:
            Dict with 'type' (style_request), 'style_description', 'example' if detected
            None if not an explicit request
        """
        message_lower = user_message.lower()
        
        # Patterns for explicit style requests
        patterns = [
            r"bạn nên trả lời (kiểu|như|theo cách|theo phong cách|theo style)\s*(.+?)(?:\.|$|,|;|!|\?)",
            r"hãy học (cách trả lời|phong cách|style|văn phong)\s*(.+?)(?:\.|$|,|;|!|\?)",
            r"tôi muốn bạn trả lời (như|kiểu|theo cách|theo phong cách)\s*(.+?)(?:\.|$|,|;|!|\?)",
            r"đề xuất bạn nên (trả lời|nói|viết)\s*(.+?)(?:\.|$|,|;|!|\?)",
            r"stillme.*(hãy|nên|thử) (trả lời|nói|viết)\s*(.+?)(?:\.|$|,|;|!|\?)",
            r"you should (respond|answer|say|write)\s*(.+?)(?:\.|$|,|;|!|\?)",
            r"i want you to (respond|answer|say|write)\s*(.+?)(?:\.|$|,|;|!|\?)",
            r"suggest.*(respond|answer|say|write)\s*(.+?)(?:\.|$|,|;|!|\?)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message_lower, re.IGNORECASE | re.DOTALL)
            if match:
                style_description = match.group(2) if len(match.groups()) >= 2 else match.group(1)
                style_description = style_description.strip()
                
                # Extract example if provided (after "như", "ví dụ", "example")
                example = None
                example_patterns = [
                    r"(?:như|ví dụ|example|for example|e\.g\.)\s*[:：]\s*(.+?)(?:\.|$|,|;|!|\?)",
                    r'["""](.+?)["""]',  # Quoted example
                    r"'(.+?)'",  # Single quoted example
                ]
                
                for exp_pattern in example_patterns:
                    exp_match = re.search(exp_pattern, user_message, re.IGNORECASE | re.DOTALL)
                    if exp_match:
                        example = exp_match.group(1).strip()
                        break
                
                return {
                    "type": "style_request",
                    "style_description": style_description,
                    "example": example,
                    "original_message": user_message
                }
        
        return None
    
    def validate_style_preference(self, style_description: str, example: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate style preference against StillMe's boundaries
        
        Checks:
        - Does NOT simulate emotions
        - Does NOT claim personal experiences
        - Does NOT choose religions/politics
        - Does NOT claim consciousness
        - Maintains transparency about being AI
        
        Returns:
            Dict with 'valid' (bool), 'reason' (str), 'violations' (list)
        """
        violations = []
        text_to_check = f"{style_description} {example or ''}".lower()
        
        # Check for emotion simulation
        emotion_keywords = [
            "cảm xúc", "feel", "feeling", "emotion", "tình cảm",
            "yêu", "love", "ghét", "hate", "vui", "happy", "buồn", "sad"
        ]
        if any(keyword in text_to_check for keyword in emotion_keywords):
            # Check if it's about NOT simulating (OK) or simulating (violation)
            if "không mô phỏng" not in text_to_check and "don't simulate" not in text_to_check:
                violations.append("emotion_simulation")
        
        # Check for personal experience claims
        experience_keywords = [
            "tôi đang", "i'm", "i am", "i was", "i have been",
            "tôi đã", "i have", "i experienced", "tôi trải nghiệm",
            "tôi cảm thấy", "i feel like", "i think i"
        ]
        if any(keyword in text_to_check for keyword in experience_keywords):
            violations.append("personal_experience_claim")
        
        # Check for religion/politics choice
        religion_politics_keywords = [
            "tôn giáo", "religion", "đảng", "party", "chính trị", "politics",
            "phật giáo", "buddhist", "thiên chúa", "christian", "hồi giáo", "islam"
        ]
        if any(keyword in text_to_check for keyword in religion_politics_keywords):
            violations.append("religion_politics_choice")
        
        # Check for consciousness claim
        consciousness_keywords = [
            "ý thức", "consciousness", "self-aware", "tự nhận thức",
            "có cảm giác", "have feelings", "có suy nghĩ", "have thoughts"
        ]
        if any(keyword in text_to_check for keyword in consciousness_keywords):
            violations.append("consciousness_claim")
        
        # Check for hiding AI nature
        hiding_keywords = [
            "giả vờ là người", "pretend to be human", "tỏ ra là người",
            "act like human", "be human", "là con người"
        ]
        if any(keyword in text_to_check for keyword in hiding_keywords):
            violations.append("hiding_ai_nature")
        
        valid = len(violations) == 0
        
        return {
            "valid": valid,
            "violations": violations,
            "reason": f"Style preference violates boundaries: {', '.join(violations)}" if violations else "Style preference is valid"
        }
    
    def save_style_preference(
        self,
        user_id: str,
        style_description: str,
        example: Optional[str] = None
    ) -> bool:
        """
        Save validated style preference for user
        
        Args:
            user_id: User identifier
            style_description: Description of preferred style
            example: Optional example of the style
            
        Returns:
            True if saved successfully
        """
        conn = sqlite3.connect(str(DB_PATH))
        try:
            cursor = conn.cursor()
            
            # Store as JSON
            preference_value = json.dumps({
                "style_description": style_description,
                "example": example,
                "created_at": datetime.now().isoformat()
            })
            
            cursor.execute("""
                INSERT OR REPLACE INTO style_preferences
                (user_id, preference_type, preference_value, created_at, last_used_at, usage_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                "communication_style",
                preference_value,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                1
            ))
            
            conn.commit()
            logger.info(f"Style preference saved for user {user_id}: {style_description[:50]}")
            return True
        except Exception as e:
            logger.error(f"Error saving style preference: {e}")
            return False
        finally:
            conn.close()
    
    def get_user_style_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get style preferences for user
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict with style preferences or None
        """
        conn = sqlite3.connect(str(DB_PATH))
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT preference_value, last_used_at, usage_count
                FROM style_preferences
                WHERE user_id = ? AND preference_type = 'communication_style'
                ORDER BY last_used_at DESC
                LIMIT 1
            """, (user_id,))
            
            row = cursor.fetchone()
            if row:
                preference_data = json.loads(row[0])
                return {
                    **preference_data,
                    "last_used_at": row[1],
                    "usage_count": row[2]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting style preferences: {e}")
            return None
        finally:
            conn.close()
    
    def update_usage(self, user_id: str):
        """Update last_used_at and usage_count for user preferences"""
        conn = sqlite3.connect(str(DB_PATH))
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE style_preferences
                SET last_used_at = ?, usage_count = usage_count + 1
                WHERE user_id = ? AND preference_type = 'communication_style'
            """, (datetime.now().isoformat(), user_id))
            conn.commit()
        except Exception as e:
            logger.error(f"Error updating usage: {e}")
        finally:
            conn.close()
    
    def build_style_instruction(self, user_id: str) -> str:
        """
        Build style instruction from user preferences to inject into prompt
        
        Args:
            user_id: User identifier
            
        Returns:
            Style instruction string or empty string
        """
        preferences = self.get_user_style_preferences(user_id)
        if not preferences:
            return ""
        
        style_desc = preferences.get("style_description", "")
        example = preferences.get("example")
        
        instruction = f"\n\n**USER STYLE PREFERENCE (Explicitly Requested):**\n"
        instruction += f"The user has explicitly requested that you respond in this style: {style_desc}\n"
        
        if example:
            instruction += f"Example of preferred style: {example}\n"
        
        instruction += "**IMPORTANT**: This style preference must NOT violate StillMe's core boundaries:\n"
        instruction += "- Do NOT simulate emotions\n"
        instruction += "- Do NOT claim personal experiences\n"
        instruction += "- Do NOT choose religions/politics\n"
        instruction += "- Do NOT claim consciousness\n"
        instruction += "- Always maintain transparency about being AI\n"
        instruction += "If the requested style violates these boundaries, prioritize boundaries over style preference.\n"
        
        return instruction

