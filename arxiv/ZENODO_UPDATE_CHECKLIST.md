# ✅ Checklist Cập Nhật Zenodo DOI trong GitHub Release

## 📋 Sau Khi Publish Zenodo Thành Công

Khi Zenodo đã cung cấp DOI mới, bạn cần cập nhật **CẢ HAI** trong GitHub Release:

### 1. ✅ DOI (Đã cập nhật - Đúng!)
```
DOI: https://doi.org/10.5281/zenodo.17738949
```

### 2. ⚠️ Zenodo Record Link (Cần cập nhật!)

**Link cũ (SAI):**
```
Zenodo Record: https://zenodo.org/records/17637315
```

**Link mới (ĐÚNG):**
```
Zenodo Record: https://zenodo.org/records/17738949
```

## 🔍 Cách Lấy Zenodo Record URL

1. Vào Zenodo record mới: `https://doi.org/10.5281/zenodo.17738949`
2. Copy URL từ thanh address bar: `https://zenodo.org/records/17738949`
3. Hoặc click vào "View on Zenodo" → Copy URL

## 📝 Template GitHub Release Description (Đúng)

```markdown
## StillMe Preprint v0.2 - Updated Evaluation Results

This release contains the updated preprint of the StillMe framework with latest evaluation results:

**StillMe: A Practical Framework for Building Transparent, Validated Retrieval-Augmented Generation Systems**

### Key Updates:
- ✅ Updated evaluation results: 35% accuracy (20-question subset), 13.5% (full 790-question)
- ✅ Updated citation rate: 91.1% (full evaluation)
- ✅ Updated transparency score: 85.8% (full evaluation)
- ✅ All metrics now reflect current system performance

### Files Included:
- `main.pdf` - Updated preprint with latest results
- `main.tex` - LaTeX source (updated)
- `refs.bib` - Bibliography
- `figures/` - All figures

### DOI:
- **DOI**: https://doi.org/10.5281/zenodo.17738949
- **Zenodo Record**: https://zenodo.org/records/17738949

### Overview:
StillMe is a transparency-first framework designed to transform commercial LLMs into fully auditable systems without any model training or labeled datasets.

This paper introduces:
- A multi-layer Validation Chain to reduce hallucination
- A continuous learning pipeline updating every 4 hours (RSS, arXiv, CrossRef, Wikipedia)
```

## 🔗 Phân Biệt DOI vs Zenodo Record URL

### DOI (Digital Object Identifier)
- Format: `https://doi.org/10.5281/zenodo.17738949`
- Dùng để cite trong papers, references
- Permanent, không đổi
- Redirect đến Zenodo record

### Zenodo Record URL
- Format: `https://zenodo.org/records/17738949`
- Direct link đến Zenodo record page
- Có thể thay đổi nếu Zenodo thay đổi URL structure (hiếm)
- Thường dùng để link trực tiếp

### Mối Quan Hệ
- DOI `10.5281/zenodo.17738949` → Record ID: `17738949`
- Record URL: `https://zenodo.org/records/17738949`
- Cả hai đều trỏ đến cùng một record, nhưng:
  - DOI là permanent identifier (dùng để cite)
  - Record URL là direct link (dùng để access)

## ✅ Checklist Cuối Cùng

Sau khi cập nhật GitHub Release, kiểm tra:

- [ ] DOI mới đã được cập nhật: `https://doi.org/10.5281/zenodo.17738949`
- [ ] Zenodo Record link đã được cập nhật: `https://zenodo.org/records/17738949`
- [ ] Cả hai links đều hoạt động (click để test)
- [ ] Record ID trong URL khớp với DOI (17738949)
- [ ] Không còn reference đến record cũ (17637315) trong description

## 🎯 Quick Fix

Nếu bạn thấy trong description có:
```
DOI: https://doi.org/10.5281/zenodo.17738949
Zenodo Record: https://zenodo.org/records/17637315  ← SAI!
```

Thì cần sửa thành:
```
DOI: https://doi.org/10.5281/zenodo.17738949
Zenodo Record: https://zenodo.org/records/17738949  ← ĐÚNG!
```

**Lưu ý:** Record ID trong URL (`17738949`) phải khớp với số trong DOI (`zenodo.17738949`).

