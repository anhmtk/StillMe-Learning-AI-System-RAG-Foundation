#!/usr/bin/env python3
"""
Demo Script - Test augmentation system với sample data
Tạo 50 seed mẫu và demo augment ra 500-1000 câu
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from augmentor.augment_runner import AugmentConfig, AugmentRunner
from augmentor.backtranslate import BacktranslateConfig
from augmentor.paraphraser import ParaphraseConfig
from augmentor.template_filler import TemplateConfig


async def demo_augmentation():
    """Demo augmentation với sample data"""

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)
    logger.info("Starting augmentation demo...")

    # Create output directory
    output_dir = Path("datasets/augmented")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Configuration for demo
    config = AugmentConfig(
        seed_file="datasets/seed/sample_seeds.jsonl",
        output_dir=str(output_dir),
        use_paraphrase=True,
        use_backtranslate=True,
        use_template_fill=True,
        max_seed_size=50,  # Limit for demo
        paraphrase_config=ParaphraseConfig(
            model="gemma2:2b",
            num_variants=3,  # Reduced for demo
            temperature=0.7
        ),
        backtranslate_config=BacktranslateConfig(
            intermediate_languages=["en", "ja", "ko"],  # Reduced for demo
            max_rounds=2
        ),
        template_config=TemplateConfig(
            num_variants_per_template=5,  # Reduced for demo
            use_ai_generation=True
        )
    )

    # Run augmentation
    runner = AugmentRunner(config)

    try:
        stats = await runner.run_augmentation()

        # Print results
        print("\n" + "="*60)
        print("AUGMENTATION DEMO RESULTS")
        print("="*60)
        print(f"Total Seeds Processed: {stats.total_seeds}")
        print(f"Total Outputs Generated: {stats.total_outputs}")
        print(f"Processing Time: {stats.processing_time:.2f} seconds")
        print(f"Methods Used: {', '.join(stats.methods_used)}")

        print("\nSuccess Rates by Method:")
        for method, rate in stats.success_rates.items():
            print(f"  {method}: {rate:.2%}")

        print(f"\nOutput Files Generated: {len(stats.output_files)}")
        for file_path in stats.output_files:
            file_size = Path(file_path).stat().st_size if Path(file_path).exists() else 0
            print(f"  - {file_path} ({file_size} bytes)")

        # Show sample outputs
        print("\nSample Outputs:")
        for output_file in stats.output_files:
            if Path(output_file).exists() and "combined" not in output_file:
                print(f"\n--- {Path(output_file).name} ---")
                with open(output_file, encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        if i >= 3:  # Show only first 3 lines
                            break
                        try:
                            data = json.loads(line.strip())
                            if 'variant' in data:
                                print(f"  {data['variant']}")
                            elif 'text' in data:
                                print(f"  {data['text']}")
                        except:
                            print(f"  {line.strip()}")

        print("="*60)

        return stats

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise

async def demo_individual_methods():
    """Demo từng method riêng lẻ"""

    logger = logging.getLogger(__name__)
    logger.info("Testing individual augmentation methods...")

    # Test Paraphrase
    print("\n--- Testing Paraphrase ---")
    from augmentor.paraphraser import ParaphraseAugmentor, ParaphraseConfig

    paraphrase_config = ParaphraseConfig(
        model="gemma2:2b",
        num_variants=3,
        temperature=0.7
    )

    paraphraser = ParaphraseAugmentor(paraphrase_config)

    # Test single text
    result = await paraphraser.paraphraser.paraphrase_text("Xin chào, hôm nay thế nào?")
    print(f"Original: {result.original}")
    print("Variants:")
    for i, variant in enumerate(result.variants, 1):
        print(f"  {i}. {variant}")

    # Test Template Fill
    print("\n--- Testing Template Fill ---")
    from augmentor.template_filler import TemplateConfig, TemplateFillerAugmentor

    template_config = TemplateConfig(
        num_variants_per_template=3,
        use_ai_generation=True
    )

    template_filler = TemplateFillerAugmentor(template_config)

    # Test with one template
    from augmentor.template_filler import Template, TemplateSlot
    test_template = Template(
        name="test_greeting",
        template="[GREETING] [ROLE], [TIME] [QUESTION]?",
        slots=[
            TemplateSlot("GREETING", "greeting", ["Xin chào", "Chào", "Hi"]),
            TemplateSlot("ROLE", "role", ["bạn", "anh", "chị"]),
            TemplateSlot("TIME", "time", ["hôm nay", "hôm qua", "ngày mai"]),
            TemplateSlot("QUESTION", "question", ["thế nào", "có gì mới", "có khỏe không"])
        ]
    )

    template_result = await template_filler.template_filler.fill_template(test_template)
    print(f"Template: {template_result.original_template}")
    print("Generated variants:")
    for i, variant in enumerate(template_result.variants[:5], 1):  # Show first 5
        print(f"  {i}. {variant}")

async def main():
    """Main demo function"""
    print("🚀 StillMe Test Harness - Augmentation Demo")
    print("="*60)

    try:
        # Test individual methods first
        await demo_individual_methods()

        # Run full augmentation demo
        print("\n🔄 Running full augmentation pipeline...")
        stats = await demo_augmentation()

        print("\n✅ Demo completed successfully!")
        print(f"📊 Generated {stats.total_outputs} variants from {stats.total_seeds} seeds")
        print(f"⏱️  Processing time: {stats.processing_time:.2f} seconds")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
