# Script to verify GitHub CLI permissions
# Ensures limited permissions are set correctly

Write-Host "🔍 Verifying GitHub CLI Setup..." -ForegroundColor Cyan
Write-Host ""

# Check if gh is installed
Write-Host "1. Checking GitHub CLI installation..." -ForegroundColor Yellow
try {
    $version = gh --version
    Write-Host "   ✅ GitHub CLI installed: $($version -split "`n" | Select-Object -First 1)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ GitHub CLI not found. Please install first." -ForegroundColor Red
    exit 1
}

# Check authentication
Write-Host "`n2. Checking authentication status..." -ForegroundColor Yellow
try {
    $authStatus = gh auth status 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Authenticated with GitHub" -ForegroundColor Green
        Write-Host "   $($authStatus -join "`n   ")" -ForegroundColor Gray
    } else {
        Write-Host "   ❌ Not authenticated. Run: gh auth login" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   ❌ Authentication check failed" -ForegroundColor Red
    exit 1
}

# Test read permissions (Issues)
Write-Host "`n3. Testing READ permissions (Issues)..." -ForegroundColor Yellow
try {
    $issues = gh issue list --repo anhmtk/StillMe---Self-Evolving-AI-System --limit 1 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Can read issues" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Cannot read issues. Check permissions." -ForegroundColor Red
        Write-Host "   Error: $issues" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ⚠️  Could not test read permissions" -ForegroundColor Yellow
}

# Test write permissions (Create test issue)
Write-Host "`n4. Testing WRITE permissions (Issues)..." -ForegroundColor Yellow
Write-Host "   ⚠️  Skipping - would create actual issue. Manual test required:" -ForegroundColor Yellow
Write-Host "   → Run: gh issue create --repo anhmtk/StillMe---Self-Evolving-AI-System --title '[TEST]' --body 'Test'" -ForegroundColor Gray

# Test merge permissions (should fail)
Write-Host "`n5. Testing MERGE permissions (should FAIL)..." -ForegroundColor Yellow
Write-Host "   ℹ️  Note: If you can merge PRs, permissions are too broad!" -ForegroundColor Yellow
Write-Host "   → Run: gh pr merge 999999 --squash (should fail)" -ForegroundColor Gray

# Summary
Write-Host "`n" -ForegroundColor Cyan
Write-Host "📋 Permission Summary:" -ForegroundColor Cyan
Write-Host "   ✅ Should have: Issues (Read/Write), Discussions (Read/Write)" -ForegroundColor Green
Write-Host "   ✅ Should have: PRs (Read only), Contents (Read only)" -ForegroundColor Green
Write-Host "   ❌ Should NOT have: PRs (Write/Merge), Administration, Secrets" -ForegroundColor Red
Write-Host "`n" -ForegroundColor Cyan
Write-Host "✅ Setup verification complete!" -ForegroundColor Green

