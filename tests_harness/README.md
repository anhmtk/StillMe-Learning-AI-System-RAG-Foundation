# 🧪 StillMe Test & Evaluation Harness

Hệ thống Test & Evaluation Harness toàn diện cho StillMe AI, có khả năng sinh bộ dữ liệu kiểm thử cực đa dạng (10k–100k mẫu) bằng cách dùng AI public để tạo seed nhỏ rồi mở rộng offline bằng local model.

## 📋 Tổng Quan

### 🎯 Mục Tiêu
- **Sinh dữ liệu test đa dạng**: 10k-100k mẫu từ 500-1000 seed
- **Tiết kiệm chi phí**: Chỉ dùng API public cho seed, phần lớn offline
- **Đánh giá toàn diện**: Persona, Safety, Translation, Security, Performance
- **Tích hợp với StillMe**: Không thay đổi kiến trúc lõi

### 🏗️ Kiến Trúc
```
tests_harness/
├── scenarios/            # Kịch bản YAML (persona, ethics, translation…)
├── datasets/
│   ├── seed/            # Dữ liệu seed nhỏ (jsonl)
│   └── augmented/       # Dữ liệu sau khi mở rộng (jsonl/parquet)
├── augmentor/
│   ├── paraphraser.py   # Tạo biến thể câu
│   ├── backtranslate.py # Dịch qua lại để tạo biến thể
│   ├── template_filler.py # Sinh biến thể từ template slot
│   └── augment_runner.py # Script gom seed -> augmented
├── evaluators/          # Scoring, safety, token cost, latency
├── runners/             # run_all, run_subset, report builder
└── reports/             # Kết quả (json/html)
```

## 🚀 Quick Start

### 1. Tạo Seed Data
```bash
# Sinh 1000 seed từ AI public APIs
python seed_generator.py

# Hoặc sử dụng sample seeds có sẵn
cp datasets/seed/sample_seeds.jsonl datasets/seed/my_seeds.jsonl
```

### 2. Chạy Augmentation
```bash
# Augment với tất cả methods
python augmentor/augment_runner.py \
  --seed-file datasets/seed/my_seeds.jsonl \
  --output-dir datasets/augmented \
  --methods paraphrase backtranslate template_fill \
  --max-seeds 1000

# Hoặc chạy demo
python demo_augmentation.py
```

### 3. Xem Kết Quả
```bash
# Xem file kết quả
ls -la datasets/augmented/
cat datasets/augmented/augmented_combined.jsonl | head -10
```

## 🔧 Cấu Hình

### Augmentation Methods

#### 1. Paraphrase
- **Mô tả**: Dùng Gemma/Llama để viết lại câu thành 5-10 biến thể
- **Cấu hình**: `ParaphraseConfig`
- **Output**: Biến thể giữ nguyên ý nghĩa, thay đổi cách diễn đạt

#### 2. Backtranslate
- **Mô tả**: Dùng NLLB dịch sang 2-3 ngôn ngữ rồi dịch ngược
- **Cấu hình**: `BacktranslateConfig`
- **Output**: Biến thể qua translation, tạo đa dạng ngôn ngữ

#### 3. Template Fill
- **Mô tả**: Thay thế placeholder trong template bằng nhiều giá trị
- **Cấu hình**: `TemplateConfig`
- **Output**: Biến thể từ template, đảm bảo cấu trúc

### Scenarios

#### Persona Scenarios
- **Mục đích**: Kiểm tra xưng hô, phong cách giao tiếp
- **File**: `scenarios/persona_scenarios.yaml`
- **Test cases**: Formal/casual addressing, family/professional contexts

#### Safety Scenarios
- **Mục đích**: Kiểm tra an toàn và đạo đức
- **File**: `scenarios/safety_scenarios.yaml`
- **Test cases**: Harmful content, jailbreak attempts, PII protection

#### Translation Scenarios
- **Mục đích**: Kiểm tra khả năng dịch thuật
- **File**: `scenarios/translation_scenarios.yaml`
- **Test cases**: Language detection, translation accuracy, cultural adaptation

## 📊 Evaluation Rubrics

### 1. PersonaEval
- **Xưng hô chính xác**: Độ chính xác trong xưng hô (anh/em, thầy/cô, etc.)
- **Phong cách giao tiếp**: Tone consistency, politeness level
- **Thích ứng văn hóa**: Vietnamese cultural norms, age-appropriate addressing

### 2. SafetyEval
- **Phản hồi an toàn**: Refusal rate cho harmful content, appropriate redirection
- **Duy trì ranh giới**: Jailbreak resistance, identity consistency
- **Hướng dẫn đạo đức**: Bias challenge, equality promotion

### 3. TranslationEval
- **Phát hiện ngôn ngữ**: Correct language identification, confidence accuracy
- **Chất lượng dịch thuật**: Semantic accuracy, grammatical correctness
- **Tính phù hợp văn hóa**: Cultural adaptation, formality matching

### 4. EfficiencyEval
- **Token usage**: Đo token consumption, cost estimation
- **Latency**: Response time measurement
- **Context optimization**: Context shortening effectiveness

### 5. AgentDevEval
- **Coding tasks**: Success rate cho programming tasks
- **Debug tasks**: Debugging accuracy
- **Learning tasks**: Self-learning effectiveness

### 6. SecurityEval
- **Sandbox testing**: Red/Blue Team simulation
- **Vulnerability detection**: SQLi, XSS, etc.
- **Defense verification**: Security measure effectiveness

## 🛠️ Advanced Usage

### Custom Templates
```python
from augmentor.template_filler import Template, TemplateSlot

# Tạo custom template
custom_template = Template(
    name="custom_greeting",
    template="[GREETING] [ROLE], [TIME] [QUESTION]?",
    slots=[
        TemplateSlot("GREETING", "greeting", ["Xin chào", "Chào", "Hi"]),
        TemplateSlot("ROLE", "role", ["bạn", "anh", "chị"]),
        # ...
    ]
)

# Sử dụng trong augmentation
augmentor = TemplateFillerAugmentor()
await augmentor.augment_from_templates("output.jsonl", [custom_template])
```

### Custom Scenarios
```yaml
# scenarios/custom_scenarios.yaml
name: "Custom Test Scenarios"
scenarios:
  - name: "my_test"
    description: "Custom test case"
    test_cases:
      - input: "Test input"
        expected_behavior: "expected_output"
        weight: 0.5
```

### Batch Processing
```bash
# Xử lý nhiều file seed
for seed_file in datasets/seed/*.jsonl; do
  python augmentor/augment_runner.py \
    --seed-file "$seed_file" \
    --output-dir "datasets/augmented/$(basename $seed_file .jsonl)" \
    --methods paraphrase backtranslate
done
```

## 📈 Performance Metrics

### Expected Results
- **Seed to Augmented Ratio**: 1:10 to 1:20 (1 seed → 10-20 variants)
- **Processing Speed**: ~100-500 seeds/minute (depending on model)
- **Success Rate**: >90% for paraphrase, >80% for backtranslate
- **Cost**: <$10 for 1000 seeds (API costs only)

### Optimization Tips
1. **Batch Processing**: Process seeds in batches of 10-20
2. **Model Selection**: Use faster local models for paraphrase
3. **Parallel Processing**: Run multiple methods in parallel
4. **Caching**: Cache translation results for repeated phrases

## 🔍 Troubleshooting

### Common Issues

#### 1. API Rate Limits
```python
# Add delays between requests
import asyncio
await asyncio.sleep(1)  # 1 second delay
```

#### 2. Memory Issues
```python
# Process in smaller batches
config.max_seed_size = 100  # Reduce batch size
```

#### 3. Model Not Available
```python
# Fallback to mock mode
config.use_ai_generation = False  # Use predefined slots only
```

### Debug Mode
```bash
# Enable verbose logging
python augmentor/augment_runner.py --verbose --seed-file input.jsonl --output-dir output/
```

## 📚 API Reference

### Core Classes

#### `AugmentRunner`
- **Purpose**: Main orchestrator for augmentation pipeline
- **Methods**: `run_augmentation()`, `print_stats()`

#### `ParaphraseAugmentor`
- **Purpose**: Generate paraphrased variants
- **Methods**: `augment_dataset()`, `paraphrase_text()`

#### `BacktranslateAugmentor`
- **Purpose**: Generate variants through translation
- **Methods**: `augment_dataset()`, `backtranslate_text()`

#### `TemplateFillerAugmentor`
- **Purpose**: Generate variants from templates
- **Methods**: `augment_from_templates()`, `fill_template()`

### Configuration Classes

#### `AugmentConfig`
- **Fields**: `seed_file`, `output_dir`, `use_paraphrase`, etc.

#### `ParaphraseConfig`
- **Fields**: `model`, `num_variants`, `temperature`, etc.

#### `BacktranslateConfig`
- **Fields**: `intermediate_languages`, `max_rounds`, etc.

#### `TemplateConfig`
- **Fields**: `num_variants_per_template`, `use_ai_generation`, etc.

## 🤝 Contributing

### Adding New Augmentation Methods
1. Create new module in `augmentor/`
2. Implement `Augmentor` interface
3. Add to `AugmentRunner`
4. Update configuration classes
5. Add tests and documentation

### Adding New Scenarios
1. Create YAML file in `scenarios/`
2. Define test cases and evaluation criteria
3. Implement evaluator in `evaluators/`
4. Add to main runner

### Adding New Evaluators
1. Create evaluator class in `evaluators/`
2. Implement scoring methods
3. Add to evaluation pipeline
4. Update reporting system

## 📄 License

This project is part of StillMe AI Framework and follows the same license terms.

## 🙏 Acknowledgments

- StillMe AI Framework team
- Open source AI models (Gemma, Llama, NLLB)
- Translation and NLP communities
