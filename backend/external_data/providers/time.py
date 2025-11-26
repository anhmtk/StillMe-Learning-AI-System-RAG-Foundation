"""
Time Provider - Returns current time and date

No external API needed - uses system datetime.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False

from .base import ExternalDataProvider, ExternalDataResult

logger = logging.getLogger(__name__)


class TimeProvider(ExternalDataProvider):
    """Time provider - returns current time and date"""
    
    def get_provider_name(self) -> str:
        return "System"
    
    def supports(self, intent_type: str, params: Dict[str, Any]) -> bool:
        """Check if this provider supports time intent"""
        return intent_type == "time"
    
    async def fetch(self, intent_type: str, params: Dict[str, Any]) -> ExternalDataResult:
        """
        Fetch current time and date
        
        Args:
            intent_type: Should be "time"
            params: Optional timezone parameter
            
        Returns:
            ExternalDataResult with time data
        """
        if intent_type != "time":
            return ExternalDataResult(
                data={},
                source=self.get_provider_name(),
                timestamp=datetime.utcnow(),
                cached=False,
                success=False,
                error_message=f"Invalid intent type: {intent_type}"
            )
        
        try:
            # Get current time in UTC
            current_time_utc = datetime.now(timezone.utc)
            
            # Get local time (default to Asia/Ho_Chi_Minh)
            timezone_name = params.get("timezone", "Asia/Ho_Chi_Minh")
            
            if PYTZ_AVAILABLE:
                try:
                    local_tz = pytz.timezone(timezone_name)
                    local_time = current_time_utc.astimezone(local_tz)
                except Exception:
                    # Fallback to UTC if timezone invalid
                    local_time = current_time_utc
                    timezone_name = "UTC"
            else:
                local_time = current_time_utc
                timezone_name = "UTC"
            
            # Format time data
            time_data = {
                "utc_time": current_time_utc.strftime("%Y-%m-%d %H:%M:%S"),
                "local_time": local_time.strftime("%Y-%m-%d %H:%M:%S"),
                "timezone": timezone_name,
                "date": local_time.strftime("%Y-%m-%d"),
                "time": local_time.strftime("%H:%M:%S"),
                "day_of_week": local_time.strftime("%A"),
                "iso_format": current_time_utc.isoformat(),
            }
            
            return ExternalDataResult(
                data=time_data,
                source=self.get_provider_name(),
                timestamp=current_time_utc,
                cached=False,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Time provider error: {e}", exc_info=True)
            return ExternalDataResult(
                data={},
                source=self.get_provider_name(),
                timestamp=datetime.utcnow(),
                cached=False,
                success=False,
                error_message=f"Error: {str(e)}"
            )

