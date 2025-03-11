#!/usr/bin/env python3
"""
Script to verify that all imports are working correctly.
This script imports all modules from the backend package.
"""

import sys
import os

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

print("Verifying imports...")

# Import all modules
try:
    from backend.config import config
    print("✓ backend.config.config")
except ImportError as e:
    print(f"✗ backend.config.config: {e}")

try:
    from backend.src import app
    print("✓ backend.src.app")
except ImportError as e:
    print(f"✗ backend.src.app: {e}")

try:
    from backend.src import models
    print("✓ backend.src.models")
except ImportError as e:
    print(f"✗ backend.src.models: {e}")

try:
    from backend.src import blockchain
    print("✓ backend.src.blockchain")
except ImportError as e:
    print(f"✗ backend.src.blockchain: {e}")

try:
    from backend.src import routes
    print("✓ backend.src.routes")
except ImportError as e:
    print(f"✗ backend.src.routes: {e}")

try:
    from backend.src import tasks
    print("✓ backend.src.tasks")
except ImportError as e:
    print(f"✗ backend.src.tasks: {e}")

try:
    from backend.src import utils
    print("✓ backend.src.utils")
except ImportError as e:
    print(f"✗ backend.src.utils: {e}")

print("\nVerification complete.")