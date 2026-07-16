#!/usr/bin/env python3
"""
Setup script for The Impossible Challenge
Automates installation and configuration
"""

import os
import subprocess
import sys

def run_command(command, cwd=None):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✓ {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {command}")
        print(f"  Error: {e.stderr}")
        return False

def main():
    print("=" * 60)
    print("THE IMPOSSIBLE CHALLENGE - SETUP")
    print("=" * 60)
    print()
    
    # Get the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Step 1: Check Python version
    print("Step 1: Checking Python version...")
    if sys.version_info < (3, 8):
        print("✗ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print()
    
    # Step 2: Install dependencies
    print("Step 2: Installing Python dependencies...")
    if not run_command("pip install -r requirements.txt", cwd=script_dir):
        print("Failed to install dependencies")
        sys.exit(1)
    print()
    
    # Step 3: Package extension
    print("Step 3: Packaging browser extension...")
    extension_dir = os.path.join(script_dir, "extension")
    if not run_command("python package_extension.py", cwd=extension_dir):
        print("Failed to package extension")
        sys.exit(1)
    print()
    
    # Step 4: Create necessary directories
    print("Step 4: Creating directories...")
    dirs = ["templates", "static/css", "static/js"]
    for d in dirs:
        dir_path = os.path.join(script_dir, d)
        os.makedirs(dir_path, exist_ok=True)
        print(f"✓ {d}")
    print()
    
    # Done
    print("=" * 60)
    print("SETUP COMPLETE!")
    print("=" * 60)
    print()
    print("To start the challenge:")
    print(f"  cd {script_dir}")
    print("  python server.py")
    print()
    print("Then open your browser to:")
    print("  http://localhost:5000")
    print()
    print("Good luck, challenger!")
    print("=" * 60)

if __name__ == '__main__':
    main()
