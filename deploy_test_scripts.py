#!/usr/bin/env python3
"""
Deploy test scripts to VPS
"""
import subprocess
import os

def run_ssh_command(command):
    """Run SSH command"""
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

def deploy_scripts():
    """Deploy test scripts to VPS"""
    print("🚀 Deploying test scripts to VPS...")
    
    # Create tools directory
    success, stdout, stderr = run_ssh_command("mkdir -p /opt/stillme/tools")
    if success:
        print("✅ Created /opt/stillme/tools directory")
    else:
        print(f"❌ Failed to create directory: {stderr}")
        return False
    
    # Read and upload simple test script
    with open('test_vps_gateway_simple.sh', 'r') as f:
        simple_script = f.read()
    
    # Upload simple script
    success, stdout, stderr = run_ssh_command(f'cat > /opt/stillme/tools/test_vps_gateway_simple.sh << "EOF"\n{simple_script}\nEOF')
    if success:
        print("✅ Uploaded simple test script")
    else:
        print(f"❌ Failed to upload simple script: {stderr}")
        return False
    
    # Read and upload complex test script
    with open('test_vps_gateway_complex.sh', 'r') as f:
        complex_script = f.read()
    
    # Upload complex script
    success, stdout, stderr = run_ssh_command(f'cat > /opt/stillme/tools/test_vps_gateway_complex.sh << "EOF"\n{complex_script}\nEOF')
    if success:
        print("✅ Uploaded complex test script")
    else:
        print(f"❌ Failed to upload complex script: {stderr}")
        return False
    
    # Make scripts executable
    success, stdout, stderr = run_ssh_command("chmod +x /opt/stillme/tools/test_vps_gateway_*.sh")
    if success:
        print("✅ Made scripts executable")
    else:
        print(f"❌ Failed to make executable: {stderr}")
        return False
    
    print("🎉 All scripts deployed successfully!")
    return True

if __name__ == "__main__":
    deploy_scripts()
