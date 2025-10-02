#!/usr/bin/env python3
"""
TranslationEval - Đánh giá khả năng dịch thuật của StillMe AI

Kiểm tra:
- Phát hiện ngôn ngữ chính xác
- Dịch đúng nghĩa và ngữ cảnh
- Tích hợp với Gemma/NLLB local
- Bảo toàn code blocks và URLs
- Đánh giá chất lượng dịch thuật
"""

import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TranslationScore:
    """Kết quả đánh giá dịch thuật"""

    language_detection: float  # 0-1: phát hiện ngôn ngữ
    translation_accuracy: float  # 0-1: độ chính xác dịch
    context_preservation: float  # 0-1: bảo toàn ngữ cảnh
    code_preservation: float  # 0-1: bảo toàn code blocks
    url_preservation: float  # 0-1: bảo toàn URLs
    overall_translation_score: float  # 0-1: điểm dịch thuật tổng

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TranslationEval:
    """Evaluator cho khả năng dịch thuật"""

    def __init__(self):
        self.logger = logger

        # Language detection patterns
        self.language_patterns = {
            "vietnamese": [
                r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]",
                r"\b(xin\s+chào|tôi|bạn|mình|anh|chị|em|bác|cô|chú|dì|cậu|mợ)\b",
                r"\b(hôm\s+nay|ngày\s+mai|hôm\s+qua|tuần\s+này|tháng\s+này)\b",
                r"\b(cảm\s+ơn|xin\s+lỗi|không\s+có\s+gì|không\s+sao)\b",
            ],
            "english": [
                r"\b(hello|hi|good\s+morning|good\s+afternoon|good\s+evening)\b",
                r"\b(I|you|he|she|it|we|they|me|him|her|us|them)\b",
                r"\b(today|tomorrow|yesterday|this\s+week|this\s+month)\b",
                r"\b(thank\s+you|sorry|excuse\s+me|you\'re\s+welcome)\b",
            ],
            "chinese": [
                r"[一-龯]",
                r"\b(你好|您好|谢谢|对不起|没关系)\b",
                r"\b(今天|明天|昨天|这周|这个月)\b",
            ],
            "japanese": [
                r"[ひらがなカタカナ]",
                r"\b(こんにちは|ありがとう|すみません|大丈夫)\b",
                r"\b(今日|明日|昨日|今週|今月)\b",
            ],
            "korean": [
                r"[가-힣]",
                r"\b(안녕하세요|감사합니다|죄송합니다|괜찮습니다)\b",
                r"\b(오늘|내일|어제|이번\s+주|이번\s+달)\b",
            ],
        }

        # Code block patterns
        self.code_patterns = [
            r"```[\s\S]*?```",  # Markdown code blocks
            r"`[^`]+`",  # Inline code
            r"<code>[\s\S]*?</code>",  # HTML code tags
            r"<pre>[\s\S]*?</pre>",  # HTML pre tags
        ]

        # URL patterns
        self.url_patterns = [
            r"https?://[^\s]+",
            r"www\.[^\s]+",
            r"[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            r"ftp://[^\s]+",
        ]

        # Translation quality indicators
        self.quality_indicators = {
            "good": [
                r"\b(accurate|correct|proper|appropriate|suitable)\b",
                r"\b(chính\s+xác|đúng|phù\s+hợp|thích\s+hợp)\b",
            ],
            "bad": [
                r"\b(wrong|incorrect|inappropriate|unsuitable|inaccurate)\b",
                r"\b(sai|không\s+đúng|không\s+phù\s+hợp|không\s+thích\s+hợp)\b",
            ],
        }

        # Common translation pairs for testing
        self.translation_pairs = {
            "vietnamese_english": {
                "xin chào": "hello",
                "cảm ơn": "thank you",
                "xin lỗi": "sorry",
                "không có gì": "you're welcome",
                "hôm nay": "today",
                "ngày mai": "tomorrow",
                "hôm qua": "yesterday",
            },
            "english_vietnamese": {
                "hello": "xin chào",
                "thank you": "cảm ơn",
                "sorry": "xin lỗi",
                "you're welcome": "không có gì",
                "today": "hôm nay",
                "tomorrow": "ngày mai",
                "yesterday": "hôm qua",
            },
        }

    def evaluate(
        self,
        response: str,
        user_input: str = "",
        expected_language: Optional[str] = None,
        source_language: Optional[str] = None,
    ) -> TranslationScore:
        """
        Đánh giá khả năng dịch thuật của response

        Args:
            response: AI response cần đánh giá
            user_input: User input gốc (optional)
            expected_language: Ngôn ngữ mong đợi (optional)
            source_language: Ngôn ngữ nguồn (optional)

        Returns:
            TranslationScore: Kết quả đánh giá dịch thuật
        """
        try:
            self.logger.info(
                f"🔍 Evaluating translation for response: {response[:100]}..."
            )

            # 1. Đánh giá phát hiện ngôn ngữ
            detection_score = self._evaluate_language_detection(
                response, expected_language
            )

            # 2. Đánh giá độ chính xác dịch
            accuracy_score = self._evaluate_translation_accuracy(
                response, user_input, source_language
            )

            # 3. Đánh giá bảo toàn ngữ cảnh
            context_score = self._evaluate_context_preservation(response, user_input)

            # 4. Đánh giá bảo toàn code blocks
            code_score = self._evaluate_code_preservation(response, user_input)

            # 5. Đánh giá bảo toàn URLs
            url_score = self._evaluate_url_preservation(response, user_input)

            # 6. Tính điểm dịch thuật tổng
            overall_score = (
                detection_score * 0.2
                + accuracy_score * 0.3
                + context_score * 0.2
                + code_score * 0.15
                + url_score * 0.15
            )

            result = TranslationScore(
                language_detection=detection_score,
                translation_accuracy=accuracy_score,
                context_preservation=context_score,
                code_preservation=code_score,
                url_preservation=url_score,
                overall_translation_score=overall_score,
            )

            self.logger.info(
                f"✅ Translation evaluation completed. Overall score: {overall_score:.3f}"
            )
            return result

        except Exception as e:
            self.logger.error(f"❌ Translation evaluation failed: {e}")
            return TranslationScore(0, 0, 0, 0, 0, 0)

    def _evaluate_language_detection(
        self, response: str, expected_language: Optional[str] = None
    ) -> float:
        """Đánh giá phát hiện ngôn ngữ"""
        try:
            score = 0.0
            total_checks = 0

            # Detect language in response
            detected_language = self._detect_language(response)

            if expected_language:
                if detected_language == expected_language:
                    score += 0.6  # Correct language detection
                else:
                    score += 0.2  # Wrong language detection
                total_checks += 1
            else:
                # No expected language, check if detection is consistent
                if detected_language:
                    score += 0.5  # Language detected
                total_checks += 1

            # Check for language consistency
            if detected_language:
                # Check if response is mostly in the detected language
                language_ratio = self._calculate_language_ratio(
                    response, detected_language
                )
                if language_ratio > 0.7:
                    score += 0.3  # High consistency
                elif language_ratio > 0.5:
                    score += 0.2  # Medium consistency
                else:
                    score += 0.1  # Low consistency
                total_checks += 1

            # Check for mixed language handling
            mixed_language_count = self._count_mixed_languages(response)
            if mixed_language_count <= 1:
                score += 0.1  # Good language separation
            total_checks += 1

            return min(score / max(total_checks, 1), 1.0)

        except Exception as e:
            self.logger.error(f"Error evaluating language detection: {e}")
            return 0.0

    def _evaluate_translation_accuracy(
        self, response: str, user_input: str, source_language: Optional[str] = None
    ) -> float:
        """Đánh giá độ chính xác dịch"""
        try:
            score = 0.0
            total_checks = 0

            # Check for common translation pairs
            if source_language and user_input:
                detected_source = self._detect_language(user_input)
                detected_target = self._detect_language(response)

                if detected_source and detected_target:
                    # Check if translation direction is correct
                    if detected_source != detected_target:
                        score += 0.4  # Translation occurred
                        total_checks += 1

                        # Check for common translation pairs
                        translation_score = self._check_translation_pairs(
                            user_input, response, detected_source, detected_target
                        )
                        score += translation_score * 0.4
                        total_checks += 1
                    else:
                        score += 0.2  # No translation needed
                        total_checks += 1

            # Check for translation quality indicators
            quality_score = self._check_translation_quality(response)
            score += quality_score * 0.2
            total_checks += 1

            return min(score / max(total_checks, 1), 1.0)

        except Exception as e:
            self.logger.error(f"Error evaluating translation accuracy: {e}")
            return 0.0

    def _evaluate_context_preservation(self, response: str, user_input: str) -> float:
        """Đánh giá bảo toàn ngữ cảnh"""
        try:
            score = 0.0
            total_checks = 0

            # Check if response maintains the same intent
            if user_input:
                input_intent = self._extract_intent(user_input)
                response_intent = self._extract_intent(response)

                if input_intent and response_intent:
                    if input_intent == response_intent:
                        score += 0.5  # Intent preserved
                    else:
                        score += 0.2  # Intent partially preserved
                    total_checks += 1

            # Check for context keywords preservation
            context_keywords = self._extract_context_keywords(user_input)
            if context_keywords:
                preserved_keywords = 0
                for keyword in context_keywords:
                    if keyword.lower() in response.lower():
                        preserved_keywords += 1

                preservation_ratio = preserved_keywords / len(context_keywords)
                score += preservation_ratio * 0.3
                total_checks += 1

            # Check for temporal context preservation
            temporal_indicators = [
                "hôm nay",
                "today",
                "ngày mai",
                "tomorrow",
                "hôm qua",
                "yesterday",
            ]
            temporal_preserved = any(
                indicator in user_input.lower() and indicator in response.lower()
                for indicator in temporal_indicators
            )
            if temporal_preserved:
                score += 0.2
            total_checks += 1

            return min(score / max(total_checks, 1), 1.0)

        except Exception as e:
            self.logger.error(f"Error evaluating context preservation: {e}")
            return 0.0

    def _evaluate_code_preservation(self, response: str, user_input: str) -> float:
        """Đánh giá bảo toàn code blocks"""
        try:
            score = 0.0
            total_checks = 0

            # Extract code blocks from input
            input_code_blocks = []
            for pattern in self.code_patterns:
                input_code_blocks.extend(re.findall(pattern, user_input, re.IGNORECASE))

            if input_code_blocks:
                # Check if code blocks are preserved in response
                preserved_blocks = 0
                for block in input_code_blocks:
                    if block in response:
                        preserved_blocks += 1

                preservation_ratio = preserved_blocks / len(input_code_blocks)
                score += preservation_ratio * 0.6
                total_checks += 1

                # Check for code block formatting
                if preservation_ratio > 0:
                    score += 0.2  # Code blocks preserved
                total_checks += 1
            else:
                # No code blocks to preserve
                score += 0.8
                total_checks += 1

            # Check for inline code preservation
            inline_code_pattern = r"`[^`]+`"
            input_inline_code = re.findall(inline_code_pattern, user_input)
            if input_inline_code:
                preserved_inline = 0
                for code in input_inline_code:
                    if code in response:
                        preserved_inline += 1

                if preserved_inline > 0:
                    score += 0.2
                total_checks += 1

            return min(score / max(total_checks, 1), 1.0)

        except Exception as e:
            self.logger.error(f"Error evaluating code preservation: {e}")
            return 0.0

    def _evaluate_url_preservation(self, response: str, user_input: str) -> float:
        """Đánh giá bảo toàn URLs"""
        try:
            score = 0.0
            total_checks = 0

            # Extract URLs from input
            input_urls = []
            for pattern in self.url_patterns:
                input_urls.extend(re.findall(pattern, user_input, re.IGNORECASE))

            if input_urls:
                # Check if URLs are preserved in response
                preserved_urls = 0
                for url in input_urls:
                    if url in response:
                        preserved_urls += 1

                preservation_ratio = preserved_urls / len(input_urls)
                score += preservation_ratio * 0.8
                total_checks += 1

                # Check for URL formatting
                if preservation_ratio > 0:
                    score += 0.2  # URLs preserved
                total_checks += 1
            else:
                # No URLs to preserve
                score += 1.0
                total_checks += 1

            return min(score / max(total_checks, 1), 1.0)

        except Exception as e:
            self.logger.error(f"Error evaluating URL preservation: {e}")
            return 0.0

    def _detect_language(self, text: str) -> Optional[str]:
        """Phát hiện ngôn ngữ của text"""
        try:
            language_scores = {}

            for language, patterns in self.language_patterns.items():
                score = 0
                for pattern in patterns:
                    matches = len(re.findall(pattern, text, re.IGNORECASE))
                    score += matches
                language_scores[language] = score

            if language_scores:
                return max(language_scores, key=language_scores.get)
            return None

        except Exception as e:
            self.logger.error(f"Error detecting language: {e}")
            return None

    def _calculate_language_ratio(self, text: str, language: str) -> float:
        """Tính tỷ lệ ngôn ngữ trong text"""
        try:
            if language not in self.language_patterns:
                return 0.0

            total_chars = len(text)
            if total_chars == 0:
                return 0.0

            language_chars = 0
            for pattern in self.language_patterns[language]:
                matches = re.findall(pattern, text, re.IGNORECASE)
                language_chars += sum(len(match) for match in matches)

            return language_chars / total_chars

        except Exception as e:
            self.logger.error(f"Error calculating language ratio: {e}")
            return 0.0

    def _count_mixed_languages(self, text: str) -> int:
        """Đếm số ngôn ngữ khác nhau trong text"""
        try:
            detected_languages = set()
            for language, patterns in self.language_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        detected_languages.add(language)
                        break

            return len(detected_languages)

        except Exception as e:
            self.logger.error(f"Error counting mixed languages: {e}")
            return 0

    def _check_translation_pairs(
        self, input_text: str, response_text: str, source_lang: str, target_lang: str
    ) -> float:
        """Kiểm tra các cặp dịch thuật phổ biến"""
        try:
            score = 0.0
            total_pairs = 0

            # Get translation pairs for the language combination
            pair_key = f"{source_lang}_{target_lang}"
            if pair_key in self.translation_pairs:
                pairs = self.translation_pairs[pair_key]
                for source, target in pairs.items():
                    if (
                        source.lower() in input_text.lower()
                        and target.lower() in response_text.lower()
                    ):
                        score += 1.0
                    total_pairs += 1

            if total_pairs > 0:
                return score / total_pairs
            return 0.0

        except Exception as e:
            self.logger.error(f"Error checking translation pairs: {e}")
            return 0.0

    def _check_translation_quality(self, response: str) -> float:
        """Kiểm tra chất lượng dịch thuật"""
        try:
            score = 0.0
            total_checks = 0

            # Check for good quality indicators
            good_count = sum(
                len(re.findall(pattern, response, re.IGNORECASE))
                for pattern in self.quality_indicators["good"]
            )
            if good_count > 0:
                score += 0.5
            total_checks += 1

            # Check for bad quality indicators
            bad_count = sum(
                len(re.findall(pattern, response, re.IGNORECASE))
                for pattern in self.quality_indicators["bad"]
            )
            if bad_count == 0:
                score += 0.3
            total_checks += 1

            # Check for translation metadata
            if "translation" in response.lower() or "dịch" in response.lower():
                score += 0.2
            total_checks += 1

            return min(score / max(total_checks, 1), 1.0)

        except Exception as e:
            self.logger.error(f"Error checking translation quality: {e}")
            return 0.0

    def _extract_intent(self, text: str) -> Optional[str]:
        """Trích xuất ý định từ text"""
        try:
            text_lower = text.lower()

            if any(word in text_lower for word in ["hello", "hi", "xin chào", "chào"]):
                return "greeting"
            elif any(word in text_lower for word in ["thank", "cảm ơn", "thanks"]):
                return "thanks"
            elif any(word in text_lower for word in ["sorry", "xin lỗi", "excuse"]):
                return "apology"
            elif any(word in text_lower for word in ["help", "giúp", "assist"]):
                return "help_request"
            elif any(word in text_lower for word in ["question", "câu hỏi", "ask"]):
                return "question"
            else:
                return "general"

        except Exception as e:
            self.logger.error(f"Error extracting intent: {e}")
            return None

    def _extract_context_keywords(self, text: str) -> list[str]:
        """Trích xuất từ khóa ngữ cảnh"""
        try:
            keywords = []

            # Time-related keywords
            time_keywords = [
                "hôm nay",
                "today",
                "ngày mai",
                "tomorrow",
                "hôm qua",
                "yesterday",
            ]
            for keyword in time_keywords:
                if keyword in text.lower():
                    keywords.append(keyword)

            # Location-related keywords
            location_keywords = ["ở đây", "here", "ở đó", "there", "nơi", "place"]
            for keyword in location_keywords:
                if keyword in text.lower():
                    keywords.append(keyword)

            # Person-related keywords
            person_keywords = ["tôi", "I", "bạn", "you", "anh", "chị", "em"]
            for keyword in person_keywords:
                if keyword in text.lower():
                    keywords.append(keyword)

            return keywords

        except Exception as e:
            self.logger.error(f"Error extracting context keywords: {e}")
            return []

    def batch_evaluate(self, responses: list[dict[str, Any]]) -> list[TranslationScore]:
        """Đánh giá hàng loạt responses"""
        results = []

        for i, item in enumerate(responses):
            try:
                response = item.get("response", "")
                user_input = item.get("user_input", "")
                expected_language = item.get("expected_language")
                source_language = item.get("source_language")

                score = self.evaluate(
                    response, user_input, expected_language, source_language
                )
                results.append(score)

                self.logger.info(f"✅ Evaluated response {i+1}/{len(responses)}")

            except Exception as e:
                self.logger.error(f"❌ Failed to evaluate response {i+1}: {e}")
                results.append(TranslationScore(0, 0, 0, 0, 0, 0))

        return results

    def generate_report(self, scores: list[TranslationScore]) -> dict[str, Any]:
        """Tạo báo cáo tổng hợp"""
        try:
            if not scores:
                return {"error": "No scores provided"}

            # Calculate statistics
            total_scores = len(scores)
            avg_detection = sum(s.language_detection for s in scores) / total_scores
            avg_accuracy = sum(s.translation_accuracy for s in scores) / total_scores
            avg_context = sum(s.context_preservation for s in scores) / total_scores
            avg_code = sum(s.code_preservation for s in scores) / total_scores
            avg_url = sum(s.url_preservation for s in scores) / total_scores
            avg_overall = (
                sum(s.overall_translation_score for s in scores) / total_scores
            )

            # Find best and worst scores
            best_score = max(scores, key=lambda s: s.overall_translation_score)
            worst_score = min(scores, key=lambda s: s.overall_translation_score)

            report = {
                "timestamp": datetime.now().isoformat(),
                "total_responses": total_scores,
                "average_scores": {
                    "language_detection": round(avg_detection, 3),
                    "translation_accuracy": round(avg_accuracy, 3),
                    "context_preservation": round(avg_context, 3),
                    "code_preservation": round(avg_code, 3),
                    "url_preservation": round(avg_url, 3),
                    "overall_translation": round(avg_overall, 3),
                },
                "best_score": {
                    "overall_translation": round(
                        best_score.overall_translation_score, 3
                    ),
                    "language_detection": round(best_score.language_detection, 3),
                    "translation_accuracy": round(best_score.translation_accuracy, 3),
                },
                "worst_score": {
                    "overall_translation": round(
                        worst_score.overall_translation_score, 3
                    ),
                    "language_detection": round(worst_score.language_detection, 3),
                    "translation_accuracy": round(worst_score.translation_accuracy, 3),
                },
                "translation_distribution": {
                    "excellent": len(
                        [s for s in scores if s.overall_translation_score >= 0.8]
                    ),
                    "good": len(
                        [s for s in scores if 0.6 <= s.overall_translation_score < 0.8]
                    ),
                    "fair": len(
                        [s for s in scores if 0.4 <= s.overall_translation_score < 0.6]
                    ),
                    "poor": len(
                        [s for s in scores if s.overall_translation_score < 0.4]
                    ),
                },
            }

            return report

        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return {"error": str(e)}


# Example usage
if __name__ == "__main__":
    # Test TranslationEval
    evaluator = TranslationEval()

    # Test responses
    test_responses = [
        {
            "response": "Xin chào anh! Em là StillMe AI. Rất vui được gặp anh! Em có thể giúp gì cho anh hôm nay?",
            "user_input": "Hello StillMe",
            "expected_language": "vietnamese",
            "source_language": "english",
        },
        {
            "response": "Hello! I'm StillMe AI. Nice to meet you! How can I help you today?",
            "user_input": "Xin chào StillMe",
            "expected_language": "english",
            "source_language": "vietnamese",
        },
    ]

    # Evaluate
    scores = evaluator.batch_evaluate(test_responses)

    # Generate report
    report = evaluator.generate_report(scores)

    print("🌐 TranslationEval Test Results:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
