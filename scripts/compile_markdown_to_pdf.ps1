# PowerShell script to compile Markdown to PDF
# Usage: .\scripts\compile_markdown_to_pdf.ps1 [input_file] [output_file]
# Example: .\scripts\compile_markdown_to_pdf.ps1 docs\EXECUTIVE_SUMMARY.md docs\EXECUTIVE_SUMMARY.pdf

param(
    [string]$InputFile = "docs\EXECUTIVE_SUMMARY.md",
    [string]$OutputFile = "docs\EXECUTIVE_SUMMARY.pdf"
)

Write-Host "Compiling Markdown to PDF..." -ForegroundColor Green
Write-Host "Input: $InputFile" -ForegroundColor Cyan
Write-Host "Output: $OutputFile" -ForegroundColor Cyan
Write-Host ""

# Check if input file exists
if (-not (Test-Path $InputFile)) {
    Write-Host "[ERROR] Input file not found: $InputFile" -ForegroundColor Red
    exit 1
}

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found. Please install Python." -ForegroundColor Red
    exit 1
}

# Check for required packages
Write-Host "Checking for required packages..." -ForegroundColor Cyan

$requiredPackages = @("markdown", "weasyprint")
$missingPackages = @()

foreach ($package in $requiredPackages) {
    $installed = python -m pip show $package 2>&1
    if ($LASTEXITCODE -ne 0) {
        $missingPackages += $package
        Write-Host "[WARNING] $package not found" -ForegroundColor Yellow
    } else {
        Write-Host "[OK] $package found" -ForegroundColor Green
    }
}

# Install missing packages
if ($missingPackages.Count -gt 0) {
    Write-Host ""
    Write-Host "Installing missing packages..." -ForegroundColor Cyan
    foreach ($package in $missingPackages) {
        Write-Host "Installing $package..." -ForegroundColor Yellow
        python -m pip install $package --quiet
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Failed to install $package" -ForegroundColor Red
            exit 1
        }
    }
}

Write-Host ""
Write-Host "Converting Markdown to PDF..." -ForegroundColor Cyan

# Create temporary Python script
$tempScript = [System.IO.Path]::GetTempFileName() + ".py"
$pythonCode = @"
import sys
import markdown
from weasyprint import HTML, CSS
from pathlib import Path

# Read markdown file
input_file = r"$InputFile"
output_file = r"$OutputFile"

print(f"Reading: {input_file}")
with open(input_file, 'r', encoding='utf-8') as f:
    md_content = f.read()

# Convert markdown to HTML
print("Converting Markdown to HTML...")
html_content = markdown.markdown(md_content, extensions=['extra', 'codehilite', 'tables'])

# Add CSS styling
html_document = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {{
            size: A4;
            margin: 2cm;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-bottom: 2px solid #95a5a6;
            padding-bottom: 8px;
            margin-top: 30px;
        }}
        h3 {{
            color: #555;
            margin-top: 20px;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        blockquote {{
            border-left: 4px solid #3498db;
            margin: 20px 0;
            padding-left: 20px;
            color: #555;
        }}
        ul, ol {{
            margin: 10px 0;
            padding-left: 30px;
        }}
        li {{
            margin: 5px 0;
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""

# Convert HTML to PDF
print(f"Generating PDF: {output_file}")
HTML(string=html_document).write_pdf(output_file)

print(f"[SUCCESS] PDF created: {output_file}")
"@

# Write Python script to temp file
[System.IO.File]::WriteAllText($tempScript, $pythonCode)

# Run Python script
python $tempScript

# Clean up
Remove-Item $tempScript -ErrorAction SilentlyContinue

# Check if PDF was created
if (Test-Path $OutputFile) {
    Write-Host ""
    Write-Host "[SUCCESS] PDF created successfully!" -ForegroundColor Green
    Write-Host "Output: $OutputFile" -ForegroundColor Cyan
    $fileSize = (Get-Item $OutputFile).Length / 1KB
    Write-Host "File size: $([math]::Round($fileSize, 2)) KB" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "[ERROR] PDF generation failed" -ForegroundColor Red
    exit 1
}

