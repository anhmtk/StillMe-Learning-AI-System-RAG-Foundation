#!/usr/bin/env python3
"""
Privacy Manager - MINIMAL CONTRACT derived from tests/usages
"""

from enum import Enum


class PIIType(Enum):
    """PII Type enum - MINIMAL CONTRACT derived from tests/usages"""
    EMAIL = "email"
    PHONE = "phone"
    NAME = "name"
    IP_ADDRESS = "ip_address"
    TOKEN = "token"
    ID_NUMBER = "id_number"
    CREDIT_CARD = "credit_card"
    SSN = "ssn"

class PrivacyManager:
    """Privacy Manager - MINIMAL CONTRACT derived from tests/usages"""

    def __init__(self):
        """Initialize Privacy Manager"""
        pass

__all__ = ["PIIType", "PrivacyManager"]
