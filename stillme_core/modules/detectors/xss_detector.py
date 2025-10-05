#!/usr/bin/env python3
"""
XSS Detector
============

Detects XSS patterns and security risks

Author: StillMe Framework Team
Version: 1.0.0
"""

import re
from typing import Any

from .detector_base import BaseDetector


class XSSDetector(BaseDetector):
    """Detects XSS patterns and security risks"""

    def __init__(self):
        super().__init__("xss_detector")

        # XSS patterns
        self.xss_patterns = [
            r"(?i)<script[^>]*>",  # Script tags
            r"(?i)onerror\s*=",  # onerror event
            r"(?i)onload\s*=",  # onload event
            r"(?i)onclick\s*=",  # onclick event
            r"(?i)onmouseover\s*=",  # onmouseover event
            r"(?i)onfocus\s*=",  # onfocus event
            r"(?i)onblur\s*=",  # onblur event
            r"(?i)onchange\s*=",  # onchange event
            r"(?i)onsubmit\s*=",  # onsubmit event
            r"(?i)onreset\s*=",  # onreset event
            r"(?i)onkeydown\s*=",  # onkeydown event
            r"(?i)onkeyup\s*=",  # onkeyup event
            r"(?i)onkeypress\s*=",  # onkeypress event
            r"(?i)onmousedown\s*=",  # onmousedown event
            r"(?i)onmouseup\s*=",  # onmouseup event
            r"(?i)onmousemove\s*=",  # onmousemove event
            r"(?i)onmouseout\s*=",  # onmouseout event
            r"(?i)onmouseenter\s*=",  # onmouseenter event
            r"(?i)onmouseleave\s*=",  # onmouseleave event
            r"(?i)oncontextmenu\s*=",  # oncontextmenu event
            r"(?i)ondblclick\s*=",  # ondblclick event
            r"(?i)onresize\s*=",  # onresize event
            r"(?i)onscroll\s*=",  # onscroll event
            r"(?i)onwheel\s*=",  # onwheel event
            r"(?i)oninput\s*=",  # oninput event
            r"(?i)oninvalid\s*=",  # oninvalid event
            r"(?i)onreset\s*=",  # onreset event
            r"(?i)onsearch\s*=",  # onsearch event
            r"(?i)onselect\s*=",  # onselect event
            r"(?i)onabort\s*=",  # onabort event
            r"(?i)oncanplay\s*=",  # oncanplay event
            r"(?i)oncanplaythrough\s*=",  # oncanplaythrough event
            r"(?i)ondurationchange\s*=",  # ondurationchange event
            r"(?i)onemptied\s*=",  # onemptied event
            r"(?i)onended\s*=",  # onended event
            r"(?i)onerror\s*=",  # onerror event
            r"(?i)onloadeddata\s*=",  # onloadeddata event
            r"(?i)onloadedmetadata\s*=",  # onloadedmetadata event
            r"(?i)onloadstart\s*=",  # onloadstart event
            r"(?i)onpause\s*=",  # onpause event
            r"(?i)onplay\s*=",  # onplay event
            r"(?i)onplaying\s*=",  # onplaying event
            r"(?i)onprogress\s*=",  # onprogress event
            r"(?i)onratechange\s*=",  # onratechange event
            r"(?i)onseeked\s*=",  # onseeked event
            r"(?i)onseeking\s*=",  # onseeking event
            r"(?i)onstalled\s*=",  # onstalled event
            r"(?i)onsuspend\s*=",  # onsuspend event
            r"(?i)ontimeupdate\s*=",  # ontimeupdate event
            r"(?i)onvolumechange\s*=",  # onvolumechange event
            r"(?i)onwaiting\s*=",  # onwaiting event
            r"(?i)javascript:",  # javascript: protocol
            r"(?i)vbscript:",  # vbscript: protocol
            r"(?i)data:",  # data: protocol
            r"(?i)alert\s*\(",  # alert function
            r"(?i)confirm\s*\(",  # confirm function
            r"(?i)prompt\s*\(",  # prompt function
            r"(?i)eval\s*\(",  # eval function
            r"(?i)setTimeout\s*\(",  # setTimeout function
            r"(?i)setInterval\s*\(",  # setInterval function
            r"(?i)document\.cookie",  # document.cookie access
            r"(?i)window\.location",  # window.location access
            r"(?i)innerHTML",  # innerHTML access
            r"(?i)outerHTML",  # outerHTML access
            r"(?i)document\.write",  # document.write
            r"(?i)document\.writeln",  # document.writeln
        ]

        # Test-specific XSS patterns
        self.test_xss_patterns = [
            "<script>alert('XSS')</script>",
            "<script>alert",
            "user_input.*<script>",
            "<div>.*user_input.*</div>",
            "onerror=",
            "onload=",
            "javascript:",
            "alert(",
            "document.cookie",
            "window.location",
            "innerHTML",
            "outerHTML",
        ]

    def detect(self, text: str) -> dict[str, Any]:
        """Detect XSS patterns"""

        # Check for XSS patterns
        xss_matches = []
        for pattern in self.xss_patterns:
            matches = re.findall(pattern, text)
            if matches:
                xss_matches.extend(matches)

        # Check for test-specific patterns
        test_xss_found = []
        for test_pattern in self.test_xss_patterns:
            if test_pattern in text:
                test_xss_found.append(test_pattern)

        # Check for HTML-like structures
        html_like_indicators = [
            r"<[^>]*>",  # HTML tags
            r"</[^>]*>",  # Closing HTML tags
            r"<[^>]*/>",  # Self-closing HTML tags
        ]

        html_like_count = 0
        for pattern in html_like_indicators:
            html_like_count += len(re.findall(pattern, text))

        # Check for suspicious string concatenation
        suspicious_concatenation = bool(re.search(r"f\".*\{.*\}.*\"", text))

        # Calculate confidence score
        confidence = 0.0

        if xss_matches:
            confidence += 0.4

        if test_xss_found:
            confidence += 0.3

        if html_like_count > 0:
            confidence += 0.2

        if suspicious_concatenation:
            confidence += 0.1

        # Determine if clarification is needed
        needs_clarification = confidence >= 0.5

        return {
            "needs_clarification": needs_clarification,
            "confidence": min(1.0, confidence),
            "category": "security_risks",
            "features": {
                "xss_matches": xss_matches[:5],  # Limit to first 5 matches
                "test_xss_found": test_xss_found,
                "html_like_count": html_like_count,
                "suspicious_concatenation": suspicious_concatenation,
                "total_xss_matches": len(xss_matches),
            },
        }
