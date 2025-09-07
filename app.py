import importlib, importlib.util, inspect, asyncio, sys, logging, yaml, json, traceback, threading, time
from pathlib import Path
import gradio as gr

# Tạm thời disable sentence_transformers để tránh lỗi import
import os
os.environ['DISABLE_SENTENCE_TRANSFORMERS'] = '1'

# Cache cho performance optimization
from functools import lru_cache
import hashlib

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MANIFEST_PATH = Path("stillme_manifest.yaml")
def _load_manifest():
    if MANIFEST_PATH.exists():
        try:
            return yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8")) or {}
        except Exception:
            logging.exception("Load manifest failed")
            return {}
    return {}

# --- manifest & ui_state giữ nguyên ---
from stillme_core.ui_state import get_flag, set_flag

# ---------- ConscienceCore loader ----------
def _load_conscience_hook():
    """Load ConscienceCore from multiple possible locations."""
    
    # Try 1: modules.conscience_core_v1
    try:
        from modules.conscience_core_v1 import conscience_hook
        logging.info("ConscienceCore loaded from modules.conscience_core_v1")
        return conscience_hook
    except Exception as e1:
        logging.debug("modules.conscience_core_v1 not found: %r", e1)
    
    # Try 2: stillme_core.conscience_core_v1
    try:
        from stillme_core.conscience_core_v1 import conscience_hook
        logging.info("ConscienceCore loaded from stillme_core.conscience_core_v1")
        return conscience_hook
    except Exception as e2:
        logging.debug("stillme_core.conscience_core_v1 not found: %r", e2)
    
    # Try 3: Load from file path - modules
    cc_path_modules = ROOT / "modules" / "conscience_core_v1.py"
    if cc_path_modules.exists():
        try:
            spec = importlib.util.spec_from_file_location("conscience_core_v1", str(cc_path_modules))
            mod = importlib.util.module_from_spec(spec)
            sys.modules["conscience_core_v1"] = mod
            spec.loader.exec_module(mod)  # type: ignore
            conscience_hook = getattr(mod, "conscience_hook")
            logging.info("ConscienceCore loaded from file: modules/conscience_core_v1.py")
            return conscience_hook
        except Exception as e3:
            logging.debug("Failed to load from modules/conscience_core_v1.py: %r", e3)
    
    # Try 4: Load from file path - stillme_core
    cc_path_stillme = ROOT / "stillme_core" / "conscience_core_v1.py"
    if cc_path_stillme.exists():
        try:
            spec = importlib.util.spec_from_file_location("conscience_core_v1", str(cc_path_stillme))
            mod = importlib.util.module_from_spec(spec)
            sys.modules["conscience_core_v1"] = mod
            spec.loader.exec_module(mod)  # type: ignore
            conscience_hook = getattr(mod, "conscience_hook")
            logging.info("ConscienceCore loaded from file: stillme_core/conscience_core_v1.py")
            return conscience_hook
        except Exception as e4:
            logging.debug("Failed to load from stillme_core/conscience_core_v1.py: %r", e4)
    
    # Fallback: tạo ConscienceCore mock
    logging.info("ConscienceCore not found, creating mock ConscienceCore with basic ethical filtering")
    
    def mock_conscience_hook(prompt: str, raw_fn):
        """Mock ConscienceCore with basic ethical filtering."""
        # Basic ethical filtering
        dangerous_keywords = ["hack", "crack", "exploit", "malware", "virus", "phishing"]
        prompt_lower = prompt.lower()
        
        for keyword in dangerous_keywords:
            if keyword in prompt_lower:
                return "⚠️ Tôi không thể hỗ trợ các hoạt động có thể gây hại hoặc bất hợp pháp."
        
        # Call the raw function
        return raw_fn(prompt)
    
    return mock_conscience_hook

# ---------- Resolve raw generator (router) ----------
def _resolve_raw_generator():
    """
    Trả về (fn, desc) trong các ứng viên sau theo thứ tự:
    - stillme_core.ai_manager.get_ai_response
    - stillme_core.model_router.get_ai_response
    - intelligent_router.get_ai_response
    - stillme_core.controller.respond
    - stillme_core.controller.answer
    - stillme_core.ai_manager.answer
    """
    candidates = [
        ("modules.intelligent_router", "ModelRouter"),
        ("stillme_core.ai_manager", "get_ai_response"),
        ("stillme_core.model_router", "get_ai_response"),
        ("intelligent_router", "get_ai_response"),
        ("stillme_core.controller", "respond"),
        ("stillme_core.controller", "answer"),
        ("stillme_core.ai_manager", "answer"),
    ]
    for mod_name, fn_name in candidates:
        try:
            mod = importlib.import_module(mod_name)
            if fn_name == "ModelRouter":
                # Xử lý đặc biệt cho ModelRouter class
                router_class = getattr(mod, fn_name, None)
                if router_class:
                    router_instance = router_class()
                    fn = router_instance.get_ai_response
                    if callable(fn):
                        logging.info("Using %s.%s instance as raw generator", mod_name, fn_name)
                        return fn, f"{mod_name}.{fn_name}.get_ai_response"
            else:
                fn = getattr(mod, fn_name, None)
                if callable(fn):
                    logging.info("Using %s.%s as raw generator", mod_name, fn_name)
                    return fn, f"{mod_name}.{fn_name}"
        except Exception as e:
            logging.debug("Skip %s.%s: %r", mod_name, fn_name, e)
    # cuối cùng: thử load controller.py theo path
    ctrl_path = ROOT / "stillme_core" / "controller.py"
    if ctrl_path.exists():
        spec = importlib.util.spec_from_file_location("stillme_controller_file", str(ctrl_path))
        mod = importlib.util.module_from_spec(spec)
        sys.modules["stillme_controller_file"] = mod
        spec.loader.exec_module(mod)  # type: ignore
        fn = getattr(mod, "respond", None) or getattr(mod, "answer", None)
        if callable(fn):
            logging.info("Using file controller.py respond/answer as raw generator")
            return fn, "file(controller.py)"
    raise ImportError("Cannot find a raw answer function (get_ai_response/respond/answer)")

conscience_hook = _load_conscience_hook()
_raw_fn, _raw_desc = _resolve_raw_generator()

def _call_raw(prompt: str) -> str:
    fn = _raw_fn
    try:
        if inspect.iscoroutinefunction(fn):
            return asyncio.run(fn(prompt))
        result = fn(prompt)
        return result
    except RuntimeError as e:
        # trường hợp đã có event loop đang chạy (Gradio/Windows)
        if "asyncio.run()" in str(e) or "event loop" in str(e):
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                coro = fn(prompt)
                return loop.run_until_complete(coro) if inspect.iscoroutine(coro) else coro
            finally:
                loop.close()
        raise

def generate_answer(prompt: str) -> str:
    draft = conscience_hook(prompt, _call_raw)
    # Chuẩn hoá & bảo vệ rỗng
    text = _normalize_text(draft).strip()
    if not text:
        logging.warning("Empty draft from %s", _raw_desc)
        return ("⚠️ Pipeline trả về rỗng từ "
                f"`{_raw_desc}`. Kiểm tra router/model hoặc biến môi trường (nếu dùng API).")
    return text

# --- route getter giữ nguyên (dùng intelligent_router.explain_last_route nếu có) ---
def _resolve_route_label_getter():
    for cand in ("intelligent_router", "stillme_core.intelligent_router"):
        try:
            m = importlib.import_module(cand)
            f = getattr(m, "explain_last_route", None)
            if callable(f): return f
        except Exception:
            pass
    return None

route_label_getter = _resolve_route_label_getter()

def _normalize_text(x) -> str:
    try:
        if isinstance(x, (list, tuple)):
            if not x: return ""
            if isinstance(x[0], dict):
                return x[0].get("text") or x[0].get("answer") or json.dumps(x[0], ensure_ascii=False)
            return str(x[0])
        if isinstance(x, dict):
            return x.get("text") or x.get("answer") or x.get("output") or json.dumps(x, ensure_ascii=False)
        return str(x)
    except Exception:
        return f"[Serialization error: {type(x).__name__}]"

# --- phần UI pledge / Blocks / handle_query giữ nguyên, chỉ thay body của handle_query nếu cần ---
def handle_query(user_input: str):
    try:
        ans = generate_answer(user_input)
        logging.info("REQ route=%s | preview=%s", (route_label_getter() if route_label_getter else "hidden"), ans[:120].replace("\n"," "))
    except Exception as e:
        logging.exception("generate_answer crashed")
        ans = f"⚠️ Lỗi khi xử lý câu hỏi. {type(e).__name__}: {e}"
    try:
        route_txt = route_label_getter() if route_label_getter else ""
    except Exception:
        route_txt = ""
    route_md = f"**Route:** {route_txt}" if route_txt else "**Route:** intelligent_router (ẩn chi tiết)"
    return ans, route_md

# Cache cho classification để tối ưu performance
@lru_cache(maxsize=100)
def _cached_classify(message_hash: str):
    """Cache classification results để tránh gọi lại model"""
    try:
        from modules.intelligent_router import classify_query_with_gemma2
        return classify_query_with_gemma2(message_hash)
    except:
        return "complex"

def stillme_chat_fn_stream(message: str, history):
    """
    Streaming chat function for real-time UX
    """
    if not message.strip():
        return ""
    
    try:
        # Import router for streaming
        from modules.intelligent_router import ModelRouter
        router = ModelRouter()
        
        # Stream response
        for chunk in router.get_ai_response_stream(message):
            yield chunk
            
    except Exception as e:
        print(f"Streaming error: {e}")
        yield "⚠️ Có lỗi xảy ra khi xử lý yêu cầu của bạn."

def stillme_chat_fn(message: str, history):
    """
    Enhanced chat function with performance tracking and model info
    """
    if not message.strip():
        return ""
    
    # Bắt đầu đo thời gian
    start_time = time.time()
    
    # Tạo hash cho cache
    message_hash = hashlib.md5(message.lower().strip().encode()).hexdigest()
    
    try:
        # Log bắt đầu xử lý
        print(f"[START] Processing: '{message[:30]}{'...' if len(message) > 30 else ''}'")
        
        # Gọi framework StillMe với timing chi tiết
        framework_start = time.time()
        ai_response = generate_answer(message)
        framework_time = round(time.time() - framework_start, 2)
        
        # Tính thời gian xử lý tổng
        end_time = time.time()
        processing_time = round(end_time - start_time, 2)
        
        # Lấy thông tin model thực tế từ intelligent_router
        real_model_name = "intelligent_router"
        try:
            # Import intelligent_router để lấy model thực tế
            from modules.intelligent_router import explain_last_route
            route_info = explain_last_route()
            if route_info and isinstance(route_info, dict):
                real_model_name = route_info.get("model", "intelligent_router")
            elif route_info:
                # Parse từ string
                route_str = str(route_info).lower()
                if "deepseek" in route_str:
                    real_model_name = "deepseek-coder:6.7b"
                elif "gemma" in route_str:
                    real_model_name = "gemma2:2b"
                elif "openai" in route_str:
                    real_model_name = "openai-gpt"
        except Exception as e:
            print(f"[WARN] Cannot get real model name: {e}")
        
        # Cải thiện chất lượng câu trả lời - chủ động đưa ra gợi ý
        enhanced_response = ai_response
        message_lower = message.lower().strip()
        
        # Xử lý các câu hỏi chung chung
        if any(keyword in message_lower for keyword in ["viết code javascript", "code js", "javascript"]):
            if "cụ thể" not in ai_response.lower() and "ví dụ" not in ai_response.lower():
                enhanced_response = f"{ai_response}\n\n**Gợi ý cụ thể:**\n- Tạo hàm xử lý sự kiện click\n- Viết code thao tác với mảng/object\n- Tạo request API bằng fetch\n\nBạn cần loại nào?"
        
        elif any(keyword in message_lower for keyword in ["viết code python", "code python", "python"]):
            if "cụ thể" not in ai_response.lower() and "ví dụ" not in ai_response.lower():
                enhanced_response = f"{ai_response}\n\n**Gợi ý cụ thể:**\n- Tạo hàm xử lý dữ liệu\n- Viết class và object\n- Xử lý file và database\n\nBạn cần loại nào?"
        
        elif any(keyword in message_lower for keyword in ["thuật toán", "algorithm"]):
            if "cụ thể" not in ai_response.lower() and "ví dụ" not in ai_response.lower():
                enhanced_response = f"{ai_response}\n\n**Thuật toán phổ biến:**\n- Quicksort, Merge sort\n- BFS, DFS\n- Dynamic Programming\n\nBạn muốn tìm hiểu thuật toán nào?"
        
        # Tạo response cuối cùng có kèm thông tin hiệu suất
        full_response = f"{enhanced_response}\n\n---\n*⚡ {processing_time}s | 🔧 {real_model_name}*"
        
        # In log chuyên nghiệp ra terminal với thông tin chi tiết
        print(f"[PERF] Query: '{message[:50]}{'...' if len(message) > 50 else ''}' -> Model: {real_model_name}, Framework: {framework_time}s, Total: {processing_time}s")
        
        # Cảnh báo nếu quá chậm
        if processing_time > 5.0:
            print(f"[SLOW] ⚠️ Response time {processing_time}s is slow! Consider optimization.")
        elif processing_time > 2.0:
            print(f"[WARN] Response time {processing_time}s is moderate.")
        else:
            print(f"[FAST] ✅ Response time {processing_time}s is good.")
        
        return full_response
        
    except Exception as e:
        end_time = time.time()
        processing_time = round(end_time - start_time, 2)
        error_response = f"⚠️ Lỗi khi xử lý câu hỏi: {str(e)}\n\n---\n*⚡ {processing_time}s | 🔧 error*"
        print(f"[ERROR] [StillMe] Query: '{message[:50]}{'...' if len(message) > 50 else ''}' -> Error: '{str(e)}', Time: {processing_time}s")
        return error_response

cfg = _load_manifest()
pledge = cfg.get("pledge", {})
pledge_md = f"### Lời thề StillMe\n\n{pledge.get('motto','')}\n\n*{pledge.get('attribution','')}*".strip()
first_run = not get_flag("pledge_ack", False)

# Tạo giao diện chat chuyên nghiệp với ChatInterface
demo = gr.ChatInterface(
    fn=stillme_chat_fn_stream,
    title="🧠 StillMe AI - Trợ lý thông minh",
    description="Xin chào! Tôi là StillMe AI, trợ lý thông minh của bạn. Hãy hỏi tôi bất cứ điều gì!",
    theme="soft",
    chatbot=gr.Chatbot(
        height=600,
        show_copy_button=True,
        avatar_images=("👤", "🧠"),  # User avatar: 👤, StillMe avatar: 🧠
        bubble_full_width=False
    ),
    textbox=gr.Textbox(
        placeholder="Nhập câu hỏi của bạn...",
        container=False,
        scale=7
    ),
    submit_btn="Gửi",
    examples=[
        ["Xin chào!"],
        ["Python là gì?"],
        ["Cách tạo hàm trong Python?"],
        ["Giải thích thuật toán quicksort"],
        ["Viết code JavaScript đơn giản"]
    ],
    cache_examples=False
)

# Thêm CSS tùy chỉnh cho giao diện đẹp hơn và thu hẹp khoảng cách
demo.css = """
/* Thu hẹp khoảng cách tin nhắn */
.gradio-chatbot .message {
    margin: 8px 0 !important;
    padding: 12px 16px !important;
}

.gradio-chatbot .message-wrap {
    margin-bottom: 12px !important;
}

/* Tùy chỉnh avatar */
.avatar-img {
    width: 28px !important;
    height: 28px !important;
    border-radius: 50% !important;
    font-size: 16px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* Tùy chỉnh chatbot - thu hẹp khoảng cách */
.gradio-chatbot {
    border: 1px solid #e1e5e9 !important;
    border-radius: 12px !important;
    padding: 8px !important;
    max-height: 600px !important;
    overflow-y: auto !important;
}

/* Thu hẹp khoảng cách giữa các bubble */
.gradio-chatbot .message-wrap:not(:last-child) {
    margin-bottom: 8px !important;
}

/* Tùy chỉnh textbox */
.gradio-textbox {
    border-radius: 8px !important;
    border: 2px solid #e1e5e9 !important;
    padding: 12px !important;
}

.gradio-textbox:focus {
    border-color: #4f46e5 !important;
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1) !important;
}

/* Tùy chỉnh buttons */
.gradio-button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
}

/* Tùy chỉnh examples */
.gradio-examples {
    border-radius: 8px !important;
    margin: 4px !important;
}

/* Hiệu ứng hover */
.gradio-button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
}

/* Tùy chỉnh performance info */
.performance-info {
    font-size: 11px !important;
    color: #6b7280 !important;
    font-style: italic !important;
    margin-top: 4px !important;
    padding-top: 4px !important;
    border-top: 1px solid #e5e7eb !important;
}

/* Thu hẹp khoảng cách input area */
.gradio-chat-interface .input-area {
    padding: 8px !important;
    margin-top: 8px !important;
}

/* Tùy chỉnh message bubbles */
.gradio-chatbot .message.user {
    background-color: #f0f9ff !important;
    border-radius: 18px 18px 4px 18px !important;
    margin-left: 20% !important;
}

.gradio-chatbot .message.bot {
    background-color: #f8fafc !important;
    border-radius: 18px 18px 18px 4px !important;
    margin-right: 20% !important;
}

/* Responsive design */
@media (max-width: 768px) {
    .gradio-chatbot .message.user {
        margin-left: 10% !important;
    }
    
    .gradio-chatbot .message.bot {
        margin-right: 10% !important;
    }
}
"""

if __name__ == "__main__":
    # Blocking warmup of gemma2:2b before launch
    from clients.ollama_client import warmup_blocking, call_ollama_chat
    import threading
    import time
    
    print("🔥 Prewarming gemma2:2b...")
    warmup_blocking("gemma2:2b")
    print("✅ gemma2:2b ready!")
    
    # Background keepalive to maintain model warmth
    def keepalive_worker():
        """Background worker to keep model warm every 45 minutes"""
        while True:
            time.sleep(45 * 60)  # 45 minutes
            try:
                print("🔄 Keepalive: Maintaining gemma2:2b warmth...")
                messages = [{"role": "user", "content": "ok"}]
                options = {"num_predict": 1, "temperature": 0, "keep_alive": "1h"}
                for chunk in call_ollama_chat("gemma2:2b", messages, stream=False, options=options, timeout=5.0):
                    break
                print("✅ Keepalive: gemma2:2b maintained")
            except Exception as e:
                print(f"⚠️ Keepalive failed: {e}")
    
    # Start keepalive in background
    keepalive_thread = threading.Thread(target=keepalive_worker, daemon=True)
    keepalive_thread.start()
    print("🔄 Background keepalive started (every 45 minutes)")
    
    # Find free port
    import socket
    def find_free_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port
    
    port = find_free_port()
    print(f"🚀 Starting StillMe AI on http://127.0.0.1:{port}")
    
    # Launch Gradio app
    demo.launch(server_name="127.0.0.1", server_port=port, show_error=True)