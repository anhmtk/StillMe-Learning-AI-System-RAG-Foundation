#!/usr/bin/env python3
"""
Debug SEAL-GRADE Test
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stillme_core.modules.clarification_handler import ClarificationHandler
from stillme_core.modules.audit_logger import AuditLogger
import tempfile
import json

def test_basic_clarification():
    """Test basic clarification"""
    print("Testing basic clarification...")
    try:
        handler = ClarificationHandler()
        result = handler.detect_ambiguity("Do that thing now")
        print(f"✅ Basic clarification works: {result.needs_clarification}, {result.question}")
        return True
    except Exception as e:
        print(f"❌ Basic clarification failed: {e}")
        return False

def test_audit_logging():
    """Test audit logging"""
    print("Testing audit logging...")
    try:
        temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.jsonl')
        audit_config = {
            "enabled": True,
            "redact_pii": True,
            "log_file": temp_file.name,
            "privacy_filters": ["email", "password"]
        }
        
        audit_logger = AuditLogger(audit_config)
        trace_id = audit_logger.log_clarification_request(
            "user123", "session456", "My email is test@example.com", "text", "generic", "careful", {}
        )
        
        print(f"✅ Audit logging works: {trace_id}")
        
        # Check log content
        with open(temp_file.name, 'r') as f:
            log_entry = json.loads(f.readline())
        
        print(f"✅ Log entry: {log_entry}")
        return True
        
    except Exception as e:
        print(f"❌ Audit logging failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Debugging SEAL-GRADE Tests")
    print("=" * 50)
    
    test1 = test_basic_clarification()
    test2 = test_audit_logging()
    
    print("=" * 50)
    print(f"Results: Basic={test1}, Audit={test2}")
