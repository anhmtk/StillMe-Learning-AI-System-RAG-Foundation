# AgentDev System Overview

## 🎯 Mục tiêu AgentDev

**AgentDev** là một hệ thống AI agent tự động hóa quá trình phát triển phần mềm, thực hiện các tác vụ:
- **Sửa lỗi tự động**: Phân tích lỗi và tạo patch
- **Viết code mới**: Tạo module/feature theo yêu cầu
- **Chạy test**: Thực thi và verify kết quả
- **Tối ưu hóa**: Cải thiện performance và code quality

## 📊 Input/Output

### **Input**
- **Goal**: Mô tả nhiệm vụ (string) - ví dụ: "Fix failing tests", "Add new feature"
- **Max Steps**: Số bước tối đa thực hiện (default: 5)
- **Repo Root**: Đường dẫn repository (default: ".")

### **Output**
- **Summary**: Tóm tắt kết quả thực hiện
- **Steps**: Chi tiết từng bước với status (pass/fail)
- **Pass Rate**: Tỷ lệ thành công (%)
- **Duration**: Thời gian thực hiện

## 🔄 State & Event Loop

### **State Management**
```python
class AgentController:
    def __init__(self, repo_root: str = "."):
        self.planner = Planner()           # Tạo kế hoạch
        self.executor = PatchExecutor()    # Thực thi patch
        self.verifier = Verifier()         # Verify kết quả
        self.repo_root = repo_root
```

### **Event Loop: Plan → Execute → Verify → Report**
1. **Plan**: AI tạo kế hoạch chi tiết từ goal
2. **Execute**: Thực thi từng bước (apply patch, run tests)
3. **Verify**: Kiểm tra kết quả (test pass/fail)
4. **Report**: Tổng hợp và báo cáo kết quả

## 🔗 Tương tác với Framework

### **AI Manager Integration**
- Sử dụng `AIManager` để gọi AI models
- Hỗ trợ multiple providers (OpenAI, DeepSeek, local models)
- Fallback mechanism khi API fail

### **Memory System**
- Tích hợp với `LayeredMemoryV1` để lưu trữ:
  - Bug patterns và solutions
  - Code templates
  - Test results history

### **Ethics & Safety**
- Tương tác với `EthicalCoreSystem` để validate:
  - Code changes có an toàn không
  - Có vi phạm quy tắc nào không
  - Risk assessment

## 🧪 Test Integration

### **Test Execution**
- Chạy `pytest` để verify changes
- Sandbox isolation để tránh ảnh hưởng code chính
- Git branch management cho safe testing

### **Verification Process**
- Parse test output để xác định pass/fail
- Track performance metrics
- Generate detailed reports

## 📁 Core Components

### **1. Controller (`stillme_core/controller.py`)**
- Orchestrates toàn bộ workflow
- Manages state và error handling
- Logging và metrics collection

### **2. Planner (`stillme_core/planner.py`)**
- AI-powered planning với JSON schema validation
- Rule-based fixes cho common errors
- Fallback mechanisms

### **3. Executor (`stillme_core/executor.py`)**
- Apply patches và run commands
- Sandbox management
- Git operations

### **4. Verifier (`stillme_core/verifier.py`)**
- Test result parsing
- Success/failure determination
- Performance tracking

## 🚀 CLI Interface

```bash
# Basic usage
python -m stillme_core.agent_dev --goal "Fix failing tests" --max-steps 3

# With custom repo
python -m stillme_core.agent_dev --goal "Add new feature" --repo-root /path/to/repo

# Verbose output
python -m stillme_core.agent_dev --goal "Run unit tests" --verbose
```

## 📊 Current Status

### **✅ Working Components**
- CLI interface hoạt động
- Basic planning và execution
- Test framework integration
- Logging và metrics

### **⚠️ Known Issues**
- Terminal observation loop cần cải thiện
- Error handling chưa robust
- Test harness cần stabilization
- Router fallback cần enhancement

### **📈 Performance Metrics**
- **Test Pass Rate**: 2/3 tests pass (66.7%)
- **Execution Time**: ~71s cho 1 step
- **Success Rate**: 0% trong test run gần nhất
- **Error Rate**: 100% (tất cả steps fail)

## 🔧 Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI Input     │───▶│  AgentController│───▶│    Planner      │
│  (goal, steps)  │    │                 │    │   (AI-powered)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Verifier      │◀───│   Executor      │◀───│   Plan Items    │
│ (test results)  │    │ (apply patches) │    │   (JSON)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Framework     │
                       │ (Memory, Ethics)│
                       └─────────────────┘
```

## 🎯 Next Steps

1. **Fix terminal-observation loop**: Cải thiện việc đọc và parse terminal output
2. **Stabilize test harness**: Đảm bảo test framework hoạt động ổn định
3. **Enhance error handling**: Robust error recovery và fallback
4. **Improve router fallback**: Better model selection và retry logic
5. **Add safety mechanisms**: Ethics validation và guardrails
