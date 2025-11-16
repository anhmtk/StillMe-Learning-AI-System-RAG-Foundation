#!/bin/bash
# Run full evaluation with GPT-3.5-turbo (cost-effective alternative)
# Cost: ~$0.43 for 790 questions (27x cheaper than GPT-4)

echo "Running full evaluation with GPT-3.5-turbo..."
echo "Estimated cost: ~$0.43 for 790 questions (27x cheaper than GPT-4)"
echo ""

# Set GPT-3.5-turbo as model
export OPENAI_MODEL="gpt-3.5-turbo"

# Run full evaluation
python scripts/run_full_evaluation.py \
    --api-url https://stillme-backend-production.up.railway.app

echo ""
echo "Evaluation complete! Results saved to data/evaluation/results/"

