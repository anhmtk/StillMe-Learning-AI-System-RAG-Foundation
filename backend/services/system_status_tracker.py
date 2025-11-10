"""
System Status Tracker - Tracks error states of all system components
Enables StillMe to perform honest self-diagnosis
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SystemStatusTracker:
    """
    Tracks error states of all system components for self-diagnosis.
    Enables StillMe to answer truthfully about its own status.
    """
    
    def __init__(self):
        self.component_status: Dict[str, Dict[str, Any]] = {}
        self.last_update: Optional[datetime] = None
    
    def update_component_status(self, 
                               component_name: str,
                               status: str,
                               error_message: Optional[str] = None,
                               error_count: int = 0,
                               last_success: Optional[datetime] = None):
        """
        Update status of a system component
        
        Args:
            component_name: Name of component (e.g., "wikipedia_fetcher", "rss_fetcher")
            status: Status ("ok", "error", "warning")
            error_message: Error message if status is "error"
            error_count: Number of errors encountered
            last_success: Last successful operation time
        """
        self.component_status[component_name] = {
            "status": status,
            "error_message": error_message,
            "error_count": error_count,
            "last_success": last_success.isoformat() if last_success else None,
            "last_update": datetime.now().isoformat()
        }
        self.last_update = datetime.now()
        logger.debug(f"Updated {component_name} status: {status}")
    
    def get_component_status(self, component_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific component"""
        return self.component_status.get(component_name)
    
    def get_all_status(self) -> Dict[str, Any]:
        """Get status of all components"""
        return {
            "components": self.component_status,
            "last_update": self.last_update.isoformat() if self.last_update else None
        }
    
    def has_error(self, component_name: str) -> bool:
        """Check if a component has errors"""
        status = self.component_status.get(component_name)
        if not status:
            return False
        return status.get("status") == "error"
    
    def get_error_message(self, component_name: str) -> Optional[str]:
        """Get error message for a component"""
        status = self.component_status.get(component_name)
        if not status:
            return None
        return status.get("error_message")
    
    def get_status_summary(self) -> Dict[str, Any]:
        """
        Get summary of system status for self-diagnosis prompts
        
        Returns:
            Dictionary with component statuses and error messages
        """
        errors = []
        warnings = []
        
        for component_name, status_info in self.component_status.items():
            if status_info.get("status") == "error":
                errors.append({
                    "component": component_name,
                    "error": status_info.get("error_message", "Unknown error"),
                    "error_count": status_info.get("error_count", 0)
                })
            elif status_info.get("status") == "warning":
                warnings.append({
                    "component": component_name,
                    "message": status_info.get("error_message", "Warning")
                })
        
        return {
            "has_errors": len(errors) > 0,
            "has_warnings": len(warnings) > 0,
            "errors": errors,
            "warnings": warnings,
            "all_components": self.component_status
        }


# Global instance
_system_status_tracker = None


def get_system_status_tracker() -> SystemStatusTracker:
    """Get global SystemStatusTracker instance"""
    global _system_status_tracker
    if _system_status_tracker is None:
        _system_status_tracker = SystemStatusTracker()
    return _system_status_tracker

