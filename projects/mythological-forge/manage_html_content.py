#!/usr/bin/env python3
"""
HTML Content Manager for The Mythological Forge
Manages existing HTML narratives and provides easy access
"""

import os
import json
from pathlib import Path
from datetime import datetime
import webbrowser
import http.server
import socketserver
import threading
from typing import Dict, List, Optional

class HTMLContentManager:
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.html_catalog_path = self.project_root / "metadata" / "catalogs" / "html-story-catalog.json"
        
        # Known HTML content locations
        self.html_locations = {
            "Zatrix and Ariax Codex": {
                "path": "Zatrix_Ariax",
                "files": [
                    "page1-medallion.html",
                    "page2-desert.html", 
                    "page3-shadows.html",
                    "page4-threshold-king.html"
                ],
                "description": "A philosophical journey through consciousness and transformation"
            },
            "Poems": {
                "path": "Poems",
                "files": ["saturn-lantern-myth.html"],
                "description": "Cosmic poetry and mythological verses"
            },
            "Additional Pages": {
                "path": ".",
                "files": ["page5-logos.html"],
                "description": "Extended narratives and conclusions"
            },
            "Main Interface": {
                "path": "Docs_Start",
                "files": ["myth-forge.html"],
                "description": "The Mythological Forge main interface"
            }
        }
    
    def list_html_content(self) -> Dict[str, List[Dict]]:
        """List all HTML content organized by collection"""
        content = {}
        
        for collection, info in self.html_locations.items():
            content[collection] = []
            base_path = self.project_root / info["path"]
            
            for filename in info["files"]:
                file_path = base_path / filename
                if file_path.exists():
                    content[collection].append({
                        "filename": filename,
                        "path": str(file_path.relative_to(self.project_root)),
                        "exists": True,
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
                else:
                    content[collection].append({
                        "filename": filename,
                        "path": str((base_path / filename).relative_to(self.project_root)),
                        "exists": False
                    })
        
        return content
    
    def create_index_html(self) -> str:
        """Create an index page for all HTML content"""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Mythological Forge - HTML Content Index</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');
        
        :root {
            --primary: #9370DB;
            --secondary: #40E0D0;
            --accent: #FFD700;
            --dark: #1a0033;
            --text: #e0e0f0;
        }
        
        body {
            background: radial-gradient(ellipse at center, var(--dark) 0%, #0a0015 50%, #000000 100%);
            color: var(--text);
            font-family: 'Crimson Text', serif;
            line-height: 1.8;
            padding: 40px;
            margin: 0;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        
        h1 {
            font-family: 'Cinzel', serif;
            font-size: 3rem;
            text-align: center;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 50%, var(--accent) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 40px;
        }
        
        .collection {
            background: rgba(147, 112, 219, 0.1);
            border: 1px solid rgba(147, 112, 219, 0.3);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
        }
        
        .collection h2 {
            font-family: 'Cinzel', serif;
            color: var(--secondary);
            margin-bottom: 10px;
        }
        
        .description {
            font-style: italic;
            margin-bottom: 20px;
            opacity: 0.8;
        }
        
        .story-list {
            list-style: none;
            padding: 0;
        }
        
        .story-item {
            margin-bottom: 15px;
            padding: 10px;
            background: rgba(64, 224, 208, 0.05);
            border-left: 3px solid var(--accent);
            transition: all 0.3s ease;
        }
        
        .story-item:hover {
            background: rgba(64, 224, 208, 0.1);
            transform: translateX(5px);
        }
        
        .story-link {
            color: var(--text);
            text-decoration: none;
            font-size: 1.1rem;
        }
        
        .story-link:hover {
            color: var(--accent);
        }
        
        .metadata {
            font-size: 0.9rem;
            opacity: 0.7;
            margin-top: 5px;
        }
        
        .not-found {
            opacity: 0.5;
            font-style: italic;
        }
        
        .navigation {
            text-align: center;
            margin-top: 40px;
            padding-top: 30px;
            border-top: 1px solid rgba(147, 112, 219, 0.3);
        }
        
        .nav-link {
            display: inline-block;
            margin: 0 15px;
            padding: 10px 20px;
            background: rgba(147, 112, 219, 0.2);
            border: 1px solid var(--primary);
            border-radius: 5px;
            color: var(--text);
            text-decoration: none;
            transition: all 0.3s ease;
        }
        
        .nav-link:hover {
            background: rgba(147, 112, 219, 0.4);
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>The Mythological Forge</h1>
        <p style="text-align: center; font-style: italic; margin-bottom: 40px;">
            HTML Narrative Collection
        </p>
"""
        
        content = self.list_html_content()
        
        for collection, info in self.html_locations.items():
            html += f"""
        <div class="collection">
            <h2>{collection}</h2>
            <p class="description">{info['description']}</p>
            <ul class="story-list">
"""
            
            for file_info in content.get(collection, []):
                if file_info['exists']:
                    html += f"""
                <li class="story-item">
                    <a href="{file_info['path']}" class="story-link">{file_info['filename']}</a>
                    <div class="metadata">
                        Modified: {file_info['modified']} | 
                        Size: {file_info['size']:,} bytes
                    </div>
                </li>
"""
                else:
                    html += f"""
                <li class="story-item not-found">
                    {file_info['filename']} (not found)
                </li>
"""
            
            html += """
            </ul>
        </div>
"""
        
        html += """
        <div class="navigation">
            <a href="Docs_Start/myth-forge.html" class="nav-link">Main Interface</a>
            <a href="CONTENT_ORGANIZATION.md" class="nav-link">Organization Guide</a>
            <a href="HTML_CONTENT_GUIDE.md" class="nav-link">HTML Guide</a>
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def create_collection_viewer(self, collection_name: str) -> Optional[str]:
        """Create a viewer page for a specific collection"""
        if collection_name not in self.html_locations:
            return None
        
        collection = self.html_locations[collection_name]
        if collection_name == "Zatrix and Ariax Codex":
            return self._create_zatrix_viewer()
        elif collection_name == "Poems":
            return self._create_poems_viewer()
        else:
            return None
    
    def _create_zatrix_viewer(self) -> str:
        """Create a special viewer for the Zatrix and Ariax series"""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Codex of Zatrix and Ariax - Complete</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');
        
        body {
            background: radial-gradient(ellipse at center, #1a0033 0%, #0a0015 50%, #000000 100%);
            color: #e0e0f0;
            font-family: 'Crimson Text', serif;
            margin: 0;
            padding: 0;
        }
        
        .navigation {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            background: rgba(26, 0, 51, 0.9);
            padding: 20px;
            border: 1px solid rgba(147, 112, 219, 0.5);
            border-radius: 10px;
        }
        
        .nav-title {
            font-family: 'Cinzel', serif;
            color: #FFD700;
            margin-bottom: 15px;
            font-size: 1.2rem;
        }
        
        .page-link {
            display: block;
            color: #e0e0f0;
            text-decoration: none;
            padding: 8px;
            margin-bottom: 5px;
            transition: all 0.3s ease;
        }
        
        .page-link:hover {
            color: #40E0D0;
            transform: translateX(5px);
        }
        
        .page-link.active {
            color: #FFD700;
            border-left: 3px solid #FFD700;
            padding-left: 15px;
        }
        
        .content-frame {
            width: 100%;
            height: 100vh;
            border: none;
        }
        
        .sequence-nav {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 20px;
            background: rgba(26, 0, 51, 0.9);
            padding: 15px;
            border-radius: 30px;
            border: 1px solid rgba(147, 112, 219, 0.5);
        }
        
        .seq-btn {
            background: rgba(147, 112, 219, 0.3);
            border: 1px solid #9370DB;
            color: #e0e0f0;
            padding: 10px 20px;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: 'Crimson Text', serif;
            font-size: 1.1rem;
        }
        
        .seq-btn:hover {
            background: rgba(147, 112, 219, 0.5);
            transform: translateY(-2px);
        }
        
        .seq-btn:disabled {
            opacity: 0.3;
            cursor: not-allowed;
        }
    </style>
</head>
<body>
    <div class="navigation">
        <div class="nav-title">The Codex</div>
        <a href="#" class="page-link active" data-page="1">I. The Medallion</a>
        <a href="#" class="page-link" data-page="2">II. The Desert</a>
        <a href="#" class="page-link" data-page="3">III. Shadows</a>
        <a href="#" class="page-link" data-page="4">IV. Threshold King</a>
        <a href="#" class="page-link" data-page="5">V. Logos</a>
    </div>
    
    <iframe id="contentFrame" class="content-frame" src="Zatrix_Ariax/page1-medallion.html"></iframe>
    
    <div class="sequence-nav">
        <button class="seq-btn" id="prevBtn" onclick="navigate(-1)" disabled>← Previous</button>
        <button class="seq-btn" id="homeBtn" onclick="goHome()">Index</button>
        <button class="seq-btn" id="nextBtn" onclick="navigate(1)">Next →</button>
    </div>
    
    <script>
        const pages = [
            'Zatrix_Ariax/page1-medallion.html',
            'Zatrix_Ariax/page2-desert.html',
            'Zatrix_Ariax/page3-shadows.html',
            'Zatrix_Ariax/page4-threshold-king.html',
            'page5-logos.html'
        ];
        
        let currentPage = 0;
        
        function loadPage(index) {
            if (index >= 0 && index < pages.length) {
                document.getElementById('contentFrame').src = pages[index];
                currentPage = index;
                updateNavigation();
            }
        }
        
        function navigate(direction) {
            loadPage(currentPage + direction);
        }
        
        function goHome() {
            window.location.href = 'html_index.html';
        }
        
        function updateNavigation() {
            // Update sequential navigation
            document.getElementById('prevBtn').disabled = currentPage === 0;
            document.getElementById('nextBtn').disabled = currentPage === pages.length - 1;
            
            // Update sidebar
            document.querySelectorAll('.page-link').forEach((link, index) => {
                link.classList.toggle('active', index === currentPage);
            });
        }
        
        // Setup sidebar clicks
        document.querySelectorAll('.page-link').forEach((link, index) => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                loadPage(index);
            });
        });
    </script>
</body>
</html>
"""
        return html
    
    def serve_html_content(self, port: int = 8000):
        """Start a local server to view HTML content"""
        os.chdir(self.project_root)
        
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(self.project_root), **kwargs)
        
        with socketserver.TCPServer(("", port), Handler) as httpd:
            print(f"🌐 Serving HTML content at http://localhost:{port}")
            print(f"📄 View index at http://localhost:{port}/html_index.html")
            print("Press Ctrl+C to stop the server")
            
            # Open browser
            webbrowser.open(f"http://localhost:{port}/html_index.html")
            
            httpd.serve_forever()
    
    def generate_index(self):
        """Generate the HTML index file"""
        index_path = self.project_root / "html_index.html"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(self.create_index_html())
        print(f"✓ Created HTML index at: {index_path}")
        
        # Also create the Zatrix viewer
        viewer_path = self.project_root / "zatrix_viewer.html"
        with open(viewer_path, 'w', encoding='utf-8') as f:
            f.write(self._create_zatrix_viewer())
        print(f"✓ Created Zatrix viewer at: {viewer_path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage HTML content in The Mythological Forge")
    parser.add_argument("--list", action="store_true", help="List all HTML content")
    parser.add_argument("--index", action="store_true", help="Generate HTML index page")
    parser.add_argument("--serve", action="store_true", help="Start local server to view content")
    parser.add_argument("--port", type=int, default=8000, help="Port for local server")
    
    args = parser.parse_args()
    
    manager = HTMLContentManager()
    
    if args.list:
        content = manager.list_html_content()
        for collection, files in content.items():
            print(f"\n📚 {collection}")
            print(f"   {manager.html_locations[collection]['description']}")
            for file_info in files:
                status = "✓" if file_info['exists'] else "✗"
                print(f"   {status} {file_info['filename']}")
    
    elif args.index:
        manager.generate_index()
    
    elif args.serve:
        manager.generate_index()  # Ensure index exists
        manager.serve_html_content(args.port)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()