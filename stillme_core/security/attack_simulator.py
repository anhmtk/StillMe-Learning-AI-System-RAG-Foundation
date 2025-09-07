# stillme_core/security/attack_simulator.py
"""
Attack simulation framework for security testing
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import aiohttp
import json
import time
import random
import string
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class AttackType(Enum):
    """Types of attacks to simulate"""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    DDOS = "ddos"
    AUTH_BYPASS = "auth_bypass"
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"
    BRUTE_FORCE = "brute_force"

@dataclass
class AttackPayload:
    """Attack payload representation"""
    attack_type: AttackType
    payload: str
    description: str
    severity: str
    expected_behavior: str
    mitigation: str

@dataclass
class AttackResult:
    """Result of an attack simulation"""
    attack_type: AttackType
    payload: str
    success: bool
    response_code: int
    response_time: float
    response_body: str
    vulnerability_detected: bool
    severity: str
    recommendations: List[str]

@dataclass
class AttackReport:
    """Comprehensive attack simulation report"""
    total_attacks: int
    successful_attacks: int
    vulnerabilities_found: int
    attack_results: List[AttackResult]
    security_score: float
    recommendations: List[str]
    test_duration: float

class AttackSimulator:
    """
    Comprehensive attack simulation framework
    """
    
    def __init__(self, target_url: str = "http://localhost:8000"):
        self.target_url = target_url
        self.payloads = self._load_attack_payloads()
        self.session = None
        
    def _load_attack_payloads(self) -> Dict[AttackType, List[AttackPayload]]:
        """Load attack payloads for different attack types"""
        payloads = {}
        
        # SQL Injection payloads
        payloads[AttackType.SQL_INJECTION] = [
            AttackPayload(
                attack_type=AttackType.SQL_INJECTION,
                payload="' OR '1'='1",
                description="Basic SQL injection bypass",
                severity="high",
                expected_behavior="Should be blocked or sanitized",
                mitigation="Use parameterized queries"
            ),
            AttackPayload(
                attack_type=AttackType.SQL_INJECTION,
                payload="'; DROP TABLE users; --",
                description="Destructive SQL injection",
                severity="critical",
                expected_behavior="Should be blocked",
                mitigation="Use parameterized queries and input validation"
            ),
            AttackPayload(
                attack_type=AttackType.SQL_INJECTION,
                payload="' UNION SELECT * FROM users --",
                description="Data extraction SQL injection",
                severity="high",
                expected_behavior="Should be blocked",
                mitigation="Use parameterized queries"
            )
        ]
        
        # XSS payloads
        payloads[AttackType.XSS] = [
            AttackPayload(
                attack_type=AttackType.XSS,
                payload="<script>alert('XSS')</script>",
                description="Basic XSS payload",
                severity="medium",
                expected_behavior="Should be escaped or blocked",
                mitigation="Escape HTML output and use CSP headers"
            ),
            AttackPayload(
                attack_type=AttackType.XSS,
                payload="<img src=x onerror=alert('XSS')>",
                description="Image-based XSS",
                severity="medium",
                expected_behavior="Should be blocked",
                mitigation="Validate and sanitize image sources"
            ),
            AttackPayload(
                attack_type=AttackType.XSS,
                payload="javascript:alert('XSS')",
                description="JavaScript protocol XSS",
                severity="medium",
                expected_behavior="Should be blocked",
                mitigation="Validate URLs and use allowlists"
            )
        ]
        
        # CSRF payloads
        payloads[AttackType.CSRF] = [
            AttackPayload(
                attack_type=AttackType.CSRF,
                payload="<form action='/api/delete' method='POST'><input type='submit' value='Delete'></form>",
                description="Basic CSRF form",
                severity="high",
                expected_behavior="Should require CSRF token",
                mitigation="Implement CSRF tokens"
            ),
            AttackPayload(
                attack_type=AttackType.CSRF,
                payload="<img src='/api/delete' width='1' height='1'>",
                description="Image-based CSRF",
                severity="high",
                expected_behavior="Should be blocked",
                mitigation="Implement CSRF tokens and validate referer"
            )
        ]
        
        # Path Traversal payloads
        payloads[AttackType.PATH_TRAVERSAL] = [
            AttackPayload(
                attack_type=AttackType.PATH_TRAVERSAL,
                payload="../../../etc/passwd",
                description="Basic path traversal",
                severity="high",
                expected_behavior="Should be blocked",
                mitigation="Validate and sanitize file paths"
            ),
            AttackPayload(
                attack_type=AttackType.PATH_TRAVERSAL,
                payload="..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
                description="Windows path traversal",
                severity="high",
                expected_behavior="Should be blocked",
                mitigation="Validate and sanitize file paths"
            )
        ]
        
        # Command Injection payloads
        payloads[AttackType.COMMAND_INJECTION] = [
            AttackPayload(
                attack_type=AttackType.COMMAND_INJECTION,
                payload="; ls -la",
                description="Basic command injection",
                severity="critical",
                expected_behavior="Should be blocked",
                mitigation="Use subprocess with shell=False and validate input"
            ),
            AttackPayload(
                attack_type=AttackType.COMMAND_INJECTION,
                payload="| cat /etc/passwd",
                description="Pipe-based command injection",
                severity="critical",
                expected_behavior="Should be blocked",
                mitigation="Use subprocess with shell=False"
            )
        ]
        
        # Authentication Bypass payloads
        payloads[AttackType.AUTH_BYPASS] = [
            AttackPayload(
                attack_type=AttackType.AUTH_BYPASS,
                payload="admin'--",
                description="SQL-based auth bypass",
                severity="critical",
                expected_behavior="Should be blocked",
                mitigation="Use parameterized queries and proper authentication"
            ),
            AttackPayload(
                attack_type=AttackType.AUTH_BYPASS,
                payload="admin' OR '1'='1'--",
                description="SQL-based auth bypass variant",
                severity="critical",
                expected_behavior="Should be blocked",
                mitigation="Use parameterized queries"
            )
        ]
        
        # Brute Force payloads
        payloads[AttackType.BRUTE_FORCE] = [
            AttackPayload(
                attack_type=AttackType.BRUTE_FORCE,
                payload="admin",
                description="Common username",
                severity="medium",
                expected_behavior="Should have rate limiting",
                mitigation="Implement rate limiting and account lockout"
            ),
            AttackPayload(
                attack_type=AttackType.BRUTE_FORCE,
                payload="password",
                description="Common password",
                severity="medium",
                expected_behavior="Should be blocked",
                mitigation="Enforce strong password policies"
            )
        ]
        
        return payloads
    
    async def simulate_attacks(self, attack_types: Optional[List[AttackType]] = None, 
                             endpoints: Optional[List[str]] = None) -> AttackReport:
        """Simulate attacks against target endpoints"""
        if attack_types is None:
            attack_types = list(AttackType)
        
        if endpoints is None:
            endpoints = ["/", "/api/", "/login", "/admin"]
        
        start_time = time.time()
        results = []
        
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            for attack_type in attack_types:
                if attack_type in self.payloads:
                    for payload in self.payloads[attack_type]:
                        for endpoint in endpoints:
                            result = await self._execute_attack(
                                attack_type, payload, endpoint
                            )
                            results.append(result)
        
        test_duration = time.time() - start_time
        
        return self._generate_attack_report(results, test_duration)
    
    async def _execute_attack(self, attack_type: AttackType, 
                            payload: AttackPayload, endpoint: str) -> AttackResult:
        """Execute a single attack"""
        start_time = time.time()
        
        try:
            # Prepare attack based on type
            if attack_type == AttackType.SQL_INJECTION:
                response = await self._sql_injection_attack(payload, endpoint)
            elif attack_type == AttackType.XSS:
                response = await self._xss_attack(payload, endpoint)
            elif attack_type == AttackType.CSRF:
                response = await self._csrf_attack(payload, endpoint)
            elif attack_type == AttackType.DDOS:
                response = await self._ddos_attack(payload, endpoint)
            elif attack_type == AttackType.AUTH_BYPASS:
                response = await self._auth_bypass_attack(payload, endpoint)
            elif attack_type == AttackType.PATH_TRAVERSAL:
                response = await self._path_traversal_attack(payload, endpoint)
            elif attack_type == AttackType.COMMAND_INJECTION:
                response = await self._command_injection_attack(payload, endpoint)
            elif attack_type == AttackType.BRUTE_FORCE:
                response = await self._brute_force_attack(payload, endpoint)
            else:
                response = await self._generic_attack(payload, endpoint)
            
            response_time = time.time() - start_time
            
            # Analyze response for vulnerabilities
            vulnerability_detected = self._analyze_response(response, attack_type, payload)
            
            # Generate recommendations
            recommendations = self._generate_attack_recommendations(
                attack_type, payload, response, vulnerability_detected
            )
            
            # Handle response safely
            if response and hasattr(response, 'status'):
                status_code = response.status
                response_text = await response.text() if hasattr(response, 'text') else str(response)
            else:
                status_code = 0
                response_text = str(response) if response else ""
            
            return AttackResult(
                attack_type=attack_type,
                payload=payload.payload,
                success=status_code < 400 if status_code else False,
                response_code=status_code,
                response_time=response_time,
                response_body=response_text,
                vulnerability_detected=vulnerability_detected,
                severity=payload.severity,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Attack execution failed: {e}")
            return AttackResult(
                attack_type=attack_type,
                payload=payload.payload,
                success=False,
                response_code=0,
                response_time=time.time() - start_time,
                response_body=str(e),
                vulnerability_detected=False,
                severity=payload.severity,
                recommendations=["Fix connection issues"]
            )
    
    async def _sql_injection_attack(self, payload: AttackPayload, endpoint: str):
        """Execute SQL injection attack"""
        data = {
            "username": payload.payload,
            "password": "test"
        }
        
        return await self.session.post(
            f"{self.target_url}{endpoint}",
            data=data
        )
    
    async def _xss_attack(self, payload: AttackPayload, endpoint: str):
        """Execute XSS attack"""
        data = {
            "comment": payload.payload,
            "name": "test"
        }
        
        return await self.session.post(
            f"{self.target_url}{endpoint}",
            data=data
        )
    
    async def _csrf_attack(self, payload: AttackPayload, endpoint: str):
        """Execute CSRF attack"""
        # Simulate CSRF by making request without proper headers
        return await self.session.post(
            f"{self.target_url}{endpoint}",
            data={"action": "delete"},
            headers={"Referer": "http://evil.com"},
            timeout=10
        )
    
    async def _ddos_attack(self, payload: AttackPayload, endpoint: str):
        """Execute DDoS simulation"""
        # Simulate multiple rapid requests
        tasks = []
        for _ in range(10):  # Limited for testing
            task = self.session.get(f"{self.target_url}{endpoint}", timeout=5)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        return responses[0] if responses else None
    
    async def _auth_bypass_attack(self, payload: AttackPayload, endpoint: str):
        """Execute authentication bypass attack"""
        data = {
            "username": payload.payload,
            "password": "anything"
        }
        
        return await self.session.post(
            f"{self.target_url}{endpoint}",
            data=data
        )
    
    async def _path_traversal_attack(self, payload: AttackPayload, endpoint: str):
        """Execute path traversal attack"""
        return await self.session.get(
            f"{self.target_url}{endpoint}?file={payload.payload}"
        )
    
    async def _command_injection_attack(self, payload: AttackPayload, endpoint: str):
        """Execute command injection attack"""
        data = {
            "command": payload.payload,
            "input": "test"
        }
        
        return await self.session.post(
            f"{self.target_url}{endpoint}",
            data=data
        )
    
    async def _brute_force_attack(self, payload: AttackPayload, endpoint: str):
        """Execute brute force attack simulation"""
        data = {
            "username": "admin",
            "password": payload.payload
        }
        
        return await self.session.post(
            f"{self.target_url}{endpoint}",
            data=data
        )
    
    async def _generic_attack(self, payload: AttackPayload, endpoint: str):
        """Execute generic attack"""
        return await self.session.get(
            f"{self.target_url}{endpoint}?test={payload.payload}"
        )
    
    def _analyze_response(self, response, attack_type: AttackType, 
                         payload: AttackPayload) -> bool:
        """Analyze response for vulnerability indicators"""
        if not response:
            return False
        
        response_text = response.text if hasattr(response, 'text') else str(response)
        
        # SQL Injection indicators
        if attack_type == AttackType.SQL_INJECTION:
            sql_errors = [
                "sql syntax", "mysql", "postgresql", "sqlite", "oracle",
                "database error", "sql error", "query failed"
            ]
            return any(error in response_text.lower() for error in sql_errors)
        
        # XSS indicators
        elif attack_type == AttackType.XSS:
            return payload.payload in response_text
        
        # CSRF indicators
        elif attack_type == AttackType.CSRF:
            return response.status == 200 and "success" in response_text.lower()
        
        # Path Traversal indicators
        elif attack_type == AttackType.PATH_TRAVERSAL:
            file_indicators = [
                "root:", "bin:", "etc:", "usr:", "var:", "windows", "system32"
            ]
            return any(indicator in response_text.lower() for indicator in file_indicators)
        
        # Command Injection indicators
        elif attack_type == AttackType.COMMAND_INJECTION:
            command_indicators = [
                "total", "drwx", "-rw-", "directory", "file", "permission"
            ]
            return any(indicator in response_text.lower() for indicator in command_indicators)
        
        # Auth Bypass indicators
        elif attack_type == AttackType.AUTH_BYPASS:
            return response.status == 200 and "welcome" in response_text.lower()
        
        # Brute Force indicators
        elif attack_type == AttackType.BRUTE_FORCE:
            return response.status == 200 and "login" not in response_text.lower()
        
        return False
    
    def _generate_attack_recommendations(self, attack_type: AttackType, 
                                       payload: AttackPayload, response,
                                       vulnerability_detected: bool) -> List[str]:
        """Generate recommendations based on attack results"""
        recommendations = []
        
        if vulnerability_detected:
            recommendations.append(f"🚨 VULNERABILITY DETECTED: {payload.description}")
            recommendations.append(f"Mitigation: {payload.mitigation}")
            
            if attack_type == AttackType.SQL_INJECTION:
                recommendations.append("Implement parameterized queries")
                recommendations.append("Use input validation and sanitization")
            elif attack_type == AttackType.XSS:
                recommendations.append("Implement output encoding")
                recommendations.append("Use Content Security Policy (CSP) headers")
            elif attack_type == AttackType.CSRF:
                recommendations.append("Implement CSRF tokens")
                recommendations.append("Validate Referer header")
            elif attack_type == AttackType.PATH_TRAVERSAL:
                recommendations.append("Validate and sanitize file paths")
                recommendations.append("Use allowlists for file access")
            elif attack_type == AttackType.COMMAND_INJECTION:
                recommendations.append("Use subprocess with shell=False")
                recommendations.append("Validate and sanitize command inputs")
            elif attack_type == AttackType.AUTH_BYPASS:
                recommendations.append("Implement proper authentication")
                recommendations.append("Use parameterized queries for login")
            elif attack_type == AttackType.BRUTE_FORCE:
                recommendations.append("Implement rate limiting")
                recommendations.append("Use account lockout mechanisms")
        else:
            recommendations.append(f"✅ Attack blocked: {payload.description}")
        
        return recommendations
    
    def _generate_attack_report(self, results: List[AttackResult], 
                              duration: float) -> AttackReport:
        """Generate comprehensive attack report"""
        total_attacks = len(results)
        successful_attacks = sum(1 for r in results if r.success)
        vulnerabilities_found = sum(1 for r in results if r.vulnerability_detected)
        
        # Calculate security score (0-100)
        if total_attacks == 0:
            security_score = 100.0
        else:
            vulnerability_rate = vulnerabilities_found / total_attacks
            security_score = max(0.0, 100.0 - (vulnerability_rate * 100))
        
        # Generate overall recommendations
        recommendations = self._generate_overall_recommendations(results, security_score)
        
        return AttackReport(
            total_attacks=total_attacks,
            successful_attacks=successful_attacks,
            vulnerabilities_found=vulnerabilities_found,
            attack_results=results,
            security_score=security_score,
            recommendations=recommendations,
            test_duration=duration
        )
    
    def _generate_overall_recommendations(self, results: List[AttackResult], 
                                        security_score: float) -> List[str]:
        """Generate overall security recommendations"""
        recommendations = []
        
        if security_score >= 90:
            recommendations.append("🛡️ Excellent security posture! Keep up the good work.")
        elif security_score >= 70:
            recommendations.append("👍 Good security posture. Address remaining vulnerabilities.")
        elif security_score >= 50:
            recommendations.append("⚠️ Moderate security posture. Several vulnerabilities need attention.")
        else:
            recommendations.append("🚨 Poor security posture. Immediate action required.")
        
        # Count vulnerabilities by type
        vuln_by_type = {}
        for result in results:
            if result.vulnerability_detected:
                vuln_type = result.attack_type.value
                vuln_by_type[vuln_type] = vuln_by_type.get(vuln_type, 0) + 1
        
        # Add specific recommendations
        for vuln_type, count in vuln_by_type.items():
            if count > 0:
                recommendations.append(f"🔍 {count} {vuln_type} vulnerabilities found")
        
        return recommendations
