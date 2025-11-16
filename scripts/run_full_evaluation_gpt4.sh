#!/bin/bash
# Run full evaluation with GPT-4 (default, best baseline comparison)
# Cost: ~$11.85 for 790 questions

echo "Running full evaluation with GPT-4..."
echo "Estimated cost: ~$11.85 for 790 questions"
echo ""

# Set GPT-4 as model
export OPENAI_MODEL="gpt-4"

# Run full evaluation
python scripts/run_full_evaluation.py \
    --api-url https://stillme-backend-production.up.railway.app

echo ""
echo "Evaluation complete! Results saved to data/evaluation/results/"

