# 📚 HƯỚNG DẪN SỬ DỤNG ENHANCED AGENTDEV

## 🚀 Cách sử dụng cơ bản

### 1. Chạy Enhanced AgentDev
```bash
python enhanced_agentdev.py
```

### 2. Sử dụng trong code
```python
from enhanced_agentdev import EnhancedAgentDev

# Tạo AgentDev
agent = EnhancedAgentDev()

# Bắt đầu phiên làm việc
session = agent.start_work_session("Sửa lỗi code")

# Sửa lỗi
result = agent.fix_errors(session)

# Kết thúc phiên làm việc
agent.end_work_session(session, result)
```

### 3. Sử dụng với validation system
```python
from agentdev_validation_system import AgentDevValidator
from agentdev_honest import HonestAgentDev

# Tạo validator
validator = AgentDevValidator()

# Validation trước khi sửa
before_data = validator.validate_before_fix()

# Thực hiện sửa lỗi...

# Validation sau khi sửa
result = validator.validate_after_fix(before_data)

# Tạo báo cáo
report = validator.generate_report(result)
```

## 🔍 Tính năng chính

### 1. Bằng chứng trước/sau
- Tự động tạo file JSON chứa bằng chứng
- Lưu trữ trạng thái trước và sau khi sửa
- Có thể kiểm tra lại bất kỳ lúc nào

### 2. Phân loại lỗi
- **Lỗi nghiêm trọng**: Code không chạy được (ưu tiên cao nhất)
- **Cảnh báo**: Code chạy được nhưng có vấn đề tiềm ẩn (ưu tiên trung bình)
- **Gợi ý style**: Về mặt thẩm mỹ và chuẩn coding (ưu tiên thấp nhất)

### 3. Kiểm tra tự động
- Chạy pyright và ruff sau mỗi lần sửa
- Kiểm tra code không bị break
- Tự động tạo báo cáo

### 4. Ưu tiên chất lượng
- Quy tắc: 1 lỗi quan trọng > 100 lỗi vặt
- Tính điểm chất lượng dựa trên mức độ nghiêm trọng
- Tự động dừng khi đạt mức chất lượng tốt

## 📊 Báo cáo

### 1. Báo cáo validation
- File JSON chứa bằng chứng
- File Markdown chứa báo cáo chi tiết
- Thống kê lỗi trước/sau

### 2. Báo cáo phiên làm việc
- Session ID duy nhất
- Thời gian thực hiện
- Danh sách sửa chữa
- Điểm chất lượng

## 🔒 Cam kết trung thực

1. **Bằng chứng cụ thể**: Mọi thay đổi đều có bằng chứng
2. **Không báo cáo sai**: Số liệu luôn chính xác
3. **Ưu tiên chất lượng**: Chất lượng hơn số lượng
4. **Tuân thủ quy tắc**: 1 lỗi quan trọng > 100 lỗi vặt

## 🛠️ Troubleshooting

### Lỗi thường gặp
1. **Pyright timeout**: Tăng timeout trong code
2. **Ruff không tìm thấy**: Kiểm tra PATH
3. **File không tồn tại**: Kiểm tra đường dẫn

### Giải pháp
1. Restart IDE
2. Kiểm tra dependencies
3. Chạy từ project root

## 📞 Hỗ trợ

Nếu gặp vấn đề, hãy:
1. Kiểm tra log files
2. Xem báo cáo validation
3. Liên hệ để được hỗ trợ
