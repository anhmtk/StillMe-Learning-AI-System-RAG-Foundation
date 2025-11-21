# Simple script to compile Markdown to PDF using pandoc + MiKTeX
# This script assumes pandoc is already installed
# Usage: .\scripts\compile_simple.ps1 [input_file]

param(
    [string]$InputFile = "docs\EXECUTIVE_SUMMARY.md"
)

$OutputFile = $InputFile -replace '\.md$', '.pdf'

Write-Host "Compiling: $InputFile -> $OutputFile" -ForegroundColor Cyan
Write-Host ""

# Check if input file exists
if (-not (Test-Path $InputFile)) {
    Write-Host "[ERROR] File not found: $InputFile" -ForegroundColor Red
    exit 1
}

# Check for pandoc
$pandocPath = Get-Command pandoc -ErrorAction SilentlyContinue
if (-not $pandocPath) {
    Write-Host "[ERROR] pandoc not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install pandoc first:" -ForegroundColor Yellow
    Write-Host "  1. Run: .\scripts\install_pandoc.ps1" -ForegroundColor White
    Write-Host "  2. Or download from: https://pandoc.org/installing.html" -ForegroundColor White
    Write-Host "  3. Restart PowerShell after installation" -ForegroundColor White
    exit 1
}

# Check for MiKTeX
$xelatexPath = Get-Command xelatex -ErrorAction SilentlyContinue
$pdflatexPath = Get-Command pdflatex -ErrorAction SilentlyContinue

if ($xelatexPath) {
    $pdfEngine = "xelatex"
    Write-Host "[OK] Using xelatex (better for Vietnamese)" -ForegroundColor Green
} elseif ($pdflatexPath) {
    $pdfEngine = "pdflatex"
    Write-Host "[OK] Using pdflatex" -ForegroundColor Green
} else {
    Write-Host "[ERROR] MiKTeX not found!" -ForegroundColor Red
    Write-Host "Please install MiKTeX from: https://miktex.org/download" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] pandoc found" -ForegroundColor Green
Write-Host ""

# Compile
Write-Host "Compiling PDF..." -ForegroundColor Yellow
pandoc $InputFile -o $OutputFile `
    --pdf-engine=$pdfEngine `
    -V geometry:margin=2cm `
    -V fontsize=11pt `
    -V mainfont="Times New Roman" `
    -V lang=vi `
    --highlight-style=tango `
    --toc `
    --toc-depth=3

if ($LASTEXITCODE -eq 0 -and (Test-Path $OutputFile)) {
    Write-Host ""
    Write-Host "[SUCCESS] PDF created!" -ForegroundColor Green
    Write-Host "Output: $OutputFile" -ForegroundColor Cyan
    $fileSize = (Get-Item $OutputFile).Length / 1KB
    Write-Host "File size: $([math]::Round($fileSize, 2)) KB" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "[ERROR] PDF generation failed" -ForegroundColor Red
    Write-Host "Check the error messages above" -ForegroundColor Yellow
    exit 1
}

