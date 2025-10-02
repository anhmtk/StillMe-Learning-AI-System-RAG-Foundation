#!/usr/bin/env python3
"""
Create ZIP archive for VPS deployment
"""

import os
import zipfile
from pathlib import Path


def create_zip():
    """Create ZIP archive of deployment package"""
    print("📦 Creating ZIP archive...")

    zip_path = "stillme_deployment.zip"

    # Remove existing ZIP if exists
    if os.path.exists(zip_path):
        os.remove(zip_path)
        print(f"🗑️ Removed existing {zip_path}")

    # Create ZIP file
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add all files from deployment_package
        for root, dirs, files in os.walk("deployment_package"):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, "deployment_package")
                zipf.write(file_path, arcname)
                print(f"✅ Added: {arcname}")

    # Get file size
    size = os.path.getsize(zip_path)
    size_mb = size / (1024 * 1024)

    print(f"🎉 ZIP created successfully: {zip_path} ({size_mb:.1f} MB)")
    return True

if __name__ == "__main__":
    create_zip()
