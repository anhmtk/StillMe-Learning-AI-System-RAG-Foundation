# PowerShell script to run comparison with environment variables set directly
# This bypasses .env file loading issues

Write-Host "==================================================================================" -ForegroundColor Cyan
Write-Host "StillMe Evaluation - System Comparison" -ForegroundColor Cyan
Write-Host "==================================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if API keys are set
$openaiKey = $env:OPENAI_API_KEY
$deepseekKey = $env:DEEPSEEK_API_KEY
$openrouterKey = $env:OPENROUTER_API_KEY

Write-Host "Checking API keys..." -ForegroundColor Yellow
Write-Host ""

if ($openaiKey) {
    $masked = $openaiKey.Substring(0, [Math]::Min(15, $openaiKey.Length)) + "..." + $openaiKey.Substring([Math]::Max(0, $openaiKey.Length - 4))
    Write-Host "✅ OPENAI_API_KEY: $masked" -ForegroundColor Green
} else {
    Write-Host "⚠️  OPENAI_API_KEY not set" -ForegroundColor Yellow
    Write-Host "   Set it with: `$env:OPENAI_API_KEY='sk-proj-...'" -ForegroundColor Gray
}

if ($deepseekKey) {
    $masked = $deepseekKey.Substring(0, [Math]::Min(15, $deepseekKey.Length)) + "..." + $deepseekKey.Substring([Math]::Max(0, $deepseekKey.Length - 4))
    Write-Host "✅ DEEPSEEK_API_KEY: $masked" -ForegroundColor Green
} else {
    Write-Host "⚠️  DEEPSEEK_API_KEY not set" -ForegroundColor Yellow
}

if ($openrouterKey) {
    $masked = $openrouterKey.Substring(0, [Math]::Min(15, $openrouterKey.Length)) + "..." + $openrouterKey.Substring([Math]::Max(0, $openrouterKey.Length - 4))
    Write-Host "✅ OPENROUTER_API_KEY: $masked" -ForegroundColor Green
} else {
    Write-Host "⚠️  OPENROUTER_API_KEY not set" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Running comparison..." -ForegroundColor Cyan
Write-Host ""

# Run the comparison script
python scripts/run_comparison_only.py --api-url https://stillme-backend-production.up.railway.app --num-questions 50

Write-Host ""
Write-Host "==================================================================================" -ForegroundColor Cyan
Write-Host "Done!" -ForegroundColor Cyan
Write-Host "==================================================================================" -ForegroundColor Cyan

