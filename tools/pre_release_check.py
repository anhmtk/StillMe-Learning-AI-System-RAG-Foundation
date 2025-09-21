#!/usr/bin/env python3
"""
StillMe Pre-Release Security Check
Kiểm tra bảo mật trước khi deploy
"""
import os
import re
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any

class SecurityChecker:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.checks_passed = 0
        self.total_checks = 0
    
    def check(self, name: str, condition: bool, error_msg: str = "", warning_msg: str = ""):
        """Run a security check"""
        self.total_checks += 1
        if condition:
            self.checks_passed += 1
            print(f"✅ {name}")
        else:
            if error_msg:
                self.errors.append(f"❌ {name}: {error_msg}")
                print(f"❌ {name}: {error_msg}")
            if warning_msg:
                self.warnings.append(f"⚠️  {name}: {warning_msg}")
                print(f"⚠️  {name}: {warning_msg}")
    
    def check_file_exists(self, filepath: str, name: str):
        """Check if file exists"""
        exists = os.path.exists(filepath)
        self.check(
            f"File exists: {name}",
            exists,
            f"File not found: {filepath}"
        )
        return exists
    
    def check_no_secrets_in_code(self):
        """Check for secrets in code files"""
        print("\n🔍 Checking for secrets in code...")
        
        # Patterns to check for
        secret_patterns = [
            r'sk-[a-zA-Z0-9]{20,}',  # OpenAI API keys
            r'api[_-]?key["\']?\s*[:=]\s*["\'][^"\']+["\']',  # API keys
            r'password["\']?\s*[:=]\s*["\'][^"\']+["\']',  # Passwords
            r'secret["\']?\s*[:=]\s*["\'][^"\']+["\']',  # Secrets
            r'\.env["\']?\s*[:=]\s*["\'][^"\']+["\']',  # .env files
        ]
        
        # Files to check
        code_files = [
            'local_stillme_backend.py',
            'vps_gateway_proxy.py',
            'deploy_vps_proxy.sh',
        ]
        
        for filepath in code_files:
            if not os.path.exists(filepath):
                continue
                
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for pattern in secret_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    self.check(
                        f"No secrets in {filepath}",
                        False,
                        f"Found potential secrets: {matches[:3]}"  # Show first 3 matches
                    )
                else:
                    self.check(
                        f"No secrets in {filepath}",
                        True
                    )
    
    def check_env_configuration(self):
        """Check environment configuration"""
        print("\n🔧 Checking environment configuration...")
        
        # Check .env.example exists
        self.check_file_exists('env.example', '.env.example')
        
        # Check if .env files are in .gitignore
        gitignore_exists = os.path.exists('.gitignore')
        if gitignore_exists:
            with open('.gitignore', 'r') as f:
                gitignore_content = f.read()
            
            self.check(
                ".env files in .gitignore",
                '.env' in gitignore_content,
                ".env files not ignored in .gitignore"
            )
        else:
            self.check(
                ".gitignore exists",
                False,
                ".gitignore file not found"
            )
    
    def check_security_features(self):
        """Check security features in code"""
        print("\n🔒 Checking security features...")
        
        # Check local backend security
        if os.path.exists('local_stillme_backend.py'):
            with open('local_stillme_backend.py', 'r') as f:
                backend_content = f.read()
            
            self.check(
                "Local backend binds to 127.0.0.1",
                "('127.0.0.1', BACKEND_PORT)" in backend_content,
                "Local backend not binding to 127.0.0.1"
            )
            
            self.check(
                "HMAC verification in backend",
                "verify_hmac" in backend_content,
                "HMAC verification not found in backend"
            )
        
        # Check VPS gateway security
        if os.path.exists('vps_gateway_proxy.py'):
            with open('vps_gateway_proxy.py', 'r') as f:
                gateway_content = f.read()
            
            self.check(
                "Rate limiting in gateway",
                "check_rate_limit" in gateway_content,
                "Rate limiting not found in gateway"
            )
            
            self.check(
                "HMAC signing in gateway",
                "create_hmac_signature" in gateway_content,
                "HMAC signing not found in gateway"
            )
            
            self.check(
                "Timeout configuration in gateway",
                "REQUEST_CONNECT_TIMEOUT" in gateway_content,
                "Timeout configuration not found in gateway"
            )
    
    def check_deployment_files(self):
        """Check deployment files"""
        print("\n🚀 Checking deployment files...")
        
        # Check deploy script
        self.check_file_exists('deploy_vps_proxy.sh', 'deploy_vps_proxy.sh')
        
        # Check tunnel scripts
        self.check_file_exists('tools/start_tunnel.ps1', 'Windows tunnel script')
        self.check_file_exists('tools/start_tunnel.sh', 'Linux tunnel script')
        
        # Check systemd service configuration
        if os.path.exists('deploy_vps_proxy.sh'):
            with open('deploy_vps_proxy.sh', 'r') as f:
                deploy_content = f.read()
            
            self.check(
                "systemd service configuration",
                "EnvironmentFile=/opt/stillme/.env" in deploy_content,
                "systemd EnvironmentFile not configured"
            )
    
    def check_documentation(self):
        """Check documentation"""
        print("\n📚 Checking documentation...")
        
        self.check_file_exists('ARCHITECTURE.md', 'ARCHITECTURE.md')
        
        if os.path.exists('ARCHITECTURE.md'):
            with open('ARCHITECTURE.md', 'r') as f:
                arch_content = f.read()
            
            self.check(
                "SSH tunnel documented",
                "SSH Reverse Tunnel" in arch_content,
                "SSH tunnel not documented"
            )
            
            self.check(
                "HMAC authentication documented",
                "HMAC" in arch_content,
                "HMAC authentication not documented"
            )
    
    def run_all_checks(self):
        """Run all security checks"""
        print("🔒 StillMe Pre-Release Security Check")
        print("=" * 50)
        
        self.check_no_secrets_in_code()
        self.check_env_configuration()
        self.check_security_features()
        self.check_deployment_files()
        self.check_documentation()
        
        # Summary
        print("\n" + "=" * 50)
        print(f"📊 Security Check Summary:")
        print(f"   ✅ Passed: {self.checks_passed}/{self.total_checks}")
        print(f"   ❌ Errors: {len(self.errors)}")
        print(f"   ⚠️  Warnings: {len(self.warnings)}")
        
        if self.errors:
            print(f"\n❌ CRITICAL ERRORS:")
            for error in self.errors:
                print(f"   {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   {warning}")
        
        # Return status
        if self.errors:
            print(f"\n🚫 SECURITY CHECK FAILED - Fix errors before deployment")
            return False
        elif self.warnings:
            print(f"\n⚠️  SECURITY CHECK PASSED WITH WARNINGS")
            return True
        else:
            print(f"\n✅ SECURITY CHECK PASSED - Ready for deployment")
            return True

def main():
    """Main function"""
    checker = SecurityChecker()
    success = checker.run_all_checks()
    
    if not success:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
