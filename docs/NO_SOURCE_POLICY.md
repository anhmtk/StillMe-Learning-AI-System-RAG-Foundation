# 🧾 No‑Source Policy (When Evidence Is Missing)

This policy defines **how StillMe must respond** when users ask for sources but the RAG knowledge base cannot support the answer.

---

## Core Rule

If the user **explicitly asks for sources/timestamps/links** and **no relevant context exists**, StillMe must:

1. **Say it does not have verified sources**
2. **Refuse to fabricate**
3. **Offer next steps or alternatives**

---

## Trigger Examples (Source‑Required Questions)

- “Bạn có thể dẫn nguồn không?”
- “Cho mình link chính xác?”
- “Timestamp của bài đó là gì?”
- “Citation/DOI đâu?”

---

## ✅ Good Responses (Correct)

**Vietnamese**

```
Mình không có nguồn đáng tin cậy trong RAG cho câu hỏi này,
nên mình không thể dẫn nguồn hoặc timestamp chính xác.

Gợi ý:
- Bạn muốn mình tóm tắt các nghiên cứu liên quan hiện có trong KB không?
- Nếu cần nguồn mới nhất, bạn có thể tra arXiv/Google Scholar theo từ khóa phù hợp.
```

**English**

```
I don’t have verified sources in the current RAG knowledge base,
so I can’t provide accurate citations or timestamps.
If you want, I can summarize what exists in the KB or suggest search keywords.
```

---

## ❌ Bad Responses (Forbidden)

```
Here are the sources: [random links]
```

```
I’m not sure, but I think it’s correct. [general knowledge]
```

```
(Provides a confident answer without any sources)
```

---

## Implementation Reference

- `backend/validators/citation.py`
  - Refusal logic for source‑required questions with no context.

---

## Minimal Compliance Checklist

- [ ] The response explicitly says **no verified sources**
- [ ] No external links are invented
- [ ] Offers alternatives (summary of existing KB, or suggest where to search)

