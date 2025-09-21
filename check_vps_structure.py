#!/usr/bin/env python3
"""
Check VPS structure and find gateway files
"""
import subprocess
import os

def run_ssh_command(command):
    """Run SSH command with timeout"""
    try:
        result = subprocess.run(
            f'ssh root@160.191.89.99 "{command}"',
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "SSH timeout"
    except Exception as e:
        return False, "", str(e)

def check_vps_structure():
    """Check VPS file structure"""
    print("🔍 Checking VPS structure...")
    
    commands = [
        "ls -la /opt/stillme/",
        "find /opt/stillme -name '*.py' -type f | head -10",
        "ps aux | grep -E '(gateway|gunicorn|python)' | grep -v grep",
        "systemctl list-units --type=service | grep stillme",
        "cat /opt/stillme/.env | grep -E '(ROUTING|MODEL|DEEPSEEK|GEMMA)' || echo 'No routing config found'"
    ]
    
    for i, cmd in enumerate(commands, 1):
        print(f"\n{i}. {cmd}")
        success, stdout, stderr = run_ssh_command(cmd)
        if success:
            print(stdout)
        else:
            print(f"Error: {stderr}")

if __name__ == "__main__":
    check_vps_structure()
