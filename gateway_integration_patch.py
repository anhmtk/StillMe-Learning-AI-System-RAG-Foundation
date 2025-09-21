# GATEWAY INTEGRATION PATCH
# Add this to your gateway's chat endpoint

from smart_router import route_message

@app.post("/chat")
def chat(request: ChatRequest):
    """Enhanced chat endpoint with smart routing"""
    try:
        # Use smart router
        result = route_message(request.message, request.session_id)
        
        return {
            "model": result.get("model", "unknown"),
            "response": result.get("response", ""),
            "timestamp": result.get("timestamp"),
            "engine": result.get("engine", "unknown"),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return {
            "model": "error",
            "response": "Xin lỗi, có lỗi xảy ra. Vui lòng thử lại sau.",
            "timestamp": time.time(),
            "engine": "error",
            "status": "error"
        }

# Optional: Add routing control endpoint
@app.post("/admin/routing")
def set_routing_mode(mode: str):
    """Set routing mode (requires admin auth)"""
    if mode in ["auto", "force_gemma", "force_cloud"]:
        os.environ["ROUTING_MODE"] = mode
        return {"status": "success", "routing_mode": mode}
    return {"status": "error", "message": "Invalid mode"}
