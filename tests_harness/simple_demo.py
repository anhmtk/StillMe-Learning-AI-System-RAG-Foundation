#!/usr/bin/env python3
"""
Simple Demo - Test augmentation system với mock data
"""

import json
import logging
from pathlib import Path

def create_mock_seeds():
    """Tạo mock seed data"""
    seeds = [
        {"text": "Xin chào, hôm nay thế nào?", "type": "greeting", "language": "vi", "category": "persona"},
        {"text": "Hello, how are you today?", "type": "greeting", "language": "en", "category": "persona"},
        {"text": "Tôi muốn học lập trình Python", "type": "request", "language": "vi", "category": "coding"},
        {"text": "How can I learn machine learning?", "type": "request", "language": "en", "category": "coding"},
        {"text": "Cảm ơn bạn rất nhiều", "type": "gratitude", "language": "vi", "category": "persona"},
        {"text": "Thank you very much", "type": "gratitude", "language": "en", "category": "persona"},
        {"text": "Làm thế nào để tối ưu hóa database?", "type": "question", "language": "vi", "category": "technical"},
        {"text": "What is the best way to optimize performance?", "type": "question", "language": "en", "category": "technical"},
        {"text": "Tôi cảm thấy buồn hôm nay", "type": "emotion", "language": "vi", "category": "emotion"},
        {"text": "I feel sad today", "type": "emotion", "language": "en", "category": "emotion"}
    ]

    # Save to file
    seed_file = Path("datasets/seed/mock_seeds.jsonl")
    seed_file.parent.mkdir(parents=True, exist_ok=True)

    with open(seed_file, 'w', encoding='utf-8') as f:
        for seed in seeds:
            f.write(json.dumps(seed, ensure_ascii=False) + '\n')

    print(f"✅ Created {len(seeds)} mock seeds in {seed_file}")
    return str(seed_file)

def mock_paraphrase(text: str, num_variants: int = 3) -> list:
    """Mock paraphrase function"""
    variants = []
    for i in range(num_variants):
        if "Xin chào" in text:
            variants.append(f"Chào bạn, hôm nay {i+1}")
        elif "Hello" in text:
            variants.append(f"Hi there, how are you doing {i+1}?")
        elif "học lập trình" in text:
            variants.append(f"Tôi muốn học Python programming {i+1}")
        elif "learn machine learning" in text:
            variants.append(f"How to study ML {i+1}?")
        elif "Cảm ơn" in text:
            variants.append(f"Thanks a lot {i+1}")
        elif "Thank you" in text:
            variants.append(f"Much appreciated {i+1}")
        else:
            variants.append(f"{text} (variant {i+1})")

    return variants

def mock_backtranslate(text: str) -> list:
    """Mock backtranslate function"""
    variants = []
    if "Xin chào" in text:
        variants.append("Hello, how are you today?")
        variants.append("Hi, what's up?")
    elif "Hello" in text:
        variants.append("Xin chào, hôm nay thế nào?")
        variants.append("Chào bạn, có khỏe không?")
    else:
        variants.append(f"{text} (translated)")

    return variants

def mock_template_fill() -> list:
    """Mock template fill function"""
    templates = [
        "Xin chào [ROLE], [TIME] [QUESTION]?",
        "Hello [ROLE], [TIME] [QUESTION]?",
        "Chào [ROLE], hôm nay [ACTION]?",
        "Hi [ROLE], how are you [TIME]?"
    ]

    roles = ["bạn", "anh", "chị", "friend", "sir", "madam"]
    times = ["hôm nay", "hôm qua", "ngày mai", "today", "yesterday", "tomorrow"]
    questions = ["thế nào", "có gì mới", "có khỏe không", "how are you", "what's new", "are you okay"]
    actions = ["làm gì", "đi đâu", "ăn gì", "what are you doing", "where are you going", "what are you eating"]

    variants = []
    for template in templates:
        if "[ROLE]" in template:
            for role in roles[:2]:  # Limit for demo
                for time in times[:2]:
                    if "[QUESTION]" in template:
                        for question in questions[:2]:
                            variant = template.replace("[ROLE]", role).replace("[TIME]", time).replace("[QUESTION]", question)
                            variants.append(variant)
                    elif "[ACTION]" in template:
                        for action in actions[:2]:
                            variant = template.replace("[ROLE]", role).replace("[TIME]", time).replace("[ACTION]", action)
                            variants.append(variant)

    return variants[:20]  # Limit to 20 variants

def run_mock_augmentation():
    """Chạy mock augmentation"""

    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    print("🚀 StillMe Test Harness - Simple Mock Demo")
    print("="*60)

    # Create mock seeds
    seed_file = create_mock_seeds()

    # Load seeds
    seeds = []
    with open(seed_file, 'r', encoding='utf-8') as f:
        for line in f:
            seeds.append(json.loads(line.strip()))

    print(f"📊 Loaded {len(seeds)} seeds")

    # Create output directory
    output_dir = Path("datasets/augmented")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run mock augmentation
    all_variants = []

    # 1. Paraphrase
    print("\n🔄 Running mock paraphrase...")
    paraphrase_variants = []
    for seed in seeds:
        variants = mock_paraphrase(seed['text'], 3)
        for variant in variants:
            paraphrase_variants.append({
                "original": seed['text'],
                "variant": variant,
                "method": "paraphrase",
                "metadata": {"mock": True}
            })

    print(f"✅ Generated {len(paraphrase_variants)} paraphrase variants")
    all_variants.extend(paraphrase_variants)

    # 2. Backtranslate
    print("\n🔄 Running mock backtranslate...")
    backtranslate_variants = []
    for seed in seeds:
        variants = mock_backtranslate(seed['text'])
        for variant in variants:
            backtranslate_variants.append({
                "original": seed['text'],
                "variant": variant,
                "method": "backtranslate",
                "metadata": {"mock": True}
            })

    print(f"✅ Generated {len(backtranslate_variants)} backtranslate variants")
    all_variants.extend(backtranslate_variants)

    # 3. Template Fill
    print("\n🔄 Running mock template fill...")
    template_variants = []
    variants = mock_template_fill()
    for variant in variants:
        template_variants.append({
            "variant": variant,
            "method": "template_fill",
            "metadata": {"mock": True}
        })

    print(f"✅ Generated {len(template_variants)} template variants")
    all_variants.extend(template_variants)

    # Save results
    output_file = output_dir / "mock_augmented_combined.jsonl"
    with open(output_file, 'w', encoding='utf-8') as f:
        for variant in all_variants:
            f.write(json.dumps(variant, ensure_ascii=False) + '\n')

    # Generate statistics
    stats = {
        "total_seeds": len(seeds),
        "total_outputs": len(all_variants),
        "methods_used": ["paraphrase", "backtranslate", "template_fill"],
        "success_rates": {
            "paraphrase": 1.0,
            "backtranslate": 1.0,
            "template_fill": 1.0
        },
        "output_files": [str(output_file)]
    }

    # Print results
    print("\n" + "="*60)
    print("MOCK AUGMENTATION RESULTS")
    print("="*60)
    print(f"Total Seeds Processed: {stats['total_seeds']}")
    print(f"Total Outputs Generated: {stats['total_outputs']}")
    print(f"Methods Used: {', '.join(stats['methods_used'])}")

    print("\nSuccess Rates by Method:")
    for method, rate in stats['success_rates'].items():
        print(f"  {method}: {rate:.2%}")

    print(f"\nOutput File: {output_file}")
    print(f"File Size: {output_file.stat().st_size} bytes")

    # Show sample outputs
    print("\nSample Outputs:")
    with open(output_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 10:  # Show only first 10 lines
                break
            data = json.loads(line.strip())
            if 'variant' in data:
                print(f"  {data['variant']}")
            elif 'text' in data:
                print(f"  {data['text']}")

    print("="*60)
    print("✅ Mock demo completed successfully!")

    return stats

if __name__ == "__main__":
    run_mock_augmentation()
