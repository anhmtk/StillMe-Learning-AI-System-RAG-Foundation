# Script to push current branch with force-with-lease using Personal Access Token
# Usage: .\scripts\push_force_with_token.ps1 [branch-name]
# If branch-name not provided, uses current branch
# 
# --force-with-lease is safer than --force: it only pushes if remote hasn't changed

param(
    [string]$BranchName = ""
)

Write-Host "GitHub Force Push (with lease) using Personal Access Token" -ForegroundColor Cyan
Write-Host "⚠️  Using --force-with-lease (safer than --force)" -ForegroundColor Yellow
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

# Set URL with token (temporary)
git remote set-url origin "https://$plainToken@github.com/anhmtk/StillMe---Self-Evolving-AI-System.git"

Write-Host "Token set. Force pushing branch '$BranchName' with --force-with-lease..." -ForegroundColor Green
Write-Host ""

# Push branch with force-with-lease (safer than --force)
git push --force-with-lease origin $BranchName

$pushExitCode = $LASTEXITCODE

# Remove token from URL (security)
Write-Host ""
Write-Host "Removing token from URL..." -ForegroundColor Yellow
git remote set-url origin "https://github.com/anhmtk/StillMe---Self-Evolving-AI-System.git"

Write-Host "Token removed from URL." -ForegroundColor Green
Write-Host ""

if ($pushExitCode -eq 0) {
    Write-Host "✅ Force push successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Verify branch on GitHub: origin/$BranchName" -ForegroundColor Gray
    Write-Host "2. Create/Update Pull Request if needed" -ForegroundColor Gray
} else {
    Write-Host "❌ Force push failed. Check error message above." -ForegroundColor Red
    Write-Host ""
    Write-Host "Possible reasons:" -ForegroundColor Yellow
    Write-Host "  - Remote branch has new commits (--force-with-lease protects against this)" -ForegroundColor Gray
    Write-Host "  - Token expired or invalid" -ForegroundColor Gray
    Write-Host "  - No push permission to repo" -ForegroundColor Gray
    Write-Host "  - Branch name incorrect: $BranchName" -ForegroundColor Gray
    Write-Host ""
    Write-Host "If remote has new commits, you may need to:" -ForegroundColor Yellow
    Write-Host "  1. Fetch latest: git fetch origin" -ForegroundColor Gray
    Write-Host "  2. Review changes: git log HEAD..origin/$BranchName" -ForegroundColor Gray
    Write-Host "  3. Rebase if needed: git rebase origin/$BranchName" -ForegroundColor Gray
}

# Clear token from memory
$plainToken = $null
$token = $null

