#!/usr/bin/env python3
"""
Security Analyzer - Senior Developer Security Thinking Module
Tư duy bảo mật như dev chuyên nghiệp thật - BẢO MẬT LÀ VẤN ĐỀ SỐNG CÒN

Tính năng:
1. Vulnerability Detection - Phát hiện lỗ hổng bảo mật
2. Security Best Practices - Kiểm tra best practices
3. Threat Modeling - Mô hình hóa mối đe dọa
4. Compliance Checking - Kiểm tra tuân thủ
5. Risk Assessment - Đánh giá rủi ro
6. Security Architecture Review - Đánh giá kiến trúc bảo mật
7. Incident Response Planning - Lập kế hoạch ứng phó sự cố
"""

import re
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class SecurityLevel(Enum):
    """Mức độ bảo mật"""
    CRITICAL = "critical"      # Sống còn
    HIGH = "high"             # Cao
    MEDIUM = "medium"         # Trung bình
    LOW = "low"               # Thấp
    MINIMAL = "minimal"       # Tối thiểu

class ThreatLevel(Enum):
    """Mức độ đe dọa"""
    CRITICAL = "critical"      # Nguy hiểm cực độ
    HIGH = "high"             # Nguy hiểm cao
    MEDIUM = "medium"         # Nguy hiểm trung bình
    LOW = "low"               # Nguy hiểm thấp
    MINIMAL = "minimal"       # Nguy hiểm tối thiểu

class ComplianceStandard(Enum):
    """Tiêu chuẩn tuân thủ"""
    GDPR = "gdpr"             # General Data Protection Regulation
    SOX = "sox"               # Sarbanes-Oxley Act
    HIPAA = "hipaa"           # Health Insurance Portability and Accountability Act
    PCI_DSS = "pci_dss"       # Payment Card Industry Data Security Standard
    ISO27001 = "iso27001"     # ISO/IEC 27001
    NIST = "nist"             # NIST Cybersecurity Framework

@dataclass
class Vulnerability:
    """Lỗ hổng bảo mật"""
    vulnerability_type: str
    severity: SecurityLevel
    description: str
    affected_components: List[str]
    exploitability: str        # "easy", "moderate", "difficult"
    impact: str               # "low", "medium", "high", "critical"
    remediation: List[str]    # Cách khắc phục
    references: List[str]     # Tài liệu tham khảo

@dataclass
class SecurityBestPractice:
    """Best practice bảo mật"""
    practice_name: str
    category: str             # "authentication", "authorization", "encryption", etc.
    importance: SecurityLevel
    description: str
    implementation_guidance: List[str]
    compliance_requirements: List[ComplianceStandard]

@dataclass
class ThreatModel:
    """Mô hình mối đe dọa"""
    threat_actor: str         # "external_attacker", "insider", "malware", etc.
    attack_vector: str        # "network", "application", "physical", etc.
    threat_level: ThreatLevel
    potential_impact: str
    mitigation_strategies: List[str]
    detection_methods: List[str]

@dataclass
class ComplianceCheck:
    """Kiểm tra tuân thủ"""
    standard: ComplianceStandard
    requirement: str
    compliance_status: str    # "compliant", "non_compliant", "partial"
    evidence: List[str]
    remediation_actions: List[str]
    risk_level: SecurityLevel

@dataclass
class SecurityRisk:
    """Rủi ro bảo mật"""
    risk_id: str
    risk_name: str
    risk_level: SecurityLevel
    probability: float        # 0-1
    impact: float            # 0-1
    risk_score: float        # probability * impact
    description: str
    affected_assets: List[str]
    mitigation_controls: List[str]
    residual_risk: SecurityLevel

@dataclass
class SecurityArchitecture:
    """Kiến trúc bảo mật"""
    defense_in_depth: bool
    zero_trust_implementation: bool
    encryption_at_rest: bool
    encryption_in_transit: bool
    access_controls: List[str]
    monitoring_capabilities: List[str]
    incident_response_plan: bool
    security_gaps: List[str]
    recommendations: List[str]

@dataclass
class SecurityAnalysisResult:
    """Kết quả phân tích bảo mật"""
    overall_security_score: float      # 0-1
    security_level: SecurityLevel
    vulnerabilities: List[Vulnerability]
    best_practices: List[SecurityBestPractice]
    threat_models: List[ThreatModel]
    compliance_checks: List[ComplianceCheck]
    security_risks: List[SecurityRisk]
    architecture_review: SecurityArchitecture
    
    critical_issues: List[str]
    immediate_actions: List[str]
    security_recommendations: List[str]
    compliance_gaps: List[str]
    analysis_time: float

class SecurityAnalyzer:
    """Senior Developer Security Analyzer - BẢO MẬT LÀ VẤN ĐỀ SỐNG CÒN"""
    
    def __init__(self):
        self.vulnerability_patterns = self._load_vulnerability_patterns()
        self.best_practice_patterns = self._load_best_practice_patterns()
        self.threat_patterns = self._load_threat_patterns()
        self.compliance_patterns = self._load_compliance_patterns()
        
    def _load_vulnerability_patterns(self) -> Dict[str, Dict]:
        """Load vulnerability detection patterns"""
        return {
            'sql_injection': {
                'patterns': [
                    r'execute\(.*\+', r'cursor\.execute\(.*%', r'query.*format\(',
                    r'SELECT.*\+', r'INSERT.*\+', r'UPDATE.*\+', r'DELETE.*\+',
                    r'f".*SELECT', r'f".*INSERT', r'f".*UPDATE', r'f".*DELETE'
                ],
                'severity': SecurityLevel.CRITICAL,
                'exploitability': 'easy',
                'impact': 'critical'
            },
            'xss_vulnerability': {
                'patterns': [
                    r'innerHTML\s*=', r'document\.write\(', r'eval\(',
                    r'\.html\(', r'\.append\(.*\+', r'innerText\s*=.*\+'
                ],
                'severity': SecurityLevel.HIGH,
                'exploitability': 'easy',
                'impact': 'high'
            },
            'path_traversal': {
                'patterns': [
                    r'open\(.*\.\.', r'os\.path\.join\(.*\.\.', r'file.*\.\.',
                    r'\.\./', r'\.\.\\', r'%2e%2e', r'%2E%2E'
                ],
                'severity': SecurityLevel.HIGH,
                'exploitability': 'moderate',
                'impact': 'high'
            },
            'hardcoded_secrets': {
                'patterns': [
                    r'password\s*=\s*["\'][^"\']+["\']', r'api_key\s*=\s*["\'][^"\']+["\']',
                    r'token\s*=\s*["\'][^"\']+["\']', r'secret\s*=\s*["\'][^"\']+["\']',
                    r'private_key\s*=\s*["\'][^"\']+["\']', r'access_key\s*=\s*["\'][^"\']+["\']'
                ],
                'severity': SecurityLevel.CRITICAL,
                'exploitability': 'easy',
                'impact': 'critical'
            },
            'insecure_random': {
                'patterns': [
                    r'random\.random\(\)', r'random\.randint\(', r'random\.choice\(',
                    r'Math\.random\(\)', r'rand\(\)', r'random\(\)'
                ],
                'severity': SecurityLevel.MEDIUM,
                'exploitability': 'moderate',
                'impact': 'medium'
            },
            'weak_encryption': {
                'patterns': [
                    r'MD5\(', r'SHA1\(', r'DES\(', r'RC4\(',
                    r'encrypt.*md5', r'encrypt.*sha1', r'hash.*md5'
                ],
                'severity': SecurityLevel.HIGH,
                'exploitability': 'moderate',
                'impact': 'high'
            },
            'insecure_communication': {
                'patterns': [
                    r'http://', r'ftp://', r'telnet://', r'ftp://',
                    r'ws://', r'wss://.*false', r'ssl.*false'
                ],
                'severity': SecurityLevel.HIGH,
                'exploitability': 'easy',
                'impact': 'high'
            },
            'authentication_bypass': {
                'patterns': [
                    r'if.*admin.*true', r'if.*user.*admin', r'bypass.*auth',
                    r'skip.*authentication', r'disable.*auth'
                ],
                'severity': SecurityLevel.CRITICAL,
                'exploitability': 'easy',
                'impact': 'critical'
            }
        }
    
    def _load_best_practice_patterns(self) -> Dict[str, Dict]:
        """Load security best practice patterns"""
        return {
            'authentication': {
                'patterns': [
                    r'multi.*factor', r'2fa', r'mfa', r'biometric',
                    r'strong.*password', r'password.*policy', r'account.*lockout'
                ],
                'importance': SecurityLevel.CRITICAL,
                'category': 'authentication'
            },
            'authorization': {
                'patterns': [
                    r'role.*based', r'rbac', r'principle.*least.*privilege',
                    r'access.*control', r'permission.*check', r'authorization'
                ],
                'importance': SecurityLevel.HIGH,
                'category': 'authorization'
            },
            'encryption': {
                'patterns': [
                    r'aes.*256', r'rsa.*2048', r'tls.*1\.3', r'https',
                    r'encrypt.*data', r'encryption.*at.*rest', r'encryption.*in.*transit'
                ],
                'importance': SecurityLevel.CRITICAL,
                'category': 'encryption'
            },
            'input_validation': {
                'patterns': [
                    r'validate.*input', r'sanitize.*input', r'whitelist',
                    r'parameterized.*query', r'prepared.*statement'
                ],
                'importance': SecurityLevel.HIGH,
                'category': 'input_validation'
            },
            'logging_monitoring': {
                'patterns': [
                    r'audit.*log', r'security.*log', r'monitor.*access',
                    r'intrusion.*detection', r'siem', r'security.*monitoring'
                ],
                'importance': SecurityLevel.HIGH,
                'category': 'logging_monitoring'
            },
            'secure_coding': {
                'patterns': [
                    r'secure.*coding', r'owasp', r'security.*review',
                    r'code.*analysis', r'static.*analysis', r'dynamic.*analysis'
                ],
                'importance': SecurityLevel.HIGH,
                'category': 'secure_coding'
            }
        }
    
    def _load_threat_patterns(self) -> Dict[str, Dict]:
        """Load threat modeling patterns"""
        return {
            'external_attacker': {
                'patterns': ['external', 'hacker', 'attacker', 'malicious'],
                'threat_level': ThreatLevel.HIGH,
                'attack_vectors': ['network', 'application', 'social_engineering']
            },
            'insider_threat': {
                'patterns': ['insider', 'employee', 'contractor', 'privileged'],
                'threat_level': ThreatLevel.MEDIUM,
                'attack_vectors': ['physical', 'application', 'data_access']
            },
            'malware': {
                'patterns': ['malware', 'virus', 'trojan', 'ransomware'],
                'threat_level': ThreatLevel.HIGH,
                'attack_vectors': ['network', 'email', 'usb', 'download']
            },
            'data_breach': {
                'patterns': ['data.*breach', 'data.*leak', 'exfiltration'],
                'threat_level': ThreatLevel.CRITICAL,
                'attack_vectors': ['database', 'api', 'file_system']
            },
            'ddos': {
                'patterns': ['ddos', 'denial.*service', 'overload'],
                'threat_level': ThreatLevel.MEDIUM,
                'attack_vectors': ['network', 'application']
            }
        }
    
    def _load_compliance_patterns(self) -> Dict[str, Dict]:
        """Load compliance checking patterns"""
        return {
            'gdpr': {
                'patterns': ['gdpr', 'personal.*data', 'privacy', 'consent'],
                'standard': ComplianceStandard.GDPR,
                'requirements': ['data_protection', 'consent_management', 'right_to_be_forgotten']
            },
            'sox': {
                'patterns': ['sox', 'financial.*control', 'audit', 'compliance'],
                'standard': ComplianceStandard.SOX,
                'requirements': ['financial_reporting', 'internal_controls', 'audit_trail']
            },
            'hipaa': {
                'patterns': ['hipaa', 'health.*data', 'phi', 'medical'],
                'standard': ComplianceStandard.HIPAA,
                'requirements': ['health_data_protection', 'access_controls', 'encryption']
            },
            'pci_dss': {
                'patterns': ['pci', 'payment.*card', 'credit.*card', 'cardholder'],
                'standard': ComplianceStandard.PCI_DSS,
                'requirements': ['cardholder_data_protection', 'secure_networks', 'access_control']
            }
        }
    
    def detect_vulnerabilities(self, task: str) -> List[Vulnerability]:
        """Phát hiện lỗ hổng bảo mật"""
        vulnerabilities = []
        task_lower = task.lower()
        
        for vuln_type, vuln_info in self.vulnerability_patterns.items():
            for pattern in vuln_info['patterns']:
                if re.search(pattern, task_lower):
                    vulnerability = Vulnerability(
                        vulnerability_type=vuln_type,
                        severity=vuln_info['severity'],
                        description=f"Potential {vuln_type} vulnerability detected",
                        affected_components=[task],
                        exploitability=vuln_info['exploitability'],
                        impact=vuln_info['impact'],
                        remediation=self._get_remediation_actions(vuln_type),
                        references=self._get_security_references(vuln_type)
                    )
                    vulnerabilities.append(vulnerability)
                    break  # Avoid duplicate detections
        
        return vulnerabilities
    
    def _get_remediation_actions(self, vuln_type: str) -> List[str]:
        """Get remediation actions for vulnerability type"""
        remediation_map = {
            'sql_injection': [
                "Use parameterized queries or prepared statements",
                "Implement input validation and sanitization",
                "Use ORM with built-in SQL injection protection",
                "Apply principle of least privilege to database users"
            ],
            'xss_vulnerability': [
                "Sanitize and validate all user input",
                "Use Content Security Policy (CSP)",
                "Escape output properly (HTML, JavaScript, CSS)",
                "Implement XSS filters and validation"
            ],
            'path_traversal': [
                "Validate and sanitize file paths",
                "Use whitelist of allowed directories",
                "Implement proper access controls",
                "Use chroot or sandboxing for file operations"
            ],
            'hardcoded_secrets': [
                "Use environment variables for secrets",
                "Implement secret management system (e.g., HashiCorp Vault)",
                "Never commit secrets to version control",
                "Use secure key derivation functions"
            ],
            'insecure_random': [
                "Use cryptographically secure random number generators",
                "Use secrets module for Python",
                "Use crypto.getRandomValues() for JavaScript",
                "Implement proper random number generation"
            ],
            'weak_encryption': [
                "Use strong encryption algorithms (AES-256, RSA-2048+)",
                "Use secure hash functions (SHA-256, SHA-3)",
                "Implement proper key management",
                "Use TLS 1.3 for secure communication"
            ],
            'insecure_communication': [
                "Use HTTPS instead of HTTP",
                "Implement certificate pinning",
                "Use secure protocols (TLS 1.3, SSH)",
                "Disable insecure protocols and ciphers"
            ],
            'authentication_bypass': [
                "Implement proper authentication mechanisms",
                "Use multi-factor authentication",
                "Implement session management",
                "Remove authentication bypass code"
            ]
        }
        return remediation_map.get(vuln_type, ["Review and fix security vulnerability"])
    
    def _get_security_references(self, vuln_type: str) -> List[str]:
        """Get security references for vulnerability type"""
        references_map = {
            'sql_injection': [
                "OWASP SQL Injection Prevention Cheat Sheet",
                "CWE-89: Improper Neutralization of Special Elements"
            ],
            'xss_vulnerability': [
                "OWASP XSS Prevention Cheat Sheet",
                "CWE-79: Improper Neutralization of Input"
            ],
            'path_traversal': [
                "OWASP Path Traversal Prevention",
                "CWE-22: Improper Limitation of Pathname"
            ],
            'hardcoded_secrets': [
                "OWASP Secure Coding Practices",
                "CWE-798: Use of Hard-coded Credentials"
            ],
            'insecure_random': [
                "OWASP Cryptographic Storage Cheat Sheet",
                "CWE-330: Use of Insufficiently Random Values"
            ],
            'weak_encryption': [
                "OWASP Cryptographic Storage Cheat Sheet",
                "NIST Cryptographic Standards"
            ],
            'insecure_communication': [
                "OWASP Transport Layer Protection Cheat Sheet",
                "CWE-319: Cleartext Transmission of Sensitive Information"
            ],
            'authentication_bypass': [
                "OWASP Authentication Cheat Sheet",
                "CWE-287: Improper Authentication"
            ]
        }
        return references_map.get(vuln_type, ["OWASP Top 10", "CWE Database"])
    
    def check_best_practices(self, task: str) -> List[SecurityBestPractice]:
        """Kiểm tra security best practices"""
        best_practices = []
        task_lower = task.lower()
        
        for practice_type, practice_info in self.best_practice_patterns.items():
            for pattern in practice_info['patterns']:
                if re.search(pattern, task_lower):
                    best_practice = SecurityBestPractice(
                        practice_name=practice_type,
                        category=practice_info['category'],
                        importance=practice_info['importance'],
                        description=f"Security best practice: {practice_type}",
                        implementation_guidance=self._get_implementation_guidance(practice_type),
                        compliance_requirements=self._get_compliance_requirements(practice_type)
                    )
                    best_practices.append(best_practice)
                    break
        
        return best_practices
    
    def _get_implementation_guidance(self, practice_type: str) -> List[str]:
        """Get implementation guidance for best practice"""
        guidance_map = {
            'authentication': [
                "Implement multi-factor authentication (MFA)",
                "Use strong password policies",
                "Implement account lockout mechanisms",
                "Use secure session management"
            ],
            'authorization': [
                "Implement role-based access control (RBAC)",
                "Apply principle of least privilege",
                "Implement proper access controls",
                "Regular access reviews and audits"
            ],
            'encryption': [
                "Use AES-256 for data encryption",
                "Use RSA-2048+ for key exchange",
                "Implement TLS 1.3 for communication",
                "Use secure key management practices"
            ],
            'input_validation': [
                "Validate all user inputs",
                "Use whitelist validation",
                "Implement proper sanitization",
                "Use parameterized queries"
            ],
            'logging_monitoring': [
                "Implement comprehensive audit logging",
                "Monitor security events",
                "Use SIEM for log analysis",
                "Implement intrusion detection"
            ],
            'secure_coding': [
                "Follow OWASP secure coding practices",
                "Implement code security reviews",
                "Use static and dynamic analysis tools",
                "Regular security training for developers"
            ]
        }
        return guidance_map.get(practice_type, ["Follow security best practices"])
    
    def _get_compliance_requirements(self, practice_type: str) -> List[ComplianceStandard]:
        """Get compliance requirements for best practice"""
        compliance_map = {
            'authentication': [ComplianceStandard.GDPR, ComplianceStandard.SOX, ComplianceStandard.HIPAA],
            'authorization': [ComplianceStandard.GDPR, ComplianceStandard.SOX, ComplianceStandard.HIPAA],
            'encryption': [ComplianceStandard.GDPR, ComplianceStandard.HIPAA, ComplianceStandard.PCI_DSS],
            'input_validation': [ComplianceStandard.GDPR, ComplianceStandard.PCI_DSS],
            'logging_monitoring': [ComplianceStandard.SOX, ComplianceStandard.HIPAA],
            'secure_coding': [ComplianceStandard.ISO27001, ComplianceStandard.NIST]
        }
        return compliance_map.get(practice_type, [ComplianceStandard.ISO27001])
    
    def model_threats(self, task: str) -> List[ThreatModel]:
        """Mô hình hóa mối đe dọa"""
        threat_models = []
        task_lower = task.lower()
        
        for threat_type, threat_info in self.threat_patterns.items():
            for pattern in threat_info['patterns']:
                if re.search(pattern, task_lower):
                    threat_model = ThreatModel(
                        threat_actor=threat_type,
                        attack_vector=threat_info['attack_vectors'][0],
                        threat_level=threat_info['threat_level'],
                        potential_impact=self._get_threat_impact(threat_type),
                        mitigation_strategies=self._get_threat_mitigations(threat_type),
                        detection_methods=self._get_threat_detection(threat_type)
                    )
                    threat_models.append(threat_model)
                    break
        
        return threat_models
    
    def _get_threat_impact(self, threat_type: str) -> str:
        """Get potential impact of threat"""
        impact_map = {
            'external_attacker': 'Data breach, system compromise, financial loss',
            'insider_threat': 'Data theft, system sabotage, intellectual property theft',
            'malware': 'System infection, data encryption, network compromise',
            'data_breach': 'Regulatory fines, reputation damage, legal liability',
            'ddos': 'Service unavailability, revenue loss, customer impact'
        }
        return impact_map.get(threat_type, 'System compromise and data loss')
    
    def _get_threat_mitigations(self, threat_type: str) -> List[str]:
        """Get mitigation strategies for threat"""
        mitigation_map = {
            'external_attacker': [
                'Implement network segmentation',
                'Use intrusion detection systems',
                'Regular security updates and patches',
                'Employee security awareness training'
            ],
            'insider_threat': [
                'Implement least privilege access',
                'Monitor user activities',
                'Regular access reviews',
                'Background checks for sensitive roles'
            ],
            'malware': [
                'Deploy endpoint protection',
                'Implement email security',
                'Regular security updates',
                'User security training'
            ],
            'data_breach': [
                'Implement data encryption',
                'Use data loss prevention (DLP)',
                'Regular security assessments',
                'Incident response planning'
            ],
            'ddos': [
                'Implement DDoS protection',
                'Use content delivery networks',
                'Load balancing and redundancy',
                'Traffic monitoring and filtering'
            ]
        }
        return mitigation_map.get(threat_type, ['Implement comprehensive security controls'])
    
    def _get_threat_detection(self, threat_type: str) -> List[str]:
        """Get detection methods for threat"""
        detection_map = {
            'external_attacker': [
                'Network monitoring and analysis',
                'Intrusion detection systems',
                'Security information and event management (SIEM)',
                'Anomaly detection'
            ],
            'insider_threat': [
                'User behavior analytics',
                'Access log monitoring',
                'Data loss prevention systems',
                'Privileged access monitoring'
            ],
            'malware': [
                'Endpoint detection and response (EDR)',
                'Antivirus and antimalware',
                'Network traffic analysis',
                'File integrity monitoring'
            ],
            'data_breach': [
                'Data loss prevention (DLP)',
                'Database activity monitoring',
                'Network traffic analysis',
                'Access pattern analysis'
            ],
            'ddos': [
                'Network traffic monitoring',
                'DDoS detection systems',
                'Performance monitoring',
                'Traffic pattern analysis'
            ]
        }
        return detection_map.get(threat_type, ['Implement comprehensive monitoring'])
    
    def check_compliance(self, task: str) -> List[ComplianceCheck]:
        """Kiểm tra tuân thủ"""
        compliance_checks = []
        task_lower = task.lower()
        
        for compliance_type, compliance_info in self.compliance_patterns.items():
            for pattern in compliance_info['patterns']:
                if re.search(pattern, task_lower):
                    compliance_check = ComplianceCheck(
                        standard=compliance_info['standard'],
                        requirement=compliance_info['requirements'][0],
                        compliance_status=self._assess_compliance_status(task_lower, compliance_type),
                        evidence=self._get_compliance_evidence(compliance_type),
                        remediation_actions=self._get_compliance_remediation(compliance_type),
                        risk_level=self._get_compliance_risk_level(compliance_type)
                    )
                    compliance_checks.append(compliance_check)
                    break
        
        return compliance_checks
    
    def _assess_compliance_status(self, task: str, compliance_type: str) -> str:
        """Assess compliance status"""
        # Simple assessment based on keywords
        if 'implement' in task and 'security' in task:
            return 'compliant'
        elif 'review' in task or 'assess' in task:
            return 'partial'
        else:
            return 'non_compliant'
    
    def _get_compliance_evidence(self, compliance_type: str) -> List[str]:
        """Get compliance evidence"""
        evidence_map = {
            'gdpr': ['Data protection impact assessment', 'Privacy policy', 'Consent management system'],
            'sox': ['Financial controls documentation', 'Audit trail', 'Internal control testing'],
            'hipaa': ['Risk assessment', 'Access controls', 'Encryption implementation'],
            'pci_dss': ['Network security assessment', 'Cardholder data protection', 'Access controls']
        }
        return evidence_map.get(compliance_type, ['Security documentation', 'Risk assessment'])
    
    def _get_compliance_remediation(self, compliance_type: str) -> List[str]:
        """Get compliance remediation actions"""
        remediation_map = {
            'gdpr': [
                'Implement data protection by design',
                'Create privacy impact assessments',
                'Implement consent management',
                'Establish data subject rights procedures'
            ],
            'sox': [
                'Implement financial controls',
                'Create audit trails',
                'Establish internal controls',
                'Regular compliance testing'
            ],
            'hipaa': [
                'Implement administrative safeguards',
                'Establish physical safeguards',
                'Implement technical safeguards',
                'Regular risk assessments'
            ],
            'pci_dss': [
                'Implement network security controls',
                'Protect cardholder data',
                'Implement access controls',
                'Regular security testing'
            ]
        }
        return remediation_map.get(compliance_type, ['Implement compliance controls', 'Regular compliance assessments'])
    
    def _get_compliance_risk_level(self, compliance_type: str) -> SecurityLevel:
        """Get compliance risk level"""
        risk_map = {
            'gdpr': SecurityLevel.HIGH,    # High fines
            'sox': SecurityLevel.HIGH,     # Criminal penalties
            'hipaa': SecurityLevel.HIGH,   # Civil and criminal penalties
            'pci_dss': SecurityLevel.MEDIUM # Fines and loss of certification
        }
        return risk_map.get(compliance_type, SecurityLevel.MEDIUM)
    
    def assess_security_risks(self, task: str) -> List[SecurityRisk]:
        """Đánh giá rủi ro bảo mật"""
        security_risks = []
        vulnerabilities = self.detect_vulnerabilities(task)
        
        for vuln in vulnerabilities:
            # Calculate risk score
            probability = self._get_vulnerability_probability(vuln.vulnerability_type)
            impact = self._get_vulnerability_impact(vuln.vulnerability_type)
            risk_score = probability * impact
            
            security_risk = SecurityRisk(
                risk_id=f"RISK_{vuln.vulnerability_type.upper()}",
                risk_name=f"{vuln.vulnerability_type.replace('_', ' ').title()} Risk",
                risk_level=vuln.severity,
                probability=probability,
                impact=impact,
                risk_score=risk_score,
                description=vuln.description,
                affected_assets=[task],
                mitigation_controls=vuln.remediation,
                residual_risk=self._calculate_residual_risk(risk_score)
            )
            security_risks.append(security_risk)
        
        return security_risks
    
    def _get_vulnerability_probability(self, vuln_type: str) -> float:
        """Get vulnerability probability"""
        probability_map = {
            'sql_injection': 0.8,      # High probability
            'xss_vulnerability': 0.7,  # High probability
            'path_traversal': 0.6,     # Medium-high probability
            'hardcoded_secrets': 0.9,  # Very high probability
            'insecure_random': 0.5,    # Medium probability
            'weak_encryption': 0.6,    # Medium-high probability
            'insecure_communication': 0.7, # High probability
            'authentication_bypass': 0.8   # High probability
        }
        return probability_map.get(vuln_type, 0.5)
    
    def _get_vulnerability_impact(self, vuln_type: str) -> float:
        """Get vulnerability impact"""
        impact_map = {
            'sql_injection': 0.9,      # Critical impact
            'xss_vulnerability': 0.7,  # High impact
            'path_traversal': 0.8,     # High impact
            'hardcoded_secrets': 0.9,  # Critical impact
            'insecure_random': 0.6,    # Medium impact
            'weak_encryption': 0.8,    # High impact
            'insecure_communication': 0.7, # High impact
            'authentication_bypass': 0.9   # Critical impact
        }
        return impact_map.get(vuln_type, 0.5)
    
    def _calculate_residual_risk(self, risk_score: float) -> SecurityLevel:
        """Calculate residual risk level"""
        if risk_score >= 0.8:
            return SecurityLevel.CRITICAL
        elif risk_score >= 0.6:
            return SecurityLevel.HIGH
        elif risk_score >= 0.4:
            return SecurityLevel.MEDIUM
        elif risk_score >= 0.2:
            return SecurityLevel.LOW
        else:
            return SecurityLevel.MINIMAL
    
    def review_security_architecture(self, task: str) -> SecurityArchitecture:
        """Đánh giá kiến trúc bảo mật"""
        task_lower = task.lower()
        
        # Check for security architecture components
        defense_in_depth = any(keyword in task_lower for keyword in ['layered', 'defense', 'multiple', 'redundant'])
        zero_trust = any(keyword in task_lower for keyword in ['zero.*trust', 'never.*trust', 'verify.*always'])
        encryption_at_rest = any(keyword in task_lower for keyword in ['encrypt.*data', 'encryption.*at.*rest', 'data.*encryption'])
        encryption_in_transit = any(keyword in task_lower for keyword in ['https', 'tls', 'ssl', 'encryption.*in.*transit'])
        
        # Identify access controls
        access_controls = []
        if 'authentication' in task_lower:
            access_controls.append('Authentication')
        if 'authorization' in task_lower:
            access_controls.append('Authorization')
        if 'rbac' in task_lower or 'role.*based' in task_lower:
            access_controls.append('Role-based Access Control')
        
        # Identify monitoring capabilities
        monitoring_capabilities = []
        if 'monitor' in task_lower or 'logging' in task_lower:
            monitoring_capabilities.append('Logging and Monitoring')
        if 'audit' in task_lower:
            monitoring_capabilities.append('Audit Trail')
        if 'siem' in task_lower:
            monitoring_capabilities.append('SIEM')
        
        # Check for incident response plan
        incident_response_plan = any(keyword in task_lower for keyword in ['incident.*response', 'security.*plan', 'emergency.*plan'])
        
        # Identify security gaps
        security_gaps = []
        if not defense_in_depth:
            security_gaps.append('Lack of defense in depth')
        if not zero_trust:
            security_gaps.append('No zero trust implementation')
        if not encryption_at_rest:
            security_gaps.append('No encryption at rest')
        if not encryption_in_transit:
            security_gaps.append('No encryption in transit')
        if not access_controls:
            security_gaps.append('Insufficient access controls')
        if not monitoring_capabilities:
            security_gaps.append('Insufficient monitoring')
        if not incident_response_plan:
            security_gaps.append('No incident response plan')
        
        # Generate recommendations
        recommendations = []
        if security_gaps:
            recommendations.extend([f"Implement {gap.lower()}" for gap in security_gaps])
        recommendations.extend([
            "Conduct regular security assessments",
            "Implement security awareness training",
            "Establish security metrics and KPIs",
            "Regular penetration testing"
        ])
        
        return SecurityArchitecture(
            defense_in_depth=defense_in_depth,
            zero_trust_implementation=zero_trust,
            encryption_at_rest=encryption_at_rest,
            encryption_in_transit=encryption_in_transit,
            access_controls=access_controls,
            monitoring_capabilities=monitoring_capabilities,
            incident_response_plan=incident_response_plan,
            security_gaps=security_gaps,
            recommendations=recommendations
        )
    
    def analyze_security_risks(self, task: str) -> SecurityAnalysisResult:
        """Phân tích rủi ro bảo mật toàn diện"""
        start_time = time.time()
        
        # Run all security analyses
        vulnerabilities = self.detect_vulnerabilities(task)
        best_practices = self.check_best_practices(task)
        threat_models = self.model_threats(task)
        compliance_checks = self.check_compliance(task)
        security_risks = self.assess_security_risks(task)
        architecture_review = self.review_security_architecture(task)
        
        # Calculate overall security score
        security_score = self._calculate_security_score(vulnerabilities, best_practices, security_risks, architecture_review)
        
        # Determine overall security level
        if security_score >= 0.8:
            security_level = SecurityLevel.CRITICAL
        elif security_score >= 0.6:
            security_level = SecurityLevel.HIGH
        elif security_score >= 0.4:
            security_level = SecurityLevel.MEDIUM
        elif security_score >= 0.2:
            security_level = SecurityLevel.LOW
        else:
            security_level = SecurityLevel.MINIMAL
        
        # Identify critical issues
        critical_issues = []
        for vuln in vulnerabilities:
            if vuln.severity == SecurityLevel.CRITICAL:
                critical_issues.append(f"CRITICAL: {vuln.vulnerability_type}")
        
        for risk in security_risks:
            if risk.risk_level == SecurityLevel.CRITICAL:
                critical_issues.append(f"CRITICAL RISK: {risk.risk_name}")
        
        # Generate immediate actions
        immediate_actions = []
        if critical_issues:
            immediate_actions.append("Address critical security vulnerabilities immediately")
            immediate_actions.append("Implement emergency security controls")
            immediate_actions.append("Notify security team and management")
        
        # Generate security recommendations
        security_recommendations = []
        security_recommendations.extend(architecture_review.recommendations)
        for vuln in vulnerabilities:
            security_recommendations.extend(vuln.remediation[:2])  # Top 2 recommendations
        
        # Identify compliance gaps
        compliance_gaps = []
        for check in compliance_checks:
            if check.compliance_status != 'compliant':
                compliance_gaps.append(f"{check.standard.value}: {check.requirement}")
        
        analysis_time = time.time() - start_time
        
        return SecurityAnalysisResult(
            overall_security_score=security_score,
            security_level=security_level,
            vulnerabilities=vulnerabilities,
            best_practices=best_practices,
            threat_models=threat_models,
            compliance_checks=compliance_checks,
            security_risks=security_risks,
            architecture_review=architecture_review,
            critical_issues=critical_issues,
            immediate_actions=immediate_actions,
            security_recommendations=security_recommendations,
            compliance_gaps=compliance_gaps,
            analysis_time=analysis_time
        )
    
    def _calculate_security_score(self, vulnerabilities, best_practices, security_risks, architecture_review) -> float:
        """Calculate overall security score"""
        # Start with base score
        score = 1.0
        
        # Deduct for vulnerabilities
        for vuln in vulnerabilities:
            if vuln.severity == SecurityLevel.CRITICAL:
                score -= 0.3
            elif vuln.severity == SecurityLevel.HIGH:
                score -= 0.2
            elif vuln.severity == SecurityLevel.MEDIUM:
                score -= 0.1
            else:
                score -= 0.05
        
        # Deduct for security risks
        for risk in security_risks:
            score -= risk.risk_score * 0.2
        
        # Deduct for security gaps
        score -= len(architecture_review.security_gaps) * 0.05
        
        # Add for best practices
        score += len(best_practices) * 0.02
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))

# Test function
if __name__ == "__main__":
    analyzer = SecurityAnalyzer()
    result = analyzer.analyze_security_risks("Implement SQL injection protection and secure authentication")
    
    print("=== SECURITY ANALYSIS RESULT ===")
    print(f"Overall Security Score: {result.overall_security_score:.2f}")
    print(f"Security Level: {result.security_level.value}")
    print(f"Vulnerabilities: {len(result.vulnerabilities)}")
    print(f"Best Practices: {len(result.best_practices)}")
    print(f"Security Risks: {len(result.security_risks)}")
    print(f"Critical Issues: {len(result.critical_issues)}")
    print(f"Analysis Time: {result.analysis_time:.3f}s")
