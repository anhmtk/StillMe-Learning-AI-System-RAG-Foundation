# Script to push current branch with Personal Access Token
# Usage: .\scripts\push_branch_with_token.ps1 [branch-name]
# If branch-name not provided, uses current branch

param(
    [string]$BranchName = ""
)

Write-Host "GitHub Push Branch with Personal Access Token" -ForegroundColor Cyan
Write-Host ""

# Get current branch if not provided
if ([string]::IsNullOrWhiteSpace($BranchName)) {
    $BranchName = git branch --show-current
    if ([string]::IsNullOrWhiteSpace($BranchName)) {
        Write-Host "Error: Could not determine current branch. Please specify branch name." -ForegroundColor Red
        exit 1
    }
}

Write-Host "Branch to push: $BranchName" -ForegroundColor Yellow
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

# Get current remote URL (without token)
$currentRemote = git remote get-url origin
if ($currentRemote -match "https://.*@github.com") {
    # Remove existing token if present
    $currentRemote = $currentRemote -replace "https://.*@", "https://"
}

# Set URL with token (temporary)
git remote set-url origin "https://$plainToken@github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation.git"

Write-Host "Token set. Pushing branch '$BranchName'..." -ForegroundColor Green
Write-Host ""

# Push branch (with upstream tracking)
git push -u origin $BranchName

$pushExitCode = $LASTEXITCODE

# Remove token from URL (security)
Write-Host ""
Write-Host "Removing token from URL..." -ForegroundColor Yellow
git remote set-url origin "https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation.git"

Write-Host "Token removed from URL." -ForegroundColor Green
Write-Host ""

if ($pushExitCode -eq 0) {
    Write-Host "Push successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Go to GitHub and create Pull Request" -ForegroundColor Gray
    Write-Host "2. Base: main, Compare: $BranchName" -ForegroundColor Gray
    Write-Host "3. Reference issue #56 in PR description" -ForegroundColor Gray
} else {
    Write-Host "Push failed. Check error message above." -ForegroundColor Red
    Write-Host ""
    Write-Host "Tips:" -ForegroundColor Yellow
    Write-Host "  - Verify token has repo permission" -ForegroundColor Gray
    Write-Host "  - Check token not expired" -ForegroundColor Gray
    Write-Host "  - Verify you have push permission to repo" -ForegroundColor Gray
    Write-Host "  - Check branch name is correct: $BranchName" -ForegroundColor Gray
}

# Clear token from memory
$plainToken = $null
$token = $null

