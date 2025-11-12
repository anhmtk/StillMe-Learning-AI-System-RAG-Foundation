"""
Conversation Learning Extractor Service
Extracts valuable knowledge from user conversations and requests permission to learn
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ConversationLearningExtractor:
    """
    Extracts valuable knowledge from user conversations
    Detects when user provides information that StillMe could learn from
    """
    
    def __init__(self):
        """Initialize conversation learning extractor"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("Conversation Learning Extractor initialized")
    
    def analyze_conversation_for_learning(
        self,
        user_message: str,
        assistant_response: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze conversation to detect valuable knowledge that StillMe could learn
        
        Args:
            user_message: User's message
            assistant_response: StillMe's response
            context: RAG context used for the response
            
        Returns:
            Dict with learning proposal if valuable knowledge detected, None otherwise
        """
        try:
            # Check if user message contains valuable knowledge
            # Criteria:
            # 1. Length: At least 100 characters (substantial content)
            # 2. Information density: Contains facts, explanations, or insights
            # 3. Not a question: User is providing information, not asking
            # 4. Not personal: Doesn't contain personal information
            # 5. Educational value: Could benefit other users
            
            if len(user_message.strip()) < 100:
                return None
            
            # Check if it's a question (questions are not learning material)
            is_question = self._is_question(user_message)
            if is_question:
                return None
            
            # Check if it contains personal information (privacy concern)
            if self._contains_personal_info(user_message):
                return None
            
            # Check if it's valuable knowledge (facts, explanations, insights)
            knowledge_score = self._assess_knowledge_value(user_message)
            if knowledge_score < 0.6:  # Threshold for valuable knowledge
                return None
            
            # Extract knowledge snippet
            knowledge_snippet = self._extract_knowledge_snippet(user_message)
            if not knowledge_snippet:
                return None
            
            # Check if this knowledge is already in RAG (avoid duplicates)
            # This would require RAG search - for now, we'll skip this check
            # and rely on user permission
            
            # Build learning proposal
            learning_proposal = {
                "knowledge_snippet": knowledge_snippet,
                "source": "user_conversation",
                "knowledge_score": knowledge_score,
                "timestamp": datetime.now().isoformat(),
                "reason": self._generate_learning_reason(user_message, knowledge_snippet)
            }
            
            self.logger.info(f"Detected valuable knowledge from conversation (score: {knowledge_score:.2f})")
            return learning_proposal
            
        except Exception as e:
            self.logger.error(f"Error analyzing conversation for learning: {e}")
            return None
    
    def _is_question(self, text: str) -> bool:
        """Check if text is a question"""
        question_indicators = [
            r'\?',  # Question mark
            r'^(ai|who|what|where|when|why|how|bạn|ai|tại sao|như thế nào|gì|là gì)',
            r'(là gì|what is|how does|why does|can you|có thể|bạn có thể)',
        ]
        
        text_lower = text.lower().strip()
        for pattern in question_indicators:
            if re.search(pattern, text_lower):
                return True
        return False
    
    def _contains_personal_info(self, text: str) -> bool:
        """Check if text contains personal information"""
        personal_indicators = [
            r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',  # Dates (birthdays)
            r'\b\d{10,}\b',  # Long numbers (phone, SSN, etc.)
            r'\b(email|@|phone|điện thoại|số điện thoại)\b',
            r'\b(tôi|mình|tớ|em|anh|chị)\s+(tên|tên là|name is)',
            r'\b(my name|my email|my phone|my address)',
        ]
        
        text_lower = text.lower()
        for pattern in personal_indicators:
            if re.search(pattern, text_lower):
                return True
        return False
    
    def _assess_knowledge_value(self, text: str) -> float:
        """
        Assess the value of knowledge in the text
        Returns score between 0.0 and 1.0
        """
        score = 0.0
        
        # Length factor (longer = potentially more valuable, but not always)
        length_score = min(1.0, len(text) / 500.0)  # Normalize to 500 chars
        score += length_score * 0.2
        
        # Information density indicators
        # Facts, definitions, explanations
        fact_indicators = [
            r'\b(là|is|are|means|định nghĩa|definition|theo|according to)',
            r'\b(ví dụ|example|for instance|chẳng hạn)',
            r'\b(nguyên nhân|cause|reason|lý do)',
            r'\b(kết quả|result|outcome|hậu quả)',
            r'\b(phương pháp|method|approach|cách)',
            r'\b(nguyên tắc|principle|rule|quy tắc)',
        ]
        
        fact_count = sum(1 for pattern in fact_indicators if re.search(pattern, text, re.IGNORECASE))
        fact_score = min(1.0, fact_count / 3.0)  # Normalize to 3 facts
        score += fact_score * 0.3
        
        # Educational value indicators
        educational_indicators = [
            r'\b(học|learn|study|research|nghiên cứu)',
            r'\b(kiến thức|knowledge|information|thông tin)',
            r'\b(giải thích|explain|describe|mô tả)',
            r'\b(phân tích|analyze|analysis)',
            r'\b(quan điểm|viewpoint|perspective|góc nhìn)',
        ]
        
        educational_count = sum(1 for pattern in educational_indicators if re.search(pattern, text, re.IGNORECASE))
        educational_score = min(1.0, educational_count / 2.0)
        score += educational_score * 0.3
        
        # Structure indicators (well-structured content is more valuable)
        structure_indicators = [
            r'^\d+\.',  # Numbered list
            r'^[-*•]',  # Bullet points
            r':\s',  # Colon (often indicates explanation)
        ]
        
        structure_count = sum(1 for pattern in structure_indicators if re.search(pattern, text, re.MULTILINE))
        structure_score = min(1.0, structure_count / 2.0)
        score += structure_score * 0.2
        
        return min(1.0, score)
    
    def _extract_knowledge_snippet(self, text: str, max_length: int = 500) -> Optional[str]:
        """
        Extract a clean knowledge snippet from text
        Removes personal references, questions, and keeps core knowledge
        """
        # Remove personal references
        text = re.sub(r'\b(tôi|mình|tớ|em|anh|chị|bạn|you|your)\b', '', text, flags=re.IGNORECASE)
        
        # Remove question marks and questions
        text = re.sub(r'\?.*$', '', text, flags=re.MULTILINE)
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        # Truncate if too long
        if len(text) > max_length:
            # Try to truncate at sentence boundary
            sentences = re.split(r'[.!?]\s+', text)
            snippet = ""
            for sentence in sentences:
                if len(snippet + sentence) > max_length:
                    break
                snippet += sentence + ". "
            text = snippet.strip()
            if not text:
                text = text[:max_length] + "..."
        
        if len(text.strip()) < 50:  # Too short to be valuable
            return None
        
        return text.strip()
    
    def _generate_learning_reason(self, original_text: str, snippet: str) -> str:
        """
        Generate a human-readable reason why StillMe wants to learn this
        """
        # Detect what type of knowledge it is
        if re.search(r'\b(định nghĩa|definition|là|is|means)\b', original_text, re.IGNORECASE):
            return "Contains valuable definition or explanation that could help other users"
        elif re.search(r'\b(ví dụ|example|instance)\b', original_text, re.IGNORECASE):
            return "Contains useful example or case study"
        elif re.search(r'\b(phương pháp|method|approach|cách)\b', original_text, re.IGNORECASE):
            return "Contains practical method or approach"
        elif re.search(r'\b(quan điểm|viewpoint|perspective|góc nhìn)\b', original_text, re.IGNORECASE):
            return "Contains valuable perspective or viewpoint"
        else:
            return "Contains valuable information that could benefit the knowledge base"
    
    def format_permission_request(
        self,
        learning_proposal: Dict[str, Any],
        language: str = 'en'
    ) -> str:
        """
        Format a permission request message to ask user if StillMe can learn from their input
        
        Args:
            learning_proposal: Learning proposal from analyze_conversation_for_learning
            language: Language code ('vi', 'en', etc.)
            
        Returns:
            Formatted permission request message
        """
        snippet = learning_proposal.get("knowledge_snippet", "")
        reason = learning_proposal.get("reason", "")
        
        if language == 'vi':
            return f"""💡 **Yêu cầu học tập từ cuộc trò chuyện**

Tôi nhận thấy thông tin bạn vừa chia sẻ có giá trị học tập:

**Nội dung:** {snippet[:200]}{'...' if len(snippet) > 200 else ''}

**Lý do:** {reason}

Bạn có đồng ý để tôi học từ thông tin này và thêm vào cơ sở tri thức của mình không? Thông tin sẽ được lưu trữ công khai trong RAG database với nguồn gốc rõ ràng.

**Quyền của bạn:**
- Bạn có thể từ chối - tôi sẽ không lưu thông tin này
- Bạn có thể chỉnh sửa nội dung trước khi cho phép
- Bạn có thể yêu cầu xóa thông tin đã học bất cứ lúc nào

Vui lòng trả lời: "đồng ý" / "không" / hoặc chỉnh sửa nội dung"""
        
        else:  # English default
            return f"""💡 **Learning Request from Conversation**

I noticed valuable information in your message:

**Content:** {snippet[:200]}{'...' if len(snippet) > 200 else ''}

**Reason:** {reason}

Would you allow me to learn from this information and add it to my knowledge base? The information will be stored publicly in the RAG database with clear attribution.

**Your Rights:**
- You can decline - I will not save this information
- You can edit the content before granting permission
- You can request deletion of learned information at any time

Please reply: "yes" / "no" / or edit the content"""


def get_conversation_learning_extractor():
    """Get conversation learning extractor service (singleton pattern)"""
    import backend.api.main as main_module
    if not hasattr(main_module, 'conversation_learning_extractor'):
        main_module.conversation_learning_extractor = ConversationLearningExtractor()
    return main_module.conversation_learning_extractor


def validate_learning_content(content: str) -> Tuple[bool, Optional[str]]:
    """
    Validate learning content before adding to RAG
    
    Args:
        content: Content to validate
        
    Returns:
        Tuple of (is_valid, reason_if_invalid)
    """
    import re
    
    # Check length
    if len(content.strip()) < 50:
        return (False, "Content too short (minimum 50 characters)")
    
    if len(content.strip()) > 2000:
        return (False, "Content too long (maximum 2000 characters)")
    
    # Check for personal information
    personal_patterns = [
        r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',  # Dates
        r'\b\d{10,}\b',  # Long numbers
        r'\b(email|@|phone|điện thoại)\b',
    ]
    
    for pattern in personal_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return (False, "Contains personal information")
    
    # Check for spam/malicious content (basic checks)
    spam_indicators = [
        r'\b(buy now|click here|free money|get rich)\b',
        r'\b(viagra|casino|lottery|winner)\b',
        r'http[s]?://(?!en\.wikipedia|arxiv|doi\.org)',  # Suspicious URLs (except trusted sources)
    ]
    
    for pattern in spam_indicators:
        if re.search(pattern, content, re.IGNORECASE):
            return (False, "Contains spam or suspicious content")
    
    return (True, None)

