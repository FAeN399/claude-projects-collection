# Implementation Guide - The Mythological Forge

## Quick Start

This guide provides step-by-step instructions for implementing The Mythological Forge organizational system.

## Phase 1: Initial Setup (Week 1)

### 1. Directory Structure
```bash
# Navigate to project root
cd /path/to/The-Mythological-Forge

# Create directory structure (already done)
# The structure has been created as per ORGANIZATION_SYSTEM.md
```

### 2. Database Setup

#### PostgreSQL Installation
```bash
# Install PostgreSQL (if not already installed)
sudo apt-get install postgresql postgresql-contrib

# Create database
sudo -u postgres psql
CREATE DATABASE mythological_forge;
CREATE USER forge_admin WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE mythological_forge TO forge_admin;
\q
```

#### Run Schema
```bash
# Apply database schema
psql -U forge_admin -d mythological_forge -f database/schema.sql
```

### 3. Initial Configuration
Create configuration file:
```bash
# Create config file
touch config/forge.config.json
```

Add configuration:
```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "name": "mythological_forge",
    "user": "forge_admin",
    "password": "your_secure_password"
  },
  "storage": {
    "content_root": "./content",
    "import_root": "./import",
    "export_root": "./export",
    "media_root": "./content/media"
  },
  "processing": {
    "batch_size": 10,
    "timeout": 300,
    "formats": ["md", "txt", "html", "pdf", "docx"]
  }
}
```

## Phase 2: Content Import Tools (Week 2)

### 1. Create Import Scripts

#### Basic Import Script
Create `scripts/import-content.py`:
```python
#!/usr/bin/env python3
"""Basic content import script"""

import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path

class ContentImporter:
    def __init__(self, config_path='config/forge.config.json'):
        with open(config_path) as f:
            self.config = json.load(f)
        self.import_queue = Path(self.config['storage']['import_root']) / 'queue'
        self.content_root = Path(self.config['storage']['content_root'])
    
    def scan_import_queue(self):
        """Scan import queue for new files"""
        return list(self.import_queue.glob('*'))
    
    def process_file(self, file_path):
        """Process a single file"""
        # Generate metadata
        metadata = {
            'id': str(uuid.uuid4()),
            'original_filename': file_path.name,
            'import_date': datetime.now().isoformat(),
            'status': 'processing'
        }
        
        # Determine content type and destination
        # (Add logic based on file analysis)
        
        print(f"Processing: {file_path.name}")
        return metadata
    
    def run(self):
        """Run import process"""
        files = self.scan_import_queue()
        print(f"Found {len(files)} files to import")
        
        for file_path in files:
            try:
                metadata = self.process_file(file_path)
                # Move to processing directory
                # Validate content
                # Extract metadata
                # Store in appropriate location
                # Update database
                print(f"Successfully imported: {file_path.name}")
            except Exception as e:
                print(f"Error importing {file_path.name}: {e}")

if __name__ == '__main__':
    importer = ContentImporter()
    importer.run()
```

### 2. Validation Script
Create `scripts/validate-content.py`:
```python
#!/usr/bin/env python3
"""Content validation script"""

import json
import jsonschema
from pathlib import Path

class ContentValidator:
    def __init__(self):
        self.schemas = {}
        self.load_schemas()
    
    def load_schemas(self):
        """Load all JSON schemas"""
        schema_dir = Path('metadata/schemas')
        for schema_file in schema_dir.glob('*.json'):
            with open(schema_file) as f:
                schema_name = schema_file.stem
                self.schemas[schema_name] = json.load(f)
    
    def validate_metadata(self, metadata, schema_type):
        """Validate metadata against schema"""
        schema = self.schemas.get(f'{schema_type}-schema')
        if not schema:
            raise ValueError(f"Unknown schema type: {schema_type}")
        
        try:
            jsonschema.validate(metadata, schema)
            return True, "Valid"
        except jsonschema.ValidationError as e:
            return False, str(e)
    
    def validate_file(self, file_path):
        """Validate a content file"""
        # Read file metadata
        # Determine type
        # Validate against appropriate schema
        pass

if __name__ == '__main__':
    validator = ContentValidator()
    # Add command line interface
```

## Phase 3: Search Implementation (Week 3)

### 1. Elasticsearch Setup
```bash
# Install Elasticsearch
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.11.0-linux-x86_64.tar.gz
tar -xzf elasticsearch-8.11.0-linux-x86_64.tar.gz
cd elasticsearch-8.11.0

# Start Elasticsearch
./bin/elasticsearch
```

### 2. Create Search Indexer
Create `scripts/index-content.py`:
```python
#!/usr/bin/env python3
"""Search indexing script"""

from elasticsearch import Elasticsearch
import json
from pathlib import Path

class SearchIndexer:
    def __init__(self):
        self.es = Elasticsearch(['http://localhost:9200'])
        self.index_name = 'mythological_forge'
    
    def create_index(self):
        """Create search index with mapping"""
        mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "title": {"type": "text"},
                    "content": {"type": "text"},
                    "type": {"type": "keyword"},
                    "culture": {"type": "keyword"},
                    "tags": {"type": "keyword"},
                    "created_date": {"type": "date"}
                }
            }
        }
        
        if not self.es.indices.exists(index=self.index_name):
            self.es.indices.create(index=self.index_name, body=mapping)
    
    def index_document(self, doc_id, document):
        """Index a single document"""
        self.es.index(
            index=self.index_name,
            id=doc_id,
            body=document
        )
    
    def search(self, query):
        """Search the index"""
        results = self.es.search(
            index=self.index_name,
            body={
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^3", "tags^2", "content"]
                    }
                }
            }
        )
        return results

if __name__ == '__main__':
    indexer = SearchIndexer()
    indexer.create_index()
```

## Phase 4: Web Interface (Week 4)

### 1. API Server
Create `api/server.py`:
```python
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app)

# Database connection
def get_db():
    return psycopg2.connect(
        host="localhost",
        database="mythological_forge",
        user="forge_admin",
        password="your_secure_password",
        cursor_factory=RealDictCursor
    )

@app.route('/api/v1/stories', methods=['GET'])
def get_stories():
    """Get list of stories"""
    conn = get_db()
    cur = conn.cursor()
    
    # Add pagination
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    offset = (page - 1) * limit
    
    cur.execute(
        "SELECT * FROM stories ORDER BY created_at DESC LIMIT %s OFFSET %s",
        (limit, offset)
    )
    stories = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return jsonify({
        'stories': stories,
        'page': page,
        'limit': limit
    })

@app.route('/api/v1/stories/<story_id>', methods=['GET'])
def get_story(story_id):
    """Get single story"""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM stories WHERE id = %s", (story_id,))
    story = cur.fetchone()
    
    cur.close()
    conn.close()
    
    if story:
        return jsonify(story)
    return jsonify({'error': 'Story not found'}), 404

@app.route('/api/v1/search', methods=['GET'])
def search():
    """Search endpoint"""
    query = request.args.get('q', '')
    # Implement search logic
    return jsonify({'results': [], 'query': query})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

### 2. Basic Web UI
Create `frontend/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Mythological Forge</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .search-box {
            width: 100%;
            padding: 10px;
            font-size: 16px;
            margin-bottom: 20px;
        }
        .content-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }
        .content-card {
            border: 1px solid #ddd;
            padding: 15px;
            border-radius: 8px;
        }
        .content-card h3 {
            margin-top: 0;
        }
        .tag {
            display: inline-block;
            background: #e0e0e0;
            padding: 3px 8px;
            margin: 2px;
            border-radius: 12px;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <h1>The Mythological Forge</h1>
    <input type="search" class="search-box" placeholder="Search myths, characters, themes...">
    
    <div id="content" class="content-grid">
        <!-- Content will be loaded here -->
    </div>

    <script>
        const API_URL = 'http://localhost:5000/api/v1';
        
        async function loadStories() {
            try {
                const response = await fetch(`${API_URL}/stories`);
                const data = await response.json();
                displayStories(data.stories);
            } catch (error) {
                console.error('Error loading stories:', error);
            }
        }
        
        function displayStories(stories) {
            const contentDiv = document.getElementById('content');
            contentDiv.innerHTML = stories.map(story => `
                <div class="content-card">
                    <h3>${story.title}</h3>
                    <p><strong>Type:</strong> ${story.type}</p>
                    <p><strong>Culture:</strong> ${story.culture || 'Unknown'}</p>
                    <p>${story.summary || 'No summary available'}</p>
                    <div class="tags">
                        ${story.tags ? story.tags.map(tag => `<span class="tag">#${tag}</span>`).join('') : ''}
                    </div>
                </div>
            `).join('');
        }
        
        // Load stories on page load
        loadStories();
        
        // Search functionality
        document.querySelector('.search-box').addEventListener('input', async (e) => {
            const query = e.target.value;
            if (query.length > 2) {
                // Implement search
                console.log('Searching for:', query);
            }
        });
    </script>
</body>
</html>
```

## Phase 5: Automation and Maintenance (Week 5)

### 1. Automated Tasks
Create `scripts/daily-maintenance.sh`:
```bash
#!/bin/bash
# Daily maintenance tasks

echo "Starting daily maintenance - $(date)"

# Process import queue
python3 scripts/import-content.py

# Update search indexes
python3 scripts/index-content.py --update

# Validate all content
python3 scripts/validate-content.py --all

# Backup database
pg_dump -U forge_admin mythological_forge > "database/backups/backup-$(date +%Y%m%d).sql"

# Clean up old logs
find logs/ -name "*.log" -mtime +30 -delete

echo "Daily maintenance complete - $(date)"
```

### 2. Setup Cron Jobs
```bash
# Edit crontab
crontab -e

# Add daily maintenance (runs at 2 AM)
0 2 * * * /path/to/The-Mythological-Forge/scripts/daily-maintenance.sh >> /path/to/logs/maintenance.log 2>&1

# Add hourly import processing
0 * * * * python3 /path/to/The-Mythological-Forge/scripts/import-content.py >> /path/to/logs/import.log 2>&1
```

## Testing Content

### 1. Add Sample Content
Place sample files in the import queue:
```bash
# Copy existing content to import queue
cp Poems/saturn-lantern-myth.html import/queue/
cp Zatrix_Ariax/*.html import/queue/
```

### 2. Process and Verify
```bash
# Run import
python3 scripts/import-content.py

# Check database
psql -U forge_admin -d mythological_forge -c "SELECT title, type, culture FROM stories;"

# Test search
curl "http://localhost:5000/api/v1/search?q=saturn"
```

## Next Steps

1. **Enhance Import Pipeline**
   - Add OCR for scanned documents
   - Implement advanced metadata extraction
   - Create content deduplication

2. **Improve Search**
   - Add faceted search
   - Implement similarity search
   - Create recommendation engine

3. **Build Analytics**
   - Usage tracking
   - Popular content reports
   - Gap analysis

4. **Add Collaboration**
   - User authentication
   - Content contributions
   - Review workflow

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL is running
   - Verify credentials
   - Check firewall settings

2. **Import Not Working**
   - Check file permissions
   - Verify import queue path
   - Check logs for errors

3. **Search Not Returning Results**
   - Verify Elasticsearch is running
   - Check index exists
   - Rebuild search index

## Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Elasticsearch Guide](https://www.elastic.co/guide/)
- [Python JSON Schema](https://python-jsonschema.readthedocs.io/)
- [Flask Documentation](https://flask.palletsprojects.com/)

---
*Last Updated: 2024-01-15*
*Version: 1.0*