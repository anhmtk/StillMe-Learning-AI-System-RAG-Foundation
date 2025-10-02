"""
HTTP Fuzz Testing for Security
Tests for OWASP ZAP baseline scan and custom fuzz testing
"""

import json
import time
from typing import Any

import requests

from stillme_core.security import RateLimiter, SecurityAuditLogger, SecurityHeaders


class HTTPFuzzTester:
    """HTTP fuzz testing implementation"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.security_headers = SecurityHeaders()
        self.rate_limiter = RateLimiter()
        self.audit_logger = SecurityAuditLogger()
        self.findings = []

    def test_sql_injection(self) -> list[dict[str, Any]]:
        """Test for SQL injection vulnerabilities"""
        findings = []
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "1' OR 1=1 --",
            "admin'--",
            "admin'/*",
            "' OR 1=1#",
            "' OR 'x'='x",
        ]

        test_endpoints = ["/api/users", "/api/login", "/api/search", "/api/data"]

        for endpoint in test_endpoints:
            for payload in sql_payloads:
                try:
                    # Test GET request
                    response = requests.get(
                        f"{self.base_url}{endpoint}",
                        params={"q": payload, "id": payload},
                        timeout=5,
                    )

                    if self._check_sql_injection_response(response, payload):
                        findings.append(
                            {
                                "type": "sql_injection",
                                "endpoint": endpoint,
                                "payload": payload,
                                "method": "GET",
                                "status_code": response.status_code,
                                "severity": "HIGH",
                            }
                        )

                    # Test POST request
                    response = requests.post(
                        f"{self.base_url}{endpoint}",
                        json={"query": payload, "id": payload},
                        timeout=5,
                    )

                    if self._check_sql_injection_response(response, payload):
                        findings.append(
                            {
                                "type": "sql_injection",
                                "endpoint": endpoint,
                                "payload": payload,
                                "method": "POST",
                                "status_code": response.status_code,
                                "severity": "HIGH",
                            }
                        )

                except requests.exceptions.RequestException:
                    continue

        return findings

    def test_xss_injection(self) -> list[dict[str, Any]]:
        """Test for XSS vulnerabilities"""
        findings = []
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//",
            "\"><script>alert('XSS')</script>",
            "<iframe src=javascript:alert('XSS')>",
            "<body onload=alert('XSS')>",
        ]

        test_endpoints = ["/api/search", "/api/comment", "/api/feedback", "/api/user"]

        for endpoint in test_endpoints:
            for payload in xss_payloads:
                try:
                    response = requests.get(
                        f"{self.base_url}{endpoint}",
                        params={"q": payload, "comment": payload},
                        timeout=5,
                    )

                    if self._check_xss_response(response, payload):
                        findings.append(
                            {
                                "type": "xss_injection",
                                "endpoint": endpoint,
                                "payload": payload,
                                "method": "GET",
                                "status_code": response.status_code,
                                "severity": "MEDIUM",
                            }
                        )

                except requests.exceptions.RequestException:
                    continue

        return findings

    def test_path_traversal(self) -> list[dict[str, Any]]:
        """Test for path traversal vulnerabilities"""
        findings = []
        path_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd",
            "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",
        ]

        test_endpoints = ["/api/file", "/api/download", "/api/read", "/api/view"]

        for endpoint in test_endpoints:
            for payload in path_payloads:
                try:
                    response = requests.get(
                        f"{self.base_url}{endpoint}",
                        params={"file": payload, "path": payload},
                        timeout=5,
                    )

                    if self._check_path_traversal_response(response, payload):
                        findings.append(
                            {
                                "type": "path_traversal",
                                "endpoint": endpoint,
                                "payload": payload,
                                "method": "GET",
                                "status_code": response.status_code,
                                "severity": "HIGH",
                            }
                        )

                except requests.exceptions.RequestException:
                    continue

        return findings

    def test_command_injection(self) -> list[dict[str, Any]]:
        """Test for command injection vulnerabilities"""
        findings = []
        command_payloads = [
            "; ls -la",
            "| whoami",
            "& dir",
            "` id `",
            "$(whoami)",
            "; cat /etc/passwd",
            "| type C:\\Windows\\System32\\drivers\\etc\\hosts",
        ]

        test_endpoints = ["/api/exec", "/api/run", "/api/command", "/api/system"]

        for endpoint in test_endpoints:
            for payload in command_payloads:
                try:
                    response = requests.post(
                        f"{self.base_url}{endpoint}",
                        json={"command": payload, "input": payload},
                        timeout=5,
                    )

                    if self._check_command_injection_response(response, payload):
                        findings.append(
                            {
                                "type": "command_injection",
                                "endpoint": endpoint,
                                "payload": payload,
                                "method": "POST",
                                "status_code": response.status_code,
                                "severity": "CRITICAL",
                            }
                        )

                except requests.exceptions.RequestException:
                    continue

        return findings

    def test_header_anomalies(self) -> list[dict[str, Any]]:
        """Test for header-based vulnerabilities"""
        findings = []

        # Test for missing security headers
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            missing_headers = self._check_missing_security_headers(response)

            if missing_headers:
                findings.append(
                    {
                        "type": "missing_security_headers",
                        "endpoint": "/",
                        "missing_headers": missing_headers,
                        "severity": "MEDIUM",
                    }
                )

        except requests.exceptions.RequestException:
            pass

        # Test for header injection
        header_payloads = [
            "test\r\nX-Injected: malicious",
            "test%0d%0aX-Injected: malicious",
            "test\nX-Injected: malicious",
        ]

        for payload in header_payloads:
            try:
                response = requests.get(
                    f"{self.base_url}/api/test",
                    headers={"User-Agent": payload},
                    timeout=5,
                )

                if "X-Injected" in response.headers:
                    findings.append(
                        {
                            "type": "header_injection",
                            "payload": payload,
                            "severity": "HIGH",
                        }
                    )

            except requests.exceptions.RequestException:
                continue

        return findings

    def test_rate_limiting(self) -> list[dict[str, Any]]:
        """Test rate limiting implementation"""
        findings = []

        # Test rate limit bypass
        try:
            # Send rapid requests
            for i in range(150):  # Exceed typical rate limit
                response = requests.get(f"{self.base_url}/api/test", timeout=1)

                if response.status_code == 429:
                    # Rate limit is working
                    break
                elif i == 149:
                    # No rate limiting detected
                    findings.append(
                        {
                            "type": "rate_limit_bypass",
                            "endpoint": "/api/test",
                            "requests_sent": 150,
                            "severity": "MEDIUM",
                        }
                    )

        except requests.exceptions.RequestException:
            pass

        return findings

    def run_all_tests(self) -> dict[str, Any]:
        """Run all fuzz tests"""
        print("🔍 Starting HTTP fuzz testing...")

        all_findings = []

        # Run individual tests
        print("  Testing SQL injection...")
        all_findings.extend(self.test_sql_injection())

        print("  Testing XSS injection...")
        all_findings.extend(self.test_xss_injection())

        print("  Testing path traversal...")
        all_findings.extend(self.test_path_traversal())

        print("  Testing command injection...")
        all_findings.extend(self.test_command_injection())

        print("  Testing header anomalies...")
        all_findings.extend(self.test_header_anomalies())

        print("  Testing rate limiting...")
        all_findings.extend(self.test_rate_limiting())

        # Generate summary
        summary = self._generate_summary(all_findings)

        return {"findings": all_findings, "summary": summary, "timestamp": time.time()}

    def _check_sql_injection_response(
        self, response: requests.Response, payload: str
    ) -> bool:
        """Check if response indicates SQL injection vulnerability"""
        if response.status_code == 500:
            return True

        response_text = response.text.lower()
        sql_error_indicators = [
            "sql syntax",
            "mysql error",
            "postgresql error",
            "sqlite error",
            "database error",
            "syntax error",
            "query failed",
        ]

        return any(indicator in response_text for indicator in sql_error_indicators)

    def _check_xss_response(self, response: requests.Response, payload: str) -> bool:
        """Check if response indicates XSS vulnerability"""
        return payload in response.text

    def _check_path_traversal_response(
        self, response: requests.Response, payload: str
    ) -> bool:
        """Check if response indicates path traversal vulnerability"""
        if response.status_code == 200:
            response_text = response.text.lower()
            path_traversal_indicators = [
                "root:",
                "bin:",
                "daemon:",
                "127.0.0.1",
                "localhost",
                "windows system32",
            ]

            return any(
                indicator in response_text for indicator in path_traversal_indicators
            )

        return False

    def _check_command_injection_response(
        self, response: requests.Response, payload: str
    ) -> bool:
        """Check if response indicates command injection vulnerability"""
        if response.status_code == 200:
            response_text = response.text.lower()
            command_indicators = [
                "uid=",
                "gid=",
                "groups=",
                "total ",
                "drwx",
                "volume in drive",
            ]

            return any(indicator in response_text for indicator in command_indicators)

        return False

    def _check_missing_security_headers(self, response: requests.Response) -> list[str]:
        """Check for missing security headers"""
        required_headers = [
            "Content-Security-Policy",
            "Strict-Transport-Security",
            "X-Content-Type-Options",
            "X-Frame-Options",
            "Referrer-Policy",
        ]

        missing_headers = []
        for header in required_headers:
            if header not in response.headers:
                missing_headers.append(header)

        return missing_headers

    def _generate_summary(self, findings: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate test summary"""
        severity_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        type_counts = {}

        for finding in findings:
            severity = finding.get("severity", "LOW")
            finding_type = finding.get("type", "unknown")

            severity_counts[severity] += 1
            type_counts[finding_type] = type_counts.get(finding_type, 0) + 1

        return {
            "total_findings": len(findings),
            "severity_counts": severity_counts,
            "type_counts": type_counts,
            "high_risk_findings": severity_counts["HIGH"] + severity_counts["CRITICAL"],
        }


def main():
    """Main function to run fuzz tests"""
    import os

    # Create artifacts directory
    os.makedirs("artifacts", exist_ok=True)

    # Run fuzz tests
    fuzz_tester = HTTPFuzzTester()
    results = fuzz_tester.run_all_tests()

    # Save results
    with open("artifacts/fuzz-findings.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Print summary
    summary = results["summary"]
    print("\n📊 Fuzz Test Summary:")
    print(f"  Total findings: {summary['total_findings']}")
    print(f"  High risk findings: {summary['high_risk_findings']}")
    print(f"  Severity breakdown: {summary['severity_counts']}")
    print(f"  Type breakdown: {summary['type_counts']}")

    if summary["high_risk_findings"] > 0:
        print(f"\n⚠️  {summary['high_risk_findings']} high-risk findings detected!")
        return 1
    else:
        print("\n✅ No high-risk findings detected")
        return 0


if __name__ == "__main__":
    exit(main())
