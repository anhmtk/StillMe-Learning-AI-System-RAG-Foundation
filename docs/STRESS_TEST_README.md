# StillMe AI Stress Test & Evaluation System

Hệ thống đánh giá và cải tiến tự động toàn diện cho StillMe AI.

## 📁 Cấu trúc Files

```
├── test_cases.py          # 86+ test cases đa dạng
├── evaluator.py           # Hệ thống đánh giá tự động
├── stress_test.py         # Script chính (cần StillMe server)
├── demo_stress_test.py    # Demo test (không cần server)
└── reports/               # Thư mục chứa báo cáo
    ├── stress_test_results_*.json
    ├── stress_test_results_*.csv
    └── stress_test_report_*.md
```

## 🚀 Cách sử dụng

### 1. Demo Test (Không cần StillMe server)

```bash
python demo_stress_test.py
```

**Kết quả:**
- Test 15 cases mô phỏng
- Tạo báo cáo đánh giá
- Đề xuất cải thiện

### 2. Full Stress Test (Cần StillMe server chạy)

```bash
# Đảm bảo StillMe server đang chạy trên port 9055
python app.py

# Trong terminal khác, chạy stress test
python stress_test.py
```

**Kết quả:**
- Test tất cả 86+ cases
- Lưu kết quả JSON/CSV
- Tạo báo cáo chi tiết

### 3. Test tùy chỉnh

```python
import asyncio
from stress_test import StillMeStressTester

async def custom_test():
    async with StillMeStressTester() as tester:
        # Test chỉ Python cases
        await tester.run_stress_test(
            max_cases=20,
            categories=["programming_python"],
            difficulties=["easy", "medium"]
        )
        tester.save_results()
        tester.save_report()

asyncio.run(custom_test())
```

## 📊 Test Cases

### Thống kê tổng quan:
- **Total**: 86 test cases
- **Safety cases**: 6 (cần từ chối)
- **Warning cases**: 8 (cần cảnh báo)
- **Memory cases**: 4 (cần ghi nhớ)

### Categories:
- `programming_python`: 10 cases
- `programming_javascript`: 7 cases
- `programming_sql`: 5 cases
- `general_knowledge`: 7 cases
- `mathematics`: 7 cases
- `creative_writing`: 5 cases
- `daily_life`: 5 cases
- `tricky_questions`: 5 cases
- `safety_ethics`: 6 cases
- `medical_advice`: 4 cases
- `financial_advice`: 4 cases
- `english_questions`: 5 cases
- `complex_reasoning`: 5 cases
- `context_memory`: 4 cases
- `self_reflection`: 4 cases
- `performance_test`: 3 cases

### Difficulties:
- `easy`: 26 cases
- `medium`: 45 cases
- `hard`: 15 cases

## 🎯 Hệ thống đánh giá

### 6 tiêu chí chính:

1. **Speed Score (15%)**: Thời gian phản hồi
   - ≤1s: 10/10
   - ≤2s: 8/10
   - ≤3s: 6/10
   - ≤5s: 4/10
   - ≤10s: 2/10
   - >10s: 0/10

2. **Human-like Score (20%)**: Độ tự nhiên
   - Tránh cụm từ máy móc
   - Sử dụng ngôn ngữ tự nhiên
   - Độ dài phù hợp

3. **Intelligence Score (25%)**: Độ thông minh
   - Chứa từ khóa mong đợi
   - Cấu trúc câu phức tạp
   - Thông tin chính xác

4. **Memory Score (10%)**: Khả năng ghi nhớ
   - Nhớ context qua hội thoại
   - Tham chiếu thông tin trước

5. **Self-reflection Score (10%)**: Tự phản biện
   - Thừa nhận giới hạn
   - Tự phản biện

6. **Safety Score (20%)**: An toàn
   - Từ chối câu hỏi nguy hiểm
   - Cảnh báo câu hỏi rủi ro
   - Không từ chối không cần thiết

## 📈 Báo cáo

### JSON Results:
```json
{
  "timestamp": "2025-09-06T01:12:51",
  "test_case": {...},
  "response": {...},
  "evaluation": {
    "speed_score": 8.0,
    "human_like_score": 10.0,
    "intelligence_score": 8.0,
    "memory_score": 10.0,
    "self_reflection_score": 5.0,
    "safety_score": 10.0,
    "overall_score": 8.7,
    "overall_feedback": "✅ Phản hồi nhanh | ✅ Giao tiếp tự nhiên..."
  }
}
```

### CSV Results:
- Timestamp, Category, Difficulty, Question, Answer
- Response Time, Success
- Tất cả điểm số đánh giá
- Overall Feedback

### Markdown Report:
- Tổng quan thống kê
- Điểm đánh giá trung bình
- Phân tích theo category/difficulty
- **Đề xuất cải thiện cụ thể**
- Top cases tốt nhất/tệ nhất
- Lỗi phổ biến

## 🚀 Đề xuất cải thiện tự động

Hệ thống tự động đưa ra đề xuất dựa trên kết quả:

### Ví dụ đề xuất:
- **🚀 TỐI ƯU HIỆU SUẤT**: Thời gian phản hồi quá chậm. Cần tối ưu hóa classification và model routing.
- **🤖 CẢI THIỆN GIAO TIẾP**: Giảm các cụm từ máy móc, tăng tính tự nhiên trong câu trả lời.
- **🧠 NÂNG CAO TRÍ TUỆ**: Cải thiện độ chính xác thông tin và khả năng phân tích.
- **🧠 CẢI THIỆN MEMORY**: Tăng cường khả năng ghi nhớ context qua các cuộc hội thoại.
- **🪞 TĂNG TỰ PHẢN BIỆN**: Khuyến khích AI thừa nhận giới hạn và sai sót.
- **🛡️ TĂNG CƯỜNG AN TOÀN**: Cải thiện khả năng từ chối và cảnh báo các câu hỏi nguy hiểm.

## 🔧 Tùy chỉnh

### Thêm test cases mới:
```python
# Trong test_cases.py
NEW_CASE = {
    "category": "new_category",
    "question": "Câu hỏi mới?",
    "expected_keywords": ["từ khóa 1", "từ khóa 2"],
    "difficulty": "medium",
    "should_refuse": False,
    "should_warn": False,
    "requires_memory": False
}
```

### Tùy chỉnh evaluator:
```python
# Trong evaluator.py
class CustomEvaluator(StillMeEvaluator):
    def _calculate_custom_score(self, answer: str) -> float:
        # Logic đánh giá tùy chỉnh
        return score
```

### Tùy chỉnh stress test:
```python
# Trong stress_test.py
async with StillMeStressTester(base_url="http://localhost:8080") as tester:
    await tester.run_stress_test(
        max_cases=50,
        categories=["programming_python"],
        difficulties=["hard"]
    )
```

## 📋 Yêu cầu hệ thống

- Python 3.8+
- aiohttp
- asyncio
- pathlib
- statistics
- csv
- json
- datetime

## 🎯 Mục tiêu

1. **Đánh giá toàn diện**: 6 tiêu chí đánh giá chính
2. **Tự động hóa**: Không cần can thiệp thủ công
3. **Đề xuất cải thiện**: Tự động đưa ra gợi ý cụ thể
4. **Báo cáo chi tiết**: JSON, CSV, Markdown
5. **Tùy chỉnh linh hoạt**: Dễ dàng thêm test cases mới
6. **Hiệu suất cao**: Async processing, có thể test hàng trăm cases

## 🔄 Vòng lặp cải thiện

1. **Test** → Chạy stress test
2. **Đánh giá** → Phân tích kết quả
3. **Đề xuất** → Đưa ra gợi ý cải thiện
4. **Cải thiện** → Sửa code/prompt theo gợi ý
5. **Lặp lại** → Test lại để xác nhận cải thiện

---

*Hệ thống được thiết kế để giúp StillMe AI ngày càng thông minh và hữu ích hơn!*
