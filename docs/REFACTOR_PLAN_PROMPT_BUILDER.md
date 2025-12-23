# Refactor Plan: Configuration-Driven Prompt Builder

## Vấn Đề Hiện Tại

1. **`prompt_builder.py` quá dài**: 1,927 dòng
2. **Hardcoded instructions**: 228 lần "CRITICAL/MANDATORY"
3. **Pattern matching rải rác**: 17 patterns cho validator count
4. **Approach reactive**: "Cầm cây đi dò nước lũ" - fix từng issue một
5. **Không scalable**: Mỗi issue mới = thêm code vào file khổng lồ

## Giải Pháp: Configuration-Driven Architecture

### Phase 1: Tách Instructions Ra Config Files

```
backend/identity/
├── instructions/
│   ├── __init__.py
│   ├── validator_count.yaml      # Instructions cho validator count questions
│   ├── stillme_technical.yaml    # Instructions cho StillMe technical queries
│   ├── philosophical.yaml        # Instructions cho philosophical questions
│   ├── citation.yaml             # Citation rules
│   └── anti_hallucination.yaml   # Anti-hallucination rules
├── prompt_builder.py             # Chỉ còn logic, không có hardcoded text
└── instruction_loader.py        # Load và merge instructions từ YAML
```

### Phase 2: Rule Engine Thay Vì Pattern Matching

```python
# Thay vì:
if "bao nhiêu" in question and "lớp" in question and "validator" in question:
    # hardcoded instruction

# Dùng:
rule_engine = RuleEngine()
rule_engine.add_rule(
    pattern="validator_count",
    matcher=ValidatorCountMatcher(),
    instruction="instructions/validator_count.yaml"
)
```

### Phase 3: Data-Driven Approach

```yaml
# instructions/validator_count.yaml
detection:
  patterns:
    - "bao nhiêu.*lớp.*validator"
    - "how many.*layer.*validator"
  priority: P1_CRITICAL

instruction:
  vi: |
    Hệ thống của tôi có **19 validators total, chia thành 7 lớp (layers) validation framework**.
    ...
  en: |
    My system has **19 validators total, organized into 7 layers (validation framework layers)**.
    ...

metadata:
  version: "1.0"
  last_updated: "2025-12-21"
  author: "system"
```

### Phase 4: Testing & Versioning

```python
# tests/test_instructions.py
def test_validator_count_instruction():
    loader = InstructionLoader()
    instruction = loader.get_instruction("validator_count", lang="vi")
    assert "19 validators" in instruction
    assert "7 lớp" in instruction
```

## Lợi Ích

1. **Maintainability**: Dễ sửa instructions (chỉ cần edit YAML)
2. **Scalability**: Thêm instruction mới = thêm file YAML, không cần sửa code
3. **Testability**: Unit test từng instruction type
4. **Versioning**: Track changes qua Git
5. **Collaboration**: Non-technical team có thể edit instructions
6. **Performance**: Load instructions once, cache trong memory

## Migration Path

1. **Week 1**: Tạo structure, migrate 1 instruction type (validator_count)
2. **Week 2**: Migrate remaining instruction types
3. **Week 3**: Remove hardcoded instructions từ prompt_builder.py
4. **Week 4**: Add tests và documentation

## Team Dev Chuyên Nghiệp Sẽ Làm Gì?

1. **Separation of Concerns**: Logic vs Content
2. **Configuration Management**: YAML/JSON config files
3. **Rule Engine**: Dùng library như `pyknow` hoặc custom engine
4. **Testing**: Unit tests cho từng instruction
5. **Documentation**: Swagger/OpenAPI cho instruction schema
6. **CI/CD**: Validate YAML syntax trong CI pipeline
7. **Monitoring**: Track instruction usage và effectiveness

## Kết Luận

Approach hiện tại (hardcode trong Python) là **technical debt** cần refactor. Configuration-driven approach là **best practice** cho LLM applications.

