#!/usr/bin/env python3
"""
Script to rebuild deployment.zip with latest code
"""
import os
import shutil
import zipfile
from pathlib import Path

# Set up paths
base_dir = Path(__file__).parent
deployment_dir = base_dir / 'deployment'
output_zip = base_dir / 'deployment.zip'

print(f"Base directory: {base_dir}")
print(f"Deployment directory: {deployment_dir}")
print(f"Output zip: {output_zip}")

# Remove old zip if exists
if output_zip.exists():
    print(f"Removing old {output_zip.name}...")
    output_zip.unlink()

# Create zip file
print("\nCreating deployment.zip...")
with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
    # Walk through deployment directory and add all files
    for root, dirs, files in os.walk(deployment_dir):
        for file in files:
            file_path = Path(root) / file
            # Get relative path from deployment directory
            arcname = file_path.relative_to(base_dir)
            print(f"  Adding: {arcname}")
            zipf.write(file_path, arcname=arcname)

# Verify zip file
zip_size_mb = output_zip.stat().st_size / (1024 * 1024)
print(f"\nDeployment zip created successfully!")
print(f"File: {output_zip.name}")
print(f"Size: {zip_size_mb:.2f} MB")

# Count files in zip
with zipfile.ZipFile(output_zip, 'r') as zipf:
    file_count = len(zipf.namelist())
    print(f"Files: {file_count}")
    print("\nFirst 10 files in zip:")
    for name in zipf.namelist()[:10]:
        print(f"  - {name}")

print("\n[SUCCESS] Deployment package rebuilt!")
