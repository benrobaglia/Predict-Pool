#!/usr/bin/env python3
"""
Main entry point for the PredictPool backend application in Docker.
This script creates and runs the Flask application.
"""

import sys
import os

# Create Docker-specific versions of the files with relative imports
def fix_imports():
    """Fix imports in all Python files to use relative imports instead of absolute imports"""
    import re
    
    # Define the files to fix
    files = [
        ('src/app.py', r'from backend\.src import', 'from src import'),
        ('src/app.py', r'from backend\.config import', 'from config import'),
        ('src/models.py', r'from backend\.config import', 'from config import'),
        ('src/blockchain.py', r'from backend\.config import', 'from config import'),
        ('src/tasks.py', r'from backend\.src import', 'from src import'),
        ('src/tasks.py', r'from backend\.config import', 'from config import'),
        ('src/routes.py', r'from backend\.src import', 'from src import'),
        ('src/routes.py', r'from backend\.src\.tasks import', 'from src.tasks import'),
    ]
    
    for file_path, pattern, replacement in files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Replace the imports
            modified_content = re.sub(pattern, replacement, content)
            
            with open(file_path, 'w') as f:
                f.write(modified_content)
            
            print(f"Fixed imports in {file_path}")

# Fix imports before importing the app
fix_imports()

# Import the app module
from src.app import create_app

if __name__ == '__main__':
    app = create_app()
    
    try:
        # Run the app
        from config import config
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=config.DEBUG,
            use_reloader=False  # Disable reloader to prevent duplicate scheduler initialization
        )
    except KeyboardInterrupt:
        print("Application stopped")