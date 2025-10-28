"""
API Client for Evolution System
Handles all HTTP requests to the backend
"""

import requests
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class EvolutionAPIClient:
    """Client for Evolution System API"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.timeout = 30
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {method} {url} - {str(e)}")
            return None
    
    def get_evolution_status(self) -> Optional[Dict[str, Any]]:
        """Get current evolution status"""
        return self._make_request("GET", "/learning/evolution/status")
    
    def get_learning_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get learning history"""
        result = self._make_request("GET", f"/learning/evolution/history?days={days}")
        return result or []
    
    def get_evolution_metrics(self) -> Optional[Dict[str, Any]]:
        """Get evolution metrics"""
        return self._make_request("GET", "/learning/evolution/metrics")
    
    def run_daily_learning_session(self) -> Optional[Dict[str, Any]]:
        """Run daily learning session"""
        return self._make_request("POST", "/learning/evolution/run-session")
    
    def trigger_manual_learning(self, proposal_ids: List[str]) -> Optional[Dict[str, Any]]:
        """Trigger manual learning for proposals"""
        data = {"proposal_ids": proposal_ids}
        return self._make_request("POST", "/learning/evolution/manual-learning", json=data)
    
    def self_assess(self) -> Optional[Dict[str, Any]]:
        """Perform self-assessment"""
        return self._make_request("POST", "/learning/assess")
    
    def get_pending_review_proposals(self) -> List[Dict[str, Any]]:
        """Get proposals pending review"""
        result = self._make_request("GET", "/learning/evolution/pending-review")
        return result or []
    
    def approve_proposal(self, proposal_id: str, reason: str = "") -> bool:
        """Approve a proposal"""
        data = {"proposal_id": proposal_id, "reason": reason}
        result = self._make_request("POST", "/learning/admin/approve-proposal", json=data)
        return result.get('success', False) if result else False
    
    def reject_proposal(self, proposal_id: str, reason: str = "") -> bool:
        """Reject a proposal"""
        data = {"proposal_id": proposal_id, "reason": reason}
        result = self._make_request("POST", "/learning/admin/reject-proposal", json=data)
        return result.get('success', False) if result else False
    
    def get_community_proposals(self, min_votes: int = 0) -> List[Dict[str, Any]]:
        """Get community proposals with vote counts"""
        # This would integrate with your community voting system
        return []
    
    def send_chat_message(self, message: str) -> Optional[Dict[str, Any]]:
        """Send chat message to AI"""
        data = {"message": message}
        return self._make_request("POST", "/chat/send", json=data)