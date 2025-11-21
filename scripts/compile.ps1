# Simple PowerShell script to compile Markdown to PDF
# Usage: .\scripts\compile.ps1
# Or: .\scripts\compile.ps1 docs\EXECUTIVE_SUMMARY.md

param(
    [string]$InputFile = "docs\EXECUTIVE_SUMMARY.md"
)

$OutputFile = $InputFile -replace '\.md$', '.pdf'

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Compile Markdown to PDF" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if input file exists
if (-not (Test-Path $InputFile)) {
    Write-Host "[ERROR] File not found: $InputFile" -ForegroundColor Red
    exit 1
}

Write-Host "Input:  $InputFile" -ForegroundColor Yellow
Write-Host "Output: $OutputFile" -ForegroundColor Yellow
Write-Host ""

# Method 1: Try pandoc with MiKTeX (if available)
Write-Host "Method 1: Trying pandoc with MiKTeX..." -ForegroundColor Cyan

# Check for MiKTeX
$pdflatexPath = Get-Command pdflatex -ErrorAction SilentlyContinue
$xelatexPath = Get-Command xelatex -ErrorAction SilentlyContinue

if ($pdflatexPath -or $xelatexPath) {
    $miktexVersion = pdflatex --version 2>&1 | Select-Object -First 1
    Write-Host "[OK] MiKTeX found: $miktexVersion" -ForegroundColor Green
} else {
    Write-Host "[SKIP] MiKTeX not found" -ForegroundColor Yellow
}

$pandocPath = Get-Command pandoc -ErrorAction SilentlyContinue
if ($pandocPath) {
    Write-Host "[OK] pandoc found" -ForegroundColor Green
    
    # Try xelatex first (better for Unicode/Vietnamese), then pdflatex
    $pdfEngine = "xelatex"
    if (-not $xelatexPath) {
        $pdfEngine = "pdflatex"
    }
    
    Write-Host "Using PDF engine: $pdfEngine" -ForegroundColor Yellow
    Write-Host "Running pandoc..." -ForegroundColor Yellow
    
    # Pandoc command with MiKTeX
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
        Write-Host "[SUCCESS] PDF created using pandoc + MiKTeX!" -ForegroundColor Green
        Write-Host "Output: $OutputFile" -ForegroundColor Cyan
        $fileSize = (Get-Item $OutputFile).Length / 1KB
        Write-Host "File size: $([math]::Round($fileSize, 2)) KB" -ForegroundColor Cyan
        exit 0
    } else {
        Write-Host "[WARNING] pandoc failed, trying next method..." -ForegroundColor Yellow
    }
} else {
    Write-Host "[SKIP] pandoc not found" -ForegroundColor Yellow
    Write-Host "[INFO] Install pandoc from: https://pandoc.org/installing.html" -ForegroundColor Yellow
}

Write-Host ""

# Method 2: Try Python with markdown + weasyprint
Write-Host "Method 2: Trying Python (markdown + weasyprint)..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python found: $pythonVersion" -ForegroundColor Green
    
    # Check for weasyprint
    $weasyprint = python -m pip show weasyprint 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[INFO] Installing weasyprint..." -ForegroundColor Yellow
        python -m pip install weasyprint --quiet
    }
    
    # Run Python conversion
    Write-Host "Converting..." -ForegroundColor Yellow
    python -c @"
import sys
import markdown
from weasyprint import HTML
from pathlib import Path

input_file = r'$InputFile'
output_file = r'$OutputFile'

with open(input_file, 'r', encoding='utf-8') as f:
    md_content = f.read()

html_content = markdown.markdown(md_content, extensions=['extra', 'codehilite', 'tables'])

html_doc = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset=\"UTF-8\">
    <style>
        @page {{ size: A4; margin: 2cm; }}
        body {{ font-family: 'Segoe UI', sans-serif; line-height: 1.6; color: #333; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #95a5a6; padding-bottom: 8px; margin-top: 30px; }}
        h3 {{ color: #555; margin-top: 20px; }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
        pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background: #3498db; color: white; }}
        tr:nth-child(even) {{ background: #f2f2f2; }}
        blockquote {{ border-left: 4px solid #3498db; margin: 20px 0; padding-left: 20px; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>'''

HTML(string=html_doc).write_pdf(output_file)
print(f'[SUCCESS] PDF created: {output_file}')
"@
    
    if (Test-Path $OutputFile) {
        Write-Host ""
        Write-Host "[SUCCESS] PDF created using Python!" -ForegroundColor Green
        Write-Host "Output: $OutputFile" -ForegroundColor Cyan
        exit 0
    }
} catch {
    Write-Host "[WARNING] Python method failed: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[ERROR] All methods failed. Please install one of:" -ForegroundColor Red
Write-Host "  1. pandoc: https://pandoc.org/installing.html" -ForegroundColor Yellow
Write-Host "  2. Python + weasyprint: pip install weasyprint markdown" -ForegroundColor Yellow
exit 1

