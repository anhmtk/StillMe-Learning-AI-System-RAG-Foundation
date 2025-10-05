# Dynamic Communication Style for StillMe AI

## Tổng quan

StillMe AI đã được cập nhật để hỗ trợ **Dynamic Communication Style** thay vì xưng hô cứng "anh/em". Hệ thống mới cho phép:

1. **User Override**: Người dùng có thể yêu cầu thay đổi xưng hô qua headers hoặc tin nhắn
2. **Memory-based Preferences**: Lưu trữ sở thích xưng hô của người dùng
3. **Neutral Defaults**: Mặc định sử dụng "mình/bạn" thay vì "anh/em"
4. **Runtime Detection**: Tự động phát hiện yêu cầu thay đổi xưng hô trong hội thoại

## Các thay đổi chính

### 1. Loại bỏ xưng hô cứng

**Trước:**
```python
system_prompt = """Bạn là StillMe AI...
Quy tắc giao tiếp:
- Luôn gọi người dùng là "anh" (viết tắt là "a")
- Luôn xưng "em" với người dùng
..."""
```

**Sau:**
```python
system_prompt = compose_system_prompt(base_identity, comms_prefs)
# Tự động tạo prompt với xưng hô linh hoạt
```

### 2. Module mới

#### `stillme_core/common/comms_style_policy.py`
- `CommsPrefs`: Dataclass lưu trữ preferences
- `resolve_prefs()`: Ưu tiên override → memory → default
- `detect_communication_override()`: Phát hiện yêu cầu thay đổi trong tin nhắn
- `update_prefs_from_message()`: Cập nhật preferences từ tin nhắn

#### `stillme_core/common/system_prompt_builder.py`
- `compose_system_prompt()`: Tạo system prompt động
- `get_base_identity()`: Lấy base identity không có xưng hô cứng

### 3. Gateway hỗ trợ headers

Gateway giờ nhận các headers:
- `X-Preferred-Name`: Tên ưa thích (ví dụ: "chị Mai")
- `X-Preferred-Pronoun-Self`: Xưng của AI (ví dụ: "em", "tôi", "mình")
- `X-Preferred-Pronoun-User`: Gọi người dùng (ví dụ: "anh", "chị", "bạn")
- `X-Tone`: Giọng điệu (ví dụ: "thân thiện", "trang trọng")

### 4. Runtime Override Detection

Hệ thống tự động phát hiện các pattern:
- "hãy gọi tôi là [name]"
- "hãy xưng là [pronoun]"
- "gọi tôi là [pronoun]"
- "đừng gọi tôi là [pronoun]"

## Cách sử dụng

### 1. API với headers

```bash
curl -X POST http://localhost:21568/send-message \
  -H "Content-Type: application/json" \
  -H "X-Preferred-Pronoun-User: chị" \
  -H "X-Preferred-Pronoun-Self: em" \
  -d '{"message":"xin chào","language":"vi"}'
```

### 2. Runtime override trong tin nhắn

```
User: "hãy gọi tôi là chị Mai và xưng là em"
AI: "Chào chị Mai! Em rất vui được gặp chị..."
```

### 3. Default neutral

```
User: "xin chào"
AI: "Chào bạn! Mình rất vui được gặp bạn..."
```

## Tests

Module đã được test với:
- Default neutral preferences
- Memory-based preferences
- User override preferences
- Runtime override detection
- System prompt composition

## Lợi ích

1. **Linh hoạt**: Người dùng có thể chọn xưng hô phù hợp
2. **Tôn trọng**: Không ép buộc xưng hô cứng
3. **Trung tính**: Mặc định "mình/bạn" phù hợp với mọi người
4. **Thông minh**: Tự động phát hiện và cập nhật preferences
5. **Tương thích**: Không ảnh hưởng đến API hiện tại

## Migration

- ✅ Đã loại bỏ tất cả xưng hô cứng
- ✅ API backward compatible
- ✅ Tests đã pass
- ✅ Chat UI hoạt động bình thường
- ✅ AI routing vẫn hoạt động

## Tương lai

- [ ] Tích hợp với LayeredMemory để lưu preferences
- [ ] Hỗ trợ multiple languages
- [ ] Advanced tone detection
- [ ] User profile management
