# 🤖 StillMe AI Models Explanation

## Overview

StillMe sử dụng **3 loại models** khác nhau, mỗi loại có chức năng riêng:

---

## 1. **all-MiniLM-L6-v2** (Embedding Model)

### Công dụng:
- **Chuyển đổi text thành vector embeddings** (số thực đa chiều)
- Tạo embeddings cho documents và queries để lưu trữ và tìm kiếm trong vector database

### Chức năng:
- **Text → Vector**: Chuyển câu hỏi và documents thành vectors 384 chiều
- **Semantic Search**: So sánh độ tương đồng giữa các vectors để tìm documents liên quan
- **RAG Foundation**: Cung cấp nền tảng cho hệ thống RAG (Retrieval-Augmented Generation)

### Kỹ thuật:
- **Model**: `all-MiniLM-L6-v2` từ `sentence-transformers` library
- **Size**: ~80MB
- **Dimension**: 384 dimensions
- **Language**: Multilingual (hỗ trợ nhiều ngôn ngữ)
- **Framework**: `sentence-transformers` (Python library)

### Ví dụ:
```
Input: "How does StillMe work?"
Output: [0.123, -0.456, 0.789, ..., 0.234] (384 số thực)
```

---

## 2. **sentence-transformers** (Framework/Library)

### Công dụng:
- **KHÔNG PHẢI là một model riêng** - đây là một Python library/framework
- Cung cấp API và tools để sử dụng các embedding models (như `all-MiniLM-L6-v2`)

### Chức năng:
- Load và quản lý embedding models
- Cung cấp `SentenceTransformer` class để encode text
- Xử lý batch processing, caching, và optimization

### Tương tự:
- Giống như `tensorflow` là framework để chạy models
- `sentence-transformers` là framework để chạy embedding models

---

## 3. **ChromaDB ONNX Model** (Optimization Model)

### Công dụng:
- **Tối ưu hóa performance** của ChromaDB vector search
- Chuyển đổi embeddings sang ONNX format để query nhanh hơn

### Chức năng:
- **Speed Optimization**: Tăng tốc độ vector search trong ChromaDB
- **ONNX Runtime**: Sử dụng ONNX runtime để tối ưu inference
- **Automatic Download**: ChromaDB tự động tải model này khi cần

### Kỹ thuật:
- **Format**: ONNX (Open Neural Network Exchange)
- **Size**: ~79MB
- **Location**: `~/.cache/chroma/onnx_models/all-MiniLM-L6-v2/`
- **Purpose**: Optimize vector similarity search

---

## Tóm tắt

| Model/Component | Type | Size | Purpose | Location |
|----------------|------|------|---------|----------|
| **all-MiniLM-L6-v2** | Embedding Model | ~80MB | Text → Vector embeddings | `/app/.model_cache/` |
| **sentence-transformers** | Framework | N/A | Library để sử dụng embedding models | Python package |
| **ChromaDB ONNX** | Optimization Model | ~79MB | Tối ưu vector search | `/app/.cache/chroma/onnx_models/` |

## Workflow

1. **User asks question** → Text input
2. **all-MiniLM-L6-v2** (via sentence-transformers) → Converts question to embedding vector
3. **ChromaDB** (with ONNX optimization) → Searches similar vectors in database
4. **Retrieved documents** → Context for LLM
5. **LLM** (DeepSeek/OpenAI) → Generates response using context

---

## Lưu ý

- **all-MiniLM-L6-v2** và **ChromaDB ONNX** là 2 models **khác nhau**:
  - `all-MiniLM-L6-v2`: Tạo embeddings từ text
  - ChromaDB ONNX: Tối ưu search performance
  
- **sentence-transformers** là **framework**, không phải model:
  - Giống như `pytorch` hoặc `tensorflow` - là công cụ để sử dụng models

- Tất cả 3 components đều được **pre-download trong Docker image** để tránh re-download mỗi lần deploy.

