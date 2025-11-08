# Script to commit, push, and create PR automatically
# Usage: .\scripts\commit_and_pr.ps1 "commit message" [branch-name]
# If branch-name not provided, uses current branch

param(
    [Parameter(Mandatory=$true)]
    [string]$CommitMessage,
    [string]$BranchName = ""
)

Write-Host "GitHub Commit, Push & Create PR" -ForegroundColor Cyan
Write-Host ""

# Check if there are changes to commit
$status = git status --short
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "⚠️ No changes to commit. Working directory is clean." -ForegroundColor Yellow
    Write-Host "Skipping commit step..." -ForegroundColor Gray
    $skipCommit = $true
} else {
    Write-Host "Changes detected:" -ForegroundColor Yellow
    git status --short
    Write-Host ""
    $skipCommit = $false
}

# Get current branch if not provided
if ([string]::IsNullOrWhiteSpace($BranchName)) {
    $BranchName = git branch --show-current
    if ([string]::IsNullOrWhiteSpace($BranchName)) {
        Write-Host "Error: Could not determine current branch. Please specify branch name." -ForegroundColor Red
        exit 1
    }
}

Write-Host "Branch: $BranchName" -ForegroundColor Yellow
Write-Host "Commit message: $CommitMessage" -ForegroundColor Yellow
Write-Host ""

# Stage all changes (if not skipping commit)
if (-not $skipCommit) {
    Write-Host "Staging all changes..." -ForegroundColor Yellow
    git add .
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to stage changes. Exiting..." -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Changes staged" -ForegroundColor Green
    Write-Host ""
    
    # Commit
    Write-Host "Committing changes..." -ForegroundColor Yellow
    git commit -m $CommitMessage
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to commit. Exiting..." -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Committed successfully" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "Skipping commit (no changes)" -ForegroundColor Gray
    Write-Host ""
}

# Now call push_and_create_pr.ps1
Write-Host "Calling push_and_create_pr.ps1..." -ForegroundColor Cyan
Write-Host ""

# Get the directory of this script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pushScript = Join-Path $scriptDir "push_and_create_pr.ps1"

# Call push_and_create_pr with the commit message as PR title
& $pushScript -BranchName $BranchName -PRTitle $CommitMessage

