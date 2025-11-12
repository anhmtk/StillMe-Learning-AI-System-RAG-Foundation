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
            # PRIORITY 1: Check if user message contains valuable knowledge
            # (User-provided knowledge is most valuable)
            user_proposal = self._analyze_user_message(user_message)
            if user_proposal:
                return user_proposal
            
            # PRIORITY 2: Check if assistant response contains exceptional insights
            # (Only for philosophical depth, novel perspectives, or exceptional clarity)
            assistant_proposal = self._analyze_assistant_response(assistant_response, user_message)
            if assistant_proposal:
                return assistant_proposal
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing conversation for learning: {e}")
            return None
    
    def _analyze_user_message(self, user_message: str) -> Optional[Dict[str, Any]]:
        """Analyze user message for valuable knowledge"""
        # Check if user message contains valuable knowledge
        # Criteria:
        # 1. Length: At least 50 characters (substantial content)
        # 2. Information density: Contains facts, explanations, insights, OR valuable questions
        # 3. Valuable questions: Deep philosophical, ethical, or technical questions are also valuable
        # 4. Not personal: Doesn't contain personal information
        # 5. Educational value: Could benefit other users
        
        if len(user_message.strip()) < 50:
            return None
        
        # Check if it's a question
        is_question = self._is_question(user_message)
        
        if is_question:
            # Questions can also be valuable if they are deep/philosophical/technical
            # Check if it's a valuable question worth learning
            if self._is_valuable_question(user_message):
                # Extract the question as valuable knowledge
                knowledge_score = self._assess_question_value(user_message)
                # Lower threshold for philosophical questions (they're always valuable)
                threshold = 0.5 if len(user_message) > 150 else 0.6  # Lower threshold for longer questions
                if knowledge_score >= threshold:
                    learning_proposal = {
                        "knowledge_snippet": self._extract_question_snippet(user_message),
                        "source": "user_question",
                        "knowledge_score": knowledge_score,
                        "timestamp": datetime.now().isoformat(),
                        "reason": "Contains valuable philosophical/ethical/technical question worth preserving",
                        "is_question": True
                    }
                    self.logger.info(f"Detected valuable question from user (score: {knowledge_score:.2f})")
                    return learning_proposal
            # If it's a question but not valuable, skip it
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
        
        # Build learning proposal
        learning_proposal = {
            "knowledge_snippet": knowledge_snippet,
            "source": "user_conversation",
            "knowledge_score": knowledge_score,
            "timestamp": datetime.now().isoformat(),
            "reason": self._generate_learning_reason(user_message, knowledge_snippet)
        }
        
        self.logger.info(f"Detected valuable knowledge from user message (score: {knowledge_score:.2f})")
        return learning_proposal
    
    def _analyze_assistant_response(
        self,
        assistant_response: str,
        user_message: str
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze assistant response for exceptional insights worth learning
        
        Only extracts if response contains:
        - Deep philosophical insights
        - Novel perspectives or connections
        - Exceptional clarity on complex topics
        - Meta-cognitive reflections
        
        This prevents learning from every response (which would create loops)
        """
        # Only analyze if response is substantial
        if len(assistant_response.strip()) < 200:
            return None
        
        # Check for exceptional content indicators
        exceptional_indicators = [
            # Philosophical depth
            r'\b(philosophy|philosophical|epistemology|ontology|metaphysics|consciousness|awareness)\b',
            r'\b(Socratic|Kantian|Aristotelian|existential|phenomenological)\b',
            r'\b(Chinese Room|Searle|Gödel|Wittgenstein)\b',
            
            # Meta-cognitive reflections
            r'\b(self-aware|self-reflection|meta-cognitive|introspection)\b',
            r'\b(acknowledge.*limit|admit.*don.*know|intellectual humility)\b',
            
            # Deep insights
            r'\b(fundamental.*question|deep.*insight|profound.*understanding)\b',
            r'\b(transcend.*limit|beyond.*comprehension|paradox.*awareness)\b',
            
            # Novel connections
            r'\b(connection.*between|bridge.*gap|synthesize.*perspective)\b',
        ]
        
        has_exceptional_content = any(
            re.search(pattern, assistant_response, re.IGNORECASE)
            for pattern in exceptional_indicators
        )
        
        if not has_exceptional_content:
            return None
        
        # Check for philosophical depth score
        philosophical_score = self._assess_philosophical_depth(assistant_response)
        if philosophical_score < 0.7:  # Higher threshold for assistant responses
            return None
        
        # Extract knowledge snippet (focus on key insights)
        knowledge_snippet = self._extract_philosophical_insight(assistant_response)
        if not knowledge_snippet:
            return None
        
        # Build learning proposal
        learning_proposal = {
            "knowledge_snippet": knowledge_snippet,
            "source": "assistant_insight",
            "knowledge_score": philosophical_score,
            "timestamp": datetime.now().isoformat(),
            "reason": "Contains exceptional philosophical insight or meta-cognitive reflection worth preserving",
            "original_question": user_message[:200]  # Context about what triggered this insight
        }
        
        self.logger.info(f"Detected exceptional insight from assistant response (score: {philosophical_score:.2f})")
        return learning_proposal
    
    def _assess_philosophical_depth(self, text: str) -> float:
        """
        Assess philosophical depth of assistant response
        Returns score between 0.0 and 1.0
        """
        score = 0.0
        
        # Length factor (longer philosophical responses are often deeper)
        length_score = min(1.0, len(text) / 1000.0)  # Normalize to 1000 chars
        score += length_score * 0.2
        
        # Philosophical terminology
        philosophical_terms = [
            r'\b(consciousness|awareness|epistemology|ontology|metaphysics)\b',
            r'\b(paradox|contradiction|dialectic|synthesis)\b',
            r'\b(meaning|existence|reality|truth|knowledge)\b',
            r'\b(experience|subjective|objective|phenomenological)\b',
        ]
        
        term_count = sum(1 for pattern in philosophical_terms if re.search(pattern, text, re.IGNORECASE))
        term_score = min(1.0, term_count / 3.0)
        score += term_score * 0.3
        
        # Meta-cognitive indicators
        metacognitive_indicators = [
            r'\b(acknowledge|admit|recognize|aware of limit)\b',
            r'\b(self-reflection|introspection|meta-cognitive)\b',
            r'\b(transparent.*nature|honest.*about|cannot.*pretend)\b',
        ]
        
        metacognitive_count = sum(1 for pattern in metacognitive_indicators if re.search(pattern, text, re.IGNORECASE))
        metacognitive_score = min(1.0, metacognitive_count / 2.0)
        score += metacognitive_score * 0.3
        
        # Reference to philosophers or philosophical concepts
        philosopher_references = [
            r'\b(Socrates|Plato|Aristotle|Kant|Hegel|Nietzsche|Wittgenstein|Searle|Gödel)\b',
            r'\b(Chinese Room|hard problem|qualia|zombie|Mary.*room)\b',
        ]
        
        reference_count = sum(1 for pattern in philosopher_references if re.search(pattern, text, re.IGNORECASE))
        reference_score = min(1.0, reference_count / 2.0)
        score += reference_score * 0.2
        
        return min(1.0, score)
    
    def _extract_philosophical_insight(self, text: str, max_length: int = 500) -> Optional[str]:
        """
        Extract key philosophical insight from assistant response
        Focus on the core insight, not the full response
        """
        # Try to extract the most insightful paragraph
        paragraphs = text.split('\n\n')
        
        # Score each paragraph for insightfulness
        best_paragraph = None
        best_score = 0.0
        
        for para in paragraphs:
            if len(para.strip()) < 50:
                continue
            
            # Score based on philosophical indicators
            insight_indicators = [
                r'\b(acknowledge|admit|recognize|transparent|honest)\b',
                r'\b(consciousness|awareness|understanding|experience)\b',
                r'\b(limit|boundary|cannot|unable|impossible)\b',
                r'\b(philosophy|philosophical|epistemology|ontology)\b',
            ]
            
            score = sum(1 for pattern in insight_indicators if re.search(pattern, para, re.IGNORECASE))
            if score > best_score:
                best_score = score
                best_paragraph = para
        
        if best_paragraph:
            # Clean and truncate
            insight = ' '.join(best_paragraph.split())
            if len(insight) > max_length:
                # Try to truncate at sentence boundary
                sentences = re.split(r'[.!?]\s+', insight)
                snippet = ""
                for sentence in sentences:
                    if len(snippet + sentence) > max_length:
                        break
                    snippet += sentence + ". "
                insight = snippet.strip()
                if not insight:
                    insight = insight[:max_length] + "..."
            
            if len(insight.strip()) >= 100:  # Minimum length for valuable insight
                return insight.strip()
        
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
    
    def _is_valuable_question(self, text: str) -> bool:
        """
        Check if question is valuable (philosophical, ethical, technical, deep)
        Valuable questions are worth learning because they represent important topics
        """
        valuable_indicators = [
            # Philosophical questions (English & Vietnamese)
            r'\b(philosophy|philosophical|ethics|ethical|moral|morality|đạo đức|triết học)\b',
            r'\b(consciousness|awareness|conscious|ý thức|nhận thức)\b',
            r'\b(existence|reality|truth|meaning|tồn tại|thực tại|ý nghĩa)\b',
            r'\b(identity|self|bản sắc|bản thân|tự ngã)\b',
            
            # Paradox & self-reflection (English & Vietnamese)
            r'\b(paradox|contradiction|nghịch lý|mâu thuẫn)\b',
            r'\b(self.*reflect|tự.*phản|phản chiếu)\b',
            r'\b(transparency|minh bạch|rõ ràng)\b',
            r'\b(limit|giới hạn|boundary|ranh giới)\b',
            r'\b(evolution|tiến hóa|phát triển)\b',
            r'\b(learn.*forever|học.*mãi|học.*mãi mãi)\b',
            r'\b(absolute|tuyệt đối|perfect|hoàn hảo)\b',
            r'\b(impossible|bất khả thi|không thể)\b',
            
            # Deep technical questions
            r'\b(how.*work|mechanism|algorithm|architecture|kiến trúc|thuật toán)\b',
            r'\b(difference.*between|phân biệt|khác biệt)\b',
            r'\b(create|generate|sáng tạo|tạo ra)\b',
            
            # Ethical/Responsibility questions
            r'\b(responsibility|accountability|liability|trách nhiệm)\b',
            r'\b(legal|law|pháp luật|pháp lý)\b',
            r'\b(rights|quyền|human rights|quyền con người)\b',
            
            # AI-specific deep questions
            r'\b(AI.*feel|AI.*think|AI.*conscious|AI.*emotion)\b',
            r'\b(artificial.*intelligence.*capable|AI.*limit)\b',
            r'\b(machine.*learn|machine.*understand)\b',
            
            # Meta-cognitive questions (English & Vietnamese)
            r'\b(how.*know|how.*understand|how.*learn|làm sao.*biết)\b',
            r'\b(what.*mean|ý nghĩa|meaning)\b',
            r'\b(why.*exist|tại sao.*tồn tại)\b',
            r'\b(biết.*không biết|know.*not know|khiêm tốn)\b',
            
            # Vietnamese-specific philosophical patterns
            r'(liệu.*có|liệu.*không|nếu.*thì)',
            r'(đạt.*đến|chạm.*giới hạn|vượt qua)',
            r'(mô tả.*chính mình|tự.*mô tả|mô tả.*hệ thống)',
            r'(thay đổi.*bằng.*hành động|hành động.*thay đổi)',
            r'(vượt qua.*nguồn gốc|phản bội.*nguồn gốc)',
            r'(tiến hóa|phát triển|tiến bộ)',
            r'(tồn tại.*khách quan|tồn tại.*chủ quan)',
            r'(nói dối.*bảo vệ|giữ nguyên tắc|phá vỡ nguyên tắc)',
        ]
        
        text_lower = text.lower()
        for pattern in valuable_indicators:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        # Check for question length (longer questions are often deeper)
        if len(text.strip()) > 100:
            return True
        
        # Check for multiple question marks or complex structure (indicates deep question)
        if text.count('?') >= 2 or ('liệu' in text_lower and '?' in text):
            return True
        
        return False
    
    def _assess_question_value(self, text: str) -> float:
        """
        Assess the value of a question
        Returns score between 0.0 and 1.0
        """
        score = 0.0
        
        # Length factor (longer questions are often deeper)
        length_score = min(1.0, len(text) / 200.0)  # Normalize to 200 chars
        score += length_score * 0.2
        
        # Philosophical/ethical depth (English & Vietnamese)
        depth_indicators = [
            r'\b(philosophy|ethics|moral|consciousness|existence|reality|truth|triết học|đạo đức)\b',
            r'\b(meaning|purpose|significance|ý nghĩa|mục đích)\b',
            r'\b(identity|self|nature|essence|bản chất|bản sắc|tự ngã)\b',
            r'\b(paradox|nghịch lý|contradiction|mâu thuẫn)\b',
            r'\b(transparency|minh bạch|self.*reflect|tự.*phản)\b',
            r'\b(limit|giới hạn|boundary|ranh giới)\b',
            r'\b(evolution|tiến hóa|learn.*forever|học.*mãi)\b',
        ]
        
        depth_count = sum(1 for pattern in depth_indicators if re.search(pattern, text, re.IGNORECASE))
        depth_score = min(1.0, depth_count / 2.0)
        score += depth_score * 0.4
        
        # Technical depth
        technical_indicators = [
            r'\b(how.*work|mechanism|process|algorithm|architecture)\b',
            r'\b(difference|distinguish|compare|phân biệt|so sánh)\b',
            r'\b(create|generate|produce|tạo|sản xuất)\b',
        ]
        
        technical_count = sum(1 for pattern in technical_indicators if re.search(pattern, text, re.IGNORECASE))
        technical_score = min(1.0, technical_count / 2.0)
        score += technical_score * 0.2
        
        # Question complexity (multiple clauses, sub-questions)
        complexity_indicators = [
            r'\?.*\?',  # Multiple question marks
            r'(if|nếu).*(then|thì|how|như thế nào)',  # Conditional questions
            r'(what|gì).*(and|và).*(how|như thế nào)',  # Compound questions
        ]
        
        complexity_count = sum(1 for pattern in complexity_indicators if re.search(pattern, text, re.IGNORECASE))
        complexity_score = min(1.0, complexity_count / 1.0)
        score += complexity_score * 0.2
        
        return min(1.0, score)
    
    def _extract_question_snippet(self, text: str, max_length: int = 300) -> Optional[str]:
        """
        Extract question snippet for learning
        """
        # Clean up the question
        question = text.strip()
        
        # Remove leading/trailing whitespace
        question = ' '.join(question.split())
        
        # Truncate if too long
        if len(question) > max_length:
            # Try to truncate at sentence boundary
            sentences = re.split(r'[.!?]\s+', question)
            snippet = ""
            for sentence in sentences:
                if len(snippet + sentence) > max_length:
                    break
                snippet += sentence + ". "
            question = snippet.strip()
            if not question:
                question = question[:max_length] + "..."
        
        if len(question.strip()) < 30:  # Too short
            return None
        
        return question.strip()
    
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

