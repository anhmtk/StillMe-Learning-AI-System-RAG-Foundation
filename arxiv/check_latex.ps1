# Script to check if LaTeX is installed and ready
# Usage: .\check_latex.ps1

Write-Host "Checking LaTeX installation..." -ForegroundColor Cyan
Write-Host ""

# Check pdflatex
Write-Host "Checking pdflatex..." -ForegroundColor Yellow
try {
    $pdflatexVersion = pdflatex --version 2>&1 | Select-Object -First 1
    Write-Host "[OK] pdflatex found: $pdflatexVersion" -ForegroundColor Green
    $pdflatexOK = $true
} catch {
    Write-Host "[ERROR] pdflatex not found" -ForegroundColor Red
    Write-Host "  Please install MiKTeX from: https://miktex.org/download" -ForegroundColor Yellow
    $pdflatexOK = $false
}

# Check bibtex
Write-Host ""
Write-Host "Checking bibtex..." -ForegroundColor Yellow
try {
    $bibtexVersion = bibtex --version 2>&1 | Select-Object -First 1
    Write-Host "[OK] bibtex found: $bibtexVersion" -ForegroundColor Green
    $bibtexOK = $true
} catch {
    Write-Host "[ERROR] bibtex not found" -ForegroundColor Red
    $bibtexOK = $false
}

# Summary
Write-Host ""
if ($pdflatexOK -and $bibtexOK) {
    Write-Host "[SUCCESS] LaTeX is ready! You can now run .\compile.ps1" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next step:" -ForegroundColor Cyan
    Write-Host "  .\compile.ps1" -ForegroundColor White
} else {
    Write-Host "[WARNING] LaTeX installation incomplete" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Installation steps:" -ForegroundColor Cyan
    Write-Host "1. Download MiKTeX: https://miktex.org/download" -ForegroundColor White
    Write-Host "2. Run installer and select 'Install packages on-the-fly: Yes'" -ForegroundColor White
    Write-Host "3. Restart PowerShell after installation" -ForegroundColor White
    Write-Host "4. Run this script again to verify: .\check_latex.ps1" -ForegroundColor White
}

