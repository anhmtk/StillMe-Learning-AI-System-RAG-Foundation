#!/usr/bin/env python3
"""
Generate Large Dataset - Tạo dataset 1000+ mẫu cho testing

Tính năng:
- Generate 1000+ test cases
- Sử dụng DatasetScaler
- Tạo dataset đa dạng cho testing
- Export cho real testing
"""

import json
import logging
from pathlib import Path
import sys

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from scale_dataset import DatasetScaler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main function để generate large dataset"""
    try:
        logger.info("🚀 Starting Large Dataset Generation...")

        # Create scaler
        scaler = DatasetScaler()

        # Generate large dataset
        logger.info("📊 Generating 1000+ test cases...")
        dataset = scaler.generate_large_dataset(1000)

        # Save dataset
        file_path = scaler.save_dataset(dataset, "large_dataset_1000.json")

        # Generate statistics
        stats = scaler.generate_statistics(dataset)

        # Save statistics
        stats_file = scaler.output_dir / "dataset_statistics.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        # Print results
        print("\n" + "="*80)
        print("🎉 LARGE DATASET GENERATION COMPLETED")
        print("="*80)
        print(f"📊 Total Cases Generated: {len(dataset)}")
        print(f"💾 Dataset File: {file_path}")
        print(f"📈 Statistics File: {stats_file}")
        print("\n📊 Dataset Statistics:")
        print(f"   • Categories: {len(stats['category_distribution'])}")
        print(f"   • Languages: {list(stats['language_distribution'].keys())}")
        print(f"   • Difficulties: {list(stats['difficulty_distribution'].keys())}")
        print(f"   • Scenarios: {list(stats['scenario_distribution'].keys())}")

        print("\n🎯 Ready for:")
        print("   • Real StillMe AI testing")
        print("   • Comprehensive evaluation")
        print("   • Performance benchmarking")
        print("   • CI/CD integration")
        print("="*80)

        return True

    except Exception as e:
        logger.error(f"❌ Large dataset generation failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Large dataset generation completed successfully!")
    else:
        print("\n❌ Large dataset generation failed!")
