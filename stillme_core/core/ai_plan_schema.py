# stillme_core/ai_plan_schema.py

"""
ai_plan_schema.py - Định nghĩa cấu trúc kế hoạch AI và prompt gốc
Dùng bởi Planner để gọi DeepSeek / GPT tạo kế hoạch module hoặc sửa lỗi.
"""

AI_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "module_name": {"type": "string"},
        "description": {"type": "string"},
        "objectives": {"type": "array", "items": {"type": "string"}},
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "step_id": {"type": "string"},
                    "action": {"type": "string"},
                    "reasoning": {"type": "string"},
                },
                "required": ["step_id", "action"],
            },
        },
    },
    "required": ["module_name", "description", "objectives", "steps"],
}
PLANNER_PROMPT = """
🎯 Nhiệm vụ của bạn: lập kế hoạch để tạo/sửa một module AI trong hệ thống StillMe.

Yêu cầu:
- Phân tích mục tiêu tổng quan.
- Liệt kê các bước cụ thể (steps): gồm step_id, action, reasoning.

Trả về JSON đúng schema AI_PLAN_SCHEMA gồm: module_name, description, objectives, steps.

Hãy bắt đầu với tư duy kỹ sư chuyên nghiệp, sử dụng từ ngữ rõ ràng và dễ hiểu.
"""