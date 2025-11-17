# Figures for StillMe Paper

This directory should contain the following figures for the arXiv submission:

## Required Figures

1. **fig1_architecture.pdf** (or .png)
   - StillMe System Architecture diagram
   - Shows: External Sources → Learning Pipeline → Vector DB → RAG Retrieval → Validation Chain → Response
   - Recommended tools: draw.io, Excalidraw, PowerPoint, or TikZ

2. **fig2_validation_chain.pdf** (or .png)
   - Validation Chain flow diagram
   - Shows: CitationRequired → EvidenceOverlap → NumericUnitsBasic → ConfidenceValidator → FallbackHandler → EthicsAdapter
   - Recommended tools: draw.io, Excalidraw, or TikZ

3. **fig3_results.pdf** (or .png)
   - Accuracy and Transparency Score comparison chart
   - Bar chart showing: StillMe vs Vanilla RAG vs ChatGPT
   - Metrics: Accuracy & Transparency Score
   - Recommended tools: Python (matplotlib), Excel, or any charting tool

## Figure Requirements

- **Format**: PDF (preferred) or PNG (high resolution, 300 DPI minimum)
- **Size**: Should fit within 0.9\linewidth in LaTeX (approximately 6 inches wide)
- **Resolution**: Minimum 300 DPI for PNG files
- **Font**: Use readable fonts (Times, Arial, or similar)
- **Colors**: Use colorblind-friendly palettes if using colors

## Creating Figures

### Option 1: Draw.io / Excalidraw
1. Create diagram in draw.io or Excalidraw
2. Export as PDF or high-resolution PNG
3. Save to this directory with appropriate filename

### Option 2: Python (matplotlib)
```python
import matplotlib.pyplot as plt
# Create your chart
plt.savefig('fig3_results.pdf', dpi=300, bbox_inches='tight')
```

### Option 3: PowerPoint / Keynote
1. Create diagram in PowerPoint/Keynote
2. Export as PDF or high-resolution image
3. Save to this directory

## Placeholder Note

Currently, these figures are placeholders. You need to create the actual figures before submitting to arXiv. The LaTeX document will compile without them, but the figures will be missing in the final PDF.

## Quick Test

To test if figures are properly referenced:
```bash
# Check if all figures exist
ls -la figures/fig*.pdf figures/fig*.png
```

