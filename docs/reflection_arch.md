# Reflection Controller Architecture / Kiến trúc Reflection Controller

## Overview / Tổng quan

Reflection Controller được tích hợp vào StillMe để cung cấp khả năng **phản tư có giới hạn** (bounded reflection), tối ưu đa mục tiêu và bảo vệ thông tin nội bộ.

## Integration Points / Điểm tích hợp

### 1. Primary Hook Points / Điểm hook chính

```
User Query → Reflection Controller → Enhanced Response
```

**Các điểm tích hợp:**
- `app.py:handle_query()` - Main query processing
- `stable_ai_server.py:/inference` - API endpoint
- `stillme_platform/gateway/main.py` - WebSocket endpoint
- `modules/conversational_core_v1.py:respond()` - Core conversation logic

### 2. Architecture Flow / Luồng kiến trúc

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Query    │───▶│ Reflection       │───▶│ Enhanced        │
│                 │    │ Controller       │    │ Response        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │ Reflection       │
                       │ Scorer           │
                       └──────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │ Secrecy Filter   │
                       └──────────────────┘
```

### 3. Component Integration / Tích hợp thành phần

**Reflection Controller** sẽ được tích hợp như một **middleware layer** giữa:
- Input processing và response generation
- Không thay thế logic hiện có, chỉ enhance

**Files sẽ được tạo:**
- `stillme_core/reflection_controller.py` - Main controller
- `stillme_core/reflection_scorer.py` - Scoring system
- `stillme_core/secrecy_filter.py` - Security filter
- `config/reflection.yaml` - Configuration

### 4. Hook Implementation / Triển khai hook

**Trong `app.py`:**
```python
def handle_query(user_input: str):
    # Existing logic
    ans = generate_answer(user_input)
    
    # NEW: Reflection enhancement
    if reflection_controller.should_reflect(user_input):
        ans = reflection_controller.enhance_response(ans, user_input)
    
    return ans, route_md
```

**Trong `stable_ai_server.py`:**
```python
@app.post("/inference")
async def inference(request: ChatRequest):
    # Existing logic
    response_text = stillme_ai.process_message(request.message, request.locale)
    
    # NEW: Reflection enhancement
    if reflection_controller.should_reflect(request.message):
        response_text = reflection_controller.enhance_response(
            response_text, request.message, mode="api"
        )
    
    return ChatResponse(text=response_text, ...)
```

## Benefits / Lợi ích

1. **Non-invasive integration** - Không phá vỡ kiến trúc hiện có
2. **Configurable reflection** - Có thể bật/tắt theo context
3. **Security protection** - Tự động filter thông tin nhạy cảm
4. **Performance optimization** - Bounded reflection với timeout
5. **Multi-objective optimization** - Tối ưu nhiều tiêu chí cùng lúc

## Configuration / Cấu hình

Reflection Controller sẽ được cấu hình thông qua:
- Environment variables
- `config/reflection.yaml`
- Runtime parameters

## Security Considerations / Cân nhắc bảo mật

- **Secrecy Filter** sẽ chặn thông tin nội bộ
- **Policy responses** cho câu hỏi về kiến trúc
- **No internal details** trong logs
- **Bounded execution** để tránh infinite loops
