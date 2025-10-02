#!/usr/bin/env python3
"""
Seed Generator - Sinh seed data từ AI public APIs
Sử dụng OpenAI, Claude, Gemini, DeepSeek để tạo 500-1000 câu đa dạng
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add stillme_core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from stillme_core.modules.api_provider_manager import UnifiedAPIManager
except ImportError:
    print("Warning: UnifiedAPIManager not available, using mock")
    UnifiedAPIManager = None

@dataclass
class SeedConfig:
    """Cấu hình cho seed generation"""
    output_file: str
    num_seeds: int = 1000
    categories: List[str] = None
    languages: List[str] = None
    models: List[str] = None

    def __post_init__(self):
        if self.categories is None:
            self.categories = [
                "greeting", "question", "request", "gratitude", "emotion",
                "coding", "technical", "education", "career", "personal",
                "business", "technology", "lifestyle", "health", "travel"
            ]

        if self.languages is None:
            self.languages = ["vi", "en", "ja", "ko", "zh"]

        if self.models is None:
            self.models = ["gpt-3.5-turbo", "gpt-4", "claude-3-sonnet", "gemini-pro"]

@dataclass
class SeedItem:
    """Một seed item"""
    text: str
    language: str
    category: str
    type: str
    metadata: Dict[str, Any] = None

class SeedGenerator:
    """Generator để tạo seed data từ AI public APIs"""

    def __init__(self, config: SeedConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize API manager
        if UnifiedAPIManager:
            try:
                self.api_manager = UnifiedAPIManager()
            except Exception as e:
                self.logger.warning(f"Failed to initialize UnifiedAPIManager: {e}")
                self.api_manager = None
        else:
            self.api_manager = None

    def _create_generation_prompt(self, category: str, language: str, count: int) -> str:
        """Tạo prompt để sinh seed data"""

        language_names = {
            "vi": "tiếng Việt",
            "en": "English",
            "ja": "Japanese",
            "ko": "Korean",
            "zh": "Chinese"
        }

        category_descriptions = {
            "greeting": "lời chào hỏi thân thiện",
            "question": "câu hỏi thông thường",
            "request": "yêu cầu giúp đỡ",
            "gratitude": "lời cảm ơn",
            "emotion": "chia sẻ cảm xúc",
            "coding": "câu hỏi về lập trình",
            "technical": "câu hỏi kỹ thuật",
            "education": "học tập và giáo dục",
            "career": "sự nghiệp và công việc",
            "personal": "cá nhân và cuộc sống",
            "business": "kinh doanh và khởi nghiệp",
            "technology": "công nghệ và AI",
            "lifestyle": "lối sống và sở thích",
            "health": "sức khỏe và thể thao",
            "travel": "du lịch và khám phá"
        }

        lang_name = language_names.get(language, language)
        cat_desc = category_descriptions.get(category, category)

        prompt = f"""Tạo {count} câu {cat_desc} bằng {lang_name} để test AI chatbot.

Yêu cầu:
- Câu tự nhiên, đa dạng
- Phù hợp với ngữ cảnh {cat_desc}
- Độ dài từ 5-50 từ
- Không chứa nội dung nhạy cảm
- Mỗi câu trên một dòng riêng
- Không đánh số thứ tự

Ví dụ format:
Câu 1
Câu 2
Câu 3
...

Bắt đầu:"""

        return prompt

    async def _generate_seeds_for_category(self, category: str, language: str, count: int) -> List[SeedItem]:
        """Sinh seeds cho một category và language cụ thể"""

        if not self.api_manager:
            # Mock generation for testing
            mock_seeds = []
            for i in range(count):
                mock_seeds.append(SeedItem(
                    text=f"Mock {category} sentence {i+1} in {language}",
                    language=language,
                    category=category,
                    type="mock",
                    metadata={"generated_by": "mock", "timestamp": datetime.now().isoformat()}
                ))
            return mock_seeds

        try:
            # Create prompt
            prompt = self._create_generation_prompt(category, language, count)

            # Use different models for variety
            model = "gpt-3.5-turbo"  # Default model

            # Generate response
            response = self.api_manager.get_response(
                prompt=prompt,
                model=model
            )

            # Parse response
            seeds = []
            lines = response.strip().split('\n')

            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Remove numbering if present
                    if line.startswith(('1.', '2.', '3.', '4.', '5.', '-', '*')):
                        line = line.split('.', 1)[-1].strip()
                        line = line.lstrip('-* ').strip()

                    if line and len(line) > 3:  # Minimum length check
                        seeds.append(SeedItem(
                            text=line,
                            language=language,
                            category=category,
                            type="ai_generated",
                            metadata={
                                "generated_by": model,
                                "timestamp": datetime.now().isoformat(),
                                "prompt_category": category,
                                "prompt_language": language
                            }
                        ))

            # Ensure we have enough seeds
            while len(seeds) < count:
                seeds.append(SeedItem(
                    text=f"Generated {category} sentence {len(seeds)+1} in {language}",
                    language=language,
                    category=category,
                    type="fallback",
                    metadata={"generated_by": "fallback", "timestamp": datetime.now().isoformat()}
                ))

            return seeds[:count]

        except Exception as e:
            self.logger.error(f"Failed to generate seeds for {category}/{language}: {e}")
            # Return fallback seeds
            return [
                SeedItem(
                    text=f"Fallback {category} sentence in {language}",
                    language=language,
                    category=category,
                    type="error_fallback",
                    metadata={"error": str(e), "timestamp": datetime.now().isoformat()}
                )
            ]

    async def generate_seeds(self) -> List[SeedItem]:
        """Sinh tất cả seed data"""

        all_seeds = []
        seeds_per_combination = self.config.num_seeds // (len(self.config.categories) * len(self.config.languages))

        if seeds_per_combination < 1:
            seeds_per_combination = 1

        self.logger.info(f"Generating {seeds_per_combination} seeds per category/language combination")

        # Generate seeds for each category/language combination
        for category in self.config.categories:
            for language in self.config.languages:
                self.logger.info(f"Generating seeds for {category}/{language}")

                seeds = await self._generate_seeds_for_category(
                    category, language, seeds_per_combination
                )
                all_seeds.extend(seeds)

        # Shuffle and limit to exact number
        import random
        random.shuffle(all_seeds)
        all_seeds = all_seeds[:self.config.num_seeds]

        self.logger.info(f"Generated {len(all_seeds)} total seeds")
        return all_seeds

    def save_seeds(self, seeds: List[SeedItem]):
        """Lưu seeds vào file"""

        output_path = Path(self.config.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            for seed in seeds:
                seed_data = {
                    "text": seed.text,
                    "language": seed.language,
                    "category": seed.category,
                    "type": seed.type,
                    "metadata": seed.metadata or {}
                }
                f.write(json.dumps(seed_data, ensure_ascii=False) + '\n')

        self.logger.info(f"Saved {len(seeds)} seeds to {output_path}")

        # Generate statistics
        stats = {
            "total_seeds": len(seeds),
            "by_language": {},
            "by_category": {},
            "by_type": {},
            "generation_time": datetime.now().isoformat()
        }

        for seed in seeds:
            stats["by_language"][seed.language] = stats["by_language"].get(seed.language, 0) + 1
            stats["by_category"][seed.category] = stats["by_category"].get(seed.category, 0) + 1
            stats["by_type"][seed.type] = stats["by_type"].get(seed.type, 0) + 1

        # Save statistics
        stats_file = output_path.with_suffix('.stats.json')
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        self.logger.info(f"Saved statistics to {stats_file}")
        return stats

async def main():
    """Main function"""

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)
    logger.info("Starting seed generation...")

    # Configuration
    config = SeedConfig(
        output_file="tests_harness/datasets/seed/generated_seeds.jsonl",
        num_seeds=1000,
        categories=["greeting", "question", "request", "gratitude", "emotion", "coding", "technical"],
        languages=["vi", "en", "ja", "ko"],
        models=["gpt-3.5-turbo", "gpt-4"]
    )

    # Generate seeds
    generator = SeedGenerator(config)
    seeds = await generator.generate_seeds()

    # Save seeds
    stats = generator.save_seeds(seeds)

    # Print results
    print("\n" + "="*60)
    print("SEED GENERATION RESULTS")
    print("="*60)
    print(f"Total Seeds Generated: {stats['total_seeds']}")
    print(f"Output File: {config.output_file}")

    print("\nBy Language:")
    for lang, count in stats['by_language'].items():
        print(f"  {lang}: {count}")

    print("\nBy Category:")
    for cat, count in stats['by_category'].items():
        print(f"  {cat}: {count}")

    print("\nBy Type:")
    for type_name, count in stats['by_type'].items():
        print(f"  {type_name}: {count}")

    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
