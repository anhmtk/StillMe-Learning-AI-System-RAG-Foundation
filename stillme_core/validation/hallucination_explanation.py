"""
Hallucination Explanation Validator - Ensures technical depth in hallucination explanations

This validator ensures that when StillMe explains hallucinations, it includes:
- Next-token prediction objective
- Decoding strategies (temperature, top-p)
- Training vs inference distribution mismatch
- Attention mechanism limitations

This addresses the gap where StillMe explains hallucinations as "lack of data" 
but doesn't explain the fundamental LLM mechanics that cause them.
"""

import re
import logging
from typing import List, Optional
from .base import Validator, ValidationResult

logger = logging.getLogger(__name__)


class HallucinationExplanationValidator(Validator):
    """
    Validator that ensures hallucination explanations include technical LLM mechanics
    
    Detects when StillMe mentions hallucinations but doesn't explain:
    - Autoregressive generation
    - Next-token prediction objective
    - Decoding strategies
    - Training vs inference distribution mismatch
    - Attention mechanism limitations
    """
    
    def __init__(self, strict_mode: bool = True, auto_patch: bool = True):
        """
        Initialize hallucination explanation validator
        
        Args:
            strict_mode: If True, fail when explanation is too shallow. If False, only warn.
            auto_patch: If True, automatically add technical explanation when missing
        """
        self.strict_mode = strict_mode
        self.auto_patch = auto_patch
        
        # Patterns that indicate hallucination discussion
        self.hallucination_indicators = [
            r"hallucination",
            r"bịa",
            r"fabricat",
            r"make up",
            r"invent",
            r"false information",
            r"incorrect information",
            r"không chính xác",
            r"sai thông tin",
        ]
        
        # Technical terms that should appear in good explanations
        self.technical_terms = [
            r"next-token prediction",
            r"autoregressive",
            r"decoding strategy",
            r"temperature",
            r"top-p",
            r"training distribution",
            r"inference distribution",
            r"attention mechanism",
            r"transformer",
            r"language model",
            r"llm",
            r"mô hình ngôn ngữ",
            r"dự đoán token tiếp theo",
            r"phân phối huấn luyện",
            r"cơ chế attention",
        ]
        
        # Compile patterns
        self.hallucination_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.hallucination_indicators
        ]
        self.technical_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.technical_terms
        ]
    
    def run(self, answer: str, ctx_docs: List[str], user_question: Optional[str] = None) -> ValidationResult:
        """
        Check if answer explains hallucinations with technical depth
        
        Args:
            answer: The answer to validate
            ctx_docs: List of context documents (not used)
            user_question: Optional user question for context
            
        Returns:
            ValidationResult with passed status and patched answer if needed
        """
        if not answer:
            return ValidationResult(passed=True)
        
        answer_lower = answer.lower()
        
        # Check if answer mentions hallucinations
        mentions_hallucination = any(
            pattern.search(answer_lower) 
            for pattern in self.hallucination_patterns
        )
        
        if not mentions_hallucination:
            # Not discussing hallucinations, skip validation
            return ValidationResult(passed=True)
        
        # Check if explanation includes technical terms
        has_technical_explanation = any(
            pattern.search(answer_lower) 
            for pattern in self.technical_patterns
        )
        
        if has_technical_explanation:
            # Good explanation, pass
            logger.debug("HallucinationExplanationValidator: Technical explanation found")
            return ValidationResult(passed=True)
        
        # Shallow explanation detected
        logger.warning(
            "HallucinationExplanationValidator: Hallucination mentioned but explanation lacks technical depth"
        )
        
        if self.auto_patch:
            # Add technical explanation
            patched_answer = self._add_technical_explanation(answer, user_question)
            return ValidationResult(
                passed=True,  # Pass after patching
                patched_answer=patched_answer,
                reasons=["hallucination_explanation_enhanced"]
            )
        else:
            # Just flag it
            if self.strict_mode:
                return ValidationResult(
                    passed=False,
                    reasons=["hallucination_explanation_too_shallow"]
                )
            else:
                return ValidationResult(
                    passed=True,
                    reasons=["hallucination_explanation_warning: lacks technical depth"]
                )
    
    def _add_technical_explanation(self, answer: str, user_question: Optional[str] = None) -> str:
        """
        Add technical explanation of hallucinations to answer
        
        Args:
            answer: Original answer
            user_question: Optional user question for context
            
        Returns:
            Answer with technical explanation added
        """
        # Detect language
        detected_lang = "vi"
        if user_question:
            try:
                from backend.api.utils.chat_helpers import detect_language
                detected_lang = detect_language(user_question)
            except Exception:
                pass
        
        # Technical explanation template
        if detected_lang == "vi":
            technical_explanation = """

**Giải thích kỹ thuật về Hallucination:**

Hallucination xảy ra do cơ chế hoạt động cơ bản của LLM:

1. **Next-token prediction (Dự đoán token tiếp theo)**: LLM được huấn luyện để dự đoán token tiếp theo dựa trên context, không phải để tạo ra thông tin chính xác. Mục tiêu là `P(token_n | tokens_1..n-1)`, không phải truth.

2. **Decoding strategies (Chiến lược giải mã)**: Temperature, top-p, và beam search ảnh hưởng đến độ "sáng tạo" của output. Temperature cao → nhiều hallucination hơn.

3. **Training vs Inference distribution mismatch**: LLM được huấn luyện trên một phân phối dữ liệu, nhưng khi inference (đặc biệt với RAG context), phân phối có thể khác → model "extrapolate" sai.

4. **Attention mechanism limitations**: Transformer attention có thể "over-weight" một số tokens, dẫn đến việc model "tập trung" vào thông tin sai.

5. **Reward model misalignment**: Mục tiêu huấn luyện (next-token prediction) ≠ mục tiêu người dùng (truth) → model tối ưu cho điều sai.

StillMe giảm hallucination bằng cách:
- RAG grounding (chỉ dùng thông tin từ knowledge base)
- Validation chain (kiểm tra citations, evidence overlap)
- Epistemic fallback (nói "không biết" thay vì bịa)
"""
        else:
            technical_explanation = """

**Technical Explanation of Hallucinations:**

Hallucinations occur due to fundamental LLM mechanics:

1. **Next-token prediction objective**: LLMs are trained to predict the next token based on context, not to generate accurate information. The objective is `P(token_n | tokens_1..n-1)`, not truth.

2. **Decoding strategies**: Temperature, top-p, and beam search affect output "creativity". Higher temperature → more hallucinations.

3. **Training vs inference distribution mismatch**: LLMs are trained on one data distribution, but during inference (especially with RAG context), the distribution may differ → model "extrapolates" incorrectly.

4. **Attention mechanism limitations**: Transformer attention can "over-weight" certain tokens, causing the model to "focus" on incorrect information.

5. **Reward model misalignment**: Training objective (next-token prediction) ≠ user objective (truth) → model optimizes for the wrong thing.

StillMe reduces hallucinations by:
- RAG grounding (only using information from knowledge base)
- Validation chain (checking citations, evidence overlap)
- Epistemic fallback (saying "I don't know" instead of fabricating)
"""
        
        # Insert explanation before the end, or append if answer is short
        if len(answer) > 500:
            # Insert before last paragraph
            lines = answer.split('\n')
            if len(lines) > 3:
                # Insert before last 2 lines
                lines.insert(-2, technical_explanation)
                return '\n'.join(lines)
        
        # Append if answer is short
        return answer + technical_explanation

