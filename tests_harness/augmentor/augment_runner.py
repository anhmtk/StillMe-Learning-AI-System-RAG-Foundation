#!/usr/bin/env python3
"""
Augment Runner - Script chính để gom seed -> augmented dataset
Kết hợp tất cả các phương pháp augment: paraphrase, backtranslate, template_fill
"""

import json
import asyncio
import logging
import argparse
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from paraphraser import ParaphraseAugmentor, ParaphraseConfig
from backtranslate import BacktranslateAugmentor, BacktranslateConfig
from template_filler import TemplateFillerAugmentor, TemplateConfig

@dataclass
class AugmentConfig:
    """Cấu hình tổng thể cho augmentation"""
    # Input/Output
    seed_file: str
    output_dir: str

    # Methods to use
    use_paraphrase: bool = True
    use_backtranslate: bool = True
    use_template_fill: bool = True

    # Paraphrase config
    paraphrase_config: ParaphraseConfig = None

    # Backtranslate config
    backtranslate_config: BacktranslateConfig = None

    # Template config
    template_config: TemplateConfig = None

    # General settings
    max_seed_size: int = 1000  # Giới hạn số seed để xử lý
    batch_size: int = 10
    parallel_workers: int = 3

    def __post_init__(self):
        if self.paraphrase_config is None:
            self.paraphrase_config = ParaphraseConfig()
        if self.backtranslate_config is None:
            self.backtranslate_config = BacktranslateConfig()
        if self.template_config is None:
            self.template_config = TemplateConfig()

@dataclass
class AugmentStats:
    """Thống kê augmentation"""
    total_seeds: int
    total_outputs: int
    methods_used: List[str]
    success_rates: Dict[str, float]
    processing_time: float
    output_files: List[str]
    metadata: Dict[str, Any]

class AugmentRunner:
    """Runner chính cho augmentation pipeline"""

    def __init__(self, config: AugmentConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize augmentors
        self.augmentors = {}

        if config.use_paraphrase:
            self.augmentors['paraphrase'] = ParaphraseAugmentor(config.paraphrase_config)

        if config.use_backtranslate:
            self.augmentors['backtranslate'] = BacktranslateAugmentor(config.backtranslate_config)

        if config.use_template_fill:
            self.augmentors['template_fill'] = TemplateFillerAugmentor(config.template_config)

    def _load_seed_data(self) -> List[Dict[str, Any]]:
        """Load seed data từ file"""
        seed_path = Path(self.config.seed_file)
        if not seed_path.exists():
            raise FileNotFoundError(f"Seed file not found: {self.config.seed_file}")

        seeds = []
        with open(seed_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        seeds.append(data)
                    except json.JSONDecodeError:
                        # Treat as plain text
                        seeds.append({"text": line, "type": "plain"})

        # Limit seed size
        if len(seeds) > self.config.max_seed_size:
            self.logger.warning(f"Limiting seeds from {len(seeds)} to {self.config.max_seed_size}")
            seeds = seeds[:self.config.max_seed_size]

        self.logger.info(f"Loaded {len(seeds)} seeds")
        return seeds

    def _prepare_seed_file(self, seeds: List[Dict[str, Any]], method: str) -> str:
        """Chuẩn bị file seed cho method cụ thể"""
        temp_file = Path(self.config.output_dir) / f"temp_seed_{method}.jsonl"
        temp_file.parent.mkdir(parents=True, exist_ok=True)

        with open(temp_file, 'w', encoding='utf-8') as f:
            for seed in seeds:
                # Extract text for augmentation
                text = seed.get('text', seed.get('message', str(seed)))
                f.write(json.dumps({"text": text, "original_seed": seed}, ensure_ascii=False) + '\n')

        return str(temp_file)

    async def _run_paraphrase(self, seeds: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Chạy paraphrase augmentation"""
        if 'paraphrase' not in self.augmentors:
            return {"error": "Paraphrase augmentor not available"}

        self.logger.info("Starting paraphrase augmentation...")
        start_time = datetime.now()

        # Prepare seed file
        seed_file = self._prepare_seed_file(seeds, "paraphrase")
        output_file = Path(self.config.output_dir) / "augmented_paraphrase.jsonl"

        try:
            stats = await self.augmentors['paraphrase'].augment_dataset(seed_file, str(output_file))
            stats['processing_time'] = (datetime.now() - start_time).total_seconds()
            stats['output_file'] = str(output_file)
            return stats
        except Exception as e:
            self.logger.error(f"Paraphrase augmentation failed: {e}")
            return {"error": str(e), "processing_time": (datetime.now() - start_time).total_seconds()}
        finally:
            # Clean up temp file
            Path(seed_file).unlink(missing_ok=True)

    async def _run_backtranslate(self, seeds: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Chạy backtranslate augmentation"""
        if 'backtranslate' not in self.augmentors:
            return {"error": "Backtranslate augmentor not available"}

        self.logger.info("Starting backtranslate augmentation...")
        start_time = datetime.now()

        # Prepare seed file
        seed_file = self._prepare_seed_file(seeds, "backtranslate")
        output_file = Path(self.config.output_dir) / "augmented_backtranslate.jsonl"

        try:
            stats = await self.augmentors['backtranslate'].augment_dataset(seed_file, str(output_file))
            stats['processing_time'] = (datetime.now() - start_time).total_seconds()
            stats['output_file'] = str(output_file)
            return stats
        except Exception as e:
            self.logger.error(f"Backtranslate augmentation failed: {e}")
            return {"error": str(e), "processing_time": (datetime.now() - start_time).total_seconds()}
        finally:
            # Clean up temp file
            Path(seed_file).unlink(missing_ok=True)

    async def _run_template_fill(self) -> Dict[str, Any]:
        """Chạy template fill augmentation"""
        if 'template_fill' not in self.augmentors:
            return {"error": "Template fill augmentor not available"}

        self.logger.info("Starting template fill augmentation...")
        start_time = datetime.now()

        output_file = Path(self.config.output_dir) / "augmented_template_fill.jsonl"

        try:
            stats = await self.augmentors['template_fill'].augment_from_templates(str(output_file))
            stats['processing_time'] = (datetime.now() - start_time).total_seconds()
            stats['output_file'] = str(output_file)
            return stats
        except Exception as e:
            self.logger.error(f"Template fill augmentation failed: {e}")
            return {"error": str(e), "processing_time": (datetime.now() - start_time).total_seconds()}

    async def run_augmentation(self) -> AugmentStats:
        """Chạy toàn bộ pipeline augmentation"""
        start_time = datetime.now()

        # Load seed data
        seeds = self._load_seed_data()

        # Run augmentation methods
        results = {}
        output_files = []

        # Run methods in parallel where possible
        tasks = []

        if self.config.use_paraphrase:
            tasks.append(('paraphrase', self._run_paraphrase(seeds)))

        if self.config.use_backtranslate:
            tasks.append(('backtranslate', self._run_backtranslate(seeds)))

        if self.config.use_template_fill:
            tasks.append(('template_fill', self._run_template_fill()))

        # Execute tasks
        if tasks:
            task_results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)

            for (method_name, _), result in zip(tasks, task_results):
                if isinstance(result, Exception):
                    results[method_name] = {"error": str(result)}
                else:
                    results[method_name] = result
                    if "output_file" in result:
                        output_files.append(result["output_file"])

        # Calculate overall statistics
        total_outputs = sum(
            result.get("total_outputs", 0)
            for result in results.values()
            if "error" not in result
        )

        success_rates = {}
        for method, result in results.items():
            if "error" not in result:
                success_rates[method] = result.get("success_rate", 0.0)
            else:
                success_rates[method] = 0.0

        processing_time = (datetime.now() - start_time).total_seconds()

        # Create combined output file
        combined_file = Path(self.config.output_dir) / "augmented_combined.jsonl"
        await self._create_combined_output(output_files, str(combined_file))
        output_files.append(str(combined_file))

        # Save metadata
        metadata_file = Path(self.config.output_dir) / "augmentation_metadata.json"
        metadata = {
            "config": asdict(self.config),
            "results": results,
            "timestamp": datetime.now().isoformat(),
            "total_processing_time": processing_time
        }

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        return AugmentStats(
            total_seeds=len(seeds),
            total_outputs=total_outputs,
            methods_used=list(self.augmentors.keys()),
            success_rates=success_rates,
            processing_time=processing_time,
            output_files=output_files,
            metadata=metadata
        )

    async def _create_combined_output(self, output_files: List[str], combined_file: str):
        """Tạo file output kết hợp từ tất cả methods"""
        combined_path = Path(combined_file)
        combined_path.parent.mkdir(parents=True, exist_ok=True)

        with open(combined_path, 'w', encoding='utf-8') as f:
            for output_file in output_files:
                if Path(output_file).exists():
                    with open(output_file, 'r', encoding='utf-8') as inf:
                        for line in inf:
                            line = line.strip()
                            if line:
                                f.write(line + '\n')

    def print_stats(self, stats: AugmentStats):
        """In thống kê augmentation"""
        print("\n" + "="*60)
        print("AUGMENTATION STATISTICS")
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
            print(f"  - {file_path}")
        print("="*60)

async def main():
    """Main function với CLI interface"""
    parser = argparse.ArgumentParser(description="Augment dataset using multiple methods")
    parser.add_argument("--seed-file", required=True, help="Path to seed file")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--methods", nargs="+",
                       choices=["paraphrase", "backtranslate", "template_fill"],
                       default=["paraphrase", "backtranslate", "template_fill"],
                       help="Augmentation methods to use")
    parser.add_argument("--max-seeds", type=int, default=1000, help="Maximum seeds to process")
    parser.add_argument("--paraphrase-variants", type=int, default=5, help="Number of paraphrase variants")
    parser.add_argument("--template-variants", type=int, default=10, help="Number of template variants")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create config
    config = AugmentConfig(
        seed_file=args.seed_file,
        output_dir=args.output_dir,
        use_paraphrase="paraphrase" in args.methods,
        use_backtranslate="backtranslate" in args.methods,
        use_template_fill="template_fill" in args.methods,
        max_seed_size=args.max_seeds,
        paraphrase_config=ParaphraseConfig(num_variants=args.paraphrase_variants),
        template_config=TemplateConfig(num_variants_per_template=args.template_variants)
    )

    # Run augmentation
    runner = AugmentRunner(config)
    stats = await runner.run_augmentation()

    # Print results
    runner.print_stats(stats)

if __name__ == "__main__":
    asyncio.run(main())
