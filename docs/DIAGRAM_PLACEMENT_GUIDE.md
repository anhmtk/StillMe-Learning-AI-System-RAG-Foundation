# 📊 Diagram Placement Guide for StillMe

## Current Status

**✅ Existing:**
- `docs/ARCHITECTURE.md` - Has Mermaid text-based diagrams (auto-rendered by GitHub)
- `arxiv/figures/` - Has PNG/PDF files (may be outdated/placeholders)
- `docs/VALIDATION_CHAIN_TEXT_DIAGRAM.md` - Text-based diagram reference

**❌ Missing:**
- No diagram images in README.md
- No `docs/assets/` folder for diagram images
- No screenshot examples

## Recommended Structure

### Option 1: Professional Structure (Recommended)

```
StillMe-Learning-AI-System-RAG-Foundation/
├── README.md
│   └── Architecture section
│       └── Small diagram: ![Architecture](docs/assets/architecture_overview.png)
│
├── docs/
│   ├── ARCHITECTURE.md
│   │   └── Full architecture with Mermaid + high-res diagram links
│   │
│   └── assets/ (NEW - create this folder)
│       ├── architecture_overview.png (800x600, for README)
│       ├── architecture_detailed.png (1200x900, for docs)
│       ├── validation_chain_diagram.png
│       ├── learning_pipeline.png
│       ├── dashboard_screenshot.png (optional)
│       └── chat_example.png (optional)
```

### Option 2: Screenshot-Based (Quick Solution)

```
StillMe-Learning-AI-System-RAG-Foundation/
├── README.md
│   └── Architecture section
│       └── Screenshot: ![Dashboard](docs/assets/dashboard_architecture.png)
│
├── docs/
│   └── assets/
│       ├── dashboard_architecture.png (screenshot of dashboard showing system)
│       ├── validation_metrics_screenshot.png
│       └── chat_interface_screenshot.png
```

## Recommendations

### For README.md:
- **Small diagram** (800x600px max) - Architecture overview
- **Text description** (keep existing) - For accessibility
- **Link to detailed docs** - "See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full architecture"

### For docs/ARCHITECTURE.md:
- **Mermaid diagrams** (keep existing) - Auto-rendered, version-controlled
- **High-res diagram** (1200x900px) - For detailed view
- **Screenshots** (optional) - Dashboard, metrics, chat examples

### For Screenshots:
- **Dashboard screenshots**: Show validation metrics, learning stats
- **Chat examples**: Show StillMe responses with citations
- **Backend logs**: Only if sanitized (no API keys, no user data)

## Best Practices

1. **Create `docs/assets/` folder** - Centralized location for all images
2. **Use descriptive filenames** - `architecture_overview.png` not `diagram1.png`
3. **Optimize file sizes** - Compress PNGs (use TinyPNG or similar)
4. **Add alt text** - For accessibility: `![Architecture Overview](path)`
5. **Version control** - Commit images to repo (GitHub LFS if > 50MB)

## Quick Solution: Screenshot Workflow

If you can't create professional diagrams:

1. **Take screenshots** of:
   - Dashboard (Validation Metrics page)
   - Dashboard (Learning Stats page)
   - Chat interface (showing StillMe response with citations)

2. **Sanitize screenshots**:
   - Remove API keys
   - Remove user data
   - Blur sensitive information
   - Add annotations (arrows, labels) using simple tools

3. **Save to `docs/assets/`**:
   - `dashboard_validation_metrics.png`
   - `dashboard_learning_stats.png`
   - `chat_example_with_citations.png`

4. **Add to README.md**:
   ```markdown
   ## 🔧 Architecture
   
   ![StillMe Dashboard - Validation Metrics](docs/assets/dashboard_validation_metrics.png)
   
   *Screenshot showing StillMe's validation chain performance*
   ```

## Professional vs Screenshot Trade-offs

| Aspect | Professional Diagram | Screenshot |
|--------|---------------------|------------|
| **Time** | 2-4 hours | 10-30 minutes |
| **Quality** | High, clean | Depends on UI |
| **Maintainability** | Easy to update | Need to retake |
| **Professionalism** | Very high | Medium |
| **Transparency** | Abstract | Shows real system |
| **Accessibility** | Good (with alt text) | Good (with alt text) |

## Recommendation

**For StillMe (transparency-focused project):**

1. **Short-term**: Use screenshots with annotations
   - Fast, shows real system
   - Aligns with transparency philosophy
   - Can improve later

2. **Long-term**: Create professional diagrams
   - When you have time/resources
   - Or when community contributes

3. **Hybrid approach**:
   - README: Screenshot (quick, shows reality)
   - docs/ARCHITECTURE.md: Mermaid + professional diagram (detailed)

## Next Steps

1. Create `docs/assets/` folder
2. Take screenshots (dashboard, chat)
3. Sanitize and annotate screenshots
4. Add to README.md Architecture section
5. Update docs/ARCHITECTURE.md with links

