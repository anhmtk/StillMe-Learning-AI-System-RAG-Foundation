# Script to push directly to main branch using Personal Access Token
# Usage: .\scripts\push_main_with_token.ps1

Write-Host "GitHub Push to Main Branch" -ForegroundColor Cyan
Write-Host ""

# Check current branch
$currentBranch = git branch --show-current
if ($currentBranch -ne "main") {
    Write-Host "⚠️ Warning: You are not on 'main' branch. Current branch: $currentBranch" -ForegroundColor Yellow
    $confirm = Read-Host "Do you want to continue? (y/n)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Host "Aborted." -ForegroundColor Red
        exit 1
    }
}

Write-Host "Branch to push: $currentBranch" -ForegroundColor Yellow
Write-Host "Target: origin/main" -ForegroundColor Yellow
Write-Host ""

# Prompt for token
Write-Host "Please paste your Personal Access Token:" -ForegroundColor Yellow
Write-Host "(Create token at: https://github.com/settings/tokens)" -ForegroundColor Gray
Write-Host "Token needs 'repo' scope for push" -ForegroundColor Gray
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

Write-Host "Token set. Pushing to 'origin/$currentBranch'..." -ForegroundColor Green
Write-Host ""

# Check if branch needs pull first
Write-Host "Checking remote status..." -ForegroundColor Yellow
git fetch origin $currentBranch 2>&1 | Out-Null

$localCommit = git rev-parse HEAD
$remoteCommit = git rev-parse "origin/$currentBranch" 2>$null

if ($remoteCommit -and $localCommit -ne $remoteCommit) {
    # Check if local is ahead (can fast-forward) or if remote has new commits
    $mergeBase = git merge-base HEAD "origin/$currentBranch" 2>$null
    $localAhead = git rev-list --count "$mergeBase..HEAD" 2>$null
    $remoteAhead = git rev-list --count "$mergeBase..origin/$currentBranch" 2>$null
    
    if ($remoteAhead -gt 0) {
        Write-Host "⚠️ Remote branch has new commits. Pulling and merging..." -ForegroundColor Yellow
        git pull origin $currentBranch --no-edit 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Pull failed. Please resolve conflicts manually." -ForegroundColor Red
            Write-Host "   You can try: git pull --rebase origin $currentBranch" -ForegroundColor Yellow
            git remote set-url origin "https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation.git"
            exit 1
        }
        Write-Host "✅ Pull and merge successful" -ForegroundColor Green
    } else {
        Write-Host "✅ Local branch is ahead, no need to pull" -ForegroundColor Green
    }
} else {
    Write-Host "✅ Local and remote are in sync (or local is ahead)" -ForegroundColor Green
}

# Push branch
Write-Host "Pushing to origin/$currentBranch..." -ForegroundColor Green
git push origin $currentBranch

$pushExitCode = $LASTEXITCODE

# Remove token from URL (security)
Write-Host ""
Write-Host "Removing token from URL..." -ForegroundColor Yellow
git remote set-url origin "https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation.git"

Write-Host "Token removed from URL." -ForegroundColor Green
Write-Host ""

if ($pushExitCode -eq 0) {
    Write-Host "✅ Push successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Railway will automatically deploy from main branch" -ForegroundColor Cyan
} else {
    Write-Host "❌ Push failed. Check error message above." -ForegroundColor Red
    Write-Host ""
    Write-Host "Tips:" -ForegroundColor Yellow
    Write-Host "  - Verify token has repo permission" -ForegroundColor Gray
    Write-Host "  - Check token not expired" -ForegroundColor Gray
    Write-Host "  - Verify you have push permission to repo" -ForegroundColor Gray
    Write-Host "  - Check branch name is correct: $currentBranch" -ForegroundColor Gray
}

# Clear token from memory
$plainToken = $null
$token = $null

