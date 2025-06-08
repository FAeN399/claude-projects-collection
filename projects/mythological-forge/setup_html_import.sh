#!/bin/bash
# Setup script for HTML content import in The Mythological Forge

echo "🔥 Setting up HTML import system for The Mythological Forge..."

# Create necessary directories
echo "📁 Creating directory structure..."
mkdir -p content/html-stories/{modern,greek,norse,egyptian,celtic,other}
mkdir -p metadata/catalogs
mkdir -p tools/import

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install beautifulsoup4 html2text pyyaml jsonschema

# Set execute permissions on import script
echo "🔧 Setting permissions..."
chmod +x tools/import/import_html_story.py

# Process existing HTML files
echo "📄 Processing existing HTML files..."
echo "Found the following HTML content:"
find . -name "*.html" -type f | grep -E "(Zatrix_Ariax|Poems|page5)" | while read -r file; do
    echo "  - $file"
done

echo ""
echo "🚀 Ready to import! Run the following command to process all existing HTML:"
echo "   python tools/import/import_html_story.py --process-existing"
echo ""
echo "Or import individual files with:"
echo "   python tools/import/import_html_story.py --file path/to/story.html"
echo ""
echo "✨ The Mythological Forge HTML import system is ready!"