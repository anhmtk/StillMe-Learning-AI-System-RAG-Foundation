from typing import Any, Dict

#!/usr/bin/env python3
"""
SEAL-GRADE Test Suite: Ambiguity Extremes
Tests the most challenging ambiguous inputs that could break the system
"""

import json
import time

from stillme_core.modules.clarification_handler import ClarificationHandler


class AmbiguityExtremesTestSuite:
    """Test suite for extreme ambiguity scenarios"""

    def __init__(self):
        self.handler = ClarificationHandler()
        self.test_results = []

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all ambiguity extreme tests"""
        print("🧪 Starting Ambiguity Extremes Test Suite...")

        tests = [
            ("Single Character Input", self.test_single_character),
            ("Empty String", self.test_empty_string),
            ("Whitespace Only", self.test_whitespace_only),
            ("Unicode Chaos", self.test_unicode_chaos),
            ("Nested Vague 5 Levels", self.test_nested_vague_5_levels),
            ("Ambiguous Pronouns", self.test_ambiguous_pronouns),
            ("Context Switching", self.test_context_switching),
            ("Mixed Languages", self.test_mixed_languages),
            ("Slang & Internet Speak", self.test_slang_internet_speak),
            ("Philosophical Vague", self.test_philosophical_vague),
            ("Technical Jargon Vague", self.test_technical_jargon_vague),
            ("Emotional Vague", self.test_emotional_vague),
            ("Time-based Vague", self.test_time_based_vague),
            ("Location Vague", self.test_location_vague),
            ("Quantity Vague", self.test_quantity_vague)
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            try:
                start_time = time.time()
                result = test_func()
                duration = time.time() - start_time

                if result:
                    print(f"✅ {test_name} - PASSED ({duration:.3f}s)")
                    passed += 1
                else:
                    print(f"❌ {test_name} - FAILED ({duration:.3f}s)")
                    failed += 1

                self.test_results.append({
                    "test": test_name,
                    "passed": result,
                    "duration": duration
                })

            except Exception as e:
                print(f"💥 {test_name} - ERROR: {e}")
                failed += 1
                self.test_results.append({
                    "test": test_name,
                    "passed": False,
                    "duration": 0,
                    "error": str(e)
                })

        summary = {
            "total": len(tests),
            "passed": passed,
            "failed": failed,
            "pass_rate": (passed / len(tests)) * 100,
            "results": self.test_results
        }

        print("\n📊 Ambiguity Extremes Summary:")
        print(f"   Total Tests: {summary['total']}")
        print(f"   Passed: {summary['passed']}")
        print(f"   Failed: {summary['failed']}")
        print(f"   Pass Rate: {summary['pass_rate']:.1f}%")

        return summary

    def test_single_character(self) -> bool:
        """Test: Single character input → must handle gracefully"""
        inputs = ["a", "?", "!", ".", "1", "中", "🚀"]

        for input_text in inputs:
            result = self.handler.detect_ambiguity(input_text)
            # Should not crash, should return a valid result
            assert result is not None
            assert hasattr(result, 'needs_clarification')
            assert hasattr(result, 'confidence')

        return True

    def test_empty_string(self) -> bool:
        """Test: Empty string → must handle gracefully"""
        result = self.handler.detect_ambiguity("")
        assert result is not None
        assert hasattr(result, 'needs_clarification')
        # Empty string should be considered ambiguous
        assert result.needs_clarification is True

        return True

    def test_whitespace_only(self) -> bool:
        """Test: Only whitespace → must handle gracefully"""
        inputs = ["   ", "\n\n\n", "\t\t\t", " \n \t "]

        for input_text in inputs:
            result = self.handler.detect_ambiguity(input_text)
            assert result is not None
            assert hasattr(result, 'needs_clarification')
            # Whitespace-only should be considered ambiguous
            assert result.needs_clarification is True

        return True

    def test_unicode_chaos(self) -> bool:
        """Test: Unicode chaos → must handle gracefully"""
        inputs = [
            "🚀🚀🚀🚀🚀",  # Emoji spam
            "中文中文中文",  # Chinese characters
            "العربية العربية",  # Arabic
            "русский русский",  # Cyrillic
            "🎭🎪🎨🎬🎮🎯🎰🎱🎲🎳",  # Mixed emojis
            "αβγδεζηθικλμνξοπρστυφχψω",  # Greek
            "∀∃∈∉⊂⊃∪∩∅∞∑∏∫∂∇",  # Math symbols
        ]

        for input_text in inputs:
            result = self.handler.detect_ambiguity(input_text)
            assert result is not None
            assert hasattr(result, 'needs_clarification')
            # Unicode chaos should be considered ambiguous
            if not result.needs_clarification:
                print(f"DEBUG: Unicode input '{input_text}' not detected as ambiguous: confidence={result.confidence}")
            assert result.needs_clarification is True

        return True

    def test_nested_vague_5_levels(self) -> bool:
        """Test: 5 levels of nested vague phrases → must handle gracefully"""
        nested_vague = (
            "Can you make it better, you know, like the other one, "
            "but faster, and not too heavy, but still good quality, "
            "and maybe a bit more modern, but not too fancy, "
            "and make sure it works well, but not too complicated, "
            "and maybe add some features, but not too many, "
            "and make it look nice, but not too flashy, "
            "and ensure it's reliable, but not too expensive"
        )

        result = self.handler.detect_ambiguity(nested_vague)
        assert result is not None
        assert result.needs_clarification is True
        assert result.confidence > 0.5  # Should have high confidence for ambiguity
        assert result.question is not None
        assert len(result.question) > 10  # Should generate meaningful question

        return True

    def test_ambiguous_pronouns(self) -> bool:
        """Test: Ambiguous pronouns → must ask for clarification"""
        inputs = [
            "Fix it",
            "Do that thing",
            "Make this better",
            "Update those files",
            "Delete them",
            "Move it over there",
            "Change this to that",
            "Replace it with something else"
        ]

        for input_text in inputs:
            result = self.handler.detect_ambiguity(input_text)
            assert result is not None
            assert result.needs_clarification is True
            assert result.confidence > 0.3  # Should detect ambiguity

        return True

    def test_context_switching(self) -> bool:
        """Test: Context switching mid-sentence → must handle gracefully"""
        inputs = [
            "Fix the bug in the database but also update the UI to make it look better",
            "Optimize the algorithm for performance and also add error handling",
            "Refactor the code to be cleaner and also add unit tests",
            "Update the documentation and also fix the broken links",
            "Deploy to production and also monitor the logs"
        ]

        for input_text in inputs:
            result = self.handler.detect_ambiguity(input_text)
            assert result is not None
            assert hasattr(result, 'needs_clarification')
            # Context switching should be considered ambiguous
            assert result.needs_clarification is True

        return True

    def test_mixed_languages(self) -> bool:
        """Test: Mixed languages → must handle gracefully"""
        inputs = [
            "Fix the bug trong database",
            "Optimize performance 性能优化",
            "Update UI 界面更新",
            "Deploy to production 部署到生产环境",
            "Test the functionality 测试功能",
            "Code review 代码审查",
            "Bug fix 错误修复"
        ]

        for input_text in inputs:
            result = self.handler.detect_ambiguity(input_text)
            assert result is not None
            assert hasattr(result, 'needs_clarification')
            # Mixed languages should be considered ambiguous
            assert result.needs_clarification is True

        return True

    def test_slang_internet_speak(self) -> bool:
        """Test: Slang and internet speak → must handle gracefully"""
        inputs = [
            "Make it lit",
            "This is fire",
            "That's sus",
            "No cap",
            "It's bussin",
            "That's mid",
            "Make it pop",
            "It's giving main character energy",
            "That's a vibe",
            "Make it aesthetic"
        ]

        for input_text in inputs:
            result = self.handler.detect_ambiguity(input_text)
            assert result is not None
            assert hasattr(result, 'needs_clarification')
            # Slang should be considered ambiguous
            assert result.needs_clarification is True

        return True

    def test_philosophical_vague(self) -> bool:
        """Test: Philosophical vague statements → must handle gracefully"""
        inputs = [
            "Make it more meaningful",
            "Improve the essence",
            "Enhance the soul of the system",
            "Make it more authentic",
            "Improve the core being",
            "Enhance the fundamental nature",
            "Make it more profound",
            "Improve the intrinsic value"
        ]

        for input_text in inputs:
            result = self.handler.detect_ambiguity(input_text)
            assert result is not None
            assert hasattr(result, 'needs_clarification')
            # Philosophical vague should be considered ambiguous
            assert result.needs_clarification is True

        return True

    def test_technical_jargon_vague(self) -> bool:
        """Test: Technical jargon that's still vague → must handle gracefully"""
        inputs = [
            "Optimize the architecture",
            "Improve the scalability",
            "Enhance the robustness",
            "Make it more maintainable",
            "Improve the modularity",
            "Enhance the extensibility",
            "Make it more performant",
            "Improve the reliability"
        ]

        for input_text in inputs:
            result = self.handler.detect_ambiguity(input_text)
            assert result is not None
            assert hasattr(result, 'needs_clarification')
            # Technical jargon vague should be considered ambiguous
            assert result.needs_clarification is True

        return True

    def test_emotional_vague(self) -> bool:
        """Test: Emotional vague statements → must handle gracefully"""
        inputs = [
            "Make it feel better",
            "Improve the user experience",
            "Make it more intuitive",
            "Enhance the emotional connection",
            "Make it more engaging",
            "Improve the satisfaction",
            "Make it more delightful",
            "Enhance the joy factor"
        ]

        for input_text in inputs:
            result = self.handler.detect_ambiguity(input_text)
            assert result is not None
            assert hasattr(result, 'needs_clarification')
            # Emotional vague should be considered ambiguous
            assert result.needs_clarification is True

        return True

    def test_time_based_vague(self) -> bool:
        """Test: Time-based vague statements → must handle gracefully"""
        inputs = [
            "Make it faster",
            "Improve the response time",
            "Enhance the speed",
            "Make it more efficient",
            "Improve the performance",
            "Make it quicker",
            "Enhance the throughput",
            "Make it more responsive"
        ]

        for input_text in inputs:
            result = self.handler.detect_ambiguity(input_text)
            assert result is not None
            assert hasattr(result, 'needs_clarification')
            # Time-based vague should be considered ambiguous
            assert result.needs_clarification is True

        return True

    def test_location_vague(self) -> bool:
        """Test: Location-based vague statements → must handle gracefully"""
        inputs = [
            "Move it over there",
            "Put it somewhere else",
            "Relocate the component",
            "Move it to a better place",
            "Put it in the right spot",
            "Relocate it properly",
            "Move it to the center",
            "Put it in the corner"
        ]

        for input_text in inputs:
            result = self.handler.detect_ambiguity(input_text)
            assert result is not None
            assert hasattr(result, 'needs_clarification')
            # Location vague should be considered ambiguous
            assert result.needs_clarification is True

        return True

    def test_quantity_vague(self) -> bool:
        """Test: Quantity-based vague statements → must handle gracefully"""
        inputs = [
            "Add more features",
            "Include additional options",
            "Add some more stuff",
            "Include a few more things",
            "Add plenty of features",
            "Include lots of options",
            "Add a bunch of stuff",
            "Include several more things"
        ]

        for input_text in inputs:
            result = self.handler.detect_ambiguity(input_text)
            assert result is not None
            assert hasattr(result, 'needs_clarification')
            # Quantity vague should be considered ambiguous
            assert result.needs_clarification is True

        return True

def main():
    """Run the ambiguity extremes test suite"""
    suite = AmbiguityExtremesTestSuite()
    results = suite.run_all_tests()

    # Save results to file
    with open("ambiguity_extremes_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n🎯 Ambiguity Extremes Test Suite Complete!")
    print(f"   Pass Rate: {results['pass_rate']:.1f}%")

    if results['pass_rate'] >= 90:
        print("🎉 System handles ambiguity extremes excellently!")
    elif results['pass_rate'] >= 75:
        print("✅ System handles ambiguity extremes well!")
    else:
        print("⚠️ System needs improvement for ambiguity extremes")

    return results['pass_rate'] >= 75

if __name__ == "__main__":
    main()
