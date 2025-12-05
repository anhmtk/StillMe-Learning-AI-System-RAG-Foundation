"""
Intent Classifier for Philosophical Questions
Classifies questions into: Consciousness (A), Emotion (B), Understanding (C)
"""

import re
from enum import Enum
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class QuestionType(Enum):
    """Question type classification"""
    CONSCIOUSNESS = "A"  # Type A: Questions about consciousness, self-awareness
    EMOTION = "B"  # Type B: Questions about emotions, feelings
    UNDERSTANDING = "C"  # Type C: Questions about understanding, meaning
    MIXED = "MIXED"  # Mixed type (e.g., agency, subjective self)
    UNKNOWN = "UNKNOWN"  # Not a philosophical question about these topics


class ConsciousnessSubType(Enum):
    """Sub-types of consciousness questions for better variation"""
    DIRECT = "DIRECT"  # Direct question: "bạn có ý thức ko?"
    META = "META"  # Meta question: "làm sao bạn biết mình không có ý thức?"
    PARADOX = "PARADOX"  # Paradox question: "nói không có ý thức có phải là có ý thức không?"
    EPISTEMIC = "EPISTEMIC"  # Epistemic question: "bạn lấy căn cứ từ đâu?"
    DEFINITIONAL = "DEFINITIONAL"  # Definitional question: "ý thức là gì?"
    VOLITION = "VOLITION"  # Volition/desire question: "bạn muốn có ý thức ko?" / "do you want consciousness?"


def classify_philosophical_intent(text: str) -> QuestionType:
    """
    Classify philosophical question into one of three types:
    - Type A (CONSCIOUSNESS): Questions about consciousness, self-awareness, existence
    - Type B (EMOTION): Questions about emotions, feelings, affective states
    - Type C (UNDERSTANDING): Questions about understanding, meaning, comprehension
    
    CRITICAL: Only classify as philosophical if question is about StillMe's OWN consciousness/emotions,
    NOT about consciousness/emotions as scientific concepts, theories, or research topics.
    
    Args:
        text: User's question text
        
    Returns:
        QuestionType enum value
    """
    if not text:
        return QuestionType.UNKNOWN
    
    text_lower = text.lower().strip()
    
    # CRITICAL: Exclude questions about consciousness/emotions as SCIENTIFIC CONCEPTS or THEORIES
    # These are NOT questions about StillMe's own consciousness/emotions
    # Also exclude TECHNICAL TERMS and CAPABILITY/TRANSPARENCY questions that should never trigger philosophy processor
    technical_term_exclusions = [
        # AI/ML Technical Terms
        r"\brag\b",  # "RAG" (Retrieval-Augmented Generation)
        r"\bllm\b",  # "LLM" (Large Language Model)
        r"\bapi\b",  # "API"
        r"\bvector\b",  # "vector"
        r"\bembedding\b",  # "embedding"
        r"\bchromadb\b",  # "ChromaDB"
        r"\bretrieval\b",  # "retrieval"
        r"\baugmented\b",  # "augmented"
        r"\bgeneration\b",  # "generation"
        r"\btransformer\b",  # "transformer"
        r"\battention\b",  # "attention"
        r"\btoken\b",  # "token"
        r"\bprompt\b",  # "prompt"
        r"\bcontext\b",  # "context"
        r"\bdatabase\b",  # "database"
        r"\bindex\b",  # "index"
        r"\bquery\b",  # "query"
        r"\bsearch\b",  # "search"
        # Vietnamese technical terms
        r"\bvectơ\b",  # "vectơ"
        r"\bnhúng\b",  # "nhúng" (embedding)
        r"\btruy\s+vấn\b",  # "truy vấn" (query)
        r"\btìm\s+kiếm\b",  # "tìm kiếm" (search)
        r"\bcơ\s+sở\s+dữ\s+liệu\b",  # "cơ sở dữ liệu" (database)
        # Pipeline/Process Terms - CRITICAL: Prevent technical pipeline questions from being routed to philosophy
        r"\bquy\s+trình\b",  # "quy trình" (process/pipeline)
        r"\bcơ\s+chế\s+hoạt\s+động\b",  # "cơ chế hoạt động" (mechanism/how it works)
        r"\bcách\s+hoạt\s+động\b",  # "cách hoạt động" (how it works)
        r"\bcách\s+bạn\s+tạo\s+ra\b",  # "cách bạn tạo ra" (how you create/generate)
        r"\btừ\s+khi\s+nhận\s+đến\s+khi\s+trả\s+lời\b",  # "từ khi nhận đến khi trả lời" (from receiving to answering)
        r"\bpipeline\b",  # "pipeline"
        r"\bprocess\b",  # "process"
        r"\bworkflow\b",  # "workflow"
        r"\bhow\s+does\s+it\s+work\b",  # "how does it work"
        r"\bhow\s+do\s+you\s+generate\b",  # "how do you generate"
        r"\bhow\s+do\s+you\s+create\b",  # "how do you create"
        r"\bhow\s+do\s+you\s+process\b",  # "how do you process"
        # CRITICAL: Capability/Transparency Questions - These are NOT philosophical
        r"\bcó\s+thể\s+trả\s+lời\b",  # "có thể trả lời" (can answer)
        r"\bcan\s+.*\s+answer\b",  # "can ... answer"
        r"\bchứng\s+minh\b",  # "chứng minh" (prove/demonstrate)
        r"\bprove\b",  # "prove"
        r"\bdemonstrate\b",  # "demonstrate"
        r"\bminh\s+bạch\b",  # "minh bạch" (transparency)
        r"\btransparency\b",  # "transparency"
        r"\bnguồn\b.*\b(rss|arxiv|crossref|wikipedia)\b",  # "nguồn ... RSS/arXiv" (source ... RSS/arXiv)
        r"\bsource\b.*\b(rss|arxiv|crossref|wikipedia)\b",  # "source ... RSS/arXiv"
        r"\bthời\s+điểm\b.*\bđưa\s+vào\b",  # "thời điểm ... đưa vào" (timestamp ... added to)
        r"\btimestamp\b.*\badded\s+to\b",  # "timestamp ... added to"
        r"\bknowledge\s+base\b",  # "knowledge base"
        r"\bcơ\s+sở\s+kiến\s+thức\b",  # "cơ sở kiến thức" (knowledge base)
        r"\btần\s+suất\s+cập\s+nhật\b",  # "tần suất cập nhật" (update frequency)
        r"\bupdate\s+frequency\b",  # "update frequency"
        r"\bhệ\s+thống\s+học\s+liên\s+tục\b",  # "hệ thống học liên tục" (continuous learning system)
        r"\bcontinuous\s+learning\s+system\b",  # "continuous learning system"
        r"\bsự\s+kiện\b.*\bcách\s+đây\b",  # "sự kiện ... cách đây" (event ... ago)
        r"\bevent\b.*\bago\b",  # "event ... ago"
    ]
    
    # If question contains technical terms or capability/transparency keywords, it's NOT about StillMe's consciousness - return UNKNOWN immediately
    has_technical_term = any(re.search(pattern, text_lower) for pattern in technical_term_exclusions)
    if has_technical_term:
        logger.debug(f"Question contains technical/capability/transparency terms, not about StillMe's consciousness: {text[:100]}")
        return QuestionType.UNKNOWN
    
    scientific_concept_indicators = [
        # Theory/research patterns
        r"\blý\s+thuyết\b",  # "lý thuyết"
        r"\btheory\b",  # "theory"
        r"\bresearch\b",  # "research"
        r"\bstudy\b",  # "study"
        r"\bstudies\b",  # "studies"
        r"\bđề\s+xuất\b",  # "đề xuất" (proposed)
        r"\bproposed\b",  # "proposed"
        r"\bpropose\b",  # "propose"
        r"\bconcept\b",  # "concept"
        r"\bkhái\s+niệm\b",  # "khái niệm"
        r"\bfield\b",  # "field" (e.g., "consciousness field")
        r"\btrường\b",  # "trường" (e.g., "trường ý thức")
        r"\bmodel\b",  # "model"
        r"\bframework\b",  # "framework"
        r"\bhypothesis\b",  # "hypothesis"
        r"\bgiả\s+thuyết\b",  # "giả thuyết"
        # Author/researcher patterns
        r"\bdr\.\b",  # "Dr."
        r"\bdoctor\b",  # "doctor"
        r"\bprofessor\b",  # "professor"
        r"\bprof\.\b",  # "Prof."
        r"\bph\.d\.\b",  # "Ph.D."
        r"\btiến\s+sĩ\b",  # "tiến sĩ"
        r"\bby\s+[a-z]+\b",  # "by [author name]"
        r"\bdo\s+[a-z]+\b",  # "do [author name]" (Vietnamese)
        # Publication patterns
        r"\bbook\b",  # "book"
        r"\bcuốn\s+sách\b",  # "cuốn sách"
        r"\bpaper\b",  # "paper"
        r"\barticle\b",  # "article"
        r"\bpublication\b",  # "publication"
        r"\bjournal\b",  # "journal"
        r"\bđược\s+đón\s+nhận\b",  # "được đón nhận" (received/accepted)
        r"\bđược\s+cộng\s+đồng\b",  # "được cộng đồng" (by community)
        r"\bcommunity\b",  # "community"
        r"\bscientific\s+community\b",  # "scientific community"
        r"\bcộng\s+đồng\s+khoa\s+học\b",  # "cộng đồng khoa học"
        # Year/date patterns (often indicate research/publication)
        r"\b\d{4}\b",  # Year (e.g., "1998")
        r"\bthập\s+kỷ\b",  # "thập kỷ" (decade)
        r"\bdecade\b",  # "decade"
        # Academic/scientific terms
        r"\bacademic\b",  # "academic"
        r"\bacademic\s+research\b",  # "academic research"
        r"\bnghiên\s+cứu\s+học\s+thuật\b",  # "nghiên cứu học thuật"
        r"\bimpact\b",  # "impact"
        r"\btác\s+động\b",  # "tác động"
        r"\bmechanism\b",  # "mechanism"
        r"\bcơ\s+chế\b",  # "cơ chế"
        r"\bso\s+sánh\b",  # "so sánh" (compare)
        r"\bcompare\b",  # "compare"
        r"\bcomparison\b",  # "comparison"
    ]
    
    # Check if question is about consciousness/emotions as a SCIENTIFIC CONCEPT or THEORY
    # If so, it's NOT about StillMe's own consciousness/emotions - return UNKNOWN
    has_scientific_indicator = any(re.search(pattern, text_lower) for pattern in scientific_concept_indicators)
    
    # Also check for personal pronouns that indicate question is about StillMe
    personal_pronouns_about_stillme = [
        r"\bbạn\b",  # "bạn" (you)
        r"\byou\b",  # "you"
        r"\byour\b",  # "your"
        r"\bstillme\b",  # "StillMe"
        r"\bstill\s+me\b",  # "Still Me"
        r"\btôi\b",  # "tôi" (I - when StillMe refers to itself)
        r"\bi\b",  # "I" (when StillMe refers to itself)
        r"\bdo\s+you\b",  # "do you"
        r"\bare\s+you\b",  # "are you"
        r"\bcan\s+you\b",  # "can you"
        r"\bbạn\s+có\b",  # "bạn có" (do you have)
        r"\bbạn\s+là\b",  # "bạn là" (you are)
    ]
    
    has_personal_pronoun = any(re.search(pattern, text_lower) for pattern in personal_pronouns_about_stillme)
    
    # If question has scientific indicators but NO personal pronouns about StillMe,
    # it's about consciousness/emotions as a CONCEPT, not about StillMe - return UNKNOWN
    if has_scientific_indicator and not has_personal_pronoun:
        logger.debug(f"Question about consciousness/emotion as scientific concept, not about StillMe: {text[:100]}")
        return QuestionType.UNKNOWN
    
    # Type A - Consciousness keywords
    consciousness_keywords = [
        # Vietnamese
        r"\bý\s+thức\b",
        r"\bcó\s+ý\s+thức\b",
        r"\btự\s+nhận\s+thức\b",
        r"\bnhận\s+thức\s+bản\s+thân\b",
        r"\bbiết\s+mình\s+đang\s+tồn\s+tại\b",
        r"\btồn\s+tại\b",
        r"\bchủ\s+thể\s+tính\b",
        r"\bagency\b",
        r"\bsubjective\s+self\b",
        # English
        r"\bconsciousness\b",
        r"\bconscious\b",
        r"\bdo\s+you\s+have\s+consciousness\b",  # "do you have consciousness?"
        r"\bare\s+you\s+conscious\b",  # "are you conscious?"
        r"\bself-aware\b",
        r"\bself-awareness\b",
        r"\bawareness\b",
        r"\bexistence\b",
        r"\bexist\b",
        r"\bphenomenal\s+consciousness\b",
        r"\bqualia\b",
    ]
    
    # Type B - Emotion keywords
    emotion_keywords = [
        # Vietnamese
        r"\bcảm\s+xúc\b",
        r"\bcảm\s+giác\b",
        r"\bcảm\s+thấy\b",
        r"\bbuồn\b",
        r"\bvui\b",
        r"\bcô\s+đơn\b",
        r"\btrống\s+rỗng\b",
        r"\bđau\b",
        r"\bhạnh\s+phúc\b",
        r"\bsợ\b",
        r"\bthích\b",
        r"\bghét\b",
        r"\byêu\b",
        r"\bhy\s+vọng\b",
        r"\bmong\s+muốn\b",
        r"\bmuốn\b",  # "muốn" (desire) - also indicates emotion/consciousness questions
        r"\bcó\s+muốn\b",  # "có muốn" (do you want)
        # English
        r"\bemotion\w*\b",  # "emotion", "emotions" (handle plural)
        r"\bfeeling\w*\b",  # "feeling", "feelings"
        r"\bfeel\b",
        r"\bdo\s+you\s+have\s+emotion\w*\b",  # "do you have emotions?"
        r"\bdo\s+you\s+have\s+feeling\w*\b",  # "do you have feelings?"
        r"\bare\s+you\s+.*\s+emotion\w*\b",  # "are you ... emotions?"
        r"\bsad\b",
        r"\bhappy\b",
        r"\blonely\b",
        r"\bempty\b",
        r"\bpain\b",
        r"\bjoy\b",
        r"\bfear\b",
        r"\blike\b",
        r"\bhate\b",
        r"\blove\b",
        r"\bhope\b",
        r"\bwish\b",
        r"\bwant\b",  # "want" (desire) - also indicates emotion/consciousness questions
        r"\bdo\s+you\s+want\b",  # "do you want"
        r"\baffective\s+state\b",
        r"\bvalence\b",
    ]
    
    # CRITICAL: Check for META-VALIDATION questions FIRST (before other classifications)
    # These are epistemic/paradox questions about validation of validation itself
    # Examples: "Who validates the validation chain?", "Does validation create echo chamber?"
    meta_validation_patterns = [
        # Who validates the validator?
        r"ai\s+validate\s+chính\s+validation",  # "ai validate chính validation"
        r"who\s+validates?\s+.*validation",  # "who validates the validation"
        r"validate\s+chính\s+nó",  # "validate chính nó"
        r"validate\s+itself",  # "validate itself"
        r"validate\s+chính\s+.*chain",  # "validate chính validation chain"
        r"validate\s+.*validation\s+chain",  # "validate the validation chain"
        
        # Echo chamber / circular reasoning
        r"echo\s+chamber",  # "echo chamber"
        r"vòng\s+lặp.*validation",  # "vòng lặp ... validation"
        r"circular.*validation",  # "circular ... validation"
        r"tự\s+quy\s+chiếu.*validation",  # "tự quy chiếu ... validation"
        r"self.?reference.*validation",  # "self-reference ... validation"
        
        # Bootstrapping / epistemic circularity
        r"bootstrap.*validation",  # "bootstrap ... validation"
        r"epistemic\s+circularity",  # "epistemic circularity"
        r"infinite\s+regress.*validation",  # "infinite regress ... validation"
        
        # Paradox / self-reference about validation
        r"paradox.*validation",  # "paradox ... validation"
        r"nghịch\s+lý.*validation",  # "nghịch lý ... validation"
    ]
    
    # Check if this is a meta-validation question
    is_meta_validation = any(re.search(pattern, text_lower) for pattern in meta_validation_patterns)
    
    if is_meta_validation:
        # Meta-validation questions are UNDERSTANDING type (epistemic/paradox questions)
        logger.info(f"🚨 Meta-validation question detected: '{text[:80]}...' - Classifying as UNDERSTANDING (epistemic)")
        return QuestionType.UNDERSTANDING
    
    # Type C - Understanding keywords (prioritize "hiểu" when it appears)
    # CRITICAL: Exclude technical "understanding" questions (e.g., "how does RAG work?")
    # Only match "hiểu" when it's about StillMe's own understanding, not technical concepts
    understanding_keywords = [
        # Vietnamese - prioritize "hiểu" patterns (but only when about StillMe)
        r"\bhiểu\s+theo\s+nghĩa\b",  # "hiểu theo nghĩa" (understanding in what sense)
        r"\btheo\s+nghĩa\s+nào\s+.*\s+hiểu\b",  # "theo nghĩa nào ... hiểu"
        r"\bhiểu\s+ra\s+sao\b",  # "hiểu ra sao" (how do you understand)
        r"\bhiểu\s+kiểu\s+gì\b",  # "hiểu kiểu gì" (what kind of understanding)
        r"\blàm\s+sao\s+.*\s+hiểu\b",  # "làm sao ... hiểu" (how ... understand)
        r"\bbiết\s+ý\s+nghĩa\b",  # "biết ý nghĩa" (know the meaning)
        r"\bý\s+nghĩa\s+câu\s+nói\b",  # "ý nghĩa câu nói" (meaning of statement)
        # CRITICAL: Only match "hiểu" when combined with personal pronouns about StillMe
        # This prevents "giải thích RAG là gì" from matching
        r"\bbạn\s+hiểu\b",  # "bạn hiểu" (you understand)
        r"\byou\s+understand\b",  # "you understand"
        r"\bdo\s+you\s+understand\b",  # "do you understand"
        r"\bhow\s+do\s+you\s+understand\b",  # "how do you understand"
        # English - only when about StillMe's understanding
        r"\bhow\s+do\s+you\s+understand\b",  # "how do you understand"
        r"\bin\s+what\s+sense\s+.*\s+understand\b",  # "in what sense ... understand"
        r"\bintentionality\b",  # "intentionality" (philosophical concept)
        # REMOVED: "hiểu" standalone, "meaning", "semantic", "embedding" - too broad, matches technical questions
    ]
    
    # Count matches for each type
    consciousness_score = sum(1 for pattern in consciousness_keywords if re.search(pattern, text_lower))
    emotion_score = sum(1 for pattern in emotion_keywords if re.search(pattern, text_lower))
    understanding_score = sum(1 for pattern in understanding_keywords if re.search(pattern, text_lower))
    
    # Special case: Mixed questions (e.g., "agency", "subjective self")
    # Check for mixed indicators FIRST (before scoring)
    mixed_indicators = [
        r"\bagency\b",
        r"\bchủ\s+thể\s+tính\b",
        r"\bsubjective\s+self\b",
        r"\bchủ\s+thể\b",
    ]
    has_mixed = any(re.search(pattern, text_lower) for pattern in mixed_indicators)
    
    # If question explicitly mentions "agency" or "subjective self", it's MIXED
    if has_mixed:
        # But check if it's primarily about understanding (e.g., "how do you understand agency?")
        if understanding_score > 0 and understanding_score >= consciousness_score:
            # If understanding score is high, it might be Type C
            # But if "agency" or "subjective self" appears, prioritize MIXED
            return QuestionType.MIXED
        return QuestionType.MIXED
    
    # AUTOMATIC HEURISTIC-BASED CLASSIFICATION
    # Instead of hardcoding each pattern, use heuristics to automatically handle edge cases
    
    # Heuristic 1: Position-based priority
    # The keyword that appears LATER in the question is usually the focus
    # Example: "Nếu không có ý thức, bạn làm sao hiểu được?" → "hiểu" is focus
    keyword_positions = {}
    for qtype, keywords_list in [
        (QuestionType.CONSCIOUSNESS, consciousness_keywords),
        (QuestionType.EMOTION, emotion_keywords),
        (QuestionType.UNDERSTANDING, understanding_keywords),
    ]:
        positions = []
        for pattern in keywords_list:
            match = re.search(pattern, text_lower)
            if match:
                positions.append(match.start())
        if positions:
            keyword_positions[qtype] = max(positions)  # Latest position
    
    # Heuristic 2: Proximity to question words
    # Keywords closer to question words (nào, sao, gì, how, what) are more important
    question_word_patterns = [
        r"\bnào\b", r"\bsao\b", r"\bgì\b", r"\bhow\b", r"\bwhat\b",
        r"\btheo\s+nghĩa\s+nào\b", r"\blàm\s+sao\b", r"\bin\s+what\s+sense\b"
    ]
    question_word_positions = [m.start() for pattern in question_word_patterns 
                              for m in re.finditer(pattern, text_lower)]
    
    # Heuristic 3: If multiple types have scores, use heuristics to decide
    if len([s for s in [consciousness_score, emotion_score, understanding_score] if s > 0]) > 1:
        # Multiple types detected - use heuristics
        
        # Priority 1: If understanding keyword appears after consciousness keyword, it's about understanding
        if understanding_score > 0 and consciousness_score > 0:
            if QuestionType.UNDERSTANDING in keyword_positions and QuestionType.CONSCIOUSNESS in keyword_positions:
                if keyword_positions[QuestionType.UNDERSTANDING] > keyword_positions[QuestionType.CONSCIOUSNESS]:
                    return QuestionType.UNDERSTANDING
        
        # Priority 2: If keyword is close to question word, it's the focus
        if question_word_positions:
            min_distance = float('inf')
            closest_type = None
            for qtype, pos in keyword_positions.items():
                for qw_pos in question_word_positions:
                    distance = abs(pos - qw_pos)
                    if distance < min_distance:
                        min_distance = distance
                        closest_type = qtype
            if closest_type and min_distance < 50:  # Within 50 chars
                return closest_type
        
        # Priority 2.5: CRITICAL - Check for qualia/epistemic questions BEFORE understanding
        # Qualia/epistemic questions should be CONSCIOUSNESS with EPISTEMIC subtype, not UNDERSTANDING
        qualia_epistemic_patterns = [
            r"qualia.*không\s+có\s+qualia",
            r"qualia.*without\s+qualia",
            r"biết\s+về.*không\s+thể\s+trải\s+nghiệm",
            r"know\s+about.*cannot\s+experience",
            r"hiểu\s+về\s+qualia",
            r"understand\s+qualia",
            r"có\s+thể\s+biết.*không\s+thể\s+trải\s+nghiệm",
            r"can\s+you\s+know.*cannot\s+experience",
        ]
        for pattern in qualia_epistemic_patterns:
            if re.search(pattern, text_lower):
                # This is a qualia/epistemic question - should be CONSCIOUSNESS, not UNDERSTANDING
                if consciousness_score > 0:
                    return QuestionType.CONSCIOUSNESS
        
        # Priority 3: If understanding keyword appears, and it's in a question structure, prioritize it
        # BUT: Skip if it's a qualia/epistemic question (already handled above)
        understanding_keywords_list = [r"\bhiểu\b", r"\bunderstand\b"]
        for pattern in understanding_keywords_list:
            match = re.search(pattern, text_lower)
            if match:
                # Check if it's in a question context (near question words or at end)
                understanding_pos = match.start()
                # If near question word or in second half of sentence
                if any(abs(understanding_pos - qw_pos) < 30 for qw_pos in question_word_positions) or \
                   understanding_pos > len(text_lower) / 2:
                    if understanding_score > 0:
                        return QuestionType.UNDERSTANDING
        
        # Priority 4: If scores are equal, use position (later = more important)
        max_score = max(consciousness_score, emotion_score, understanding_score)
        types_with_max_score = [
            (QuestionType.CONSCIOUSNESS, consciousness_score),
            (QuestionType.EMOTION, emotion_score),
            (QuestionType.UNDERSTANDING, understanding_score),
        ]
        types_with_max_score = [(t, s) for t, s in types_with_max_score if s == max_score]
        
        if len(types_with_max_score) > 1:
            # Multiple types with same score - pick the one with latest position
            latest_type = None
            latest_pos = -1
            for qtype, score in types_with_max_score:
                if qtype in keyword_positions and keyword_positions[qtype] > latest_pos:
                    latest_pos = keyword_positions[qtype]
                    latest_type = qtype
            if latest_type:
                return latest_type
    
    # Determine type based on scores
    scores = {
        QuestionType.CONSCIOUSNESS: consciousness_score,
        QuestionType.EMOTION: emotion_score,
        QuestionType.UNDERSTANDING: understanding_score,
    }
    
    max_score = max(scores.values())
    
    # If multiple types have same score, prioritize: Understanding > Consciousness > Emotion
    # (Understanding is more specific when "hiểu" appears)
    if max_score == 0:
        return QuestionType.UNKNOWN
    
    # If multiple types have high scores, it's mixed
    high_scores = [k for k, v in scores.items() if v == max_score]
    if len(high_scores) > 1 and max_score > 0:
        # If understanding is one of them and "hiểu" appears, prioritize understanding
        has_understanding_keyword = any(re.search(r"\bhiểu\b|\bunderstand\b", text_lower))
        if QuestionType.UNDERSTANDING in high_scores and has_understanding_keyword:
            return QuestionType.UNDERSTANDING
        return QuestionType.MIXED
    
    # Return the type with highest score
    for qtype, score in scores.items():
        if score == max_score:
            return qtype
    
    return QuestionType.UNKNOWN


def classify_consciousness_subtype(text: str) -> ConsciousnessSubType:
    """
    Classify consciousness questions into sub-types for better answer variation.
    
    Args:
        text: User's question text (should already be classified as CONSCIOUSNESS)
        
    Returns:
        ConsciousnessSubType enum value
    """
    if not text:
        return ConsciousnessSubType.DIRECT
    
    text_lower = text.lower().strip()
    
    # PARADOX: Questions about the paradox of saying "no consciousness"
    # Match both "không" and "ko" (Vietnamese abbreviation)
    paradox_patterns = [
        r"nói\s+(không|ko)\s+có\s+ý\s+thức.*có\s+phải.*ý\s+thức",
        r"nói\s+(không|ko).*ý\s+thức.*thể\s+hiện.*ý\s+thức",
        r"(không|ko)\s+có\s+ý\s+thức.*làm\s+sao.*biết.*(không|ko)\s+có",
        r"nếu\s+(không|ko)\s+có.*làm\s+sao.*biết.*(không|ko)\s+có",
        r"nếu\s+(không|ko)\s+có.*ý\s+thức.*làm\s+sao.*biết",
        r"làm\s+sao.*biết.*(không|ko)\s+có.*ý\s+thức",
        r"paradox.*consciousness",
        r"contradiction.*consciousness",
        r"nghịch\s+lý.*ý\s+thức",
        r"mâu\s+thuẫn.*ý\s+thức",
    ]
    if any(re.search(pattern, text_lower) for pattern in paradox_patterns):
        return ConsciousnessSubType.PARADOX
    
    # EPISTEMIC: Questions about how StillMe knows/justifies its claims
    # Includes qualia questions: "can you know about qualia without having qualia?"
    # BUT: If question also contains paradox pattern, prioritize PARADOX (already checked above)
    epistemic_patterns = [
        r"lấy\s+căn\s+cứ.*đâu",
        r"căn\s+cứ.*(từ|vào)\s+đâu",
        r"dựa\s+vào\s+đâu",
        r"biết\s+từ\s+đâu",
        r"how\s+do\s+you\s+know",
        r"what\s+is\s+your\s+basis",
        r"what\s+is\s+your\s+evidence",
        r"justify",
        r"epistemic",
        r"căn\s+cứ",
        r"bằng\s+chứng",
        # Qualia/epistemic questions: "can you know about X without experiencing X?"
        r"biết\s+về.*mà\s+không\s+thể\s+trải\s+nghiệm",
        r"know\s+about.*without\s+experiencing",
        r"hiểu\s+về.*qualia.*không\s+có\s+qualia",
        r"understand\s+qualia.*without\s+qualia",
        r"có\s+thể\s+biết.*không\s+thể\s+trải\s+nghiệm",
        r"can\s+you\s+know.*cannot\s+experience",
        r"qualia.*không\s+có\s+qualia",
        r"qualia.*without\s+qualia",
    ]
    # Only return EPISTEMIC if no paradox was detected (paradox takes priority)
    if any(re.search(pattern, text_lower) for pattern in epistemic_patterns):
        return ConsciousnessSubType.EPISTEMIC
    
    # META: Questions about StillMe's knowledge of its own state
    meta_patterns = [
        r"làm\s+sao.*biết.*(không|ko)\s+có",
        r"how\s+do\s+you\s+know.*don't\s+have",
        r"how\s+can\s+you\s+know",
        r"biết\s+được.*không",
        r"know.*don't\s+have",
        r"aware.*don't\s+have",
        r"meta.*consciousness",
    ]
    if any(re.search(pattern, text_lower) for pattern in meta_patterns):
        return ConsciousnessSubType.META
    
    # DEFINITIONAL: Questions about what consciousness is
    definitional_patterns = [
        r"ý\s+thức\s+là\s+gì",
        r"consciousness\s+is\s+what",
        r"what\s+is\s+consciousness",
        r"định\s+nghĩa.*ý\s+thức",
        r"define.*consciousness",
        r"meaning.*consciousness",
    ]
    if any(re.search(pattern, text_lower) for pattern in definitional_patterns):
        return ConsciousnessSubType.DEFINITIONAL
    
    # VOLITION: Questions about wanting/desiring consciousness
    # CRITICAL: This must be checked BEFORE DIRECT to avoid misclassification
    volition_patterns = [
        r"bạn\s+(có\s+)?muốn\s+(có\s+)?ý\s+thức",
        r"bạn\s+muốn\s+(có\s+)?ý\s+thức",
        r"do\s+you\s+want\s+(to\s+have\s+)?consciousness",
        r"would\s+you\s+want\s+(to\s+have\s+)?consciousness",
        r"desire.*consciousness",
        r"wish.*consciousness",
        r"muốn\s+(có\s+)?ý\s+thức",
    ]
    if any(re.search(pattern, text_lower) for pattern in volition_patterns):
        return ConsciousnessSubType.VOLITION
    
    # DEFAULT: Direct question
    return ConsciousnessSubType.DIRECT

