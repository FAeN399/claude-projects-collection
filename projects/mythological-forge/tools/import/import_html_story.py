#!/usr/bin/env python3
"""
HTML Story Import Tool for The Mythological Forge
Imports and processes HTML mythological stories into the system
"""

import os
import json
import yaml
import argparse
import re
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import html2text
from typing import Dict, Any, Optional, List, Tuple

class HTMLStoryImporter:
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.schema_path = self.project_root / "metadata" / "schemas" / "story-schema.json"
        self.catalog_path = self.project_root / "metadata" / "catalogs" / "html-story-catalog.json"
        self.content_dir = self.project_root / "content" / "stories"
        self.html_dir = self.project_root / "content" / "html-stories"
        
        # HTML to Markdown converter
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.body_width = 0  # Don't wrap lines
        
        # Load or create catalog
        self.catalog = self._load_catalog()
    
    def _load_catalog(self) -> Dict[str, Any]:
        """Load existing catalog or create new one"""
        if self.catalog_path.exists():
            with open(self.catalog_path, 'r') as f:
                return json.load(f)
        return {
            "html_stories": {}, 
            "converted_stories": {},
            "last_updated": None, 
            "total_count": 0
        }
    
    def _save_catalog(self):
        """Save catalog to disk"""
        self.catalog["last_updated"] = datetime.now().isoformat()
        self.catalog["total_count"] = len(self.catalog["html_stories"])
        
        os.makedirs(self.catalog_path.parent, exist_ok=True)
        with open(self.catalog_path, 'w') as f:
            json.dump(self.catalog, f, indent=2)
    
    def _extract_html_metadata(self, soup: BeautifulSoup, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from HTML file"""
        metadata = {
            "format": "html",
            "original_file": str(file_path.name),
            "date_added": datetime.now().strftime("%Y-%m-%d")
        }
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            metadata["title"] = title_tag.get_text().strip()
        
        # Extract meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name', '').lower()
            content = meta.get('content', '')
            
            if name in ['description', 'author', 'keywords']:
                metadata[name] = content
            elif name == 'myth-type':
                metadata['type'] = content
            elif name == 'myth-origin':
                metadata['origin'] = {'culture': content}
        
        # Look for structured content in the HTML
        # Check for specific divs or classes used in your HTML files
        main_content = soup.find('div', class_='container') or soup.find('main') or soup.body
        
        # Extract narrative sections
        if main_content:
            # Look for section headers
            headers = main_content.find_all(['h1', 'h2', 'h3'])
            metadata['sections'] = [h.get_text().strip() for h in headers[:5]]  # First 5 headers
            
            # Extract any verse or poem structures
            verses = main_content.find_all(class_=['verse', 'poem', 'rewritten-verse'])
            if verses:
                metadata['has_verses'] = True
                metadata['verse_count'] = len(verses)
        
        return metadata
    
    def _analyze_content_type(self, soup: BeautifulSoup, file_path: Path) -> Dict[str, Any]:
        """Analyze the type and structure of the HTML content"""
        analysis = {
            "content_type": "narrative",  # default
            "structure": {},
            "themes": []
        }
        
        # Check file path for clues
        if "Zatrix_Ariax" in str(file_path):
            analysis["content_type"] = "codex"
            analysis["collection"] = "The Codex of Zatrix and Ariax"
            analysis["themes"] = ["consciousness", "existence", "threshold", "transformation"]
        elif "Poems" in str(file_path) or "saturn-lantern" in str(file_path.name):
            analysis["content_type"] = "poem"
            analysis["themes"] = ["cosmic", "transformation", "illumination"]
        elif "page" in str(file_path.name):
            # Extract page number
            page_match = re.search(r'page(\d+)', str(file_path.name))
            if page_match:
                analysis["page_number"] = int(page_match.group(1))
        
        # Analyze CSS for thematic elements
        styles = soup.find_all('style')
        for style in styles:
            style_text = style.get_text()
            if 'cosmic' in style_text or 'radial-gradient' in style_text:
                analysis["visual_theme"] = "cosmic"
            if '#9370DB' in style_text:  # Purple color
                analysis["color_scheme"] = "mystical"
        
        return analysis
    
    def _convert_html_to_markdown(self, html_content: str, preserve_style: bool = False) -> str:
        """Convert HTML to Markdown while preserving important elements"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script tags
        for script in soup.find_all('script'):
            script.decompose()
        
        if preserve_style:
            # Keep style information as a comment
            styles = soup.find_all('style')
            style_info = []
            for style in styles:
                style_info.append(f"<!-- Style preserved:\n{style.get_text()}\n-->")
            
            # Convert to markdown
            markdown = self.h2t.handle(str(soup))
            
            # Prepend style info
            if style_info:
                markdown = '\n'.join(style_info) + '\n\n' + markdown
        else:
            # Remove style tags for cleaner markdown
            for style in soup.find_all('style'):
                style.decompose()
            
            markdown = self.h2t.handle(str(soup))
        
        return markdown.strip()
    
    def _generate_metadata_from_analysis(self, html_metadata: Dict, content_analysis: Dict, 
                                       file_path: Path) -> Dict[str, Any]:
        """Generate story metadata from HTML analysis"""
        # Start with extracted metadata
        metadata = {
            "id": Path(file_path).stem.lower().replace(' ', '-'),
            "title": html_metadata.get("title", Path(file_path).stem.replace('-', ' ').title()),
            "version": "1.0",
            "status": "imported",
            "source_format": "html",
            "date_added": datetime.now().strftime("%Y-%m-%d")
        }
        
        # Add origin information
        if "origin" in html_metadata:
            metadata["origin"] = html_metadata["origin"]
        else:
            # Try to infer from content
            metadata["origin"] = {
                "culture": "Modern",
                "source_text": "The Mythological Forge"
            }
        
        # Determine type
        if content_analysis["content_type"] == "poem":
            metadata["type"] = "wisdom"
        elif content_analysis["content_type"] == "codex":
            metadata["type"] = "transformation"
        else:
            metadata["type"] = html_metadata.get("type", "other")
        
        # Add themes
        metadata["themes"] = content_analysis.get("themes", ["consciousness"])
        
        # Add collection info if part of a series
        if "collection" in content_analysis:
            metadata["collection"] = content_analysis["collection"]
            if "page_number" in content_analysis:
                metadata["sequence_number"] = content_analysis["page_number"]
        
        # Create summary
        metadata["summary"] = html_metadata.get("description", 
                                               f"HTML narrative from {metadata['title']}")
        
        # Add HTML-specific metadata
        metadata["html_metadata"] = {
            "original_file": str(file_path.name),
            "has_styles": content_analysis.get("visual_theme") is not None,
            "visual_theme": content_analysis.get("visual_theme", "default"),
            "preserve_formatting": True
        }
        
        return metadata
    
    def import_html_story(self, file_path: str, convert_to_md: bool = True,
                         preserve_original: bool = True) -> Dict[str, Any]:
        """Import an HTML story file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        
        # Read HTML content
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract metadata and analyze content
        html_metadata = self._extract_html_metadata(soup, file_path)
        content_analysis = self._analyze_content_type(soup, file_path)
        
        # Generate full metadata
        metadata = self._generate_metadata_from_analysis(
            html_metadata, content_analysis, file_path
        )
        
        # Store HTML location
        if preserve_original:
            # Copy HTML to html-stories directory
            html_dest_dir = self.html_dir / metadata["origin"]["culture"].lower()
            os.makedirs(html_dest_dir, exist_ok=True)
            
            html_dest = html_dest_dir / file_path.name
            with open(html_dest, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            metadata["html_metadata"]["preserved_path"] = str(
                html_dest.relative_to(self.project_root)
            )
        
        # Convert to Markdown if requested
        if convert_to_md:
            markdown_content = self._convert_html_to_markdown(
                html_content, 
                preserve_style=True
            )
            
            # Create markdown file with metadata
            md_content = f"""---
{yaml.dump(metadata, default_flow_style=False, allow_unicode=True)}---

{markdown_content}

---
*Original HTML file: {file_path.name}*
*Imported: {datetime.now().strftime("%Y-%m-%d %H:%M")}*
"""
            
            # Save markdown version
            save_dir = self.content_dir / "by-origin" / metadata["origin"]["culture"].lower()
            os.makedirs(save_dir, exist_ok=True)
            
            md_filename = f"{metadata['id']}.md"
            md_path = save_dir / md_filename
            
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            metadata["markdown_path"] = str(md_path.relative_to(self.project_root))
        
        # Update catalog
        self.catalog["html_stories"][metadata["id"]] = {
            "id": metadata["id"],
            "title": metadata["title"],
            "original_file": str(file_path),
            "type": metadata["type"],
            "themes": metadata.get("themes", []),
            "html_path": metadata["html_metadata"].get("preserved_path"),
            "markdown_path": metadata.get("markdown_path"),
            "collection": metadata.get("collection"),
            "date_imported": metadata["date_added"]
        }
        
        self._save_catalog()
        
        return {
            "success": True,
            "id": metadata["id"],
            "metadata": metadata,
            "paths": {
                "html": metadata["html_metadata"].get("preserved_path"),
                "markdown": metadata.get("markdown_path")
            }
        }
    
    def process_existing_html(self) -> Dict[str, Any]:
        """Process all existing HTML files in the project"""
        results = {
            "processed": [],
            "failed": [],
            "collections_found": {}
        }
        
        # Define paths to check
        html_locations = [
            self.project_root / "Zatrix_Ariax",
            self.project_root / "Poems",
            self.project_root / "*.html"
        ]
        
        # Find all HTML files
        html_files = []
        for location in html_locations:
            if location.is_dir():
                html_files.extend(location.glob("*.html"))
            else:
                html_files.extend(self.project_root.glob(str(location.name)))
        
        # Also check for any HTML files in root
        html_files.extend(self.project_root.glob("*.html"))
        
        # Process each file
        for html_file in html_files:
            print(f"Processing: {html_file.name}")
            result = self.import_html_story(
                str(html_file),
                convert_to_md=True,
                preserve_original=True
            )
            
            if result["success"]:
                results["processed"].append({
                    "file": str(html_file.name),
                    "id": result["id"],
                    "title": result["metadata"]["title"]
                })
                
                # Track collections
                if "collection" in result["metadata"]:
                    collection = result["metadata"]["collection"]
                    if collection not in results["collections_found"]:
                        results["collections_found"][collection] = []
                    results["collections_found"][collection].append(result["id"])
            else:
                results["failed"].append({
                    "file": str(html_file.name),
                    "error": result.get("error", "Unknown error")
                })
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description="Import HTML stories into The Mythological Forge"
    )
    parser.add_argument("--file", "-f", help="Path to HTML file to import")
    parser.add_argument("--process-existing", action="store_true",
                       help="Process all existing HTML files in the project")
    parser.add_argument("--no-convert", action="store_true",
                       help="Don't convert to Markdown, just catalog")
    parser.add_argument("--project-root", help="Path to project root directory")
    
    args = parser.parse_args()
    
    importer = HTMLStoryImporter(args.project_root)
    
    if args.process_existing:
        print("Processing existing HTML files...")
        results = importer.process_existing_html()
        
        print(f"\nProcessing Complete:")
        print(f"  Successfully processed: {len(results['processed'])}")
        print(f"  Failed: {len(results['failed'])}")
        
        if results['processed']:
            print("\nProcessed files:")
            for item in results['processed']:
                print(f"  ✓ {item['file']} → {item['title']}")
        
        if results['collections_found']:
            print("\nCollections found:")
            for collection, stories in results['collections_found'].items():
                print(f"  📚 {collection}: {len(stories)} stories")
        
        if results['failed']:
            print("\nFailed files:")
            for item in results['failed']:
                print(f"  ✗ {item['file']}: {item['error']}")
    
    elif args.file:
        result = importer.import_html_story(
            args.file,
            convert_to_md=not args.no_convert
        )
        
        if result["success"]:
            print(f"✓ Successfully imported: {result['id']}")
            print(f"  Title: {result['metadata']['title']}")
            if result['paths'].get('html'):
                print(f"  HTML preserved at: {result['paths']['html']}")
            if result['paths'].get('markdown'):
                print(f"  Markdown created at: {result['paths']['markdown']}")
        else:
            print(f"✗ Import failed: {result['error']}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()