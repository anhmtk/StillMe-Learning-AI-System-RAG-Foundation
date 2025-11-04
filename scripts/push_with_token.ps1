# Script to push with Personal Access Token
# Usage: .\scripts\push_with_token.ps1

Write-Host "GitHub Push with Personal Access Token" -ForegroundColor Cyan
Write-Host ""

# Prompt for token
Write-Host "Please paste your Personal Access Token:" -ForegroundColor Yellow
Write-Host "(Create token at: https://github.com/settings/tokens)" -ForegroundColor Gray
Write-Host ""

$token = Read-Host "Personal Access Token" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($token)
$plainToken = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

if ([string]::IsNullOrWhiteSpace($plainToken)) {
    Write-Host "Error: No token provided. Exiting..." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Setting token in remote URL..." -ForegroundColor Yellow

# Set URL with token (temporary)
git remote set-url origin "https://$plainToken@github.com/anhmtk/StillMe---Self-Evolving-AI-System.git"

Write-Host "Token set. Pushing..." -ForegroundColor Green
Write-Host ""

# Push
git push origin main

$pushExitCode = $LASTEXITCODE

# Remove token from URL (security)
Write-Host ""
Write-Host "Removing token from URL..." -ForegroundColor Yellow
git remote set-url origin "https://github.com/anhmtk/StillMe---Self-Evolving-AI-System.git"

Write-Host "Token removed from URL." -ForegroundColor Green
Write-Host ""

if ($pushExitCode -eq 0) {
    Write-Host "Push successful!" -ForegroundColor Green
} else {
    Write-Host "Push failed. Check error message above." -ForegroundColor Red
    Write-Host ""
    Write-Host "Tips:" -ForegroundColor Yellow
    Write-Host "  - Verify token has repo permission" -ForegroundColor Gray
    Write-Host "  - Check token not expired" -ForegroundColor Gray
    Write-Host "  - Verify you have push permission to repo" -ForegroundColor Gray
}

# Clear token from memory
$plainToken = $null
$token = $null

