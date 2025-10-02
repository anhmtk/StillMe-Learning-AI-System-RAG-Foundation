"""
StillMe Kill Switch API
FastAPI endpoints for kill switch operations.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from stillme_core.kill_switch import KillSwitchManager, get_kill_switch


# Request/Response models
class KillSwitchRequest(BaseModel):
    actor: str
    reason: Optional[str] = None


class KillSwitchResponse(BaseModel):
    success: bool
    message: str
    state: Optional[str] = None
    armed_at: Optional[str] = None
    fired_at: Optional[str] = None
    armed_by: Optional[str] = None
    fired_by: Optional[str] = None
    reason: Optional[str] = None


class KillSwitchStatus(BaseModel):
    state: str
    armed_at: Optional[str] = None
    fired_at: Optional[str] = None
    armed_by: Optional[str] = None
    fired_by: Optional[str] = None
    reason: Optional[str] = None
    created_at: Optional[str] = None
    last_updated: Optional[str] = None
    is_armed: bool
    is_fired: bool
    is_safe: bool


class AuditLogEntry(BaseModel):
    timestamp: str
    level: str
    data: Optional[dict] = None
    message: Optional[str] = None


# Create router
router = APIRouter(prefix="/kill-switch", tags=["kill-switch"])


def get_manager() -> KillSwitchManager:
    """Dependency to get kill switch manager."""
    return get_kill_switch()


@router.get("/status", response_model=KillSwitchStatus)
async def get_status(manager: KillSwitchManager = Depends(get_manager)):
    """Get kill switch status."""
    try:
        status = manager.status()
        return KillSwitchStatus(**status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/arm", response_model=KillSwitchResponse)
async def arm_kill_switch(
    request: KillSwitchRequest, manager: KillSwitchManager = Depends(get_manager)
):
    """Arm the kill switch."""
    try:
        result = manager.arm(request.actor, request.reason)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return KillSwitchResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to arm kill switch: {str(e)}"
        )


@router.post("/fire", response_model=KillSwitchResponse)
async def fire_kill_switch(
    request: KillSwitchRequest, manager: KillSwitchManager = Depends(get_manager)
):
    """Fire the kill switch (emergency stop)."""
    try:
        result = manager.fire(request.actor, request.reason)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return KillSwitchResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fire kill switch: {str(e)}"
        )


@router.post("/disarm", response_model=KillSwitchResponse)
async def disarm_kill_switch(
    request: KillSwitchRequest, manager: KillSwitchManager = Depends(get_manager)
):
    """Disarm the kill switch."""
    try:
        result = manager.disarm(request.actor, request.reason)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return KillSwitchResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to disarm kill switch: {str(e)}"
        )


@router.get("/audit", response_model=list[AuditLogEntry])
async def get_audit_log(
    limit: int = 100, manager: KillSwitchManager = Depends(get_manager)
):
    """Get kill switch audit log."""
    try:
        entries = manager.get_audit_log(limit)
        return [AuditLogEntry(**entry) for entry in entries]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get audit log: {str(e)}"
        )


@router.get("/health")
async def health_check(manager: KillSwitchManager = Depends(get_manager)):
    """Health check endpoint."""
    try:
        status = manager.status()
        return {
            "healthy": status["is_safe"],
            "state": status["state"],
            "message": "System is safe"
            if status["is_safe"]
            else f"System is {status['state']}",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


# Middleware to check kill switch status
async def kill_switch_middleware(request, call_next):
    """Middleware to check kill switch status before processing requests."""
    # Skip kill switch endpoints themselves
    if request.url.path.startswith("/kill-switch"):
        response = await call_next(request)
        return response

    # Check if system is safe
    try:
        manager = get_kill_switch()
        if not manager.is_safe():
            status = manager.status()
            return HTTPException(
                status_code=503,
                detail={
                    "error": "System not available",
                    "state": status["state"],
                    "reason": status.get("reason"),
                    "message": "Kill switch is armed or fired",
                },
            )
    except Exception:
        # If we can't check kill switch, allow request to proceed
        # (fail-open for availability)
        pass

    response = await call_next(request)
    return response
