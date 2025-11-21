# Script to install pandoc on Windows
# Usage: .\scripts\install_pandoc.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Install Pandoc for Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Method 1: Try winget (Windows 10/11)
Write-Host "Method 1: Trying winget..." -ForegroundColor Cyan
$wingetPath = Get-Command winget -ErrorAction SilentlyContinue
if ($wingetPath) {
    Write-Host "[OK] winget found" -ForegroundColor Green
    Write-Host "Installing pandoc using winget..." -ForegroundColor Yellow
    winget install --id JohnMacFarlane.Pandoc --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[SUCCESS] Pandoc installed using winget!" -ForegroundColor Green
        Write-Host "Please restart your PowerShell session or run: refreshenv" -ForegroundColor Yellow
        exit 0
    } else {
        Write-Host "[WARNING] winget installation failed" -ForegroundColor Yellow
    }
} else {
    Write-Host "[SKIP] winget not found" -ForegroundColor Yellow
}

Write-Host ""

# Method 2: Manual download instructions
Write-Host "Method 2: Manual Installation" -ForegroundColor Cyan
Write-Host ""
Write-Host "Please download and install pandoc manually:" -ForegroundColor Yellow
Write-Host "1. Visit: https://github.com/jgm/pandoc/releases/latest" -ForegroundColor White
Write-Host "2. Download: pandoc-X.X.X-windows-x86_64.msi" -ForegroundColor White
Write-Host "3. Run the installer" -ForegroundColor White
Write-Host "4. Restart PowerShell after installation" -ForegroundColor White
Write-Host ""
Write-Host "Or use direct download link:" -ForegroundColor Yellow
Write-Host "https://github.com/jgm/pandoc/releases/download/3.7.1/pandoc-3.7.1-windows-x86_64.msi" -ForegroundColor Cyan
Write-Host ""

# Method 3: Try chocolatey with admin check
Write-Host "Method 3: Chocolatey (requires admin)" -ForegroundColor Cyan
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($isAdmin) {
    Write-Host "[OK] Running as Administrator" -ForegroundColor Green
    Write-Host "Installing pandoc using chocolatey..." -ForegroundColor Yellow
    choco install pandoc -y
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[SUCCESS] Pandoc installed using chocolatey!" -ForegroundColor Green
        exit 0
    }
} else {
    Write-Host "[SKIP] Not running as Administrator" -ForegroundColor Yellow
    Write-Host "[INFO] To use chocolatey, run PowerShell as Administrator" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "After installing pandoc, restart PowerShell and run:" -ForegroundColor Cyan
Write-Host "  .\scripts\compile.ps1" -ForegroundColor Green

