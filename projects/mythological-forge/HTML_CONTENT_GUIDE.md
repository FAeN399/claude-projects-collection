# HTML Content Management Guide

## Overview
The Mythological Forge supports both HTML and Markdown content. This guide explains how to manage your existing HTML stories and integrate new ones.

## Existing HTML Content Structure

Your project contains several HTML narratives:

### 1. **The Codex of Zatrix and Ariax** (`/Zatrix_Ariax/`)
- Multi-page philosophical narrative
- Files: `page1-medallion.html`, `page2-desert.html`, `page3-shadows.html`, `page4-threshold-king.html`
- Themes: Consciousness, existence, transformation

### 2. **Poems** (`/Poems/`)
- `saturn-lantern-myth.html` - Cosmic poetry about transformation

### 3. **Root Level**
- `page5-logos.html` - Continuation of Zatrix narrative
- `myth-forge.html` - Main interface

## Organization System for HTML

```
The-Mythological-Forge/
│
├── content/
│   ├── html-stories/              # Preserved HTML files
│   │   ├── modern/               # Modern/original works
│   │   ├── greek/                # Traditional myths in HTML
│   │   └── [culture]/            # Other origins
│   │
│   └── stories/                   # Markdown conversions
│       └── by-origin/
│           └── modern/
│               ├── zatrix-ariax-page1-medallion.md
│               ├── zatrix-ariax-page2-desert.md
│               └── saturn-lantern-myth.md
│
├── metadata/
│   └── catalogs/
│       ├── html-story-catalog.json    # Tracks all HTML content
│       └── story-catalog.json         # Unified catalog
```

## Import Process for HTML Files

### 1. Process All Existing HTML Files
```bash
python tools/import/import_html_story.py --process-existing
```

This will:
- Find all HTML files in your project
- Extract metadata from HTML structure
- Create Markdown versions while preserving original HTML
- Catalog everything for easy searching

### 2. Import Individual HTML File
```bash
python tools/import/import_html_story.py --file path/to/story.html
```

### 3. Import Without Converting (Catalog Only)
```bash
python tools/import/import_html_story.py --file story.html --no-convert
```

## HTML Metadata Extraction

The importer automatically extracts:

### From HTML Structure
- `<title>` tag content
- `<meta>` tags (description, author, keywords)
- Custom meta tags (myth-type, myth-origin)
- Section headers (h1, h2, h3)
- CSS themes and styling

### From File Analysis
- Collection membership (e.g., Zatrix_Ariax series)
- Page numbering for multi-part stories
- Content type (narrative, poem, codex)
- Visual themes (cosmic, mystical)

## Preserving HTML Features

### Visual Design
The system preserves:
- Original HTML files in `/content/html-stories/`
- CSS styles as comments in Markdown versions
- Visual theme metadata for future use

### Interactive Elements
- JavaScript preserved in original HTML
- Animations and effects documented in metadata
- Links to view original HTML maintained

## Viewing Options

### 1. Original HTML
Access preserved files directly:
```
content/html-stories/modern/zatrix-ariax-page1-medallion.html
```

### 2. Markdown Version
For editing and analysis:
```
content/stories/by-origin/modern/zatrix-ariax-page1-medallion.md
```

### 3. Web Interface
The main `myth-forge.html` can link to both versions

## Adding New HTML Content

### For Single Stories
1. Create your HTML file with the mystical styling
2. Add meta tags for better cataloging:
```html
<meta name="myth-type" content="transformation">
<meta name="myth-origin" content="Modern">
<meta name="description" content="A tale of consciousness awakening">
```
3. Import using the tool

### For Multi-Page Stories
1. Create a directory for the collection
2. Name files sequentially (page1, page2, etc.)
3. Import the directory:
```bash
python tools/import/import_html_story.py --process-existing
```

## HTML Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Story Title - The Mythological Forge</title>
    
    <!-- Mythological Forge Metadata -->
    <meta name="myth-type" content="transformation">
    <meta name="myth-origin" content="Modern">
    <meta name="author" content="Your Name">
    <meta name="description" content="Brief description">
    <meta name="keywords" content="consciousness, transformation, mythology">
    
    <style>
        /* Your cosmic/mystical styling */
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');
        
        body {
            background: radial-gradient(ellipse at center, #1a0033 0%, #0a0015 50%, #000000 100%);
            color: #e0e0f0;
            font-family: 'Crimson Text', serif;
        }
        /* ... rest of styling ... */
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Story Title</h1>
            <p class="subtitle">Subtitle or Context</p>
        </header>
        
        <main>
            <!-- Your narrative content -->
        </main>
    </div>
</body>
</html>
```

## Benefits of Dual Format

### HTML Advantages
- Rich visual presentation
- Interactive elements
- Atmospheric styling
- Web-ready display

### Markdown Advantages
- Easy editing
- Version control friendly
- Searchable content
- Cross-references
- AI processing ready

## Maintenance

### Regular Tasks
1. Run import tool when adding new HTML files
2. Update catalog after major changes
3. Backup both HTML and Markdown versions
4. Maintain cross-references between related stories

### Collection Management
For multi-part stories like Zatrix and Ariax:
```json
{
  "collection": "The Codex of Zatrix and Ariax",
  "stories": [
    "zatrix-ariax-page1-medallion",
    "zatrix-ariax-page2-desert",
    "zatrix-ariax-page3-shadows",
    "zatrix-ariax-page4-threshold-king"
  ],
  "sequence": true,
  "themes": ["consciousness", "threshold", "transformation"]
}
```

## Quick Commands

```bash
# Process all existing HTML
python tools/import/import_html_story.py --process-existing

# View HTML catalog
cat metadata/catalogs/html-story-catalog.json | python -m json.tool

# Find all HTML files
find . -name "*.html" -type f

# Create HTML stories directory
mkdir -p content/html-stories/{modern,greek,norse,egyptian}
```

## Integration with Main System

HTML stories are fully integrated:
- Appear in main story catalog
- Searchable by themes and tags
- Can be included in collections
- Cross-referenced with other myths
- Available for AI narrative generation

---

*The Mythological Forge preserves the mystical web experience while enabling powerful content management.*