# RAG Test Questions - StillMe Knowledge Base

## 🎯 Mục đích
Test khả năng RAG của StillMe retrieve thông tin từ knowledge base bằng nhiều ngôn ngữ.

## 📝 Câu hỏi Test (Nhiều ngôn ngữ)

### 🇻🇳 Tiếng Việt

1. **Câu hỏi cơ bản:**
   - "StillMe là gì?"
   - "StillMe hoạt động như thế nào?"
   - "StillMe học tập như thế nào?"

2. **Câu hỏi về RAG:**
   - "RAG system của StillMe hoạt động ra sao?"
   - "StillMe sử dụng RAG để làm gì?"
   - "Vector database của StillMe dùng công nghệ gì?"

3. **Câu hỏi về Learning:**
   - "StillMe học tập tự động như thế nào?"
   - "Learning scheduler của StillMe chạy bao lâu một lần?"
   - "StillMe thu thập kiến thức từ đâu?"

4. **Câu hỏi về Validator:**
   - "Validator chain của StillMe làm gì?"
   - "Evidence overlap validation hoạt động thế nào?"
   - "Tại sao StillMe cần citation trong câu trả lời?"

5. **Câu hỏi về Architecture:**
   - "StillMe được xây dựng bằng công nghệ gì?"
   - "ChromaDB trong StillMe dùng để làm gì?"
   - "StillMe có những component chính nào?"

### 🇬🇧 English

1. **Basic Questions:**
   - "What is StillMe?"
   - "How does StillMe work?"
   - "How does StillMe learn?"

2. **RAG Questions:**
   - "How does StillMe's RAG system work?"
   - "What does StillMe use RAG for?"
   - "What vector database technology does StillMe use?"

3. **Learning Questions:**
   - "How does StillMe perform automated learning?"
   - "How often does StillMe's learning scheduler run?"
   - "Where does StillMe collect knowledge from?"

4. **Validator Questions:**
   - "What does StillMe's validator chain do?"
   - "How does evidence overlap validation work?"
   - "Why does StillMe require citations in responses?"

5. **Architecture Questions:**
   - "What technologies is StillMe built with?"
   - "What is ChromaDB used for in StillMe?"
   - "What are the main components of StillMe?"

### 🇫🇷 Français

1. **Questions de base:**
   - "Qu'est-ce que StillMe?"
   - "Comment fonctionne StillMe?"
   - "Comment StillMe apprend-il?"

2. **Questions sur RAG:**
   - "Comment fonctionne le système RAG de StillMe?"
   - "À quoi StillMe utilise-t-il RAG?"
   - "Quelle technologie de base de données vectorielle StillMe utilise-t-il?"

3. **Questions sur l'apprentissage:**
   - "Comment StillMe effectue-t-il l'apprentissage automatisé?"
   - "À quelle fréquence le planificateur d'apprentissage de StillMe s'exécute-t-il?"
   - "D'où StillMe collecte-t-il les connaissances?"

### 🇪🇸 Español

1. **Preguntas básicas:**
   - "¿Qué es StillMe?"
   - "¿Cómo funciona StillMe?"
   - "¿Cómo aprende StillMe?"

2. **Preguntas sobre RAG:**
   - "¿Cómo funciona el sistema RAG de StillMe?"
   - "¿Para qué usa StillMe RAG?"
   - "¿Qué tecnología de base de datos vectorial usa StillMe?"

### 🇩🇪 Deutsch

1. **Grundlegende Fragen:**
   - "Was ist StillMe?"
   - "Wie funktioniert StillMe?"
   - "Wie lernt StillMe?"

2. **RAG-Fragen:**
   - "Wie funktioniert StillMes RAG-System?"
   - "Wofür verwendet StillMe RAG?"
   - "Welche Vektordatenbank-Technologie verwendet StillMe?"

### 🇯🇵 日本語

1. **基本質問:**
   - "StillMeとは何ですか？"
   - "StillMeはどのように機能しますか？"
   - "StillMeはどのように学習しますか？"

2. **RAGに関する質問:**
   - "StillMeのRAGシステムはどのように機能しますか？"
   - "StillMeはRAGを何に使用しますか？"
   - "StillMeはどのベクトルデータベース技術を使用しますか？"

### 🇨🇳 中文

1. **基本问题:**
   - "StillMe是什么？"
   - "StillMe如何工作？"
   - "StillMe如何学习？"

2. **关于RAG的问题:**
   - "StillMe的RAG系统如何工作？"
   - "StillMe使用RAG做什么？"
   - "StillMe使用什么向量数据库技术？"

## 🧪 Test Scenarios

### Scenario 1: Basic Knowledge Retrieval
**Câu hỏi:** "StillMe là gì?"
**Kỳ vọng:** Response phải có citation [1], [2] và giải thích về StillMe từ foundational knowledge.

### Scenario 2: Technical Details
**Câu hỏi:** "RAG system của StillMe hoạt động ra sao?"
**Kỳ vọng:** Response giải thích về ChromaDB, embeddings, retrieval process với citations.

### Scenario 3: Multilingual Support
**Câu hỏi:** "What is StillMe?" (English)
**Kỳ vọng:** Response bằng tiếng Anh, có citations, retrieve đúng knowledge.

### Scenario 4: Learning Mechanism
**Câu hỏi:** "StillMe học tập tự động như thế nào?"
**Kỳ vọng:** Response giải thích về learning scheduler, RSS feeds, 4-hour cycles với citations.

### Scenario 5: Validator Chain
**Câu hỏi:** "Validator chain của StillMe làm gì?"
**Kỳ vọng:** Response giải thích về citation, evidence overlap, ethics checks với citations.

## ✅ Checklist khi test

- [ ] Response có citations [1], [2], [3]...
- [ ] Response đúng ngôn ngữ (match với câu hỏi)
- [ ] Response có thông tin chính xác về StillMe
- [ ] Không bị lỗi 422 validation
- [ ] Response không bị cắt cụt
- [ ] RAG enabled = true trong response metadata (nếu có)

## 🚨 Lưu ý

- Nếu response không có citation → RAG không hoạt động đúng
- Nếu response sai ngôn ngữ → Language detection có vấn đề
- Nếu bị lỗi 422 → Validation threshold có thể quá strict
- Nếu response generic (không có thông tin cụ thể về StillMe) → RAG không retrieve được knowledge

## 📊 Expected Response Format

```json
{
  "response": "StillMe là một hệ thống AI tự học... [1] [2]",
  "metadata": {
    "rag_used": true,
    "context_docs": 3,
    "citations": ["[1]", "[2]"]
  }
}
```

