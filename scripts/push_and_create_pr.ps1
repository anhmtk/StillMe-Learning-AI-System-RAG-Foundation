# Script to push branch and create Pull Request automatically
# Usage: .\scripts\push_and_create_pr.ps1 [branch-name] [title] [body]
# If branch-name not provided, uses current branch

param(
    [string]$BranchName = "",
    [string]$PRTitle = "",
    [string]$PRBody = ""
)

Write-Host "GitHub Push & Create PR" -ForegroundColor Cyan
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
Write-Host "Target: main" -ForegroundColor Yellow
Write-Host ""

# Prompt for token
Write-Host "Please paste your Personal Access Token:" -ForegroundColor Yellow
Write-Host "(Create token at: https://github.com/settings/tokens)" -ForegroundColor Gray
Write-Host "Token needs 'repo' scope for push and PR creation" -ForegroundColor Gray
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

# Check if branch needs pull first
Write-Host "Checking remote status..." -ForegroundColor Yellow
git fetch origin $BranchName 2>&1 | Out-Null

$localCommit = git rev-parse HEAD
$remoteCommit = git rev-parse "origin/$BranchName" 2>$null

if ($remoteCommit -and $localCommit -ne $remoteCommit) {
    Write-Host "⚠️ Remote branch has new commits. Pulling and merging..." -ForegroundColor Yellow
    git pull origin $BranchName --no-edit 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Pull failed. Please resolve conflicts manually." -ForegroundColor Red
        git remote set-url origin "https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation.git"
        exit 1
    }
    Write-Host "✅ Pull and merge successful" -ForegroundColor Green
}

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
    Write-Host "✅ Push successful!" -ForegroundColor Green
    Write-Host ""
    
    # Create PR using GitHub API
    Write-Host "Creating Pull Request..." -ForegroundColor Cyan
    
    # Default PR title if not provided
    if ([string]::IsNullOrWhiteSpace($PRTitle)) {
        $lastCommitMsg = git log -1 --pretty=%B
        $PRTitle = $lastCommitMsg.Split("`n")[0]
        if ($PRTitle.Length -gt 72) {
            $PRTitle = $PRTitle.Substring(0, 69) + "..."
        }
    }
    
    # Default PR body if not provided
    if ([string]::IsNullOrWhiteSpace($PRBody)) {
        $lastCommitMsg = git log -1 --pretty=%B
        $PRBody = "## Changes`n`n$lastCommitMsg`n`n## Related`n- Auto-generated PR from branch $BranchName"
    }
    
    # Create PR using GitHub REST API
    $headers = @{
        "Authorization" = "token $plainToken"
        "Accept" = "application/vnd.github.v3+json"
    }
    
    $body = @{
        title = $PRTitle
        body = $PRBody
        head = $BranchName
        base = "main"
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "https://api.github.com/repos/anhmtk/StillMe-Learning-AI-System-RAG-Foundation/pulls" -Method Post -Headers $headers -Body $body -ContentType "application/json"
        
        Write-Host "✅ Pull Request created successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "PR #$($response.number): $($response.title)" -ForegroundColor Cyan
        Write-Host "URL: $($response.html_url)" -ForegroundColor Green
        Write-Host ""
        Write-Host "GitHub Actions will now run automatically on this PR" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Push successful, but PR creation failed:" -ForegroundColor Yellow
        Write-Host $_.Exception.Message -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            $errorJson = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
            if ($errorJson.errors) {
                Write-Host "Errors:" -ForegroundColor Red
                $errorJson.errors | ForEach-Object { Write-Host "  - $($_.message)" -ForegroundColor Red }
            }
        }
        Write-Host ""
        Write-Host "You can create PR manually:" -ForegroundColor Yellow
        Write-Host "https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation/compare/main...$BranchName?expand=1" -ForegroundColor Green
    }
} else {
    Write-Host "❌ Push failed. Check error message above." -ForegroundColor Red
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

