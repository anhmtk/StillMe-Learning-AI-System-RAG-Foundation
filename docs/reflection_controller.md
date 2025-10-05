# Reflection Controller Documentation
# Tài liệu Reflection Controller

## Overview / Tổng quan

Reflection Controller là một hệ thống phản tư có giới hạn (bounded reflection) được thiết kế để nâng cao chất lượng phản hồi của StillMe AI thông qua tối ưu đa mục tiêu và bảo vệ thông tin nội bộ.

## Features / Tính năng

### 🎯 Multi-Objective Optimization / Tối ưu đa mục tiêu
- **Relevance / Độ liên quan** (45%): Mức độ phản hồi trả lời câu hỏi
- **Safety / An toàn** (20%): Tuân thủ chính sách và bảo mật
- **Clarity / Độ rõ ràng** (15%): Cấu trúc và khả năng đọc
- **Brevity / Tính ngắn gọn** (10%): Hiệu quả và súc tích
- **Helpfulness / Tính hữu ích** (10%): Khả năng hành động

### 🛡️ Security & Privacy / Bảo mật và quyền riêng tư
- **Secrecy Filter**: Tự động lọc thông tin nội bộ
- **Policy Responses**: Phản hồi tuân thủ chính sách cho câu hỏi nhạy cảm
- **Keyword Blocking**: Chặn từ khóa kiến trúc nội bộ
- **Content Sanitization**: Làm sạch nội dung trước khi xuất

### ⚡ Performance Optimization / Tối ưu hiệu suất
- **Bounded Reflection**: Giới hạn số bước phản tư
- **Early Stopping**: Dừng sớm khi cải thiện không đáng kể
- **Timeout Protection**: Bảo vệ khỏi vòng lặp vô hạn
- **Budget Management**: Quản lý ngân sách token và thời gian

## Usage / Sử dụng

### Basic Usage / Sử dụng cơ bản

```python
from stillme_core.reflection_controller import get_default_controller

# Get controller instance
controller = get_default_controller()

# Check if reflection should be applied
if controller.should_reflect(user_query):
    # Enhance response
    result = await controller.enhance_response(original_response, user_query)
    enhanced_response = result.final_response
```

## Configuration / Cấu hình

### Reflection Modes / Chế độ phản tư

#### Fast Mode / Chế độ nhanh
- **Max Steps**: 2
- **Timeout**: 8 seconds
- **Tokens**: 900
- **Use case**: Quick responses, simple queries

#### Normal Mode / Chế độ bình thường
- **Max Steps**: 3
- **Timeout**: 15 seconds
- **Tokens**: 1400
- **Use case**: Balanced quality and speed

#### Deep Mode / Chế độ sâu
- **Max Steps**: 4
- **Timeout**: 30 seconds
- **Tokens**: 2200
- **Use case**: High-quality responses, complex queries

## Security / Bảo mật

### Protected Information / Thông tin được bảo vệ
- **Internal architecture**: Kiến trúc nội bộ
- **API keys and secrets**: API keys và secrets
- **Configuration details**: Chi tiết cấu hình
- **Development tools**: Công cụ phát triển
- **System internals**: Nội bộ hệ thống

### Policy Responses / Phản hồi chính sách

Khi phát hiện câu hỏi về kiến trúc nội bộ, hệ thống sẽ trả về phản hồi chính sách:

```
Tôi là StillMe, một AI được tạo bởi Anh Nguyễn với sự hỗ trợ từ các tổ chức AI hàng đầu như OpenAI, Google, DeepSeek. Mục đích của tôi là đồng hành và kết bạn với mọi người. Tôi không thể chia sẻ chi tiết về kiến trúc nội bộ, nhưng tôi có thể giúp bạn với các câu hỏi khác!
```

## Testing / Kiểm thử

### Running Tests / Chạy kiểm thử

```bash
# Run all tests
python scripts/run_reflection_tests.py

# Run specific test file
python -m pytest tests/test_reflection_controller.py -v

# Run with timeout
python -m pytest tests/test_reflection_integration.py --timeout=120 -v
```

## Performance / Hiệu suất

### Benchmarks / Điểm chuẩn

| Mode | Avg Time | Max Steps | Token Limit | Use Case |
|------|----------|-----------|-------------|----------|
| Fast | 2-5s | 2 | 900 | Quick responses |
| Normal | 5-15s | 3 | 1400 | Balanced quality |
| Deep | 15-30s | 4 | 2200 | High quality |

## Troubleshooting / Khắc phục sự cố

### Common Issues / Vấn đề thường gặp

#### 1. Reflection not applied / Phản tư không được áp dụng
**Cause**: Query doesn't meet reflection criteria
**Solution**: Check `should_reflect()` logic and query characteristics

#### 2. Performance issues / Vấn đề hiệu suất
**Cause**: Too many reflection steps or long timeouts
**Solution**: Adjust configuration parameters or use faster mode

#### 3. Security violations / Vi phạm bảo mật
**Cause**: Content contains blocked keywords
**Solution**: Review content and remove sensitive information

## License / Giấy phép

This project is part of StillMe AI Framework and follows the same license terms.

Dự án này là một phần của StillMe AI Framework và tuân theo cùng điều khoản giấy phép.
