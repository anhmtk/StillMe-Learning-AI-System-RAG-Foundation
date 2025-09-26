import secrets
#!/usr/bin/env python3
"""
StillMe AgentDev Security Scanner
Enterprise-grade security scanning and vulnerability assessment
"""

import re
import json
import yaml
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib

class SecuritySeverity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

@dataclass
class SecurityIssue:
    """Represents a security issue"""
    id: str
    severity: SecuritySeverity
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    cwe_id: Optional[str] = None
    remediation: Optional[str] = None
    confidence: str = "MEDIUM"

class SecurityScanner:
    """Main security scanner for AgentDev"""
    
    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.issues = []
        self.secret_patterns = self._load_secret_patterns()
        self.vulnerability_db = self._load_vulnerability_db()
        
    def scan_all(self) -> List[SecurityIssue]:
        """Run comprehensive security scan"""
        print("🔒 Starting comprehensive security scan...")
        
        self.issues = []
        
        # Secret scanning
        self.issues.extend(self.scan_secrets())
        
        # Dependency scanning
        self.issues.extend(self.scan_dependencies())
        
        # Code analysis
        self.issues.extend(self.scan_code_issues())
        
        # Configuration scanning
        self.issues.extend(self.scan_configuration())
        
        # Infrastructure scanning
        self.issues.extend(self.scan_infrastructure())
        
        return self.issues
        
    def scan_secrets(self) -> List[SecurityIssue]:
        """Scan for hardcoded secrets and credentials"""
        print("🔍 Scanning for secrets...")
        issues = []
        
        # Define secret patterns
        secret_patterns = [
            # API Keys
            (r'api[_-]?key\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', "API Key", SecuritySeverity.HIGH),
            (r'access[_-]?key\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', "Access Key", SecuritySeverity.HIGH),
            (r'secret[_-]?key\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', "Secret Key", SecuritySeverity.HIGH),
            
            # Tokens
            (r'token\s*[=:]\s*["\']?([a-zA-Z0-9_\-\.]{20,})["\']?', "Token", SecuritySeverity.HIGH),
            (r'bearer\s+([a-zA-Z0-9_\-\.]{20,})', "Bearer Token", SecuritySeverity.HIGH),
            
            # Passwords
            (r'password\s*[=:]\s*["\']?([^"\'\s]{8,})["\']?', "Password", SecuritySeverity.CRITICAL),
            (r'passwd\s*[=:]\s*["\']?([^"\'\s]{8,})["\']?', "Password", SecuritySeverity.CRITICAL),
            
            # Database credentials
            (r'db[_-]?password\s*[=:]\s*["\']?([^"\'\s]{8,})["\']?', "Database Password", SecuritySeverity.CRITICAL),
            (r'database[_-]?password\s*[=:]\s*["\']?([^"\'\s]{8,})["\']?', "Database Password", SecuritySeverity.CRITICAL),
            
            # SSH keys
            (r'-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----', "SSH Private Key", SecuritySeverity.CRITICAL),
            
            # JWT secrets
            (r'jwt[_-]?secret\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', "JWT Secret", SecuritySeverity.HIGH),
        ]
        
        # Scan files
        for file_path in self._get_scan_files():
            issues.extend(self._scan_file_for_secrets(file_path, secret_patterns))
            
        return issues
        
    def scan_dependencies(self) -> List[SecurityIssue]:
        """Scan for vulnerable dependencies"""
        print("📦 Scanning dependencies...")
        issues = []
        
        # Check Python dependencies
        issues.extend(self._scan_python_dependencies())
        
        # Check Node.js dependencies
        issues.extend(self._scan_node_dependencies())
        
        # Check Docker images
        issues.extend(self._scan_docker_images())
        
        return issues
        
    def scan_code_issues(self) -> List[SecurityIssue]:
        """Scan for code security issues"""
        print("🔍 Scanning code for security issues...")
        issues = []
        
        # SQL Injection patterns
        sql_patterns = [
            (r'execute\s*\(\s*["\'].*%s.*["\']', "Potential SQL Injection", SecuritySeverity.HIGH),
            (r'query\s*\(\s*["\'].*\+.*["\']', "Potential SQL Injection", SecuritySeverity.HIGH),
        ]
        
        # XSS patterns
        xss_patterns = [
            (r'innerHTML\s*=\s*[^;]+', "Potential XSS", SecuritySeverity.MEDIUM),
            (r'document\.write\s*\(', "Potential XSS", SecuritySeverity.MEDIUM),
        ]
        
        # Command injection patterns
        cmd_patterns = [
            (r'os\.system\s*\(', "Command Injection Risk", SecuritySeverity.HIGH),
            (r'subprocess\.call\s*\([^,)]*shell\s*=\s*True', "Command Injection Risk", SecuritySeverity.HIGH),
            (r'eval\s*\(', "Code Injection Risk", SecuritySeverity.CRITICAL),
            (r'exec\s*\(', "Code Injection Risk", SecuritySeverity.CRITICAL),
        ]
        
        # Scan files
        for file_path in self._get_scan_files():
            issues.extend(self._scan_file_for_patterns(file_path, sql_patterns))
            issues.extend(self._scan_file_for_patterns(file_path, xss_patterns))
            issues.extend(self._scan_file_for_patterns(file_path, cmd_patterns))
            
        return issues
        
    def scan_configuration(self) -> List[SecurityIssue]:
        """Scan configuration files for security issues"""
        print("⚙️  Scanning configuration...")
        issues = []
        
        # Check Docker configurations
        issues.extend(self._scan_docker_configs())
        
        # Check environment files
        issues.extend(self._scan_env_files())
        
        # Check CI/CD configurations
        issues.extend(self._scan_cicd_configs())
        
        return issues
        
    def scan_infrastructure(self) -> List[SecurityIssue]:
        """Scan infrastructure configurations"""
        print("🏗️  Scanning infrastructure...")
        issues = []
        
        # Check Kubernetes configurations
        issues.extend(self._scan_k8s_configs())
        
        # Check Terraform configurations
        issues.extend(self._scan_terraform_configs())
        
        return issues
        
    def _load_secret_patterns(self) -> Dict[str, Any]:
        """Load secret detection patterns"""
        # This would load from a comprehensive pattern database
        return {}
        
    def _load_vulnerability_db(self) -> Dict[str, Any]:
        """Load vulnerability database"""
        # This would load from CVE database or similar
        return {}
        
    def _get_scan_files(self) -> List[Path]:
        """Get list of files to scan"""
        files = []
        
        # Include common file types
        extensions = ['.py', '.js', '.ts', '.java', '.go', '.rb', '.php', '.yaml', '.yml', '.json']
        
        for ext in extensions:
            files.extend(self.repo_root.rglob(f'*{ext}'))
            
        # Exclude common directories
        exclude_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'build', 'dist'}
        
        filtered_files = []
        for file_path in files:
            if not any(exclude_dir in file_path.parts for exclude_dir in exclude_dirs):
                filtered_files.append(file_path)
                
        return filtered_files
        
    def _scan_file_for_secrets(self, file_path: Path, patterns: List[Tuple[str, str, SecuritySeverity]]) -> List[SecurityIssue]:
        """Scan file for secret patterns"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
            for line_num, line in enumerate(lines, 1):
                for pattern, secret_type, severity in patterns:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        # Skip if it's in a comment or test
                        if self._is_comment_or_test(line, file_path):
                            continue
                            
                        issues.append(SecurityIssue(
                            id=f"SECRET_{secret_type.upper().replace(' ', '_')}",
                            severity=severity,
                            title=f"Hardcoded {secret_type}",
                            description=f"Potential hardcoded {secret_type} found",
                            file_path=str(file_path),
                            line_number=line_num,
                            cwe_id="CWE-798",
                            remediation=f"Move {secret_type} to environment variables or secure secret store"
                        ))
                        
        except Exception as e:
            issues.append(SecurityIssue(
                id="FILE_READ_ERROR",
                severity=SecuritySeverity.INFO,
                title="File Read Error",
                description=f"Could not read file: {e}",
                file_path=str(file_path)
            ))
            
        return issues
        
    def _scan_file_for_patterns(self, file_path: Path, patterns: List[Tuple[str, str, SecuritySeverity]]) -> List[SecurityIssue]:
        """Scan file for security patterns"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
            for line_num, line in enumerate(lines, 1):
                for pattern, issue_type, severity in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Skip if it's in a comment or test
                        if self._is_comment_or_test(line, file_path):
                            continue
                            
                        issues.append(SecurityIssue(
                            id=f"CODE_{issue_type.upper().replace(' ', '_')}",
                            severity=severity,
                            title=issue_type,
                            description=f"Potential {issue_type.lower()} detected",
                            file_path=str(file_path),
                            line_number=line_num,
                            remediation="Review and secure the code"
                        ))
                        
        except Exception as e:
            issues.append(SecurityIssue(
                id="FILE_READ_ERROR",
                severity=SecuritySeverity.INFO,
                title="File Read Error",
                description=f"Could not read file: {e}",
                file_path=str(file_path)
            ))
            
        return issues
        
    def _is_comment_or_test(self, line: str, file_path: Path) -> bool:
        """Check if line is a comment or in test file"""
        # Check for comments
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('/*'):
            return True
            
        # Check if it's a test file
        if 'test' in str(file_path).lower():
            return True
            
        return False
        
    def _scan_python_dependencies(self) -> List[SecurityIssue]:
        """Scan Python dependencies for vulnerabilities"""
        issues = []
        
        requirements_files = [
            self.repo_root / "requirements.txt",
            self.repo_root / "requirements-dev.txt",
            self.repo_root / "pyproject.toml",
        ]
        
        for req_file in requirements_files:
            if req_file.exists():
                try:
                    # Run pip-audit if available
                    result = subprocess.run(
                        ['pip-audit', '--format=json', '--requirement', str(req_file)],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        audit_data = json.loads(result.stdout)
                        for vuln in audit_data.get('vulnerabilities', []):
                            issues.append(SecurityIssue(
                                id=f"PYTHON_VULN_{vuln.get('id', 'UNKNOWN')}",
                                severity=SecuritySeverity.HIGH,
                                title=f"Vulnerable Python Package: {vuln.get('package', 'Unknown')}",
                                description=vuln.get('description', 'No description'),
                                remediation=vuln.get('fix_versions', 'Update package')
                            ))
                            
                except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
                    # pip-audit not available or failed
                    pass
                    
        return issues
        
    def _scan_node_dependencies(self) -> List[SecurityIssue]:
        """Scan Node.js dependencies for vulnerabilities"""
        issues = []
        
        package_json = self.repo_root / "package.json"
        if package_json.exists():
            try:
                # Run npm audit if available
                result = subprocess.run(
                    ['npm', 'audit', '--json'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:  # npm audit returns non-zero for vulnerabilities
                    audit_data = json.loads(result.stdout)
                    for vuln_id, vuln_data in audit_data.get('vulnerabilities', {}).items():
                        issues.append(SecurityIssue(
                            id=f"NODE_VULN_{vuln_id}",
                            severity=SecuritySeverity.HIGH,
                            title=f"Vulnerable Node Package: {vuln_id}",
                            description=vuln_data.get('description', 'No description'),
                            remediation="Run 'npm audit fix' to update"
                        ))
                        
            except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
                # npm not available or failed
                pass
                
        return issues
        
    def _scan_docker_images(self) -> List[SecurityIssue]:
        """Scan Docker images for vulnerabilities"""
        issues = []
        
        # This would integrate with tools like Trivy or Clair
        # For now, just check for common insecure base images
        dockerfiles = list(self.repo_root.rglob("Dockerfile*"))
        
        for dockerfile in dockerfiles:
            try:
                with open(dockerfile, 'r') as f:
                    content = f.read()
                    
                # Check for insecure base images
                insecure_images = [
                    'node:latest',
                    'python:latest',
                    'ubuntu:latest',
                    'debian:latest',
                ]
                
                for image in insecure_images:
                    if image in content:
                        issues.append(SecurityIssue(
                            id="INSECURE_BASE_IMAGE",
                            severity=SecuritySeverity.MEDIUM,
                            title=f"Insecure base image: {image}",
                            description="Using 'latest' tag can lead to unpredictable builds",
                            file_path=str(dockerfile),
                            remediation="Use specific version tags"
                        ))
                        
            except Exception:
                pass
                
        return issues
        
    def _scan_docker_configs(self) -> List[SecurityIssue]:
        """Scan Docker configurations for security issues"""
        issues = []
        
        docker_compose_files = list(self.repo_root.rglob("docker-compose*.yml"))
        
        for compose_file in docker_compose_files:
            try:
                with open(compose_file, 'r') as f:
                    content = yaml.safe_load(f)
                    
                services = content.get('services', {})
                for service_name, service_config in services.items():
                    # Check for privileged mode
                    if service_config.get('privileged'):
                        issues.append(SecurityIssue(
                            id="DOCKER_PRIVILEGED",
                            severity=SecuritySeverity.HIGH,
                            title=f"Privileged Docker container: {service_name}",
                            description="Privileged containers have full host access",
                            file_path=str(compose_file),
                            remediation="Remove privileged mode if not required"
                        ))
                        
                    # Check for host network
                    if service_config.get('network_mode') == 'host':
                        issues.append(SecurityIssue(
                            id="DOCKER_HOST_NETWORK",
                            severity=SecuritySeverity.MEDIUM,
                            title=f"Host network mode: {service_name}",
                            description="Host network mode bypasses Docker networking",
                            file_path=str(compose_file),
                            remediation="Use bridge network mode"
                        ))
                        
            except Exception:
                pass
                
        return issues
        
    def _scan_env_files(self) -> List[SecurityIssue]:
        """Scan environment files for security issues"""
        issues = []
        
        env_files = list(self.repo_root.rglob(".env*"))
        
        for env_file in env_files:
            # Check if .env files are in git
            if '.git' not in str(env_file):
                try:
                    result = subprocess.run(
                        ['git', 'check-ignore', str(env_file)],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode != 0:  # Not ignored by git
                        issues.append(SecurityIssue(
                            id="ENV_IN_GIT",
                            severity=SecuritySeverity.HIGH,
                            title=f"Environment file in git: {env_file.name}",
                            description="Environment files may contain secrets",
                            file_path=str(env_file),
                            remediation="Add to .gitignore"
                        ))
                        
                except subprocess.CalledProcessError:
                    pass
                    
        return issues
        
    def _scan_cicd_configs(self) -> List[SecurityIssue]:
        """Scan CI/CD configurations for security issues"""
        issues = []
        
        # Check GitHub Actions
        github_actions = self.repo_root / ".github" / "workflows"
        if github_actions.exists():
            for workflow in github_actions.rglob("*.yml"):
                issues.extend(self._scan_github_workflow(workflow))
                
        return issues
        
    def _scan_github_workflow(self, workflow_file: Path) -> List[SecurityIssue]:
        """Scan GitHub workflow for security issues"""
        issues = []
        
        try:
            with open(workflow_file, 'r') as f:
                content = yaml.safe_load(f)
                
            # Check for hardcoded secrets in workflows
            content_str = str(content)
            if 'password' in content_str.lower() or 'token' in content_str.lower():
                issues.append(SecurityIssue(
                    id="WORKFLOW_HARDCODED_SECRET",
                    severity=SecuritySeverity.HIGH,
                    title="Potential hardcoded secret in workflow",
                    description="Workflow may contain hardcoded secrets",
                    file_path=str(workflow_file),
                    remediation="Use GitHub secrets"
                ))
                
        except Exception:
            pass
            
        return issues
        
    def _scan_k8s_configs(self) -> List[SecurityIssue]:
        """Scan Kubernetes configurations for security issues"""
        issues = []
        
        k8s_files = list(self.repo_root.rglob("*.yaml")) + list(self.repo_root.rglob("*.yml"))
        
        for k8s_file in k8s_files:
            try:
                with open(k8s_file, 'r') as f:
                    content = yaml.safe_load(f)
                    
                # Check for security contexts
                if isinstance(content, dict):
                    # Check for privileged containers
                    if content.get('kind') in ['Deployment', 'Pod', 'DaemonSet']:
                        spec = content.get('spec', {})
                        containers = spec.get('template', {}).get('spec', {}).get('containers', [])
                        
                        for container in containers:
                            security_context = container.get('securityContext', {})
                            if security_context.get('privileged'):
                                issues.append(SecurityIssue(
                                    id="K8S_PRIVILEGED",
                                    severity=SecuritySeverity.HIGH,
                                    title="Privileged Kubernetes container",
                                    description="Privileged containers have full host access",
                                    file_path=str(k8s_file),
                                    remediation="Remove privileged security context"
                                ))
                                
            except Exception:
                pass
                
        return issues
        
    def _scan_terraform_configs(self) -> List[SecurityIssue]:
        """Scan Terraform configurations for security issues"""
        issues = []
        
        tf_files = list(self.repo_root.rglob("*.tf"))
        
        for tf_file in tf_files:
            try:
                with open(tf_file, 'r') as f:
                    content = f.read()
                    
                # Check for hardcoded secrets
                if 'password' in content.lower() and 'var.' not in content:
                    issues.append(SecurityIssue(
                        id="TERRAFORM_HARDCODED_SECRET",
                        severity=SecuritySeverity.HIGH,
                        title="Potential hardcoded secret in Terraform",
                        description="Terraform may contain hardcoded secrets",
                        file_path=str(tf_file),
                        remediation="Use Terraform variables or secret management"
                    ))
                    
            except Exception:
                pass
                
        return issues
        
    def generate_report(self, issues: List[SecurityIssue]) -> str:
        """Generate security scan report"""
        if not issues:
            return "✅ No security issues found"
            
        report = "🔒 SECURITY SCAN REPORT\n"
        report += "=" * 50 + "\n\n"
        
        # Group by severity
        by_severity = {}
        for issue in issues:
            severity = issue.severity.value
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(issue)
            
        # Report by severity
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
            if severity in by_severity:
                report += f"\n{severity} ISSUES ({len(by_severity[severity])}):\n"
                report += "-" * 30 + "\n"
                
                for issue in by_severity[severity]:
                    report += f"• {issue.id}: {issue.title}\n"
                    report += f"  {issue.description}\n"
                    if issue.file_path:
                        report += f"  File: {issue.file_path}"
                        if issue.line_number:
                            report += f":{issue.line_number}"
                        report += "\n"
                    if issue.remediation:
                        report += f"  Fix: {issue.remediation}\n"
                    report += "\n"
                    
        return report
        
    def scan_and_report(self) -> bool:
        """Run scan and generate report"""
        issues = self.scan_all()
        report = self.generate_report(issues)
        print(report)
        
        # Check if any critical or high severity issues
        critical_issues = [i for i in issues if i.severity in [SecuritySeverity.CRITICAL, SecuritySeverity.HIGH]]
        
        if critical_issues:
            print(f"\n❌ Security scan FAILED - {len(critical_issues)} critical/high issues found")
            return False
        else:
            print(f"\n✅ Security scan PASSED")
            return True

def main():
    """CLI entry point for security scanner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="StillMe AgentDev Security Scanner")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--output", help="Output file for report")
    
    args = parser.parse_args()
    
    scanner = SecurityScanner(args.repo_root)
    success = scanner.scan_and_report()
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(scanner.generate_report(scanner.issues))
            
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
