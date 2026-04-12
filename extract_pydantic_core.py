#!/usr/bin/env python3
"""
Extract correct pydantic-core to deployment
"""
import zipfile
import shutil
from pathlib import Path

base = Path(__file__).parent

# Remove old
print("🗑️  Removing old pydantic_core...")
if (base / 'deployment' / 'pydantic_core').exists():
    shutil.rmtree(base / 'deployment' / 'pydantic_core')

# Find and extract the wheel
wheels = list(base.glob('pydantic_core-2.41.5*.whl'))
if not wheels:
    print("❌ Wheel not found!")
    exit(1)

wheel = wheels[0]
print(f"📦 Extracting {wheel.name}...")

with zipfile.ZipFile(wheel, 'r') as z:
    z.extractall(base / 'deployment')

print("✓ Done")

# Verify
so = base / 'deployment' / 'pydantic_core' / '_pydantic_core.cpython-311-x86_64-linux-gnu.so'
if so.exists():
    print(f"✅ Verified: {so.name}")
else:
    print("❌ .so file not found!")
