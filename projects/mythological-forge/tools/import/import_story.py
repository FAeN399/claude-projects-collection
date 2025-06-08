#!/usr/bin/env python3
"""
Story Import Tool for The Mythological Forge
Imports and validates mythological stories into the system
"""

import os
import json
import yaml
import argparse
import re
from datetime import datetime
from pathlib import Path
import hashlib
import jsonschema
from typing import Dict, Any, Optional, List

class StoryImporter:
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.schema_path = self.project_root / "metadata" / "schemas" / "story-schema.json"
        self.catalog_path = self.project_root / "metadata" / "catalogs" / "story-catalog.json"
        self.content_dir = self.project_root / "content" / "stories"
        
        # Load schema
        with open(self.schema_path, 'r') as f:
            self.schema = json.load(f)
        
        # Load or create catalog
        self.catalog = self._load_catalog()
    
    def _load_catalog(self) -> Dict[str, Any]:
        """Load existing catalog or create new one"""
        if self.catalog_path.exists():
            with open(self.catalog_path, 'r') as f:
                return json.load(f)
        return {"stories": {}, "last_updated": None, "total_count": 0}
    
    def _save_catalog(self):
        """Save catalog to disk"""
        self.catalog["last_updated"] = datetime.now().isoformat()
        self.catalog["total_count"] = len(self.catalog["stories"])
        
        os.makedirs(self.catalog_path.parent, exist_ok=True)
        with open(self.catalog_path, 'w') as f:
            json.dump(self.catalog, f, indent=2)
    
    def _generate_id(self, title: str, origin: str) -> str:
        """Generate unique ID for story"""
        base = f"{origin}-{title}".lower()
        base = re.sub(r'[^a-z0-9]+', '-', base)
        base = base.strip('-')[:50]
        
        # Ensure uniqueness
        if base not in self.catalog["stories"]:
            return base
        
        counter = 1
        while f"{base}-{counter}" in self.catalog["stories"]:
            counter += 1
        return f"{base}-{counter}"
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from markdown file"""
        # Look for YAML frontmatter
        if content.startswith('---'):
            try:
                end_index = content.index('---', 3)
                yaml_content = content[3:end_index].strip()
                metadata = yaml.safe_load(yaml_content)
                full_text = content[end_index + 3:].strip()
                return metadata, full_text
            except (ValueError, yaml.YAMLError):
                pass
        
        # If no frontmatter, return empty metadata
        return {}, content
    
    def _validate_metadata(self, metadata: Dict[str, Any]) -> List[str]:
        """Validate metadata against schema"""
        errors = []
        try:
            jsonschema.validate(metadata, self.schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Schema validation error: {e.message}")
        except jsonschema.SchemaError as e:
            errors.append(f"Schema error: {e.message}")
        
        return errors
    
    def _determine_file_path(self, metadata: Dict[str, Any]) -> Path:
        """Determine where to save the story file"""
        origin = metadata.get("origin", {}).get("culture", "unknown").lower()
        story_type = metadata.get("type", "other")
        
        # Create path based on organization preference
        by_origin = self.content_dir / "by-origin" / origin
        by_type = self.content_dir / "by-type" / story_type
        
        # Default to by-origin organization
        return by_origin
    
    def import_story(self, file_path: str, validate: bool = True, 
                    auto_fix: bool = False) -> Dict[str, Any]:
        """Import a story from file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract metadata
        metadata, full_text = self._extract_metadata(content)
        
        # Auto-generate missing required fields
        if auto_fix:
            if "id" not in metadata:
                metadata["id"] = self._generate_id(
                    metadata.get("title", "untitled"),
                    metadata.get("origin", {}).get("culture", "unknown")
                )
            
            if "date_added" not in metadata:
                metadata["date_added"] = datetime.now().strftime("%Y-%m-%d")
            
            if "version" not in metadata:
                metadata["version"] = "1.0"
            
            if "status" not in metadata:
                metadata["status"] = "draft"
            
            if "summary" not in metadata and full_text:
                # Extract first paragraph as summary
                first_para = full_text.split('\n\n')[0]
                metadata["summary"] = first_para[:500]
        
        # Store full text in metadata
        metadata["full_text"] = full_text
        
        # Validate if requested
        if validate:
            errors = self._validate_metadata(metadata)
            if errors:
                return {
                    "success": False,
                    "errors": errors,
                    "metadata": metadata
                }
        
        # Determine save location
        save_dir = self._determine_file_path(metadata)
        os.makedirs(save_dir, exist_ok=True)
        
        # Generate filename
        filename = f"{metadata['id']}.md"
        save_path = save_dir / filename
        
        # Prepare content for saving
        save_content = f"""---
{yaml.dump(metadata, default_flow_style=False, allow_unicode=True)}---

{full_text}
"""
        
        # Save file
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(save_content)
        
        # Update catalog
        self.catalog["stories"][metadata["id"]] = {
            "id": metadata["id"],
            "title": metadata["title"],
            "origin": metadata["origin"],
            "type": metadata["type"],
            "themes": metadata.get("themes", []),
            "file_path": str(save_path.relative_to(self.project_root)),
            "date_added": metadata["date_added"],
            "last_modified": metadata.get("last_modified", metadata["date_added"])
        }
        
        self._save_catalog()
        
        return {
            "success": True,
            "id": metadata["id"],
            "path": str(save_path),
            "metadata": metadata
        }
    
    def batch_import(self, directory: str, pattern: str = "*.md") -> Dict[str, Any]:
        """Import multiple stories from a directory"""
        directory = Path(directory)
        results = {
            "successful": [],
            "failed": [],
            "total": 0
        }
        
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                results["total"] += 1
                result = self.import_story(str(file_path), validate=True, auto_fix=True)
                
                if result["success"]:
                    results["successful"].append({
                        "file": str(file_path),
                        "id": result["id"]
                    })
                else:
                    results["failed"].append({
                        "file": str(file_path),
                        "error": result.get("error", result.get("errors", "Unknown error"))
                    })
        
        return results


def main():
    parser = argparse.ArgumentParser(description="Import stories into The Mythological Forge")
    parser.add_argument("--file", "-f", help="Path to story file to import")
    parser.add_argument("--directory", "-d", help="Directory containing stories to import")
    parser.add_argument("--validate", action="store_true", default=True, 
                       help="Validate metadata against schema")
    parser.add_argument("--auto-fix", action="store_true", 
                       help="Automatically fix missing required fields")
    parser.add_argument("--project-root", help="Path to project root directory")
    
    args = parser.parse_args()
    
    importer = StoryImporter(args.project_root)
    
    if args.file:
        result = importer.import_story(args.file, args.validate, args.auto_fix)
        if result["success"]:
            print(f"✓ Successfully imported: {result['id']}")
            print(f"  Saved to: {result['path']}")
        else:
            print(f"✗ Import failed:")
            if "error" in result:
                print(f"  {result['error']}")
            if "errors" in result:
                for error in result["errors"]:
                    print(f"  - {error}")
    
    elif args.directory:
        results = importer.batch_import(args.directory)
        print(f"\nBatch Import Results:")
        print(f"  Total files: {results['total']}")
        print(f"  Successful: {len(results['successful'])}")
        print(f"  Failed: {len(results['failed'])}")
        
        if results["failed"]:
            print("\nFailed imports:")
            for failure in results["failed"]:
                print(f"  - {failure['file']}: {failure['error']}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()