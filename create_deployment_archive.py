#!/usr/bin/env python3
"""
Create deployment archive for VPS upload
"""

import os
import tarfile
import subprocess
from pathlib import Path

def create_tar_gz():
    """Create tar.gz archive of deployment package"""
    print("📦 Creating deployment archive...")
    
    # Create tar.gz file
    with tarfile.open("stillme_deployment.tar.gz", "w:gz") as tar:
        tar.add("deployment_package", arcname="deployment_package")
    
    # Get file size
    size = os.path.getsize("stillme_deployment.tar.gz")
    size_mb = size / (1024 * 1024)
    
    print(f"✅ Archive created: stillme_deployment.tar.gz ({size_mb:.1f} MB)")
    return True

def main():
    """Main function"""
    print("🚀 StillMe Deployment Archive Creator")
    print("=" * 50)
    
    # Check if deployment_package exists
    if not Path("deployment_package").exists():
        print("❌ Error: deployment_package directory not found!")
        print("Please run deploy_stillme_to_vps.py first.")
        return False
    
    # Create archive
    if create_tar_gz():
        print("\n📋 UPLOAD INSTRUCTIONS:")
        print("=" * 50)
        print("1. Upload stillme_deployment.tar.gz to VPS:")
        print("   - Use SFTP client (FileZilla, WinSCP)")
        print("   - Or use web file manager if available")
        print("   - Upload to: /tmp/stillme_deployment.tar.gz")
        print()
        print("2. SSH into VPS and extract:")
        print("   ssh root@160.191.89.99")
        print("   cd /tmp")
        print("   tar -xzf stillme_deployment.tar.gz")
        print("   cd deployment_package")
        print("   chmod +x deploy.sh")
        print("   ./deploy.sh")
        print()
        print("🌐 Alternative: Use web file manager")
        print("   - Login to VPS control panel")
        print("   - Upload stillme_deployment.tar.gz")
        print("   - Extract in /tmp/ directory")
        
        return True
    
    return False

if __name__ == "__main__":
    main()
