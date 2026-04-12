#!/usr/bin/env python3
import os
import shutil
import zipfile
from pathlib import Path

# Change to script directory
os.chdir(Path(__file__).parent)

# Remove old ZIP if exists
zip_path = 'deployment.zip'
if os.path.exists(zip_path):
    os.remove(zip_path)
    print("✓ Removed old deployment.zip")

# Create new ZIP from deployment folder
deployment_dir = 'deployment'
if not os.path.exists(deployment_dir):
    print("ERROR: deployment folder not found!")
    exit(1)

print(f"Building {zip_path}...")

# Create ZIP with all files from deployment folder
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(deployment_dir):
        for file in files:
            file_path = os.path.join(root, file)
            # Archive name should be relative path from deployment folder
            arcname = os.path.relpath(file_path, deployment_dir)
            zipf.write(file_path, arcname)

# Get size
size_mb = os.path.getsize(zip_path) / (1024 * 1024)
print(f"✓ deployment.zip created: {size_mb:.2f} MB")

# List key files to verify
print("\nVerifying key files in ZIP:")
with zipfile.ZipFile(zip_path, 'r') as zipf:
    files = zipf.namelist()
    key_files = ['main.py', 'pydantic/__init__.py', 'pydantic_core/__init__.py', '_pydantic_core.cpython-311-x86_64-linux-gnu.so']
    for key_file in key_files:
        if key_file in files:
            print(f"  ✓ {key_file}")
        else:
            print(f"  ✗ {key_file} (MISSING!)")
    
    print(f"\nTotal files: {len(files)}")
