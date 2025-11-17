# Script to install required LaTeX packages for StillMe paper
# Usage: .\install_packages.ps1
# Note: This requires MiKTeX Console to be available

Write-Host "Installing required LaTeX packages for StillMe paper..." -ForegroundColor Cyan
Write-Host ""

# List of required packages
$packages = @(
    "booktabs",
    "hyperref",
    "amsmath",
    "amssymb",
    "graphicx",
    "xcolor",
    "url",
    "multirow",
    "array",
    "hycolor",  # Required by hyperref
    "kvoptions", # Required by hyperref
    "letltxmacro", # Required by hyperref
    "pdftexcmds", # Required by hyperref
    "infwarerr", # Required by hyperref
    "kvsetkeys", # Required by hyperref
    "etexcmds", # Required by hyperref
    "gettitlestring" # Required by hyperref
)

Write-Host "Required packages:" -ForegroundColor Yellow
foreach ($pkg in $packages) {
    Write-Host "  - $pkg" -ForegroundColor White
}

Write-Host ""
Write-Host "Option 1: Install via MiKTeX Console (Recommended)" -ForegroundColor Green
Write-Host "  1. Open MiKTeX Console from Start Menu" -ForegroundColor White
Write-Host "  2. Go to 'Packages' tab" -ForegroundColor White
Write-Host "  3. Search and install each package above" -ForegroundColor White
Write-Host "  4. Or use 'Update' to install all missing packages" -ForegroundColor White

Write-Host ""
Write-Host "Option 2: Let MiKTeX auto-install during compilation" -ForegroundColor Green
Write-Host "  - When dialog appears, UNCHECK 'Always show this dialog'" -ForegroundColor White
Write-Host "  - Click 'Install' for each package" -ForegroundColor White
Write-Host "  - MiKTeX will auto-install remaining packages" -ForegroundColor White

Write-Host ""
Write-Host "Option 3: Install via command line (if miktex packages command works)" -ForegroundColor Green
Write-Host "  Run these commands:" -ForegroundColor White
foreach ($pkg in $packages) {
    Write-Host "    miktex packages install $pkg" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "After installing packages, run: .\compile.ps1" -ForegroundColor Yellow

