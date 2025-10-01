#!/usr/bin/env python3
"""
Generate Shadow Evaluation Report
"""
import sys
import os
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from stillme_core.middleware.observability import ObservabilityManager

def main():
    parser = argparse.ArgumentParser(description="Generate Reflex Engine Shadow Evaluation Report")
    parser.add_argument("--hours", type=int, default=24, help="Evaluation window in hours (default: 24)")
    parser.add_argument("--output", type=str, default="docs/REFLEX_SHADOW_EVAL.md", help="Output file path")
    parser.add_argument("--config", type=str, help="Config file path (optional)")

    args = parser.parse_args()

    # Load config if provided
    config = {}
    if args.config and os.path.exists(args.config):
        import yaml
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)

    # Initialize observability manager
    obs_manager = ObservabilityManager(config)

    # Generate report
    report = obs_manager.generate_shadow_report(args.hours)

    # Write to file
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"Shadow evaluation report generated: {output_path}")
    print(f"Evaluation window: {args.hours} hours")

    # Print summary to console
    evaluation = obs_manager.get_shadow_evaluation(args.hours)
    if evaluation["evaluation_ready"]:
        performance = evaluation["performance"]
        print(f"\nSummary:")
        print(f"  Precision: {performance['precision']:.3f}")
        print(f"  Recall: {performance['recall']:.3f}")
        print(f"  F1 Score: {performance['f1_score']:.3f}")
        print(f"  FP Rate: {performance['fp_rate']:.3f}")
        print(f"  P95 Processing Time: {performance['p95_processing_time_ms']:.2f} ms")
        print(f"  Ready for Production: {'Yes' if evaluation['ready_for_production'] else 'No'}")
    else:
        print(f"\nInsufficient data for evaluation: {evaluation['sample_count']} samples")

if __name__ == "__main__":
    main()
