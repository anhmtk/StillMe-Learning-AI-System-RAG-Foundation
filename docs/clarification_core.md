# Clarification Core – StillMe

## 1. Giới thiệu

Clarification Core là công nghệ lõi của StillMe, cho phép AI **chủ động làm rõ câu hỏi của người dùng** khi prompt mơ hồ, thay vì trả lời bừa.  

**Mục tiêu**: Biến StillMe thành AI **thấu hiểu con người**, không bắt con người học cách prompt.

## 2. Lộ trình triển khai

- **Phase 1:** Clarification cơ bản (rule-based, English-first)  
- **Phase 2:** Clarification thông minh (context-aware, feedback learning)  
- **Phase 3:** Clarification nâng cao (multi-modal, proactive suggestions, enterprise features)  

## 3. Các module chính

- `clarification_handler.py` – Phát hiện & sinh câu hỏi clarification  
- `multi_modal_clarification.py` – Hỗ trợ input đa dạng (text, code, image)  
- `proactive_suggestion.py` – Đề xuất proactive khi có nhiều hướng đi  

## 4. Tích hợp

- `app.py` – Middleware cho /chat requests  
- `agentdev/self_improvement.py` – Lưu feedback & học từ kết quả  
- `context_analyzer.py` – Hiểu ngữ cảnh hội thoại  

## 5. Test & Kiểm thử

- Unit test cho từng module  
- Integration test với ConversationalCore  
- SEAL-GRADE test: chaos test, load test, fuzzing  

## 6. Metrics

- **Clarification Rate**: % prompt mơ hồ được phát hiện
- **Resolution Efficiency**: % clarification dẫn đến kết quả đúng  
- **Token Efficiency**: tokens trung bình giảm so với baseline
- **User Satisfaction Proxy**: đo bằng test harness

## 7. Tầm quan trọng

- Đây là công nghệ khác biệt giúp StillMe nổi bật so với GPT/Gemini/Claude  
- Tăng trải nghiệm người dùng, tiết kiệm chi phí, nâng cao độ chính xác  

## 8. Roadmap

- **Week 1–2**: Rule-based, toggle quick/careful  
- **Week 3–4**: Context-aware, feedback loop  
- **Week 5–6**: Multi-modal, proactive, enterprise-ready  

## 9. Persona

Clarification luôn giữ giọng điệu "StillMe": lịch sự, khiêm tốn, human-centric  

## 10. Cách sử dụng

### Basic Usage

```python
from stillme_core.modules.clarification_handler import ClarificationHandler

handler = ClarificationHandler()

# Detect ambiguity
result = handler.detect_ambiguity("Write code for this")
if result.needs_clarification:
    print(f"Question: {result.question}")
    print(f"Category: {result.category}")
    print(f"Confidence: {result.confidence}")
```

### Integration với API

```python
# Trong app.py
if clarification_handler:
    clarification_result = clarification_handler.detect_ambiguity(message)
    if clarification_result.needs_clarification:
        return {
            "type": "clarification",
            "question": clarification_result.question,
            "category": "ambiguity_detected"
        }
```

## 11. Test Cases

### Dataset Structure

```csv
id,category,prompt,expected_behavior
1,vague_instruction,"Write code for this","Should ask: What code exactly?"
2,missing_context,"Build an app","Should ask: What type of app?"
3,ambiguous_reference,"Do it now","Should ask: What does 'it' refer to?"
```

### Categories

- **vague_instruction**: "Write code for this", "Make it better"
- **missing_context**: "Build an app", "Create a website"  
- **ambiguous_reference**: "Do it now", "Fix that"
- **fuzzy_goal**: "Make it faster", "Make it smaller"
- **missing_parameter**: "Write a function", "Create a class"
- **slang_informal**: "gimme some code", "hook me up"
- **contextual_dependency**: "do the same thing", "like before"
- **cross_domain**: "analyze this", "process this"

## 12. Performance

### Benchmarks

- **Detection Speed**: < 50ms per prompt
- **Accuracy**: ≥ 80% for ambiguous prompts
- **False Positive Rate**: < 5% for clear prompts
- **Memory Usage**: < 10MB for handler instance

### Load Testing

```bash
# Run load test
python -m pytest tests/test_clarification_handler.py::TestClarificationHandler::test_performance -v
```

## 13. Configuration

### Confidence Threshold

```python
handler = ClarificationHandler()
handler.confidence_threshold = 0.7  # Default: 0.7
```

### Custom Patterns

```python
# Add custom ambiguity patterns
handler.ambiguity_patterns["custom_category"] = [
    r"\b(custom_pattern)\b"
]
```

## 14. Monitoring

### Metrics Collection

```python
stats = handler.get_clarification_stats()
print(f"Patterns loaded: {stats['patterns_loaded']}")
print(f"Categories: {stats['categories']}")
print(f"Templates loaded: {stats['templates_loaded']}")
```

### Logging

```python
import logging
logging.getLogger("clarification_handler").setLevel(logging.INFO)
```

## 15. Troubleshooting

### Common Issues

1. **Import Error**: Ensure `stillme_core` is in Python path
2. **Pattern Not Matching**: Check regex patterns in `ambiguity_patterns`
3. **Performance Issues**: Reduce confidence threshold or optimize patterns

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test specific prompt
result = handler.detect_ambiguity("Write code for this")
print(f"Debug: {result.reasoning}")
```

## 16. Future Enhancements

### Phase 2 Features

- Context-aware clarification
- Learning from user feedback
- Multi-turn clarification dialogue

### Phase 3 Features

- Multi-modal input support
- Proactive suggestions
- Enterprise monitoring

## 17. Contributing

### Adding New Patterns

1. Add pattern to `ambiguity_patterns` in `ClarificationHandler`
2. Add corresponding template to `clarification_templates`
3. Write test cases in `test_clarification_handler.py`
4. Update documentation

### Testing

```bash
# Run all tests
python -m pytest tests/test_clarification_handler.py -v

# Run specific test
python -m pytest tests/test_clarification_handler.py::TestClarificationHandler::test_vague_instruction_detection -v
```

## 18. License

Part of StillMe AI Platform - All rights reserved.

---

**Last Updated**: 2024-01-XX  
**Version**: 1.0.0  
**Status**: Phase 1 Complete
