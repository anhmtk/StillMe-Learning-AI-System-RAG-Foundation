#!/usr/bin/env python3
"""
Check VPS Gateway configuration and enable real LLM
"""
import subprocess
import json
import time

def run_ssh_command(command, password="StillMe@2025!"):
    """Run SSH command with password"""
    ssh_cmd = [
        "sshpass", "-p", password,
        "ssh", "-o", "StrictHostKeyChecking=no",
        "root@160.191.89.99",
        command
    ]
    
    try:
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except FileNotFoundError:
        return -1, "", "sshpass not found"

def check_vps_config():
    print("🔍 Checking VPS Gateway configuration...")
    
    # Check 1: Environment variables
    print("\n1️⃣ Checking environment variables...")
    code, stdout, stderr = run_ssh_command("cd /opt/stillme && env | grep -E '(ROUTING|PLACEHOLDER|MODEL|PROVIDER|API_KEY)' | head -20")
    if code == 0:
        print("   Environment variables:")
        for line in stdout.strip().split('\n'):
            if line.strip():
                # Redact API keys
                if 'API_KEY' in line or 'SECRET' in line or 'TOKEN' in line:
                    parts = line.split('=')
                    if len(parts) == 2:
                        key, value = parts
                        redacted_value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                        print(f"   {key}={redacted_value}")
                else:
                    print(f"   {line}")
    else:
        print(f"   ❌ Failed to check env vars: {stderr}")
    
    # Check 2: Gateway config files
    print("\n2️⃣ Checking gateway config files...")
    code, stdout, stderr = run_ssh_command("cd /opt/stillme && find . -name '*.py' -o -name '*.env' -o -name '*.yaml' -o -name '*.yml' | grep -E '(gateway|config|env)' | head -10")
    if code == 0:
        print("   Config files found:")
        for line in stdout.strip().split('\n'):
            if line.strip():
                print(f"   {line}")
    else:
        print(f"   ❌ Failed to find config files: {stderr}")
    
    # Check 3: Check gateway service status
    print("\n3️⃣ Checking gateway service status...")
    code, stdout, stderr = run_ssh_command("systemctl status stillme-gateway --no-pager")
    if code == 0:
        print("   Gateway service status:")
        for line in stdout.strip().split('\n')[:10]:
            if line.strip():
                print(f"   {line}")
    else:
        print(f"   ❌ Failed to check service status: {stderr}")
    
    # Check 4: Check AI server status
    print("\n4️⃣ Checking AI server status...")
    code, stdout, stderr = run_ssh_command("systemctl status stillme-ai-server --no-pager")
    if code == 0:
        print("   AI server service status:")
        for line in stdout.strip().split('\n')[:10]:
            if line.strip():
                print(f"   {line}")
    else:
        print(f"   ❌ Failed to check AI server status: {stderr}")

if __name__ == "__main__":
    check_vps_config()
