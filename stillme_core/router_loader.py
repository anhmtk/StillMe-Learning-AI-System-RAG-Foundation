import importlib
import logging
import os

log = logging.getLogger(__name__)

def load_router():
    """Load the appropriate router implementation.
    
    Priority order:
    1. STILLME_ROUTER_MODE=stub -> StubRouter
    2. STILLME_ROUTER_MODE=pro -> ProRouter (if available)
    3. Auto-detect: ProRouter if available, else StubRouter
    
    Returns:
        Router implementation (ProRouter or StubRouter)
    """
    mode = (os.getenv("STILLME_ROUTER_MODE") or "").lower()

    if mode == "stub":
        from plugins.private_stub.plugin import StubRouter
        log.warning("Using StubRouter due to STILLME_ROUTER_MODE=stub")
        return StubRouter()

    if mode == "pro":
        try:
            mod = importlib.import_module("stillme_private.plugin")
            ProRouter = mod.ProRouter
            log.info("Using ProRouter due to STILLME_ROUTER_MODE=pro")
            return ProRouter()
        except Exception as e:
            log.error(f"ProRouter requested but not available: {e}; falling back to Stub.")
            from plugins.private_stub.plugin import StubRouter
            return StubRouter()

    # Auto-detect: prefer Pro, else Stub
    try:
        mod = importlib.import_module("stillme_private.plugin")
        ProRouter = mod.ProRouter
        log.info("Using ProRouter (auto-detected).")
        return ProRouter()
    except Exception as e:
        from plugins.private_stub.plugin import StubRouter
        log.warning(f"ProRouter not found ({e}) → Using StubRouter (OSS mode).")
        return StubRouter()
