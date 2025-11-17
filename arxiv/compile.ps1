# PowerShell script to compile LaTeX document for arXiv submission
# Usage: .\compile.ps1

Write-Host "Compiling StillMe paper for arXiv submission..." -ForegroundColor Green

# Check if pdflatex is available
try {
    $pdflatexVersion = pdflatex --version 2>&1
    Write-Host "[OK] pdflatex found" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] pdflatex not found. Please install TeX Live or MiKTeX." -ForegroundColor Red
    exit 1
}

# Check if bibtex is available
$useBibtex = $true
try {
    $bibtexVersion = bibtex --version 2>&1
    Write-Host "[OK] bibtex found" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] bibtex not found. Will skip bibliography compilation." -ForegroundColor Yellow
    $useBibtex = $false
}

# Compilation steps
Write-Host ""
Write-Host "Step 1: First pdflatex pass..." -ForegroundColor Cyan
pdflatex -interaction=nonstopmode main.tex | Out-Null

# Check if PDF was created (more reliable than exit code)
if (-not (Test-Path "main.pdf")) {
    Write-Host "[ERROR] First pdflatex pass failed. Check main.log for errors." -ForegroundColor Red
    exit 1
}

if ($useBibtex) {
    Write-Host ""
    Write-Host "Step 2: Running bibtex..." -ForegroundColor Cyan
    bibtex main | Out-Null
    
    Write-Host ""
    Write-Host "Step 3: Second pdflatex pass..." -ForegroundColor Cyan
    pdflatex -interaction=nonstopmode main.tex | Out-Null
    
    Write-Host ""
    Write-Host "Step 4: Third pdflatex pass (final)..." -ForegroundColor Cyan
    pdflatex -interaction=nonstopmode main.tex | Out-Null
} else {
    Write-Host ""
    Write-Host "Step 2: Second pdflatex pass (final)..." -ForegroundColor Cyan
    pdflatex -interaction=nonstopmode main.tex | Out-Null
}

# Check final result
if (Test-Path "main.pdf") {
    Write-Host ""
    Write-Host "[SUCCESS] Compilation successful! Output: main.pdf" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Review main.pdf for formatting"
    Write-Host "2. Check main.log for any warnings"
    Write-Host "3. Prepare figures in figures/ directory"
    Write-Host "4. Submit to arXiv with main.tex, refs.bib, and figures/"
} else {
    Write-Host ""
    Write-Host "[ERROR] Compilation failed. Check main.log for errors." -ForegroundColor Red
    exit 1
}

