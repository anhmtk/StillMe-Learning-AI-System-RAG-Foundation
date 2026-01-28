"""
CitationRequired validator - Ensures answers include citations
"""

import re
from typing import List, Any, Optional, Dict
from .base import ValidationResult
import logging

logger = logging.getLogger(__name__)

# Pattern to match citations like [1], [2], [123] (for backward compatibility)
CITE_RE = re.compile(r"\[(\d+)\]")

# Pattern to match human-readable citations like [general knowledge], [research: Wikipedia]
HUMAN_READABLE_CITE_RE = re.compile(r'\[(?:general knowledge|research:|learning:|news:|reference:|foundational knowledge|discussion context|verified sources|needs research|personal analysis)[^\]]*\]', re.IGNORECASE)


class CitationRequired:
    """Validator that requires citations in answers"""
    
    def __init__(self, required: bool = True):
        """
        Initialize citation validator
        
        Args:
            required: Whether citations are required (default: True)
        """
        self.required = required
        # Import citation formatter
        try:
            from backend.utils.citation_formatter import get_citation_formatter
            self.citation_formatter = get_citation_formatter()
        except ImportError:
            logger.warning("CitationFormatter not available - using legacy numeric citations")
            self.citation_formatter = None
    
    def run(self, answer: str, ctx_docs: List[Any], is_philosophical: bool = False, user_question: str = "", context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Check if answer contains citations and auto-enforce if missing
        
        Args:
            answer: The answer to validate
            ctx_docs: List of context documents (can be dicts or objects with metadata) - if empty, citations are not required
            is_philosophical: If True, relax citation requirements for pure philosophical questions (but still require for factual claims)
            user_question: User's original question (to detect if it's a factual question with philosophical elements)
            context: Optional context dict with knowledge_docs (for foundational knowledge detection)
            
        Returns:
            ValidationResult with passed status and patched answer if citation was added
        """
        # CRITICAL: Skip citation for questions about StillMe's own codebase
        # These are self-knowledge questions - no external citation needed
        if user_question:
            question_lower = user_question.lower()
            codebase_self_patterns = [
                r"codebase.*của.*bạn",
                r"codebase.*of.*you",
                r"codebase.*stillme",
                r"validator.*trong.*codebase",
                r"validator.*in.*codebase",
                r"lớp.*validator.*trong.*codebase",
                r"layer.*validator.*in.*codebase",
                r"bao nhiêu.*lớp.*validator.*codebase",
                r"how many.*layer.*validator.*codebase"
            ]
            
            for pattern in codebase_self_patterns:
                if re.search(pattern, question_lower, re.IGNORECASE):
                    logger.info(f"✅ Self-knowledge question about codebase detected - skipping citation requirement")
                    return ValidationResult(passed=True, reasons=["self_knowledge_codebase_question"])
        # CRITICAL: Skip citation for StillMe self-knowledge questions (identity, differences, goals)
        if context and isinstance(context, dict) and context.get("is_self_knowledge_question"):
            logger.info("✅ Self-knowledge question detected - skipping citation requirement")
            return ValidationResult(passed=True, reasons=["self_knowledge_question"])
        
        # Fallback: detect self-knowledge directly from the user question
        if user_question:
            question_lower = user_question.lower()
            self_knowledge_patterns = [
                r"\b(bạn|you)\s+(là|là\s+ai|who\s+are|who\s+is)\b",
                r"\b(bạn|you)\s+(khác\s+biệt|khac\s+biet|different)\b",
                r"\b(điểm\s+khác\s+biệt|điểm\s+gì\s+khác\s+biệt|khac\s+biet)\b",
                r"\b(bạn|you)\s+(đặc\s+biệt|dac\s+biet|special|unique)\b",
                r"\b(bạn|you)\s+(ưu\s+điểm|uu\s+diem|nhược\s+điểm|nhuoc\s+diem|điểm\s+mạnh|diem\s+manh|điểm\s+yếu|diem\s+yeu)\b",
                r"\bwhat\s+(makes|make)\s+(you|bạn)\s+(different|unique|special)\b",
                r"\b(your|bạn)\s+(strength|strengths|weakness|weaknesses|advantages|disadvantages)\b",
                r"\b(stillme)\b",
            ]
            for pattern in self_knowledge_patterns:
                if re.search(pattern, question_lower, re.IGNORECASE):
                    logger.info("✅ Self-knowledge question detected (pattern) - skipping citation requirement")
                    return ValidationResult(passed=True, reasons=["self_knowledge_question_pattern"])

        def _is_source_required_question(question: str) -> bool:
            if not question:
                return False
            q_lower = question.lower()
            source_patterns = [
                r"dẫn\s+nguồn",
                r"nguồn\s+.*(đâu|nào|chính\s+xác)",
                r"có\s+nguồn\s+không",
                r"cho\s+mình\s+nguồn",
                r"timestamp",
                r"thời\s+gian\s+chính\s+xác",
                r"link|liên\s+kết|url",
                r"citation|reference|source",
                r"doi",
            ]
            for pattern in source_patterns:
                if re.search(pattern, q_lower, re.IGNORECASE):
                    return True
            return False

        def _build_no_source_response(question: str) -> str:
            if not question:
                return "Mình không có nguồn để dẫn nên không thể trả lời chính xác."
            # Simple language check
            vi_markers = ["bạn", "nguồn", "dẫn", "thời gian", "liên kết", "mình", "không"]
            is_vi = any(marker in question.lower() for marker in vi_markers)
            if is_vi:
                return (
                    "Mình không có nguồn đáng tin cậy trong RAG cho câu hỏi này, "
                    "nên mình không thể dẫn nguồn hoặc timestamp chính xác. "
                    "Nếu bạn muốn, mình có thể nói rõ mình thiếu nguồn gì để bạn bổ sung."
                )
            return (
                "I don't have reliable sources in RAG for this question, "
                "so I can't provide accurate sources or timestamps. "
                "If you'd like, I can specify what sources are missing."
            )
        
        if not self.required:
            return ValidationResult(passed=True)
        is_system_status_query = bool(context and isinstance(context, dict) and context.get("is_system_status_query"))

        is_source_required = _is_source_required_question(user_question)
        
        # CRITICAL FIX: Real factual questions (history, science, events) ALWAYS need citations
        # Even if they have philosophical elements, they are still factual questions
        # Examples: "Bretton Woods 1944", "Popper vs Kuhn", "Gödel's incompleteness theorem"
        # ALSO: Simple factual questions (geography, math, science, literature) need citations too
        is_real_factual_question = False
        is_simple_factual_question = False
        if user_question:
            question_lower = user_question.lower()
            
            # CRITICAL: Detect simple factual questions (geography, math, science, literature)
            # These are factual questions that need citations even if not historical/philosophical
            simple_factual_patterns = [
                r"\b(what is|what's|what are|what were|who is|who's|who are|who were|when is|when was|where is|where was|how many|how much)\b",  # Question words
                r"\b(capital|largest|smallest|fastest|slowest|biggest|tallest|longest|shortest|highest|lowest)\b",  # Comparative/superlative
                r"\b(wrote|author|novel|book|poem|play)\b",  # Literature
                r"\b(chemical symbol|element|atomic|molecule)\b",  # Chemistry
                r"\b(planet|solar system|star|galaxy|universe|earth|moon|sun)\b",  # Astronomy
                r"\b(speed|velocity|distance|time|light|sound|gravity)\b",  # Physics
                r"\b(prime number|even|odd|sum|difference|product|quotient|equation)\b",  # Math
                r"\b(country|city|nation|continent|ocean|sea|river|mountain)\b",  # Geography
                r"\b(boiling point|melting point|freezing point|temperature)\b",  # Science
            ]
            
            for pattern in simple_factual_patterns:
                try:
                    if re.search(pattern, question_lower, re.IGNORECASE):
                        is_simple_factual_question = True
                        logger.debug(f"✅ Detected simple factual question with pattern: {pattern[:50]}... (question: {user_question[:100]})")
                        break
                except Exception as e:
                    logger.warning(f"⚠️ Error matching simple factual pattern {pattern[:50]}: {e}")
                    continue
            
            # Detect factual indicators: years, historical events, specific people, conferences, treaties
            # CRITICAL: Expanded patterns to catch ALL factual questions, including philosophical ones with factual elements
            # IMPORTANT: Patterns must work for both English and Vietnamese questions
            factual_indicators = [
                r"\b\d{4}\b",  # Years (e.g., 1944, 1943, 1954)
                r"\b(conference|hội nghị|treaty|hiệp ước|agreement|hiệp định)\b",
                r"\b(bretton\s+woods|popper|kuhn|gödel|godel|keynes|imf|world\s+bank|searle|dennett|chinese\s+room|russell|plato|aristotle|kant|hume|descartes|spinoza)\b",
                r"\b(historical|history|lịch sử|sự kiện|event)\b",
                r"\b(scientist|philosopher|nhà khoa học|triết gia)\s+\w+",  # Named people
                # CRITICAL: Detect named philosophers/scientists (capitalized names)
                r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b",  # Two capitalized words (e.g., "Searle và Dennett", "Popper và Kuhn")
                r"\b([A-Z][a-z]+)\s+(và|and|vs|versus)\s+([A-Z][a-z]+)\b",  # "Searle và Dennett", "Popper vs Kuhn", "Plato và Aristotle", "Kant và Hume", "Descartes và Spinoza"
                # CRITICAL: Detect theorems, debates, arguments about specific people/concepts
                # Vietnamese: "Định lý của Gödel", "Tranh luận về Searle", "Paradox của Russell"
                # English: "Gödel's theorem", "Searle's argument", "Russell's paradox"
                r"\b(định\s+lý|theorem|tranh\s+luận|debate|argument|paradox|nghịch\s+lý|nghịch\s+lí)\s+(của|of|về|about)\s+([A-Z][a-z]+)",  # "Định lý của Gödel", "Tranh luận về Searle", "Paradox của Russell"
                r"\b([A-Z][a-z]+)'?s\s+(theorem|paradox|argument|debate|incompleteness)",  # "Gödel's theorem", "Russell's paradox"
                r"\b(gödel|godel|searle|dennett|popper|kuhn|russell|plato|aristotle|kant|hume|descartes|spinoza)\b",  # Direct mentions of well-known philosophers/scientists (case-insensitive)
                r"\b(incompleteness|bất\s+toàn|chinese\s+room|russell.*paradox|paradox.*russell|russell.*tập\s+hợp)\b",  # Well-known concepts/theorems
                # CRITICAL: Detect "Paradox của Russell" or "Russell's paradox" (case-insensitive, flexible word order)
                r"\b(russell|russell's)\s+(paradox|nghịch\s+lý|nghịch\s+lí)\b",
                r"\b(paradox|nghịch\s+lý|nghịch\s+lí)\s+(của|of)\s+(russell|russell's)\b",
                r"\b(russell|russell's)\b.*\b(paradox|nghịch\s+lý|nghịch\s+lí)\b",  # "Russell...paradox" (words can be separated)
                r"\b(paradox|nghịch\s+lý|nghịch\s+lí)\b.*\b(russell|russell's)\b",  # "paradox...Russell" (words can be separated)
                # CRITICAL: Detect "Tranh luận giữa X và Y" pattern (case-insensitive, Vietnamese)
                r"\b(tranh\s+luận|debate|argument)\s+(giữa|between)\s+([A-Z][a-z]+)\s+(và|and)\s+([A-Z][a-z]+)\b",
                # CRITICAL: Detect "forms" (hình thức) with Plato/Aristotle (case-insensitive, flexible word order)
                r"\b(plato|aristotle).*(forms|hình\s+thức|thực\s+tại|reality)\b",
                r"\b(forms|hình\s+thức).*(plato|aristotle)\b",
                # CRITICAL: Detect "causality" (quan hệ nhân quả) with Kant/Hume (case-insensitive, flexible word order)
                r"\b(kant|hume).*(causality|quan\s+hệ\s+nhân\s+quả|causation)\b",
                r"\b(causality|quan\s+hệ\s+nhân\s+quả|causation).*(kant|hume)\b",
                # CRITICAL: Detect "mind-body" (tâm-thể) with Descartes/Spinoza (case-insensitive, flexible word order)
                r"\b(descartes|spinoza).*(mind.*body|tâm.*thể|consciousness|ý\s+thức|matter|vật\s+chất)\b",
                r"\b(mind.*body|tâm.*thể).*(descartes|spinoza)\b",
                # CRITICAL: Detect "Geneva 1954" or "Hiệp ước Geneva 1954" (case-insensitive)
                r"\b(geneva|genève)\s+\d{4}\b",
                r"\b(hiệp\s+ước|hiệp\s+định|treaty|agreement)\s+(geneva|genève)\b",
                # CRITICAL: Detect "Bretton Woods 1944" (case-insensitive)
                r"\b(bretton\s+woods)\s+\d{4}\b",
                r"\b(hội\s+nghị|conference)\s+(bretton\s+woods)\b",
                # CRITICAL: Detect "Versailles 1919" or "Hiệp ước Versailles 1919" (case-insensitive)
                r"\b(versailles|versaille)\s+\d{4}\b",
                r"\b(hiệp\s+ước|treaty|agreement)\s+(versailles|versaille)\b",
                # CRITICAL: Detect "Yalta 1945" or "Hội nghị Yalta 1945" (case-insensitive)
                r"\b(yalta|yalta\s+conference)\s+\d{4}\b",
                r"\b(hội\s+nghị|conference)\s+(yalta)\b",
                # CRITICAL: Detect "Potsdam 1945" or "Hội nghị Potsdam 1945" (case-insensitive)
                r"\b(potsdam|potsdam\s+conference)\s+\d{4}\b",
                r"\b(hội\s+nghị|conference)\s+(potsdam)\b",
                # CRITICAL: Detect "World War I" or "Thế chiến I" (case-insensitive)
                r"\b(world\s+war\s+i|thế\s+chiến\s+i|chiến\s+tranh\s+thế\s+giới\s+thứ\s+nhất)\b",
                # CRITICAL: Detect "World War II" or "Thế chiến II" (case-insensitive)
                r"\b(world\s+war\s+ii|thế\s+chiến\s+ii|chiến\s+tranh\s+thế\s+giới\s+thứ\s+hai)\b",
                # CRITICAL: Detect "17th parallel" or "vĩ tuyến 17" (case-insensitive)
                r"\b(\d+th|\d+st|\d+nd|\d+rd)\s+parallel\b",
                r"\b(vĩ\s+tuyến|parallel)\s+\d+\b",
                # CRITICAL: Detect "Gödel's incompleteness theorem" or "Định lý bất toàn của Gödel" (case-insensitive, flexible word order)
                r"\b(gödel|godel).*(incompleteness|bất\s+toàn)\b",
                r"\b(incompleteness|bất\s+toàn).*(gödel|godel)\b",
                r"\b(định\s+lý|theorem)\s+(bất\s+toàn|incompleteness)\s+(của|of)\s+(gödel|godel)\b",
                r"\b(bất\s+toàn|incompleteness)\s+(của|of)\s+(gödel|godel)\b",
                # CRITICAL: Detect "Chinese Room" with Searle/Dennett (case-insensitive, flexible word order)
                r"\b(chinese\s+room|phòng\s+trung\s+quốc).*(searle|dennett)\b",
                r"\b(searle|dennett).*(chinese\s+room|phòng\s+trung\s+quốc)\b",
            ]
            for pattern in factual_indicators:
                try:
                    if re.search(pattern, question_lower, re.IGNORECASE):
                        is_real_factual_question = True
                        logger.debug(f"✅ Detected real factual question with pattern: {pattern[:50]}... (question: {user_question[:100]})")
                        break
                except Exception as e:
                    logger.warning(f"⚠️ Error matching pattern {pattern[:50]}: {e}")
                    continue
        
        # CRITICAL FIX: Check for philosophical factual questions BEFORE early return
        # Philosophical questions with factual elements (named philosophers, theorems, debates) still need citations
        is_philosophical_factual = False
        if is_philosophical and user_question:
            question_lower = user_question.lower()
            # Check for specific philosophers, theorems, debates mentioned in question
            philosophical_factual_indicators = [
                r"\b(russell|gödel|godel|plato|aristotle|kant|hume|descartes|spinoza|searle|dennett|popper|kuhn|berkeley|locke|leibniz|feyerabend|lakatos)\b",
                r"\b(paradox|nghịch\s+lý|theorem|định\s+lý|incompleteness|bất\s+toàn)\b",
                r"\b(tranh\s+luận|debate|argument|forms|hình\s+thức|causality|quan\s+hệ\s+nhân\s+quả)\b",
                r"\b(chinese\s+room|mind.*body|tâm.*thể)\b",
                r"\b(monads|đơn tử|primary.*secondary|qualities|phẩm chất)\b",
                # CRITICAL: Vietnamese patterns for philosophical factual questions
                r"\b(paradox|nghịch\s+lý)\s+(của|of)\s+(russell|gödel|godel)\b",
                r"\b(russell|gödel|godel).*(paradox|nghịch\s+lý)\b",
                r"\b(định\s+lý|theorem)\s+(bất\s+toàn|incompleteness)\s+(của|of)\s+(gödel|godel)\b",
                r"\b(gödel|godel).*(bất\s+toàn|incompleteness)\b",
                r"\b(tranh\s+luận|debate)\s+(giữa|between)\s+(plato|aristotle|kant|hume|searle|dennett|popper|kuhn|descartes|spinoza|berkeley|locke|leibniz|feyerabend|lakatos)\s+(và|and)\s+(plato|aristotle|kant|hume|searle|dennett|popper|kuhn|descartes|spinoza|berkeley|locke|leibniz|feyerabend|lakatos)\b",
                # CRITICAL: Detect "Tranh luận giữa X và Y về Z" (Vietnamese pattern with "về" - allow any words after "về")
                r"\b(tranh\s+luận|debate)\s+(giữa|between)\s+(plato|aristotle|kant|hume|searle|dennett|popper|kuhn|descartes|spinoza|berkeley|locke|leibniz|feyerabend|lakatos)\s+(và|and)\s+(plato|aristotle|kant|hume|searle|dennett|popper|kuhn|descartes|spinoza|berkeley|locke|leibniz|feyerabend|lakatos)\s+(về|about)\s+",
                # CRITICAL: Detect "primary và secondary qualities" or "phẩm chất sơ cấp và thứ cấp" (Berkeley-Locke)
                r"\b(primary|sơ\s+cấp)\s+(và|and)\s+(secondary|thứ\s+cấp)\s+(qualities|phẩm\s+chất)\b",
                r"\b(phẩm\s+chất|qualities)\s+(sơ\s+cấp|primary)\s+(và|and)\s+(thứ\s+cấp|secondary)\b",
            ]
            for pattern in philosophical_factual_indicators:
                try:
                    if re.search(pattern, question_lower, re.IGNORECASE):
                        is_philosophical_factual = True
                        logger.warning(f"✅ Detected philosophical factual question with pattern: {pattern[:50]}... (question: {user_question[:100]})")
                        break
                except Exception as e:
                    logger.warning(f"⚠️ Error matching philosophical factual pattern {pattern[:50]}: {e}")
                    continue
        
        # CRITICAL FIX: Run fallback detection BEFORE early return to ensure well-known debates/events are detected
        # This ensures questions like "Tranh luận giữa Searle và Dennett về Chinese Room" and "Hiệp ước Versailles 1919" are always detected
        if user_question:
            question_lower = user_question.lower()
            
            # Check for specific well-known philosophical debates that should always be detected
            # CRITICAL: Also check for "tranh luận giữa X và Y" pattern with well-known philosophers
            if is_philosophical and not is_philosophical_factual:
                well_known_debates = [
                    # Searle-Dennett: Match if "tranh luận giữa Searle và Dennett" OR if both names appear with Chinese Room
                    (r"\b(tranh\s+luận|debate).*(giữa|between).*\b(searle)\b.*\b(dennett)\b", "Searle-Dennett debate"),
                    (r"\b(tranh\s+luận|debate).*(giữa|between).*\b(dennett)\b.*\b(searle)\b", "Searle-Dennett debate"),
                    (r"\b(searle)\b.*\b(dennett)\b.*\b(chinese\s+room|understanding)\b", "Searle-Dennett Chinese Room debate"),
                    (r"\b(dennett)\b.*\b(searle)\b.*\b(chinese\s+room|understanding)\b", "Searle-Dennett Chinese Room debate"),
                    (r"\b(chinese\s+room)\b.*\b(searle|dennett)\b", "Searle-Dennett Chinese Room debate"),
                    # Berkeley-Locke
                    (r"\b(tranh\s+luận|debate).*(giữa|between).*\b(berkeley)\b.*\b(locke)\b", "Berkeley-Locke debate"),
                    (r"\b(tranh\s+luận|debate).*(giữa|between).*\b(locke)\b.*\b(berkeley)\b", "Berkeley-Locke debate"),
                    (r"\b(berkeley)\b.*\b(locke)\b.*\b(primary|secondary|qualities|phẩm\s+chất)\b", "Berkeley-Locke primary/secondary qualities debate"),
                    (r"\b(locke)\b.*\b(berkeley)\b.*\b(primary|secondary|qualities|phẩm\s+chất)\b", "Berkeley-Locke primary/secondary qualities debate"),
                    # Nagel-Chalmers
                    (r"\b(tranh\s+luận|debate).*(giữa|between).*\b(nagel)\b.*\b(chalmers)\b", "Nagel-Chalmers debate"),
                    (r"\b(tranh\s+luận|debate).*(giữa|between).*\b(chalmers)\b.*\b(nagel)\b", "Nagel-Chalmers debate"),
                    (r"\b(nagel)\b.*\b(chalmers)\b.*\b(hard\s+problem|consciousness|ý\s+thức)\b", "Nagel-Chalmers hard problem debate"),
                    (r"\b(chalmers)\b.*\b(nagel)\b.*\b(hard\s+problem|consciousness|ý\s+thức)\b", "Nagel-Chalmers hard problem debate"),
                    # Quine-Carnap
                    (r"\b(tranh\s+luận|debate).*(giữa|between).*\b(quine)\b.*\b(carnap)\b", "Quine-Carnap debate"),
                    (r"\b(tranh\s+luận|debate).*(giữa|between).*\b(carnap)\b.*\b(quine)\b", "Quine-Carnap debate"),
                    (r"\b(quine)\b.*\b(carnap)\b.*\b(analytic|synthetic|distinction)\b", "Quine-Carnap analytic-synthetic distinction debate"),
                    (r"\b(carnap)\b.*\b(quine)\b.*\b(analytic|synthetic|distinction)\b", "Quine-Carnap analytic-synthetic distinction debate"),
                    # Hegel-Marx
                    (r"\b(tranh\s+luận|debate).*(giữa|between).*\b(hegel)\b.*\b(marx)\b", "Hegel-Marx debate"),
                    (r"\b(tranh\s+luận|debate).*(giữa|between).*\b(marx)\b.*\b(hegel)\b", "Hegel-Marx debate"),
                    (r"\b(hegel)\b.*\b(marx)\b.*\b(dialectics|biện\s+chứng)\b", "Hegel-Marx dialectics debate"),
                    (r"\b(marx)\b.*\b(hegel)\b.*\b(dialectics|biện\s+chứng)\b", "Hegel-Marx dialectics debate"),
                    # Rawls-Nozick
                    (r"\b(tranh\s+luận|debate).*(giữa|between).*\b(rawls)\b.*\b(nozick)\b", "Rawls-Nozick debate"),
                    (r"\b(tranh\s+luận|debate).*(giữa|between).*\b(nozick)\b.*\b(rawls)\b", "Rawls-Nozick debate"),
                    (r"\b(rawls)\b.*\b(nozick)\b.*\b(justice|công\s+lý)\b", "Rawls-Nozick justice debate"),
                    (r"\b(nozick)\b.*\b(rawls)\b.*\b(justice|công\s+lý)\b", "Rawls-Nozick justice debate"),
                    # Mill-Bentham
                    (r"\b(tranh\s+luận|debate).*(giữa|between).*\b(mill)\b.*\b(bentham)\b", "Mill-Bentham debate"),
                    (r"\b(tranh\s+luận|debate).*(giữa|between).*\b(bentham)\b.*\b(mill)\b", "Mill-Bentham debate"),
                    (r"\b(mill)\b.*\b(bentham)\b.*\b(utilitarianism|vị\s+lợi)\b", "Mill-Bentham utilitarianism debate"),
                    (r"\b(bentham)\b.*\b(mill)\b.*\b(utilitarianism|vị\s+lợi)\b", "Mill-Bentham utilitarianism debate"),
                    # Frege-Russell
                    (r"\b(tranh\s+luận|debate).*(giữa|between).*\b(frege)\b.*\b(russell)\b", "Frege-Russell debate"),
                    (r"\b(tranh\s+luận|debate).*(giữa|between).*\b(russell)\b.*\b(frege)\b", "Frege-Russell debate"),
                    (r"\b(frege)\b.*\b(russell)\b.*\b(sense|reference|Sinn|Bedeutung)\b", "Frege-Russell sense/reference debate"),
                    (r"\b(russell)\b.*\b(frege)\b.*\b(sense|reference|Sinn|Bedeutung)\b", "Frege-Russell sense/reference debate"),
                ]
                for pattern, debate_name in well_known_debates:
                    try:
                        if re.search(pattern, question_lower, re.IGNORECASE):
                            is_philosophical_factual = True
                            logger.warning(f"✅ Force-detected philosophical factual question: {debate_name} (question: {user_question[:100]})")
                            break
                    except Exception as e:
                        logger.warning(f"⚠️ Error matching well-known debate pattern {pattern[:50]}: {e}")
                        continue
            
            # CRITICAL FALLBACK: Check for well-known historical events that should always be detected as factual
            # This ensures questions like "Hiệp ước Versailles 1919" are always detected even if initial detection failed
            if not is_real_factual_question:
                well_known_historical_events = [
                    (r"\b(versailles|versaille)\s+\d{4}\b", "Versailles Treaty"),
                    (r"\b(hiệp\s+ước|treaty|agreement)\s+(versailles|versaille)\b", "Versailles Treaty"),
                    (r"\b(yalta|yalta\s+conference)\s+\d{4}\b", "Yalta Conference"),
                    (r"\b(potsdam|potsdam\s+conference)\s+\d{4}\b", "Potsdam Conference"),
                    (r"\b(geneva|genève)\s+\d{4}\b", "Geneva Conference"),
                    (r"\b(bretton\s+woods)\s+\d{4}\b", "Bretton Woods Conference"),
                    (r"\b(tehran|tehran\s+conference)\s+\d{4}\b", "Tehran Conference"),
                    (r"\b(westphalia|westphalia\s+peace)\s+\d{4}\b", "Westphalia Peace"),
                    (r"\b(hiệp\s+ước|treaty|agreement)\s+(westphalia)\b", "Westphalia Peace"),
                ]
                for pattern, event_name in well_known_historical_events:
                    try:
                        if re.search(pattern, question_lower, re.IGNORECASE):
                            is_real_factual_question = True
                            logger.warning(f"✅ Force-detected historical factual question: {event_name} (question: {user_question[:100]})")
                            break
                    except Exception as e:
                        logger.warning(f"⚠️ Error matching well-known historical event pattern {pattern[:50]}: {e}")
                        continue
        
        # If it's a factual question (even with philosophical elements), require citations
        if is_real_factual_question:
            logger.debug(f"Real factual question detected - citations REQUIRED even if philosophical elements present")
        
        # CRITICAL FIX: Simple factual questions (geography, math, science, literature) also need citations
        # These are factual questions that should be cited for transparency
        if is_simple_factual_question:
            logger.debug(f"Simple factual question detected - citations REQUIRED for transparency")
        
        # Combine all types of factual questions (AFTER fallback detection)
        is_any_factual_question = is_real_factual_question or is_simple_factual_question or is_philosophical_factual
        
        # For pure philosophical questions (no factual elements), skip citation requirement
        # BUT: If question has factual elements (years, events, named people, philosophers, theorems), ALWAYS require citations
        # CRITICAL: Check this AFTER fallback detection and combining factual questions
        # CRITICAL: Pure philosophical questions are about reasoning, not factual claims, so citations are not needed
        if is_philosophical and not is_any_factual_question:
            logger.info(f"✅ Pure philosophical question detected (no factual elements) - skipping citation requirement (reasoning, not factual claim). Question: {user_question[:100] if user_question else 'unknown'}")
            return ValidationResult(passed=True)
        
        # CRITICAL: Log detection results for debugging
        if is_philosophical:
            logger.warning(f"🔍 CitationRequired detection: is_philosophical=True, is_philosophical_factual={is_philosophical_factual}, is_real_factual_question={is_real_factual_question}, is_any_factual_question={is_any_factual_question}, has_context={bool(ctx_docs and len(ctx_docs) > 0)}, question: {user_question[:100] if user_question else 'unknown'}")
        
        # CRITICAL: Also log for non-philosophical questions to debug historical factual questions
        if not is_philosophical and user_question:
            logger.warning(f"🔍 CitationRequired detection (non-philosophical): is_real_factual_question={is_real_factual_question}, is_any_factual_question={is_any_factual_question}, has_context={bool(ctx_docs and len(ctx_docs) > 0)}, question: {user_question[:100] if user_question else 'unknown'}")
        
        # CRITICAL FIX: For ANY factual questions, we should still try to enforce citations
        # even if context is empty, because the LLM might have base knowledge about these topics
        # However, we can only auto-add citations if we have context documents
        
        # If no context documents available:
        if not ctx_docs or len(ctx_docs) == 0:
            if is_system_status_query:
                logger.warning("🚨 System status query detected but no context docs available - failing to avoid stale/general knowledge answers")
                return ValidationResult(
                    passed=False,
                    reasons=["system_status_missing_context"]
                )
            if is_source_required and not is_philosophical:
                logger.warning("🚨 Source-required question but no context docs - refusing to answer without sources")
                return ValidationResult(
                    passed=False,
                    reasons=["source_required_no_context"],
                    patched_answer=_build_no_source_response(user_question)
                )
            # For ANY factual questions, we should still add citation for transparency
            # Even if no RAG context, the answer is based on base knowledge and should be cited
            # BUT: Skip for pure philosophical questions (already handled above)
            if is_any_factual_question:
                logger.warning(f"🚨 Factual question detected but no context documents available - adding citation for base knowledge transparency. Question: {user_question[:100] if user_question else 'unknown'}, is_philosophical_factual={is_philosophical_factual}")
                # CRITICAL: Add citation [general knowledge] even without RAG context to indicate base knowledge source
                # This ensures transparency: user knows answer is from base knowledge, not RAG
                patched_answer = self._add_citation_for_base_knowledge(answer)
                logger.warning(f"✅ Added base knowledge citation. Original length: {len(answer)}, Patched length: {len(patched_answer)}")
                return ValidationResult(
                    passed=False,  # Still mark as failed to track that RAG context was missing
                    reasons=["missing_citation_no_context", "added_citation_for_base_knowledge"],
                    patched_answer=patched_answer
                )
            else:
                logger.debug(f"No context documents available, citations not required (is_any_factual_question={is_any_factual_question})")
                return ValidationResult(passed=True)
        
        # CRITICAL: Even if context is available, check if answer already has citation
        # If not, we MUST add it (this is the main path for missing citations)
        # Check for both numeric citations [1] and human-readable citations
        has_citation = bool(CITE_RE.search(answer) or HUMAN_READABLE_CITE_RE.search(answer))

        # System status queries MUST cite real-time context, never general knowledge
        if is_system_status_query and not has_citation:
            patched_answer = self._add_citation(answer, ctx_docs, user_question, context=context)
            return ValidationResult(
                passed=False,
                reasons=["missing_citation_system_status"],
                patched_answer=patched_answer
            )
        
        # CRITICAL FIX: Check if answer mentions "Based on general knowledge" or similar phrases
        # If yes, convert to proper citation format [general knowledge]
        if not has_citation and not is_system_status_query:
            general_knowledge_patterns = [
                r'based\s+on\s+general\s+knowledge\s*(?:\([^)]*\))?(?!\s*\[)',
                r'from\s+my\s+training\s+data(?!\s*\[)',
                r'not\s+from\s+stillme\'?s\s+rag\s+knowledge\s+base(?!\s*\[)',
                r'kiến\s+thức\s+tổng\s+quát(?!\s*\[)',
                r'dựa\s+trên\s+kiến\s+thức(?!\s*\[)',
            ]
            answer_lower = answer.lower()
            for pattern in general_knowledge_patterns:
                if re.search(pattern, answer_lower, re.IGNORECASE):
                    # Convert to [general knowledge] citation format
                    logger.info(f"Found 'Based on general knowledge' text without citation format - converting to [general knowledge]")
                    # Replace the pattern with citation format
                    # Strategy: Find the pattern and add [general knowledge] after it
                    match = re.search(pattern, answer_lower, re.IGNORECASE)
                    if match:
                        # Find the actual text in original case
                        original_match = re.search(pattern, answer, re.IGNORECASE)
                        if original_match:
                            insert_pos = original_match.end()
                            # Check if [general knowledge] already exists nearby (within 50 chars)
                            nearby_text = answer[max(0, insert_pos-50):min(len(answer), insert_pos+50)]
                            if not HUMAN_READABLE_CITE_RE.search(nearby_text):
                                # Add [general knowledge] citation
                                citation_text = " [general knowledge]"
                                patched_answer = answer[:insert_pos] + citation_text + answer[insert_pos:]
                                logger.warning(f"✅ Converted 'Based on general knowledge' text to citation format")
                                return ValidationResult(
                                    passed=False,  # Still mark as failed to track the conversion
                                    reasons=["converted_general_knowledge_text_to_citation"],
                                    patched_answer=patched_answer
                                )
                    break
        
        # CRITICAL FIX: Check if answer has URLs or source references that should be converted to citations
        # If answer has URLs like "Source: https://..." or "Sources: ...", convert them to [1] format
        # ALSO: Check for bare URLs (https://...) at end of answer or after "Sources:" or "-"
        if not has_citation:
            # Pattern 1: URLs with source prefix
            url_pattern_with_prefix = re.compile(r'(?:Source|Sources|Tham\s+Khảo|Tham\s+khảo|References?):\s*(?:https?://|www\.)', re.IGNORECASE)
            # Pattern 2: Bare URLs (https:// or www.) - often at end of answer or after "-"
            url_pattern_bare = re.compile(r'(?:^|\s|[-•])\s*(?:https?://[^\s]+|www\.[^\s]+)', re.IGNORECASE)
            
            has_urls_with_prefix = bool(url_pattern_with_prefix.search(answer))
            has_bare_urls = bool(url_pattern_bare.search(answer))
            
            if has_urls_with_prefix or has_bare_urls:
                # Convert URLs to citations
                logger.info(f"Found URLs in answer (with_prefix={has_urls_with_prefix}, bare={has_bare_urls}), converting to citation format [1]")
                patched_answer = self._convert_urls_to_citations(answer, ctx_docs)
                if patched_answer:
                    return ValidationResult(
                        passed=False,  # Still mark as failed to track the issue
                        reasons=["converted_urls_to_citations"],
                        patched_answer=patched_answer
                    )
        
        # CRITICAL FIX: Even if context is not relevant, we MUST cite for transparency
        # The citation instruction says: "When context documents are available, you MUST include at least one citation [1], [2], or [3] in your response for transparency."
        # So we should ALWAYS require citation when context is available, regardless of relevance
        # BUT: For real factual questions, we MUST cite even if context is empty (use base knowledge citation)
        
        if has_citation:
            # CRITICAL: If we have numeric citations [1], [2], convert them to human-readable format
            # This ensures all citations are human-readable for better transparency
            has_numeric_only = bool(CITE_RE.search(answer)) and not bool(HUMAN_READABLE_CITE_RE.search(answer))
            
            if has_numeric_only and self.citation_formatter:
                # PHASE 1 FIX: Extract similarity scores from context for citation hierarchy
                similarity_scores = None
                if context and isinstance(context, dict):
                    knowledge_docs = context.get("knowledge_docs", [])
                    if knowledge_docs:
                        similarity_scores = []
                        for doc in knowledge_docs:
                            if isinstance(doc, dict):
                                similarity_scores.append(doc.get('similarity', 0.0))
                            elif hasattr(doc, 'similarity'):
                                similarity_scores.append(doc.similarity if isinstance(doc.similarity, (int, float)) else 0.0)
                            else:
                                similarity_scores.append(0.0)
                
                if not similarity_scores and ctx_docs:
                    similarity_scores = []
                    for doc in ctx_docs:
                        if isinstance(doc, dict):
                            similarity_scores.append(doc.get('similarity', 0.0))
                        elif hasattr(doc, 'similarity'):
                            similarity_scores.append(doc.similarity if isinstance(doc.similarity, (int, float)) else 0.0)
                        else:
                            similarity_scores.append(0.0)
                
                # Replace numeric citations with human-readable format using citation hierarchy
                citation = self.citation_formatter.get_citation_strategy(user_question, ctx_docs, similarity_scores=similarity_scores)
                # Replace all numeric citations [1], [2], [3] with human-readable citation
                patched_answer = self.citation_formatter.replace_numeric_citations(answer, citation)
                logger.info(f"Converted numeric citations to human-readable format: '{citation}' (max_similarity={max(similarity_scores) if similarity_scores else 0.0:.3f})")
                return ValidationResult(
                    passed=True,  # Still passed, but we improved the citation format
                    reasons=["converted_numeric_to_human_readable"],
                    patched_answer=patched_answer
                )
            
            logger.debug("Citation found in answer")
            return ValidationResult(passed=True)
        else:
            logger.warning("Missing citation in answer (context documents available but no citations found)")
            
            # CRITICAL: For ANY factual questions (real or simple), ALWAYS add citation
            # Even if context is available, if it's a factual question and answer doesn't have citation, we MUST add it
            if is_any_factual_question:
                if not ctx_docs or len(ctx_docs) == 0:
                    # No context - use base knowledge citation
                    logger.warning(f"Factual question detected but no context - adding base knowledge citation. Question: {user_question[:100] if user_question else 'unknown'}")
                    patched_answer = self._add_citation_for_base_knowledge(answer)
                    return ValidationResult(
                        passed=False,  # Still mark as failed to track that RAG context was missing
                        reasons=["missing_citation_no_context", "added_citation_for_base_knowledge"],
                        patched_answer=patched_answer
                    )
                else:
                    # Context available but no citation - MUST add citation for factual questions
                    logger.warning(f"Factual question detected with context but missing citation - adding citation. Question: {user_question[:100] if user_question else 'unknown'}")
                    patched_answer = self._add_citation(answer, ctx_docs, user_question, context=context)
                    return ValidationResult(
                        passed=False,  # Still mark as failed to track the issue
                        reasons=["missing_citation_factual_question", "added_citation"],
                        patched_answer=patched_answer
                    )
            
            # AUTO-ENFORCE: Add citation to response for ALL questions when context is available
            # CRITICAL: Check similarity threshold before adding citation to avoid citing irrelevant sources
            # If max_similarity < 0.5, documents are not relevant enough - use [general knowledge] instead
            # NOTE: is_philosophical_factual is already included in is_any_factual_question above
            # So if we reach here, it means it's not a factual question OR it was already handled
            if ctx_docs and len(ctx_docs) > 0:
                # Extract max_similarity from context
                max_similarity = 0.0
                if context and isinstance(context, dict):
                    knowledge_docs = context.get("knowledge_docs", [])
                    if knowledge_docs:
                        similarity_scores = []
                        for doc in knowledge_docs:
                            if isinstance(doc, dict):
                                similarity_scores.append(doc.get('similarity', 0.0))
                            elif hasattr(doc, 'similarity'):
                                similarity_scores.append(doc.similarity if isinstance(doc.similarity, (int, float)) else 0.0)
                        if similarity_scores:
                            max_similarity = max(similarity_scores)
                
                # If max_similarity is too low (< 0.5), documents are not relevant enough
                # Use [general knowledge] citation instead of citing irrelevant sources
                if max_similarity < 0.5:
                    if is_source_required and not is_philosophical:
                        logger.warning("🚨 Source-required question but low similarity context - refusing to answer without sources")
                        return ValidationResult(
                            passed=False,
                            reasons=["source_required_low_similarity"],
                            patched_answer=_build_no_source_response(user_question)
                        )
                    logger.warning(f"Context available but max_similarity={max_similarity:.3f} < 0.5 (not relevant) - using [general knowledge] citation instead of irrelevant sources")
                    patched_answer = self._add_citation_for_base_knowledge(answer)
                    return ValidationResult(
                        passed=False,  # Still mark as failed to track the issue
                        reasons=["missing_citation", "low_similarity_using_base_knowledge"],
                        patched_answer=patched_answer
                    )
                
                logger.info(f"Context available ({len(ctx_docs)} docs, max_similarity={max_similarity:.3f}) but no citation - auto-adding citation for transparency")
                patched_answer = self._add_citation(answer, ctx_docs, user_question, context=context)
                return ValidationResult(
                    passed=False,  # Still mark as failed to track the issue
                    reasons=["missing_citation"],
                    patched_answer=patched_answer
                )
            else:
                # No context and not a factual question - citations not required
                logger.debug("No context documents available and not a factual question - citations not required")
                return ValidationResult(passed=True)
    
    def _add_citation_for_base_knowledge(self, answer: str) -> str:
        """
        Add human-readable citation for base knowledge answers (when no RAG context available).
        
        CRITICAL: This function must handle Unicode (including Chinese) safely.
        
        Args:
            answer: Original answer without citation (may contain Unicode characters)
            
        Returns:
            Answer with human-readable citation added to indicate base knowledge source
        """
        # CRITICAL: Clean answer from control characters and smart quotes
        import unicodedata
        if answer and isinstance(answer, str):
            # Remove control characters and smart quotes (preserve \n, \r, \t)
            answer = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u201c\u201d\u2018\u2019]', '', answer)
            # Normalize Unicode to NFC form
            try:
                answer = unicodedata.normalize('NFC', answer)
            except Exception:
                pass  # If normalization fails, continue with cleaned text
        
        # Use citation formatter if available
        if self.citation_formatter:
            citation = self.citation_formatter.get_citation_strategy("", [])
            result = self.citation_formatter.add_citation_to_response(answer, citation)
            # CRITICAL: Validate result is not empty
            if not result or not result.strip():
                logger.warning(
                    f"⚠️ Citation formatter returned empty result, using fallback "
                    f"(answer_length={len(answer) if answer else 0})"
                )
                # Fallback to manual citation
                if answer and answer.strip():
                    return answer.rstrip() + " [general knowledge]"
                return "[general knowledge]"
            return result
        
        # Fallback to [general knowledge] format (human-readable)
        citation_text = " [general knowledge]"
        
        if not answer or len(answer.strip()) == 0:
            return answer + citation_text if answer else citation_text.strip()
        
        if len(answer.strip()) < 5:
            return answer.rstrip() + citation_text
        
        # Find the best place to add citation (prefer end of first sentence or end of answer)
        # CRITICAL: Use Unicode-safe regex matching
        sentence_end = re.search(r'[.!?]\s+', answer)
        if sentence_end:
            insert_pos = sentence_end.end()
            # CRITICAL: Safe string slicing (Python handles Unicode correctly, but add validation)
            result = answer[:insert_pos] + citation_text + " " + answer[insert_pos:]
            # CRITICAL: Validate result is not empty
            if not result or not result.strip():
                logger.warning(
                    f"⚠️ Result is empty after adding citation at sentence end, "
                    f"falling back to end of answer (answer_length={len(answer) if answer else 0})"
                )
                return answer.rstrip() + citation_text
            return result
        
        # If no sentence end found, add at the end
        result = answer.rstrip() + citation_text
        # CRITICAL: Validate result is not empty
        if not result or not result.strip():
            logger.warning(
                f"⚠️ Result is empty after adding citation at end, "
                f"returning citation only (answer_length={len(answer) if answer else 0})"
            )
            return citation_text.strip()
        return result
    
    def _add_citation_text(self, answer: str, citation_text: str) -> str:
        """
        Add citation text to answer at appropriate position.
        
        CRITICAL: This function must handle Unicode (including Chinese) safely.
        
        Args:
            answer: Original answer (may contain Unicode characters)
            citation_text: Citation text to add (e.g., "[foundational knowledge]")
            
        Returns:
            Answer with citation added
        """
        # CRITICAL: Clean answer from control characters and smart quotes
        import unicodedata
        if answer and isinstance(answer, str):
            # Remove control characters and smart quotes
            answer = re.sub(r'[\x00-\x1f\x7f-\x9f\u201c\u201d\u2018\u2019]', '', answer)
            # Normalize Unicode to NFC form
            try:
                answer = unicodedata.normalize('NFC', answer)
            except Exception:
                pass  # If normalization fails, continue with cleaned text
        
        if not answer or len(answer.strip()) == 0:
            return answer + citation_text if answer else citation_text.strip()
        
        if len(answer.strip()) < 5:
            result = answer.rstrip() + citation_text
            # CRITICAL: Validate result is not empty
            if not result or not result.strip():
                return citation_text.strip()
            return result
        
        # Find the best place to add citation (prefer end of first sentence or end of answer)
        # CRITICAL: Use Unicode-safe regex matching
        sentence_end = re.search(r'[.!?]\s+', answer)
        if sentence_end:
            insert_pos = sentence_end.end()
            # CRITICAL: Safe string slicing (Python handles Unicode correctly, but add validation)
            result = answer[:insert_pos] + citation_text + " " + answer[insert_pos:]
            # CRITICAL: Validate result is not empty
            if not result or not result.strip():
                logger.warning(
                    f"⚠️ Result is empty after adding citation at sentence end, "
                    f"falling back to end of answer (answer_length={len(answer) if answer else 0})"
                )
                return answer.rstrip() + citation_text
            return result
        
        # If no sentence end found, add at the end
        result = answer.rstrip() + citation_text
        # CRITICAL: Validate result is not empty
        if not result or not result.strip():
            logger.warning(
                f"⚠️ Result is empty after adding citation at end, "
                f"returning citation only (answer_length={len(answer) if answer else 0})"
            )
            return citation_text.strip()
        return result
    
    def _add_citation(self, answer: str, ctx_docs: List[Any], user_question: str = "", context: Optional[Dict[str, Any]] = None) -> str:
        """
        Automatically add human-readable citation to answer when missing
        
        TRUST-EFFICIENT FIX: Check if citation already exists before adding (prevent loops)
        
        Args:
            answer: Original answer without citation
            ctx_docs: List of context documents (can be dicts or objects with metadata, or just strings)
            user_question: User's original question (for citation strategy)
            context: Optional context dict with knowledge_docs (for foundational knowledge detection)
            
        Returns:
            Answer with human-readable citation added
        """
        # TRUST-EFFICIENT FIX: Check if citation already exists (prevent duplicate citations)
        if HUMAN_READABLE_CITE_RE.search(answer) or CITE_RE.search(answer):
            logger.debug("Citation already exists in answer, skipping auto-add")
            return answer
        # CRITICAL: Check if context contains foundational knowledge
        # If yes, use specific "[foundational knowledge]" citation instead of generic "[general knowledge]"
        # Priority: Check context dict first (has full metadata), then check ctx_docs
        has_foundational_knowledge = False
        
        # Method 1: Check context dict (has knowledge_docs with full metadata)
        if context and isinstance(context, dict):
            knowledge_docs = context.get("knowledge_docs", [])
            for doc in knowledge_docs:
                if isinstance(doc, dict):
                    metadata = doc.get("metadata", {})
                    source = metadata.get("source", "")
                    foundational = metadata.get("foundational", "")
                    doc_type = metadata.get("type", "")
                    tags = str(metadata.get("tags", ""))
                    
                    # Check for foundational knowledge markers
                    if (source == "CRITICAL_FOUNDATION" or 
                        foundational == "stillme" or 
                        doc_type == "foundational" or
                        "CRITICAL_FOUNDATION" in tags or
                        "foundational:stillme" in tags):
                        has_foundational_knowledge = True
                        logger.info(f"✅ Detected foundational knowledge in context dict - will use specific citation")
                        break
        
        # Method 2: Check ctx_docs (may have metadata if passed as dicts)
        if not has_foundational_knowledge and ctx_docs:
            for doc in ctx_docs:
                # Check if document is foundational knowledge
                if isinstance(doc, dict):
                    metadata = doc.get("metadata", {})
                    source = metadata.get("source", "")
                    foundational = metadata.get("foundational", "")
                    doc_type = metadata.get("type", "")
                    tags = str(metadata.get("tags", ""))
                else:
                    # If doc is an object, try to get attributes
                    metadata = getattr(doc, "metadata", {}) if hasattr(doc, "metadata") else {}
                    source = getattr(doc, "source", "") if hasattr(doc, "source") else (metadata.get("source", "") if isinstance(metadata, dict) else "")
                    foundational = metadata.get("foundational", "") if isinstance(metadata, dict) else ""
                    doc_type = metadata.get("type", "") if isinstance(metadata, dict) else ""
                    tags = str(metadata.get("tags", "")) if isinstance(metadata, dict) else ""
                
                # Check for foundational knowledge markers
                if (source == "CRITICAL_FOUNDATION" or 
                    foundational == "stillme" or 
                    doc_type == "foundational" or
                    "CRITICAL_FOUNDATION" in tags or
                    "foundational:stillme" in tags):
                    has_foundational_knowledge = True
                    logger.info(f"✅ Detected foundational knowledge in ctx_docs - will use specific citation")
                    break
        
        # Use citation formatter if available (but override with foundational knowledge citation if detected)
        if self.citation_formatter and not has_foundational_knowledge:
            # TRUST-EFFICIENT FIX: Extract similarity scores from context or ctx_docs
            # CRITICAL: In step validation, ctx_docs is List[str] (text), but context["knowledge_docs"] has similarity
            similarity_scores = None
            max_similarity = 0.0
            if context and isinstance(context, dict):
                # Try to get similarity scores from context dict (preferred - has actual similarity)
                knowledge_docs = context.get("knowledge_docs", [])
                if knowledge_docs:
                    similarity_scores = []
                    for doc in knowledge_docs:
                        if isinstance(doc, dict):
                            sim = doc.get('similarity', 0.0)
                            similarity_scores.append(sim)
                            max_similarity = max(max_similarity, sim)
                        elif hasattr(doc, 'similarity'):
                            sim = doc.similarity if isinstance(doc.similarity, (int, float)) else 0.0
                            similarity_scores.append(sim)
                            max_similarity = max(max_similarity, sim)
                        else:
                            similarity_scores.append(0.0)
            
            # If no similarity scores from context, try to extract from ctx_docs
            if not similarity_scores and ctx_docs:
                similarity_scores = []
                for doc in ctx_docs:
                    if isinstance(doc, dict):
                        sim = doc.get('similarity', 0.0)
                        similarity_scores.append(sim)
                        max_similarity = max(max_similarity, sim)
                    elif hasattr(doc, 'similarity'):
                        sim = doc.similarity if isinstance(doc.similarity, (int, float)) else 0.0
                        similarity_scores.append(sim)
                        max_similarity = max(max_similarity, sim)
                    else:
                        similarity_scores.append(0.0)
            
            # TRUST-EFFICIENT FIX: Pass similarity scores to get_citation_strategy for citation hierarchy
            # Note: ctx_docs might be List[str] (text) in step validation, but similarity_scores from context["knowledge_docs"]
            # This is OK - get_citation_strategy only needs similarity_scores for hierarchy, not ctx_docs content
            citation = self.citation_formatter.get_citation_strategy(user_question, ctx_docs, similarity_scores=similarity_scores)
            patched = self.citation_formatter.add_citation_to_response(answer, citation)
            logger.info(f"Auto-added human-readable citation '{citation}' to response (context docs: {len(ctx_docs)}, max_similarity={max_similarity:.3f})")
            return patched
        elif has_foundational_knowledge:
            # Use specific foundational knowledge citation
            citation = "[foundational knowledge]"
            # Add citation using same strategy as citation formatter
            patched = self._add_citation_text(answer, citation)
            logger.info(f"Auto-added foundational knowledge citation '{citation}' to response (context docs: {len(ctx_docs)})")
            return patched
        
        # Fallback to legacy [1] format
        # CRITICAL: Clean answer from control characters and smart quotes
        import unicodedata
        if answer and isinstance(answer, str):
            # Remove control characters and smart quotes
            answer = re.sub(r'[\x00-\x1f\x7f-\x9f\u201c\u201d\u2018\u2019]', '', answer)
            # Normalize Unicode to NFC form
            try:
                answer = unicodedata.normalize('NFC', answer)
            except Exception:
                pass  # If normalization fails, continue with cleaned text
        
        # Edge case: Empty or whitespace-only answer
        if not answer or len(answer.strip()) == 0:
            logger.warning("Cannot add citation to empty answer")
            return answer + " [1]" if answer else "[1]"
        
        # Edge case: Very short answer (< 5 chars) - just add at the end
        if len(answer.strip()) < 5:
            result = answer.rstrip() + " [1]"
            # CRITICAL: Validate result is not empty
            if not result or not result.strip():
                return "[1]"
            return result
        
        # Find the best place to add citation
        # Strategy: Add [1] after the first sentence or first paragraph
        
        # Try to find first sentence (ends with . ! ?)
        # CRITICAL: Use Unicode-safe regex matching
        sentence_end = re.search(r'[.!?]\s+', answer)
        if sentence_end:
            # Insert citation after first sentence
            insert_pos = sentence_end.end()
            citation = " [1]"
            # CRITICAL: Safe string slicing (Python handles Unicode correctly, but add validation)
            patched = answer[:insert_pos] + citation + answer[insert_pos:]
            # CRITICAL: Validate result is not empty
            if not patched or not patched.strip():
                logger.warning(
                    f"⚠️ Result is empty after adding citation at sentence end, "
                    f"falling back to end of answer (answer_length={len(answer) if answer else 0})"
                )
                patched = answer.rstrip() + " [1]"
        else:
            # If no sentence end found, add at the end of first line or beginning
            first_newline = answer.find('\n')
            if first_newline > 0 and first_newline < 100:  # Reasonable paragraph break
                insert_pos = first_newline
                citation = " [1]"
                # CRITICAL: Safe string slicing
                patched = answer[:insert_pos] + citation + answer[insert_pos:]
                # CRITICAL: Validate result is not empty
                if not patched or not patched.strip():
                    logger.warning(
                        f"⚠️ Result is empty after adding citation at newline, "
                        f"falling back to end of answer (answer_length={len(answer) if answer else 0})"
                    )
                    patched = answer.rstrip() + " [1]"
            else:
                # Add at the end
                patched = answer.rstrip() + " [1]"
        
        # CRITICAL: Final validation - ensure result is not empty
        if not patched or not patched.strip():
            logger.warning(
                f"⚠️ Result is empty after adding citation, "
                f"returning citation only (answer_length={len(answer) if answer else 0})"
            )
            return "[1]"
        
        logger.info(f"Auto-added citation [1] to response (context docs: {len(ctx_docs)})")
        return patched
    
    def _convert_urls_to_citations(self, answer: str, ctx_docs: List[str]) -> str:
        """
        Convert URLs or source references to citation format [1], [2]
        
        Examples:
        - "Source: https://example.com" → "According to [1], ..."
        - "Sources: https://example.com, https://example2.com" → "According to [1] and [2], ..."
        - "Tham Khảo: https://example.com" → "Theo [1], ..."
        - "- https://example.com" → "According to [1], ..."
        - Bare URLs at end: "https://example.com" → "[1]"
        
        Args:
            answer: Original answer with URLs
            ctx_docs: List of context documents
            
        Returns:
            Answer with URLs converted to citations, or None if conversion failed
        """
        if not answer or not ctx_docs:
            return None
        
        result = answer
        
        # Pattern 1: Source references with URLs (with prefix)
        source_pattern_with_prefix = re.compile(
            r'(?:Source|Sources|Tham\s+Khảo|Tham\s+khảo|References?):\s*(?:https?://[^\s]+|www\.[^\s]+)',
            re.IGNORECASE
        )
        
        # Pattern 2: Bare URLs (https:// or www.) - often at end of answer or after "-" or "•"
        bare_url_pattern = re.compile(
            r'(?:^|\s|[-•])\s*(https?://[^\s]+|www\.[^\s]+)',
            re.IGNORECASE
        )
        
        # Find all source references (with prefix)
        matches_with_prefix = list(source_pattern_with_prefix.finditer(result))
        
        # Find all bare URLs
        matches_bare = list(bare_url_pattern.finditer(result))
        
        # Combine and sort by position
        all_matches = []
        for match in matches_with_prefix:
            all_matches.append(('with_prefix', match))
        for match in matches_bare:
            # Only include if not already captured by prefix pattern
            url_text = match.group(1)
            is_duplicate = any(
                url_text in m.group(0) for _, m in all_matches if _ == 'with_prefix'
            )
            if not is_duplicate:
                all_matches.append(('bare', match))
        
        # Sort by position (reverse order for safe replacement)
        all_matches.sort(key=lambda x: x[1].start(), reverse=True)
        
        if not all_matches:
            return None
        
        # Replace each source reference with citation
        # Strategy: Replace "Source: URL" or bare URL with "[1]" at the beginning of the sentence/paragraph
        for i, (match_type, match) in enumerate(all_matches):  # Process in reverse order (already sorted)
            matched_text = match.group(0)
            start_pos = match.start()
            end_pos = match.end()
            
            # Determine citation number (1, 2, 3, etc.)
            citation_num = min(i + 1, len(ctx_docs))
            citation = f"[{citation_num}]"
            
            # For bare URLs, we need to handle the match differently
            if match_type == 'bare':
                # Bare URL match includes prefix (space, "-", etc.) in group(0), but URL is in group(1)
                url_start = match.start(1)  # Start of actual URL
                url_end = match.end(1)  # End of actual URL
                # Remove the entire match (including prefix like "- " or space)
                result = result[:start_pos] + f" {citation}" + result[end_pos:]
            else:
                # With prefix: "Source: https://..." - find sentence start
                sentence_start = result.rfind('\n', 0, start_pos)
                if sentence_start == -1:
                    sentence_start = 0
                else:
                    sentence_start += 1  # Skip the newline
                
                # Check if there's already a citation in this sentence
                sentence_text = result[sentence_start:end_pos]
                if CITE_RE.search(sentence_text):
                    # Already has citation, just remove the URL reference
                    result = result[:start_pos] + result[end_pos:]
                else:
                    # Replace URL reference with citation
                    # Try to insert citation at a natural position (after first sentence or at start)
                    first_sentence_end = re.search(r'[.!?]\s+', result[sentence_start:start_pos])
                    if first_sentence_end:
                        insert_pos = sentence_start + first_sentence_end.end()
                        result = result[:insert_pos] + f" {citation}" + result[insert_pos:start_pos] + result[end_pos:]
                    else:
                        # Insert at start of sentence
                        result = result[:sentence_start] + f"{citation} " + result[sentence_start:start_pos] + result[end_pos:]
        
        logger.info(f"Converted {len(all_matches)} URL reference(s) to citation format")
        return result

