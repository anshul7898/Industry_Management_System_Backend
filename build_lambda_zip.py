#!/usr/bin/env python3
"""
Build deployment.zip correctly for Lambda (files at root, not nested)
"""
import os
import zipfile
from pathlib import Path

os.chdir(Path(__file__).parent)

deployment_dir = Path('deployment')
output_zip = Path('deployment.zip')

print("🗑️  Removing old deployment.zip...")
if output_zip.exists():
    output_zip.unlink()

print("📦 Creating deployment.zip with correct structure...")
print("   (Files at root level, NOT nested in deployment/ folder)\n")

with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(deployment_dir):
        # Skip cache and hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            # Skip cache and system files
            if file.endswith(('.pyc', '.DS_Store')):
                continue
            
            file_path = Path(root) / file
            # IMPORTANT: arcname should be relative to deployment_dir, not the project root
            # This strips 'deployment/' from the path in the zip
            arcname = file_path.relative_to(deployment_dir)
            
            zipf.write(file_path, arcname)

# Verify structure
print("✅ Verifying ZIP structure...\n")
with zipfile.ZipFile(output_zip, 'r') as zipf:
    files = zipf.namelist()
    
    # Check for root level files
    root_files = [f for f in files if not '/' in f or f.count('/') == 1 and f.endswith('.py')]
    print("Root level files:")
    for f in sorted(root_files)[:10]:
        print(f"  ✓ {f}")
    
    # Check critical packages
    print("\nCritical packages:")
    for pkg in ['fastapi', 'pydantic', 'mangum', 'boto3']:
        pkg_init = f"{pkg}/__init__.py"
        if pkg_init in files:
            print(f"  ✓ {pkg}")
        else:
            print(f"  ❌ {pkg} (MISSING!)")
    
    # Check main entry point
    if 'main.py' in files:
        print("\n✓ main.py found at root level (CORRECT)")
    else:
        print("\n❌ main.py NOT at root level (ERROR)")
    
    size_mb = output_zip.stat().st_size / (1024 * 1024)
    print(f"\n📊 Summary:")
    print(f"  Total files: {len(files)}")
    print(f"  Size: {size_mb:.2f} MB")

print("\n🎉 deployment.zip ready for Lambda!")
