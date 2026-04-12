#!/usr/bin/env python3
"""
Download correct pydantic-core binaries for Lambda Python 3.11
Uses subprocess to run pip with platform-specific parameters
"""
import subprocess
import sys
import shutil
import zipfile
from pathlib import Path

Path.cwd().__class__.__enter__ = lambda self: self
Path.cwd().__class__.__exit__ = lambda self, *args: None

import os
os.chdir(Path(__file__).parent)

# Remove old pydantic_core
print("🗑️ Cleaning old pydantic_core...")
if Path('deployment/pydantic_core').exists():
    shutil.rmtree('deployment/pydantic_core')

print("📥 Installing pydantic-core for Python 3.11 Linux x86_64...")

# Use pip to download the wheel with explicit platform
cmd = [
    sys.executable, '-m', 'pip',
    'download', 'pydantic-core==2.6.3',
    '--platform', 'manylinux_2_17_x86_64',
    '--python-version', '311',
    '--only-binary=:all:',
    '--no-deps',
    '-d', '.'
]

result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode != 0:
    print(f"❌ Download failed: {result.stderr[:200]}")
    # Try alternative: use older version that might have better wheel coverage
    print("\n🔄 Trying alternative version...")
    cmd[3] = 'pydantic-core==2.5.0'
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Still failed. Error: {result.stderr[:200]}")
        exit(1)

# Find and extract the wheel
wheels = list(Path('.').glob('pydantic_core-*.whl'))
if not wheels:
    print("❌ No wheel file found!")
    exit(1)

wheel_file = wheels[0]
print(f"✓ Found: {wheel_file.name}")

print("📦 Extracting...")
with zipfile.ZipFile(wheel_file, 'r') as z:
    z.extractall('deployment')

wheel_file.unlink()

# Verify
so_file = Path('deployment/pydantic_core/_pydantic_core.cpython-311-x86_64-linux-gnu.so')
if so_file.exists():
    print(f"✅ Ready! {so_file.name}")
else:
    print("❌ .so file missing after extraction!")
    exit(1)
