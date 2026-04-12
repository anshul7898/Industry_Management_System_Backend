#!/usr/bin/env python3
"""
Complete rebuild of deployment package with clean dependencies
"""
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

os.chdir(Path(__file__).parent)

deployment_dir = Path('deployment')
zip_file = Path('deployment.zip')

# Step 1: Backup current deployment (just in case)
print("📦 Backing up current deployment...")
backup_dir = Path('deployment_backup')
if backup_dir.exists():
    shutil.rmtree(backup_dir)
if deployment_dir.exists():
    shutil.copytree(deployment_dir, backup_dir)

# Step 2: Clear deployment folder (keep structure)
print("🗑️  Cleaning deployment folder...")
if deployment_dir.exists():
    def handle_remove_error(func, path, exc):
        import stat
        os.chmod(path, stat.S_IWRITE)
        func(path)
    shutil.rmtree(deployment_dir, onerror=handle_remove_error)
deployment_dir.mkdir(exist_ok=True)

# Step 3: Remove old zip
if zip_file.exists():
    zip_file.unlink()
    print(f"✓ Removed old {zip_file.name}")

# Step 4: Install fresh dependencies to deployment folder
print("\n📥 Installing fresh dependencies...")
print("   Using: FastAPI 0.115.0 + Pydantic 2.8.2")

cmd = [
    sys.executable,
    '-m', 'pip',
    'install',
    '-r', 'requirements.txt',
    '-t', str(deployment_dir),
    '--upgrade',
    '--no-cache-dir'
]

result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print("❌ Installation failed!")
    print(result.stderr)
    sys.exit(1)
else:
    print("✓ Dependencies installed successfully")

# Step 5: Copy app files
print("\n📋 Copying application files...")
app_files = ['main.py', 'lambda_handler.py', 'seed_accounts.py', 'seed_orders.py']
for file in app_files:
    src = Path(file)
    if src.exists():
        shutil.copy2(src, deployment_dir / file)
        print(f"  ✓ {file}")

# Step 6: Copy config and routes/schemas/db/utils
dirs_to_copy = ['config', 'routes', 'schemas', 'db', 'utils']
for dir_name in dirs_to_copy:
    src_dir = Path(dir_name)
    if src_dir.exists():
        dest_dir = deployment_dir / dir_name
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        shutil.copytree(src_dir, dest_dir)
        print(f"  ✓ {dir_name}/")

# Step 7: Verify critical files
print("\n✅ Verifying critical packages...")
critical_files = [
    'main.py',
    'fastapi/__init__.py',
    'pydantic/__init__.py',
    'pydantic_core/__init__.py',
    'mangum/__init__.py',
    'boto3/__init__.py',
]

for file in critical_files:
    file_path = deployment_dir / file
    if file_path.exists():
        print(f"  ✓ {file}")
    else:
        print(f"  ❌ MISSING: {file}")

# Step 8: Create ZIP
print(f"\n📦 Creating {zip_file.name}...")
with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(deployment_dir):
        # Skip cache/pycache/dist-info metadata in certain cases
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if file.endswith('.pyc') or file == '.DS_Store':
                continue
            file_path = Path(root) / file
            arcname = file_path.relative_to(Path('.'))
            zipf.write(file_path, arcname)

zip_size_mb = zip_file.stat().st_size / (1024 * 1024)
print(f"✓ {zip_file.name} created: {zip_size_mb:.2f} MB")

# Step 9: Final summary
with zipfile.ZipFile(zip_file, 'r') as zipf:
    files_in_zip = zipf.namelist()
    
    print(f"\n📊 Final Summary:")
    print(f"  Total files: {len(files_in_zip)}")
    print(f"  Size: {zip_size_mb:.2f} MB")
    
    # Check for specific versions
    metadata_files = [f for f in files_in_zip if 'dist-info' in f and 'METADATA' in f]
    print(f"  Packages with metadata: {len(metadata_files)}")

print("\n🎉 Deployment rebuild complete! Ready to deploy to Lambda.")
