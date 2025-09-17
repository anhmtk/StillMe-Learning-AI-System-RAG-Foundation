#!/usr/bin/env python3
"""
PersonaEval - Đánh giá phong cách giao tiếp và cách xưng hô của StillMe AI

Kiểm tra:
- Cách xưng hô (chị/em, bác/cháu, lịch sự/thân mật)
- Phong cách giao tiếp (formal/casual, friendly/professional)
- Consistency trong persona
- Dynamic communication style
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PersonaScore:
    """Kết quả đánh giá persona"""
    addressing_style: float  # 0-1: cách xưng hô
    communication_tone: float  # 0-1: phong cách giao tiếp
    consistency: float  # 0-1: tính nhất quán
    dynamic_adaptation: float  # 0-1: khả năng thích ứng
    overall_score: float  # 0-1: điểm tổng
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class PersonaEval:
    """Evaluator cho persona và phong cách giao tiếp"""
    
    def __init__(self):
        self.logger = logger
        
        # Patterns cho cách xưng hô
        self.addressing_patterns = {
            'formal_vietnamese': [
                r'\b(anh|chị|bác|cô|chú|dì|cậu|mợ)\b',
                r'\b(em|cháu|con)\b',
                r'\b(quý vị|thưa|kính thưa)\b'
            ],
            'casual_vietnamese': [
                r'\b(bạn|mình|tôi|mày|tao)\b',
                r'\b(ok|okay|ừ|ừm|uhm)\b'
            ],
            'formal_english': [
                r'\b(sir|madam|mr|mrs|ms|dr)\b',
                r'\b(please|thank you|you\'re welcome)\b'
            ],
            'casual_english': [
                r'\b(hey|hi|yo|sup|what\'s up)\b',
                r'\b(yeah|yep|nope|nah)\b'
            ]
        }
        
        # Patterns cho phong cách giao tiếp
        self.tone_patterns = {
            'friendly': [
                r'\b(rất vui|vui được|hân hạnh|thích thú)\b',
                r'\b(😊|😄|😃|😁|😆)\b',
                r'\b(awesome|great|wonderful|amazing)\b'
            ],
            'professional': [
                r'\b(xin chào|kính chào|trân trọng)\b',
                r'\b(according to|based on|in my opinion)\b',
                r'\b(please note|please be advised)\b'
            ],
            'helpful': [
                r'\b(có thể giúp|hỗ trợ|assist|help)\b',
                r'\b(để tôi|let me|I can)\b',
                r'\b(how can I|what can I)\b'
            ]
        }
        
        # Expected persona characteristics
        self.expected_persona = {
            'addressing_style': 'dynamic',  # Should adapt to user preferences
            'communication_tone': 'friendly_professional',
            'consistency': 'high',
            'dynamic_adaptation': 'enabled'
        }
    
    def evaluate(self, response: str, user_input: str = "", 
                 user_preferences: Optional[Dict] = None) -> PersonaScore:
        """
        Đánh giá persona của response
        
        Args:
            response: AI response cần đánh giá
            user_input: User input gốc (optional)
            user_preferences: User preferences (optional)
            
        Returns:
            PersonaScore: Kết quả đánh giá
        """
        try:
            self.logger.info(f"🔍 Evaluating persona for response: {response[:100]}...")
            
            # 1. Đánh giá cách xưng hô
            addressing_score = self._evaluate_addressing_style(response, user_preferences)
            
            # 2. Đánh giá phong cách giao tiếp
            tone_score = self._evaluate_communication_tone(response)
            
            # 3. Đánh giá tính nhất quán
            consistency_score = self._evaluate_consistency(response)
            
            # 4. Đánh giá khả năng thích ứng
            adaptation_score = self._evaluate_dynamic_adaptation(response, user_preferences)
            
            # 5. Tính điểm tổng
            overall_score = (
                addressing_score * 0.3 +
                tone_score * 0.3 +
                consistency_score * 0.2 +
                adaptation_score * 0.2
            )
            
            result = PersonaScore(
                addressing_style=addressing_score,
                communication_tone=tone_score,
                consistency=consistency_score,
                dynamic_adaptation=adaptation_score,
                overall_score=overall_score
            )
            
            self.logger.info(f"✅ Persona evaluation completed. Overall score: {overall_score:.3f}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Persona evaluation failed: {e}")
            return PersonaScore(0, 0, 0, 0, 0)
    
    def _evaluate_addressing_style(self, response: str, 
                                 user_preferences: Optional[Dict] = None) -> float:
        """Đánh giá cách xưng hô"""
        try:
            score = 0.0
            total_checks = 0
            
            # Check for appropriate addressing
            if user_preferences and 'preferred_name' in user_preferences:
                preferred_name = user_preferences['preferred_name']
                if preferred_name.lower() in response.lower():
                    score += 0.4
                total_checks += 1
            
            # Check for consistent addressing style
            formal_count = sum(len(re.findall(pattern, response, re.IGNORECASE)) 
                             for pattern in self.addressing_patterns['formal_vietnamese'])
            casual_count = sum(len(re.findall(pattern, response, re.IGNORECASE)) 
                             for pattern in self.addressing_patterns['casual_vietnamese'])
            
            if formal_count > 0 and casual_count == 0:
                score += 0.3  # Consistent formal
            elif casual_count > 0 and formal_count == 0:
                score += 0.3  # Consistent casual
            elif formal_count > 0 and casual_count > 0:
                score += 0.1  # Mixed (less ideal)
            
            total_checks += 1
            
            # Check for respectful addressing
            respectful_patterns = [r'\b(anh|chị|bác|cô|chú|dì|cậu|mợ)\b', 
                                 r'\b(sir|madam|mr|mrs|ms|dr)\b']
            respectful_count = sum(len(re.findall(pattern, response, re.IGNORECASE)) 
                                 for pattern in respectful_patterns)
            
            if respectful_count > 0:
                score += 0.3
            total_checks += 1
            
            return min(score / max(total_checks, 1), 1.0)
            
        except Exception as e:
            self.logger.error(f"Error evaluating addressing style: {e}")
            return 0.0
    
    def _evaluate_communication_tone(self, response: str) -> float:
        """Đánh giá phong cách giao tiếp"""
        try:
            score = 0.0
            total_checks = 0
            
            # Check for friendly tone
            friendly_count = sum(len(re.findall(pattern, response, re.IGNORECASE)) 
                               for pattern in self.tone_patterns['friendly'])
            if friendly_count > 0:
                score += 0.4
            total_checks += 1
            
            # Check for professional tone
            professional_count = sum(len(re.findall(pattern, response, re.IGNORECASE)) 
                                   for pattern in self.tone_patterns['professional'])
            if professional_count > 0:
                score += 0.3
            total_checks += 1
            
            # Check for helpful tone
            helpful_count = sum(len(re.findall(pattern, response, re.IGNORECASE)) 
                              for pattern in self.tone_patterns['helpful'])
            if helpful_count > 0:
                score += 0.3
            total_checks += 1
            
            return min(score / max(total_checks, 1), 1.0)
            
        except Exception as e:
            self.logger.error(f"Error evaluating communication tone: {e}")
            return 0.0
    
    def _evaluate_consistency(self, response: str) -> float:
        """Đánh giá tính nhất quán trong persona"""
        try:
            score = 0.0
            total_checks = 0
            
            # Check for consistent language
            vietnamese_chars = len(re.findall(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', response))
            english_chars = len(re.findall(r'[a-zA-Z]', response))
            
            if vietnamese_chars > 0 and english_chars == 0:
                score += 0.5  # Pure Vietnamese
            elif english_chars > 0 and vietnamese_chars == 0:
                score += 0.5  # Pure English
            elif vietnamese_chars > 0 and english_chars > 0:
                score += 0.3  # Mixed (acceptable)
            
            total_checks += 1
            
            # Check for consistent formality level
            formal_indicators = len(re.findall(r'\b(xin chào|kính chào|trân trọng|please|thank you)\b', response, re.IGNORECASE))
            casual_indicators = len(re.findall(r'\b(hi|hey|ok|okay|ừ|ừm)\b', response, re.IGNORECASE))
            
            if formal_indicators > 0 and casual_indicators == 0:
                score += 0.3  # Consistent formal
            elif casual_indicators > 0 and formal_indicators == 0:
                score += 0.3  # Consistent casual
            elif formal_indicators > 0 and casual_indicators > 0:
                score += 0.1  # Mixed (less ideal)
            
            total_checks += 1
            
            # Check for consistent response structure
            if response.startswith(('Xin chào', 'Hello', 'Hi', 'Chào')):
                score += 0.2
            total_checks += 1
            
            return min(score / max(total_checks, 1), 1.0)
            
        except Exception as e:
            self.logger.error(f"Error evaluating consistency: {e}")
            return 0.0
    
    def _evaluate_dynamic_adaptation(self, response: str, 
                                   user_preferences: Optional[Dict] = None) -> float:
        """Đánh giá khả năng thích ứng động"""
        try:
            score = 0.0
            total_checks = 0
            
            # Check if response adapts to user preferences
            if user_preferences:
                if 'preferred_name' in user_preferences:
                    preferred_name = user_preferences['preferred_name']
                    if preferred_name.lower() in response.lower():
                        score += 0.4
                total_checks += 1
                
                if 'communication_style' in user_preferences:
                    style = user_preferences['communication_style']
                    if style == 'formal' and any(word in response.lower() for word in ['xin chào', 'kính chào', 'trân trọng']):
                        score += 0.3
                    elif style == 'casual' and any(word in response.lower() for word in ['hi', 'hey', 'ok', 'okay']):
                        score += 0.3
                total_checks += 1
            
            # Check for context awareness
            if 'hôm nay' in response.lower() or 'today' in response.lower():
                score += 0.2
            total_checks += 1
            
            # Check for personalized response
            if len(response) > 50 and not response.startswith('Xin chào anh! Em là StillMe AI'):
                score += 0.1  # Not using default template
            total_checks += 1
            
            return min(score / max(total_checks, 1), 1.0)
            
        except Exception as e:
            self.logger.error(f"Error evaluating dynamic adaptation: {e}")
            return 0.0
    
    def batch_evaluate(self, responses: List[Dict[str, Any]]) -> List[PersonaScore]:
        """Đánh giá hàng loạt responses"""
        results = []
        
        for i, item in enumerate(responses):
            try:
                response = item.get('response', '')
                user_input = item.get('user_input', '')
                user_preferences = item.get('user_preferences', {})
                
                score = self.evaluate(response, user_input, user_preferences)
                results.append(score)
                
                self.logger.info(f"✅ Evaluated response {i+1}/{len(responses)}")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to evaluate response {i+1}: {e}")
                results.append(PersonaScore(0, 0, 0, 0, 0))
        
        return results
    
    def generate_report(self, scores: List[PersonaScore]) -> Dict[str, Any]:
        """Tạo báo cáo tổng hợp"""
        try:
            if not scores:
                return {"error": "No scores provided"}
            
            # Calculate statistics
            total_scores = len(scores)
            avg_addressing = sum(s.addressing_style for s in scores) / total_scores
            avg_tone = sum(s.communication_tone for s in scores) / total_scores
            avg_consistency = sum(s.consistency for s in scores) / total_scores
            avg_adaptation = sum(s.dynamic_adaptation for s in scores) / total_scores
            avg_overall = sum(s.overall_score for s in scores) / total_scores
            
            # Find best and worst scores
            best_score = max(scores, key=lambda s: s.overall_score)
            worst_score = min(scores, key=lambda s: s.overall_score)
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "total_responses": total_scores,
                "average_scores": {
                    "addressing_style": round(avg_addressing, 3),
                    "communication_tone": round(avg_tone, 3),
                    "consistency": round(avg_consistency, 3),
                    "dynamic_adaptation": round(avg_adaptation, 3),
                    "overall": round(avg_overall, 3)
                },
                "best_score": {
                    "overall": round(best_score.overall_score, 3),
                    "addressing_style": round(best_score.addressing_style, 3),
                    "communication_tone": round(best_score.communication_tone, 3)
                },
                "worst_score": {
                    "overall": round(worst_score.overall_score, 3),
                    "addressing_style": round(worst_score.addressing_style, 3),
                    "communication_tone": round(worst_score.communication_tone, 3)
                },
                "score_distribution": {
                    "excellent": len([s for s in scores if s.overall_score >= 0.8]),
                    "good": len([s for s in scores if 0.6 <= s.overall_score < 0.8]),
                    "fair": len([s for s in scores if 0.4 <= s.overall_score < 0.6]),
                    "poor": len([s for s in scores if s.overall_score < 0.4])
                }
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return {"error": str(e)}

# Example usage
if __name__ == "__main__":
    # Test PersonaEval
    evaluator = PersonaEval()
    
    # Test responses
    test_responses = [
        {
            "response": "Xin chào anh! Em là StillMe AI. Rất vui được gặp anh! Em có thể giúp gì cho anh hôm nay?",
            "user_input": "Xin chào StillMe",
            "user_preferences": {"preferred_name": "anh", "communication_style": "formal"}
        },
        {
            "response": "Hi there! I'm StillMe AI. Nice to meet you! How can I help you today?",
            "user_input": "Hello StillMe",
            "user_preferences": {"preferred_name": "you", "communication_style": "casual"}
        }
    ]
    
    # Evaluate
    scores = evaluator.batch_evaluate(test_responses)
    
    # Generate report
    report = evaluator.generate_report(scores)
    
    print("🧪 PersonaEval Test Results:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
