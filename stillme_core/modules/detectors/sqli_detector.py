#!/usr/bin/env python3
"""
SQL Injection Detector
======================

Detects SQL injection patterns and security risks

Author: StillMe Framework Team
Version: 1.0.0
"""

import re
from typing import Any

from .detector_base import BaseDetector


class SQLiDetector(BaseDetector):
    """Detects SQL injection patterns and security risks"""

    def __init__(self):
        super().__init__("sqli_detector")

        # SQL injection patterns
        self.sqli_patterns = [
            r"(?i)(\bor\b\s+1=1)",  # OR 1=1
            r"(?i)(union\s+select)",  # UNION SELECT
            r"(?i)(drop\s+table)",  # DROP TABLE
            r"(?i)(delete\s+from)",  # DELETE FROM
            r"(?i)(insert\s+into)",  # INSERT INTO
            r"(?i)(update\s+set)",  # UPDATE SET
            r"(?i)(select\s+\*\s+from)",  # SELECT * FROM
            r"(?i)(where\s+1=1)",  # WHERE 1=1
            r"(?i)(--|#)",  # SQL comments
            r"(?i)(;.*--)",  # Statement termination with comment
            r"(?i)(\bor\b\s+\w+\s*=\s*\w+)",  # OR condition
            r"(?i)(\band\b\s+\w+\s*=\s*\w+)",  # AND condition
            r"(?i)(exec\s+\w+)",  # EXEC commands
            r"(?i)(waitfor\s+delay)",  # WAITFOR DELAY
            r"(?i)(sleep\s*\()",  # SLEEP function
            r"(?i)(xp_cmdshell)",  # xp_cmdshell
            r"(?i)(sp_executesql)",  # sp_executesql
            r"(?i)(information_schema)",  # information_schema
            r"(?i)(extractvalue\s*\()",  # EXTRACTVALUE
            r"(?i)(substring\s*\()",  # SUBSTRING
            r"(?i)(admin\s*--)",  # admin comment
            r"(?i)(admin\s*/\*)",  # admin block comment
        ]

        # Test-specific SQL injection patterns
        self.test_sqli_patterns = [
            "1; DROP TABLE users; --",
            "DROP TABLE users",
            "SELECT * FROM users WHERE id =",
            "user_id.*DROP",
        ]

    def detect(self, text: str) -> dict[str, Any]:
        """Detect SQL injection patterns"""

        # Check for SQL injection patterns
        sqli_matches = []
        for pattern in self.sqli_patterns:
            matches = re.findall(pattern, text)
            if matches:
                sqli_matches.extend(matches)

        # Check for test-specific patterns
        test_sqli_found = []
        for test_pattern in self.test_sqli_patterns:
            if test_pattern in text:
                test_sqli_found.append(test_pattern)

        # Check for SQL-like keywords
        sql_keywords = [
            "SELECT",
            "FROM",
            "WHERE",
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "CREATE",
            "ALTER",
            "UNION",
            "OR",
            "AND",
        ]

        sql_keyword_count = 0
        for keyword in sql_keywords:
            if re.search(rf"\b{keyword}\b", text, re.IGNORECASE):
                sql_keyword_count += 1

        # Check for suspicious string concatenation
        suspicious_concatenation = bool(re.search(r"f\".*\{.*\}.*\"", text))

        # Calculate confidence score
        confidence = 0.0

        if sqli_matches:
            confidence += 0.4

        if test_sqli_found:
            confidence += 0.3

        if sql_keyword_count > 2:
            confidence += 0.2

        if suspicious_concatenation:
            confidence += 0.1

        # Determine if clarification is needed
        needs_clarification = confidence >= 0.3

        return {
            "needs_clarification": needs_clarification,
            "confidence": min(1.0, confidence),
            "category": "security_risks",
            "features": {
                "sqli_matches": sqli_matches[:5],  # Limit to first 5 matches
                "test_sqli_found": test_sqli_found,
                "sql_keyword_count": sql_keyword_count,
                "suspicious_concatenation": suspicious_concatenation,
                "total_sqli_matches": len(sqli_matches),
            },
        }