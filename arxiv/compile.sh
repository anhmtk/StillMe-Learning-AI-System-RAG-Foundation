#!/bin/bash
# Compilation script for LaTeX document (Linux/Mac)
# Usage: ./compile.sh

echo "Compiling StillMe paper for arXiv submission..."

# Check if pdflatex is available
if ! command -v pdflatex &> /dev/null; then
    echo "✗ pdflatex not found. Please install TeX Live."
    exit 1
fi
echo "✓ pdflatex found"

# Check if bibtex is available
if command -v bibtex &> /dev/null; then
    echo "✓ bibtex found"
    USE_BIBTEX=true
else
    echo "⚠ bibtex not found. Will skip bibliography compilation."
    USE_BIBTEX=false
fi

# Compilation steps
echo ""
echo "Step 1: First pdflatex pass..."
pdflatex -interaction=nonstopmode main.tex

if [ $? -ne 0 ]; then
    echo "✗ First pdflatex pass failed. Check main.log for errors."
    exit 1
fi

if [ "$USE_BIBTEX" = true ]; then
    echo ""
    echo "Step 2: Running bibtex..."
    bibtex main
    
    echo ""
    echo "Step 3: Second pdflatex pass..."
    pdflatex -interaction=nonstopmode main.tex
    
    echo ""
    echo "Step 4: Third pdflatex pass (final)..."
    pdflatex -interaction=nonstopmode main.tex
else
    echo ""
    echo "Step 2: Second pdflatex pass (final)..."
    pdflatex -interaction=nonstopmode main.tex
fi

# Check final result
if [ -f "main.pdf" ]; then
    echo ""
    echo "✓ Compilation successful! Output: main.pdf"
    echo ""
    echo "Next steps:"
    echo "1. Review main.pdf for formatting"
    echo "2. Check main.log for any warnings"
    echo "3. Prepare figures in figures/ directory"
    echo "4. Submit to arXiv with main.tex, refs.bib, and figures/"
else
    echo ""
    echo "✗ Compilation failed. Check main.log for errors."
    exit 1
fi

