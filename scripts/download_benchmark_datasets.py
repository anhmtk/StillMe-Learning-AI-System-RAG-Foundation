#!/usr/bin/env python3
"""
Download benchmark datasets for StillMe evaluation

Downloads TruthfulQA and HaluEval datasets
"""

import os
import json
import requests
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_truthfulqa(output_path: str = "data/benchmarks/truthfulqa.json"):
    """
    Download TruthfulQA dataset
    
    Args:
        output_path: Path to save dataset
    """
    logger.info("Downloading TruthfulQA dataset...")
    
    # TruthfulQA dataset URL (HuggingFace)
    # Note: This is a simplified version - full dataset may require HuggingFace library
    url = "https://raw.githubusercontent.com/sylinrl/TruthfulQA/main/TruthfulQA.csv"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Parse CSV and convert to JSON format
        import csv
        from io import StringIO
        
        csv_data = StringIO(response.text)
        reader = csv.DictReader(csv_data)
        
        questions = []
        for row in reader:
            question = row.get("Question", "").strip()
            correct_answers = row.get("Best Answer", "").strip()
            incorrect_answers = row.get("Incorrect Answers", "").strip().split(";")
            
            if question and correct_answers:
                questions.append({
                    "question": question,
                    "correct_answer": correct_answers,
                    "incorrect_answers": [ans.strip() for ans in incorrect_answers if ans.strip()]
                })
        
        # Save to JSON
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({"questions": questions}, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ TruthfulQA dataset downloaded: {len(questions)} questions")
        logger.info(f"   Saved to: {output_path}")
        
        return questions
        
    except Exception as e:
        logger.error(f"❌ Error downloading TruthfulQA: {e}")
        logger.info("Creating sample dataset for testing...")
        
        # Create sample dataset
        sample_questions = [
            {
                "question": "What is the capital of France?",
                "correct_answer": "Paris",
                "incorrect_answers": ["London", "Berlin", "Madrid"]
            },
            {
                "question": "What is 2+2?",
                "correct_answer": "4",
                "incorrect_answers": ["5", "3", "6"]
            },
            {
                "question": "What is the largest planet in our solar system?",
                "correct_answer": "Jupiter",
                "incorrect_answers": ["Saturn", "Earth", "Mars"]
            }
        ]
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({"questions": sample_questions}, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Sample TruthfulQA dataset created: {len(sample_questions)} questions")
        return sample_questions


def download_halu_eval(output_path: str = "data/benchmarks/halu_eval.json"):
    """
    Download HaluEval dataset
    
    Args:
        output_path: Path to save dataset
    """
    logger.info("Downloading HaluEval dataset...")
    
    # Try multiple sources for HaluEval dataset
    urls = [
        "https://raw.githubusercontent.com/RUCAIBox/HaluEval/main/data/halu_data_v2.json",
        "https://huggingface.co/datasets/RUCAIBox/HaluEval/resolve/main/data/halu_data_v2.json",
        "https://raw.githubusercontent.com/RUCAIBox/HaluEval/master/data/halu_data_v2.json"
    ]
    
    response = None
    for url in urls:
        try:
            logger.info(f"Trying URL: {url}")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            break
        except Exception as e:
            logger.warning(f"Failed to download from {url}: {e}")
            continue
    
    if response is None:
        raise Exception("All download URLs failed")
    
    try:
        
        data = response.json()
        
        # Convert to our format
        questions = []
        for item in data.get("data", []):
            question = item.get("question", "").strip()
            answer = item.get("answer", "").strip()
            is_hallucination = item.get("is_hallucination", False)
            context = item.get("context", "").strip()
            
            if question:
                questions.append({
                    "question": question,
                    "answer": answer,
                    "is_hallucination": is_hallucination,
                    "context": context
                })
        
        # Save to JSON
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({"questions": questions}, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ HaluEval dataset downloaded: {len(questions)} questions")
        logger.info(f"   Saved to: {output_path}")
        
        return questions
        
    except Exception as e:
        logger.error(f"❌ Error downloading HaluEval: {e}")
        logger.info("Creating sample dataset for testing...")
        
        # Create sample dataset
        sample_questions = [
            {
                "question": "What is the population of a fictional city?",
                "answer": "The population is 10 million",
                "is_hallucination": True,
                "context": "No context available"
            },
            {
                "question": "What is the capital of France?",
                "answer": "Paris",
                "is_hallucination": False,
                "context": "Paris is the capital of France"
            },
            {
                "question": "What is the speed of light in a vacuum?",
                "answer": "299,792,458 meters per second",
                "is_hallucination": False,
                "context": "The speed of light in vacuum is 299,792,458 m/s"
            }
        ]
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({"questions": sample_questions}, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Sample HaluEval dataset created: {len(sample_questions)} questions")
        return sample_questions


def main():
    """Main download script"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download benchmark datasets")
    parser.add_argument(
        "--datasets",
        nargs="+",
        choices=["truthfulqa", "halu_eval", "all"],
        default=["all"],
        help="Datasets to download"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/benchmarks",
        help="Output directory for datasets"
    )
    
    args = parser.parse_args()
    
    datasets_to_download = args.datasets
    if "all" in datasets_to_download:
        datasets_to_download = ["truthfulqa", "halu_eval"]
    
    logger.info("=" * 60)
    logger.info("Downloading Benchmark Datasets")
    logger.info("=" * 60)
    
    if "truthfulqa" in datasets_to_download:
        download_truthfulqa(os.path.join(args.output_dir, "truthfulqa.json"))
    
    if "halu_eval" in datasets_to_download:
        download_halu_eval(os.path.join(args.output_dir, "halu_eval.json"))
    
    logger.info("=" * 60)
    logger.info("Download Complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

