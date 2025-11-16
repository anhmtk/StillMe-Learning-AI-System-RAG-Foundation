# Run full evaluation with both GPT-4 and GPT-3.5-turbo for comparison
# Total cost: ~$12.28 for 790 questions (GPT-4: $11.85 + GPT-3.5: $0.43)

Write-Host "Running full evaluation with BOTH GPT-4 and GPT-3.5-turbo..." -ForegroundColor Cyan
Write-Host "Total estimated cost: ~`$12.28 for 790 questions" -ForegroundColor Yellow
Write-Host ""

# Step 1: Run with GPT-4
Write-Host "Step 1/2: Running with GPT-4 (best baseline comparison)..." -ForegroundColor Green
Write-Host "Estimated cost: ~`$11.85" -ForegroundColor Yellow
$env:OPENAI_MODEL = "gpt-4"
# Resume from question 157 if previous run failed
if ($env:RESUME_FROM_QUESTION) {
    Write-Host "Resuming from question $env:RESUME_FROM_QUESTION..." -ForegroundColor Yellow
}
python scripts/run_full_evaluation.py --api-url https://stillme-backend-production.up.railway.app

Write-Host ""
Write-Host "GPT-4 evaluation complete!" -ForegroundColor Green
Write-Host ""

# Step 2: Run with GPT-3.5-turbo
Write-Host "Step 2/2: Running with GPT-3.5-turbo (cost-effective alternative)..." -ForegroundColor Green
Write-Host "Estimated cost: ~`$0.43" -ForegroundColor Yellow
$env:OPENAI_MODEL = "gpt-3.5-turbo"
python scripts/run_full_evaluation.py --api-url https://stillme-backend-production.up.railway.app

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Both evaluations complete!" -ForegroundColor Green
Write-Host "Results saved to data/evaluation/results/" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

