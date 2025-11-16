#!/usr/bin/env python3
"""
Download HaluEval dataset from HuggingFace using datasets library
"""

import json
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_halu_eval_from_hf(output_path: str = "data/benchmarks/halu_eval.json"):
    """
    Download HaluEval from HuggingFace using datasets library
    
    Args:
        output_path: Path to save dataset
    """
    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("datasets library not installed. Installing...")
        import subprocess
        subprocess.check_call(["pip", "install", "datasets"])
        from datasets import load_dataset
    
    logger.info("Downloading HaluEval from HuggingFace...")
    
    try:
        # Try to load HaluEval dataset from HuggingFace
        # HaluEval might be available under different names
        dataset_names = [
            "RUCAIBox/HaluEval",
            "halu_eval",
            "halueval"
        ]
        
        dataset = None
        for name in dataset_names:
            try:
                logger.info(f"Trying dataset name: {name}")
                dataset = load_dataset(name, trust_remote_code=True)
                logger.info(f"Successfully loaded dataset: {name}")
                break
            except Exception as e:
                logger.warning(f"Failed to load {name}: {e}")
                continue
        
        if dataset is None:
            raise Exception("Could not load HaluEval from any known source")
        
        # Convert to our format
        questions = []
        
        # Handle different dataset structures
        if isinstance(dataset, dict):
            # Multiple splits
            for split_name, split_data in dataset.items():
                logger.info(f"Processing split: {split_name} ({len(split_data)} examples)")
                for item in split_data:
                    # Handle different field names
                    question = item.get("question", item.get("Question", "")).strip()
                    answer = item.get("answer", item.get("Answer", item.get("response", ""))).strip()
                    is_hallucination = item.get("is_hallucination", item.get("label", False))
                    context = item.get("context", item.get("Context", "")).strip()
                    
                    if question:
                        questions.append({
                            "question": question,
                            "answer": answer,
                            "is_hallucination": bool(is_hallucination),
                            "context": context
                        })
        else:
            # Single dataset
            for item in dataset:
                question = item.get("question", item.get("Question", "")).strip()
                answer = item.get("answer", item.get("Answer", item.get("response", ""))).strip()
                is_hallucination = item.get("is_hallucination", item.get("label", False))
                context = item.get("context", item.get("Context", "")).strip()
                
                if question:
                    questions.append({
                        "question": question,
                        "answer": answer,
                        "is_hallucination": bool(is_hallucination),
                        "context": context
                    })
        
        # Save to JSON
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({"questions": questions}, f, indent=2, ensure_ascii=False)
        
        logger.info(f"[OK] HaluEval dataset downloaded: {len(questions)} questions")
        logger.info(f"   Saved to: {output_path}")
        
        return questions
        
    except Exception as e:
        logger.error(f"[FAIL] Error downloading HaluEval from HuggingFace: {e}")
        logger.info("You may need to:")
        logger.info("  1. Install datasets: pip install datasets")
        logger.info("  2. Or download manually from: https://github.com/RUCAIBox/HaluEval")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Download HaluEval from HuggingFace")
    parser.add_argument(
        "--output",
        type=str,
        default="data/benchmarks/halu_eval.json",
        help="Output path for dataset"
    )
    
    args = parser.parse_args()
    
    try:
        download_halu_eval_from_hf(args.output)
    except Exception as e:
        logger.error(f"Failed to download HaluEval: {e}")
        exit(1)

