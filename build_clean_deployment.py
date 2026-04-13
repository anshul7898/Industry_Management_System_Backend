#!/usr/bin/env python3
"""
Build a clean deployment.zip for AWS Lambda.

Uses deploy_temp_deps_v2/ as the dependency source (clean FastAPI 0.135.3 + Pydantic 2.12.5)
and copies application code on top.
"""
import os
import stat
import shutil
import zipfile
from pathlib import Path


def force_remove_readonly(func, path, exc_info):
    """Handle permission errors on Windows/OneDrive by removing readonly flag."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

# Change to script directory
os.chdir(Path(__file__).parent)

CLEAN_DEPLOY_DIR = "deployment_clean"
DEPS_DIR = "deploy_temp_deps_v2"
ZIP_PATH = "deployment.zip"

# Application code directories/files to include
APP_DIRS = ["config", "db", "routes", "schemas", "utils"]
APP_FILES = ["main.py", "lambda_handler.py"]

# ── Step 1: Remove old artifacts ──────────────────────────────────────────
if os.path.exists(CLEAN_DEPLOY_DIR):
    shutil.rmtree(CLEAN_DEPLOY_DIR, onerror=force_remove_readonly)
    print(f"✓ Removed old {CLEAN_DEPLOY_DIR}/")

if os.path.exists(ZIP_PATH):
    os.remove(ZIP_PATH)
    print(f"✓ Removed old {ZIP_PATH}")

# ── Step 2: Copy clean dependencies ──────────────────────────────────────
print(f"\nCopying dependencies from {DEPS_DIR}/...")
shutil.copytree(DEPS_DIR, CLEAN_DEPLOY_DIR, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
print(f"✓ Dependencies copied")

# ── Step 3: Copy application code ────────────────────────────────────────
print("\nCopying application code...")
for app_file in APP_FILES:
    if os.path.exists(app_file):
        shutil.copy2(app_file, os.path.join(CLEAN_DEPLOY_DIR, app_file))
        print(f"  ✓ {app_file}")
    else:
        print(f"  ✗ {app_file} NOT FOUND!")

for app_dir in APP_DIRS:
    dest = os.path.join(CLEAN_DEPLOY_DIR, app_dir)
    if os.path.exists(dest):
        shutil.rmtree(dest, onerror=force_remove_readonly)
    if os.path.exists(app_dir):
        shutil.copytree(app_dir, dest, ignore=shutil.ignore_patterns("__pycache__"))
        print(f"  ✓ {app_dir}/")
    else:
        print(f"  ✗ {app_dir}/ NOT FOUND!")

# ── Step 4: Remove unnecessary files/dirs from deployment ────────────────
print("\nCleaning up unnecessary files...")
cleanup_patterns = ["__pycache__", ".DS_Store", "*.pyc"]
for root, dirs, files in os.walk(CLEAN_DEPLOY_DIR):
    # Remove __pycache__ directories
    for d in list(dirs):
        if d == "__pycache__":
            shutil.rmtree(os.path.join(root, d), onerror=force_remove_readonly)
            dirs.remove(d)
    # Remove .DS_Store and .pyc files
    for f in files:
        if f == ".DS_Store" or f.endswith(".pyc"):
            os.remove(os.path.join(root, f))

# Remove bin/ directory (not needed in Lambda)
bin_dir = os.path.join(CLEAN_DEPLOY_DIR, "bin")
if os.path.exists(bin_dir):
    try:
        shutil.rmtree(bin_dir, onerror=force_remove_readonly)
        print("  ✓ Removed bin/")
    except PermissionError:
        print("  ⚠ Could not remove bin/ (permission denied, skipping)")

print("✓ Cleanup done")

# ── Step 5: Create deployment.zip ────────────────────────────────────────
print(f"\nBuilding {ZIP_PATH}...")
with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(CLEAN_DEPLOY_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            # Use forward slashes for zip paths so it works on Lambda (Linux)
            arcname = os.path.relpath(file_path, CLEAN_DEPLOY_DIR).replace("\\", "/")
            zipf.write(file_path, arcname)

size_mb = os.path.getsize(ZIP_PATH) / (1024 * 1024)
print(f"✓ {ZIP_PATH} created: {size_mb:.2f} MB")

# ── Step 6: Verify key files ────────────────────────────────────────────
print("\nVerifying key files in ZIP:")
with zipfile.ZipFile(ZIP_PATH, 'r') as zipf:
    files = zipf.namelist()
    key_files = [
        'main.py',
        'lambda_handler.py',
        'config/settings.py',
        'db/dynamodb.py',
        'routes/orders.py',
        'fastapi/__init__.py',
        'fastapi/_compat/__init__.py',
        'pydantic/__init__.py',
        'pydantic_core/__init__.py',
        'pydantic_core/_pydantic_core.cpython-311-x86_64-linux-gnu.so',
        'mangum/__init__.py',
    ]
    all_ok = True
    for key_file in key_files:
        if key_file in files:
            print(f"  ✓ {key_file}")
        else:
            print(f"  ✗ {key_file} (MISSING!)")
            all_ok = False

    # Verify NO old _compat.py file (the one that defines PYDANTIC_V2)
    if 'fastapi/_compat.py' in files:
        print(f"  ⚠ fastapi/_compat.py found (old file, should not be present with new FastAPI)")
        all_ok = False
    else:
        print(f"  ✓ No old fastapi/_compat.py (good)")

    print(f"\nTotal files: {len(files)}")
    if all_ok:
        print("\n✅ Deployment package looks good! Upload deployment.zip to Lambda.")
    else:
        print("\n⚠ Some files are missing - check the output above.")
