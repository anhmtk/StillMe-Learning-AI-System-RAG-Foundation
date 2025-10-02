#!/usr/bin/env python3
"""
Backtranslate Module - Tạo biến thể bằng dịch qua lại
Sử dụng NLLB để dịch sang nhiều ngôn ngữ rồi dịch ngược lại
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

# Add stillme_core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    from stillme_core.modules.api_provider_manager import UnifiedAPIManager
except ImportError:
    print("Warning: UnifiedAPIManager not available, using mock")
    UnifiedAPIManager = None


@dataclass
class BacktranslateConfig:
    """Cấu hình cho backtranslate"""

    intermediate_languages: list[str] = None  # Ngôn ngữ trung gian
    nllb_model: str = "facebook/nllb-200-distilled-600M"
    max_rounds: int = 2  # Số vòng dịch tối đa
    temperature: float = 0.3  # Độ sáng tạo cho translation
    preserve_meaning_threshold: float = 0.7  # Ngưỡng giữ nguyên ý nghĩa

    def __post_init__(self):
        if self.intermediate_languages is None:
            self.intermediate_languages = ["en", "ja", "ko", "zh", "fr", "de", "es"]


@dataclass
class BacktranslateResult:
    """Kết quả backtranslate"""

    original: str
    variants: list[str]
    translation_paths: list[list[str]]  # Đường đi dịch
    success: bool
    error: Optional[str] = None
    metadata: dict[str, Any] = None


class Backtranslator:
    """Backtranslator sử dụng NLLB và local models"""

    def __init__(self, config: BacktranslateConfig = None):
        self.config = config or BacktranslateConfig()
        self.logger = logging.getLogger(__name__)

        # Language mapping for NLLB
        self.language_codes = {
            "vi": "vie_Latn",  # Vietnamese
            "en": "eng_Latn",  # English
            "ja": "jpn_Jpan",  # Japanese
            "ko": "kor_Hang",  # Korean
            "zh": "zho_Hans",  # Chinese Simplified
            "fr": "fra_Latn",  # French
            "de": "deu_Latn",  # German
            "es": "spa_Latn",  # Spanish
            "ru": "rus_Cyrl",  # Russian
            "ar": "arb_Arab",  # Arabic
        }

        # Initialize API manager
        if UnifiedAPIManager:
            try:
                self.api_manager = UnifiedAPIManager()
            except Exception as e:
                self.logger.warning(f"Failed to initialize UnifiedAPIManager: {e}")
                self.api_manager = None
        else:
            self.api_manager = None

    def _detect_language(self, text: str) -> str:
        """Detect ngôn ngữ của text"""
        # Simple heuristic detection
        vietnamese_chars = sum(1 for char in text if "\u1e00" <= char <= "\u1eff")
        chinese_chars = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
        japanese_chars = sum(
            1
            for char in text
            if "\u3040" <= char <= "\u309f" or "\u30a0" <= char <= "\u30ff"
        )
        korean_chars = sum(1 for char in text if "\uac00" <= char <= "\ud7af")
        arabic_chars = sum(1 for char in text if "\u0600" <= char <= "\u06ff")
        cyrillic_chars = sum(1 for char in text if "\u0400" <= char <= "\u04ff")

        total_chars = len([c for c in text if c.isalpha()])

        if total_chars == 0:
            return "en"  # Default to English

        if vietnamese_chars / total_chars > 0.1:
            return "vi"
        elif chinese_chars / total_chars > 0.1:
            return "zh"
        elif japanese_chars / total_chars > 0.1:
            return "ja"
        elif korean_chars / total_chars > 0.1:
            return "ko"
        elif arabic_chars / total_chars > 0.1:
            return "ar"
        elif cyrillic_chars / total_chars > 0.1:
            return "ru"
        else:
            return "en"

    async def _translate_with_nllb(
        self, text: str, src_lang: str, tgt_lang: str
    ) -> str:
        """Dịch sử dụng NLLB"""
        try:
            if not self.api_manager:
                # Mock translation
                return f"[{tgt_lang}] {text}"

            # Use NLLB through UnifiedAPIManager
            result = await self.api_manager.translate(
                text=text, src_lang=src_lang, tgt_lang=tgt_lang, quality_hint="high"
            )

            return result.get("text", text)

        except Exception as e:
            self.logger.warning(f"NLLB translation failed: {e}")
            return text

    async def _translate_with_local(
        self, text: str, src_lang: str, tgt_lang: str
    ) -> str:
        """Dịch sử dụng local model"""
        try:
            if not self.api_manager:
                # Mock translation
                return f"[{tgt_lang}] {text}"

            # Create translation prompt
            prompt = f"""Dịch câu sau từ {src_lang} sang {tgt_lang}:

"{text}"

Chỉ trả về bản dịch, không giải thích:"""

            response = self.api_manager.get_response(prompt=prompt, model="gemma2:2b")

            return response.strip()

        except Exception as e:
            self.logger.warning(f"Local translation failed: {e}")
            return text

    async def _translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        """Dịch text từ src_lang sang tgt_lang"""
        # Try NLLB first, fallback to local model
        result = await self._translate_with_nllb(text, src_lang, tgt_lang)
        if result == text:  # If no change, try local model
            result = await self._translate_with_local(text, src_lang, tgt_lang)

        return result

    async def backtranslate_text(self, text: str) -> BacktranslateResult:
        """Backtranslate một câu"""
        try:
            # Detect source language
            src_lang = self._detect_language(text)
            self.logger.info(f"Detected source language: {src_lang}")

            variants = []
            translation_paths = []

            # Select intermediate languages (exclude source language)
            available_langs = [
                lang for lang in self.config.intermediate_languages if lang != src_lang
            ]

            # Limit number of paths
            max_paths = min(len(available_langs), 5)
            selected_langs = available_langs[:max_paths]

            for intermediate_lang in selected_langs:
                try:
                    # Forward translation
                    intermediate_text = await self._translate(
                        text, src_lang, intermediate_lang
                    )

                    # Backward translation
                    backtranslated_text = await self._translate(
                        intermediate_text, intermediate_lang, src_lang
                    )

                    # Check if meaning is preserved (simple heuristic)
                    if self._is_meaning_preserved(text, backtranslated_text):
                        variants.append(backtranslated_text)
                        translation_paths.append(
                            [src_lang, intermediate_lang, src_lang]
                        )

                except Exception as e:
                    self.logger.warning(
                        f"Backtranslate path failed {src_lang}->{intermediate_lang}->{src_lang}: {e}"
                    )
                    continue

            return BacktranslateResult(
                original=text,
                variants=variants,
                translation_paths=translation_paths,
                success=len(variants) > 0,
                metadata={
                    "source_language": src_lang,
                    "intermediate_languages": selected_langs,
                    "successful_paths": len(variants),
                },
            )

        except Exception as e:
            self.logger.error(f"Backtranslate failed: {e}")
            return BacktranslateResult(
                original=text,
                variants=[],
                translation_paths=[],
                success=False,
                error=str(e),
            )

    def _is_meaning_preserved(self, original: str, translated: str) -> bool:
        """Kiểm tra xem ý nghĩa có được giữ nguyên không"""
        # Simple heuristic: check length ratio and common words
        if not original or not translated:
            return False

        # Length ratio check
        length_ratio = len(translated) / len(original)
        if length_ratio < 0.3 or length_ratio > 3.0:
            return False

        # Check for common words (simple approach)
        original_words = set(original.lower().split())
        translated_words = set(translated.lower().split())

        if len(original_words) == 0:
            return True

        common_words = original_words.intersection(translated_words)
        similarity = len(common_words) / len(original_words)

        return similarity >= self.config.preserve_meaning_threshold

    async def backtranslate_batch(self, texts: list[str]) -> list[BacktranslateResult]:
        """Backtranslate nhiều câu cùng lúc"""
        tasks = [self.backtranslate_text(text) for text in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    BacktranslateResult(
                        original=texts[i],
                        variants=[],
                        translation_paths=[],
                        success=False,
                        error=str(result),
                    )
                )
            else:
                processed_results.append(result)

        return processed_results


class BacktranslateAugmentor:
    """Augmentor chính cho backtranslate"""

    def __init__(self, config: BacktranslateConfig = None):
        self.backtranslator = Backtranslator(config)
        self.logger = logging.getLogger(__name__)

    async def augment_dataset(
        self, input_file: str, output_file: str
    ) -> dict[str, Any]:
        """Augment dataset từ file input"""
        input_path = Path(input_file)
        output_path = Path(output_file)

        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        # Load input data
        texts = []
        with open(input_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        if "text" in data:
                            texts.append(data["text"])
                        elif "message" in data:
                            texts.append(data["message"])
                        else:
                            texts.append(str(data))
                    except json.JSONDecodeError:
                        texts.append(line)

        self.logger.info(f"Loaded {len(texts)} texts for backtranslation")

        # Backtranslate in batches
        batch_size = 5  # Smaller batch size for translation
        all_results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            self.logger.info(
                f"Processing batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}"
            )

            results = await self.backtranslator.backtranslate_batch(batch)
            all_results.extend(results)

        # Save results
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for result in all_results:
                if result.success:
                    for i, variant in enumerate(result.variants):
                        output_data = {
                            "original": result.original,
                            "variant": variant,
                            "method": "backtranslate",
                            "translation_path": result.translation_paths[i]
                            if i < len(result.translation_paths)
                            else [],
                            "metadata": result.metadata,
                        }
                        f.write(json.dumps(output_data, ensure_ascii=False) + "\n")

        # Generate statistics
        stats = {
            "total_inputs": len(texts),
            "total_outputs": sum(len(r.variants) for r in all_results if r.success),
            "success_rate": sum(1 for r in all_results if r.success) / len(all_results),
            "config": {
                "intermediate_languages": self.backtranslator.config.intermediate_languages,
                "max_rounds": self.backtranslator.config.max_rounds,
            },
        }

        self.logger.info(f"Backtranslate augmentation completed: {stats}")
        return stats


async def main():
    """Demo function"""
    config = BacktranslateConfig(
        intermediate_languages=["en", "ja", "ko"], max_rounds=2
    )

    augmentor = BacktranslateAugmentor(config)

    # Test single text
    result = await augmentor.backtranslator.backtranslate_text(
        "Xin chào, hôm nay thế nào?"
    )
    print(f"Original: {result.original}")
    print("Variants:")
    for i, variant in enumerate(result.variants, 1):
        print(f"  {i}. {variant}")
        if i <= len(result.translation_paths):
            print(f"     Path: {' -> '.join(result.translation_paths[i-1])}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
