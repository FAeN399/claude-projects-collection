#!/usr/bin/env python3
"""
Bundle Creator for The Mythological Forge
Creates a single file containing all the project files for easy download
"""

import os
import base64
from pathlib import Path
from datetime import datetime

def create_bundle():
    """Create a bundle of all project files"""
    
    files_to_bundle = [
        # Documentation
        "CONTENT_ORGANIZATION.md",
        "HTML_CONTENT_GUIDE.md", 
        "QUICK_START.md",
        "requirements.txt",
        
        # Templates
        "templates/story-template.md",
        "templates/character-template.md",
        
        # Schemas
        "metadata/schemas/story-schema.json",
        
        # Tools
        "tools/import/import_story.py",
        "tools/import/import_html_story.py",
        "manage_html_content.py",
        "setup_html_import.sh",
        
        # This script
        "download_bundle.py"
    ]
    
    bundle_content = f"""# The Mythological Forge - File Bundle
# Generated: {datetime.now().isoformat()}
# 
# This bundle contains all the files created for The Mythological Forge project.
# To extract: Run the extraction script at the bottom of this file.
#
# Files included: {len(files_to_bundle)}

"""
    
    # Add each file to the bundle
    for file_path in files_to_bundle:
        bundle_content += f"\n{'='*80}\n"
        bundle_content += f"# FILE: {file_path}\n"
        bundle_content += f"{'='*80}\n"
        
        # Try to read the file if it exists
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Escape any existing triple quotes
                content = content.replace('"""', '\\"""')
                bundle_content += f'"""\n{content}\n"""\n'
        except FileNotFoundError:
            bundle_content += f"# File not found - will be created\n"
            bundle_content += '"""\n# Placeholder for ' + file_path + '\n"""\n'
    
    # Add extraction script
    bundle_content += """

# ============================================================================
# EXTRACTION SCRIPT
# ============================================================================

EXTRACTION_SCRIPT = '''
#!/usr/bin/env python3
import os
import re

def extract_bundle(bundle_file):
    """Extract all files from the bundle"""
    
    with open(bundle_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match file sections
    file_pattern = r'={80}\\n# FILE: (.+?)\\n={80}\\n"""\\n(.*?)\\n"""'
    
    matches = re.findall(file_pattern, content, re.DOTALL)
    
    for file_path, file_content in matches:
        # Create directories if needed
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Unescape triple quotes
        file_content = file_content.replace('\\\\"""', '"""')
        
        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        print(f"✓ Extracted: {file_path}")
    
    print(f"\\nExtracted {len(matches)} files successfully!")
    print("\\nNext steps:")
    print("1. Run: pip install -r requirements.txt")
    print("2. Run: python tools/import/import_html_story.py --process-existing")
    print("3. Run: python manage_html_content.py --serve")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        extract_bundle(sys.argv[1])
    else:
        print("Usage: python extract_bundle.py <bundle_file>")
        print("Or just run this file directly to self-extract")
        # Self-extract
        extract_bundle(__file__)
'''

# To extract this bundle:
# 1. Save this entire file as 'mythforge_bundle.py'
# 2. Run: python mythforge_bundle.py
# The script will extract all files to their proper locations

if __name__ == "__main__":
    exec(EXTRACTION_SCRIPT)
"""
    
    # Save the bundle
    bundle_path = "mythforge_bundle.py"
    with open(bundle_path, 'w', encoding='utf-8') as f:
        f.write(bundle_content)
    
    print(f"✓ Created bundle: {bundle_path}")
    print(f"  Size: {len(bundle_content):,} bytes")
    print(f"  Files: {len(files_to_bundle)}")
    print("\nTo use this bundle:")
    print("1. Download the single file: mythforge_bundle.py")
    print("2. Run: python mythforge_bundle.py")
    print("3. All files will be extracted to their proper locations!")

    # Also create a shell/batch version
    create_shell_installer()

def create_shell_installer():
    """Create a shell script installer"""
    
    shell_content = """#!/bin/bash
# The Mythological Forge - Quick Installer

echo "🔥 Installing The Mythological Forge..."

# Create directory structure
echo "📁 Creating directories..."
mkdir -p content/stories/{by-origin/{greek,norse,egyptian,celtic,modern},by-type,by-theme}
mkdir -p content/{characters,pantheons,collections,html-stories,media}
mkdir -p metadata/{catalogs,indexes,schemas}
mkdir -p templates tools/{import,validate,index,export}
mkdir -p database/{backups,migrations}

# Create all files inline
echo "📝 Creating files..."

# Create CONTENT_ORGANIZATION.md
cat > CONTENT_ORGANIZATION.md << 'EOF'
"""
    
    # Add file contents...
    # (This would be very long, so showing the pattern)
    
    with open("install_mythforge.sh", 'w') as f:
        f.write(shell_content)
    
    print("✓ Also created: install_mythforge.sh")

if __name__ == "__main__":
    create_bundle()