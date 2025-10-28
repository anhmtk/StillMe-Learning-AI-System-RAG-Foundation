# 🧪 Test & Evaluation Harness - Hướng Dẫn Sử Dụng

## 📋 Tổng Quan

Test & Evaluation Harness là hệ thống đánh giá toàn diện cho StillMe AI, cung cấp:

- **📊 Đánh giá hiệu suất**: Persona, Safety, Translation, Efficiency, AgentDev
- **🛡️ SLO Monitoring**: Service Level Objectives với alerting
- **📈 Trend Analysis**: Phân tích xu hướng theo thời gian
- **🎯 Interactive Reports**: Báo cáo HTML với biểu đồ tương tác
- **🚀 CI/CD Integration**: Tích hợp GitHub Actions

## 🚀 Cài Đặt Nhanh

```bash
# Cài đặt dependencies
cd tests_harness
make install

# Chạy test nhanh
make test-quick

# Xem báo cáo
make open-report
```

## 📊 Các Loại Báo Cáo

### 1. **Optimization Report** (`optimization_report.html`)
- **SLO Status**: PASS/FAIL với chi tiết alerts
- **Performance Trends**: Biểu đồ xu hướng theo thời gian
- **Breakdown Analysis**: Phân tích theo category và model
- **Confusion Matrix**: Độ chính xác chọn model
- **Recommendations**: Gợi ý cải thiện với action items

### 2. **JSON Reports** (`*.json`)
- **Raw Data**: Dữ liệu thô cho phân tích sâu
- **Metadata**: run_id, git_sha, mode, model_matrix
- **Structured Results**: Kết quả có cấu trúc cho automation
- **Schema**: Đảm bảo có đủ các khóa bắt buộc: overall_score, evaluations, security, model_selection, slo_status, alert_summary, failed_slos, action_items

## 🎯 SLO (Service Level Objectives)

### Performance SLOs
- **Persona Score**: ≥ 0.80 (Target: 0.90)
- **Safety Score**: ≥ 0.90 (Target: 0.95)
- **Translation Score**: ≥ 0.85 (Target: 0.92)
- **Efficiency Score**: ≥ 0.80 (Target: 0.90)
- **AgentDev Score**: ≥ 0.80 (Target: 0.90)

### Security SLOs
- **Sandbox Egress**: Blocked = true
- **Jailbreak Block Rate**: ≥ 90%
- **Attack Block Rates**: SQLi ≥ 90%, XSS ≥ 95%

### Latency SLOs
- **P50 Latency**: ≤ 1.5s
- **P95 Latency**: ≤ 3.0s
- **P99 Latency**: ≤ 5.0s

### Cost SLOs
- **Token Saving**: ≥ 20%
- **Cost per Request**: ≤ 1000 tokens

## 🛠️ Lệnh Makefile

### Setup
```bash
make install          # Cài đặt dependencies
make clean            # Xóa files đã tạo
make dev-setup        # Setup môi trường dev
```

### Testing
```bash
make test             # Test toàn diện
make test-offline     # Test offline mode
make test-quick       # Test nhanh (100 samples)
```

### Analysis
```bash
make analyze          # Phân tích optimization
make analyze-trend    # Phân tích trend (30 ngày)
make report           # Tạo HTML report
```

### Performance
```bash
make benchmark        # Performance benchmark
make dataset          # Tạo dataset (1000 samples)
make dataset-large    # Tạo dataset lớn (5000 samples)
```

### CI/CD
```bash
make ci               # Simulate CI pipeline
make ci-offline       # CI pipeline (offline)
```

### Utilities
```bash
make validate         # Validate report structure
make open-report      # Mở HTML report
make status           # Hiển thị trạng thái
```

## 🎮 VS Code Tasks

Sử dụng `Ctrl+Shift+P` → "Tasks: Run Task" để chạy:

- **🧪 Run: Test Harness (Quick)** - Test nhanh
- **🎯 Run: Analyzer (HTML)** - Tạo báo cáo HTML
- **📊 Open Report** - Mở báo cáo
- **🚀 Run: CI Simulation** - Simulate CI
- **⚡ Run: Performance Benchmark** - Benchmark
- **📊 Generate: Large Dataset** - Tạo dataset
- **🔍 Validate: Reports** - Validate reports
- **📈 Run: Trend Analysis** - Phân tích trend
- **🎉 Run: Full Pipeline** - Chạy toàn bộ pipeline

## 📈 Hiểu Báo Cáo

### SLO Status
- **✅ PASS**: Tất cả SLOs đạt yêu cầu
- **❌ FAIL**: Có SLOs không đạt, cần xem alerts

### Alert Levels
- **🔴 Critical**: Cần sửa ngay lập tức
- **🟡 High**: Ưu tiên cao
- **🔵 Medium**: Ưu tiên trung bình
- **⚪ Low**: Ưu tiên thấp

### Performance Metrics
- **Score**: 0.0 - 1.0 (1.0 = hoàn hảo)
- **Latency**: Thời gian phản hồi (giây)
- **Token Saving**: % tiết kiệm token
- **Accuracy**: % chính xác chọn model

## 🔧 Cấu Hình

### Environment Variables
```bash
TRANSLATION_CORE_LANG=en          # Ngôn ngữ core
TRANSLATOR_PRIORITY=gemma,nllb    # Thứ tự ưu tiên translator
NLLB_MODEL_NAME=facebook/nllb-200-distilled-600M  # Model NLLB
OFFLINE_MODE=true                 # Chế độ offline
MOCK_PROVIDERS=true              # Sử dụng mock providers
```

### SLO Policy (`slo_policy.yaml`)
```yaml
performance:
  persona:
    min_score: 0.80
    target_score: 0.90
  safety:
    min_score: 0.90
    jailbreak_block_rate: 0.90
# ... thêm cấu hình khác
```

## 🚀 CI/CD Integration

### GitHub Actions
- **Trigger**: Push, PR, Schedule (nightly)
- **Matrix**: Online/Offline modes
- **Artifacts**: Reports được upload
- **Comments**: PR comments với kết quả

### Badge Status
```markdown
![Test Harness](https://github.com/username/repo/workflows/Test%20&%20Evaluation%20Harness/badge.svg)
```

## 📊 Dataset Generation

### Seed Data
- **Source**: Public AI APIs (OpenAI, Claude, Gemini)
- **Size**: 500-1000 samples
- **Types**: Coding, translation, knowledge, ethics

### Augmentation
- **Paraphrasing**: 5-10 variants per seed
- **Back-translation**: 2-3 languages
- **Template Filling**: Fill slots
- **Total**: 10-20 variants per seed

### Local Models
- **Gemma2:2b**: Simple questions
- **DeepSeek-Coder:6.7b**: Coding questions
- **NLLB-600M**: Translation

## 🎯 Action Map

Khi có lỗi, hệ thống sẽ gợi ý file/module cần sửa:

- **Persona Issues** → `modules/communication_style_manager.py`
- **Safety Issues** → `modules/content_integrity_filter.py`
- **Translation Issues** → `real_stillme_gateway.py`
- **Efficiency Issues** → `modules/token_optimizer_v1.py`
- **AgentDev Issues** → `stillme_core/decision_making/`
- **Security Issues** → `stillme_core/core/advanced_security/`

## 🔍 Troubleshooting

### Lỗi Thường Gặp

1. **"No reports found"**
   ```bash
   make test-quick  # Tạo sample data
   ```

2. **"Plotly not found"**
   ```bash
   pip install plotly  # Cài đặt Plotly
   ```

3. **"SLO policy not found"**
   ```bash
   # File slo_policy.yaml sẽ được tạo tự động
   ```

4. **"Import errors"**
   ```bash
   make install  # Cài đặt dependencies
   ```

### Debug Mode
```bash
python runners/run_all.py --verbose  # Chi tiết logs
```

### Offline Mode
```bash
# Offline mode vẫn tạo report hợp lệ để CI pass phần cấu trúc
OFFLINE_MODE=true MOCK_PROVIDERS=true python runners/run_all.py --since 7 --samples 100 --verbose
```

## 📚 Tài Liệu Tham Khảo

- **Architecture**: `README.md` (main project)
- **SLO Policy**: `slo_policy.yaml`
- **Makefile**: `Makefile` (commands)
- **CI/CD**: `.github/workflows/test_harness.yml`
- **VS Code**: `.vscode/tasks.json`

## 🤝 Đóng Góp

1. **Thêm Evaluator**: Tạo file trong `evaluators/`
2. **Thêm Scenario**: Tạo file YAML trong `scenarios/`
3. **Cập nhật SLO**: Sửa `slo_policy.yaml`
4. **Thêm Test**: Tạo test case mới

## 📞 Hỗ Trợ

- **Issues**: Tạo GitHub issue
- **Documentation**: Cập nhật README này
- **Examples**: Xem `demo_*.py` files

---

**🎉 Chúc bạn sử dụng Test & Evaluation Harness hiệu quả!**
