#!/usr/bin/env python3
"""
Package the browser extension into a ZIP file
Run this script to create impossible_ext.zip
"""

import os
import zipfile

def create_extension_zip():
    extension_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(extension_dir, 'impossible_ext.zip')
    
    files_to_include = [
        'manifest.json',
        'background.js',
        'popup.html',
        'popup.js',
        'content.js',
        'content.css'
    ]
    
    print("Packaging extension...")
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files_to_include:
            file_path = os.path.join(extension_dir, file)
            if os.path.exists(file_path):
                zipf.write(file_path, file)
                print(f"  Added: {file}")
            else:
                print(f"  Warning: {file} not found")
    
    print(f"\nExtension packaged: {output_path}")
    print(f"Size: {os.path.getsize(output_path)} bytes")

if __name__ == '__main__':
    create_extension_zip()
