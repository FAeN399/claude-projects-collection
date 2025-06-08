# The Mythological Forge - Content Organization System

## Overview
This document outlines the organizational structure for managing external mythological stories and content within The Mythological Forge project.

## Directory Structure

```
The-Mythological-Forge/
│
├── content/                      # All mythological content
│   ├── stories/                  # Individual myths and narratives
│   │   ├── by-origin/           # Organized by cultural origin
│   │   │   ├── greek/
│   │   │   ├── norse/
│   │   │   ├── egyptian/
│   │   │   ├── celtic/
│   │   │   ├── mesopotamian/
│   │   │   ├── asian/
│   │   │   ├── american/
│   │   │   ├── african/
│   │   │   └── modern/
│   │   ├── by-type/             # Organized by story type
│   │   │   ├── creation-myths/
│   │   │   ├── hero-journeys/
│   │   │   ├── transformation/
│   │   │   ├── wisdom-tales/
│   │   │   └── apocalyptic/
│   │   └── by-theme/            # Organized by theme
│   │       ├── consciousness/
│   │       ├── death-rebirth/
│   │       ├── power/
│   │       ├── love/
│   │       └── sacrifice/
│   │
│   ├── characters/              # Mythological figures
│   │   ├── deities/
│   │   ├── heroes/
│   │   ├── tricksters/
│   │   ├── monsters/
│   │   └── mortals/
│   │
│   ├── pantheons/               # Groups of related deities
│   │   ├── olympian/
│   │   ├── asgardian/
│   │   ├── egyptian-ennead/
│   │   └── [pantheon-name]/
│   │
│   ├── collections/             # Curated story collections
│   │   ├── threshold-crossings/
│   │   ├── shadow-work/
│   │   └── [collection-name]/
│   │
│   └── media/                   # Images, audio, video
│       ├── images/
│       ├── audio/
│       └── diagrams/
│
├── metadata/                    # Content metadata and catalogs
│   ├── catalogs/               # JSON catalogs of all content
│   │   ├── master-catalog.json
│   │   ├── story-catalog.json
│   │   ├── character-catalog.json
│   │   └── relationship-map.json
│   │
│   ├── indexes/                # Search indexes
│   │   ├── tag-index.json
│   │   ├── theme-index.json
│   │   └── archetype-index.json
│   │
│   └── schemas/                # JSON schemas for validation
│       ├── story-schema.json
│       ├── character-schema.json
│       └── pantheon-schema.json
│
├── templates/                   # Templates for new content
│   ├── story-template.md
│   ├── character-template.md
│   └── collection-template.md
│
├── tools/                       # Management scripts
│   ├── import/                 # Scripts for importing content
│   ├── validate/               # Content validation tools
│   ├── index/                  # Indexing and search tools
│   └── export/                 # Export tools
│
└── database/                    # Database files
    ├── myth-forge.db           # SQLite database (or connection config)
    ├── backups/                # Database backups
    └── migrations/             # Database migration scripts
```

## File Naming Conventions

### Stories
Format: `[origin]-[type]-[title-slug]-[version].md`
Example: `greek-hero-perseus-medusa-v1.md`

### Characters
Format: `[pantheon]-[role]-[name]-profile.md`
Example: `olympian-deity-athena-profile.md`

### Collections
Format: `collection-[theme]-[name].json`
Example: `collection-consciousness-awakening.json`

## Metadata Schema

### Story Metadata
```json
{
  "id": "unique-identifier",
  "title": "Story Title",
  "alternate_titles": [],
  "origin": {
    "culture": "Greek",
    "region": "Ancient Greece",
    "time_period": "Classical Period",
    "source_text": "Theogony"
  },
  "type": "hero-journey",
  "themes": ["transformation", "sacrifice", "wisdom"],
  "archetypes": ["hero", "mentor", "threshold-guardian"],
  "characters": [
    {
      "id": "character-id",
      "name": "Perseus",
      "role": "protagonist"
    }
  ],
  "relationships": [
    {
      "type": "mentorship",
      "from": "athena",
      "to": "perseus"
    }
  ],
  "tags": ["medusa", "gorgon", "divine-assistance"],
  "summary": "Brief summary of the myth",
  "date_added": "2024-01-20",
  "last_modified": "2024-01-20",
  "version": "1.0",
  "status": "reviewed",
  "external_links": [],
  "media": {
    "images": [],
    "audio": [],
    "diagrams": []
  }
}
```

## Content Management Workflow

### 1. Import Process
```
External Source → Validation → Formatting → Metadata Assignment → Cataloging → Integration
```

### 2. Organization Steps
1. **Receive Content**: Accept story from external source
2. **Validate Format**: Ensure it meets template requirements
3. **Assign Metadata**: Fill out complete metadata
4. **Categorize**: Place in appropriate directories
5. **Index**: Update all relevant indexes
6. **Cross-Reference**: Link to related content
7. **Review**: Quality check and approval
8. **Publish**: Make available in the system

### 3. Search & Discovery
- Full-text search across all content
- Filter by origin, type, theme, archetype
- Relationship exploration
- Tag-based navigation
- Collection browsing

## Quick Start Commands

```bash
# Import a new story
python tools/import/import_story.py --file path/to/story.md --validate

# Update indexes
python tools/index/update_indexes.py --all

# Search content
python tools/search.py --query "threshold crossing" --type story

# Generate catalog
python tools/catalog/generate_catalog.py --output metadata/catalogs/

# Validate all content
python tools/validate/validate_all.py --fix-issues
```

## Integration Points

1. **Web Interface**: Browse and search through HTML interface
2. **API Access**: RESTful API for programmatic access
3. **Export Options**: Generate collections in various formats
4. **Analytics**: Track popular themes and relationships
5. **AI Integration**: Feed organized content to narrative generation

## Best Practices

1. **Always validate** content before importing
2. **Maintain consistent** metadata across all entries
3. **Regular backups** of database and content
4. **Version control** all content changes
5. **Document sources** and attributions
6. **Tag thoroughly** for better discoverability
7. **Review regularly** for quality and accuracy

## Next Steps

1. Set up the directory structure
2. Create initial templates
3. Build import/validation scripts
4. Develop the search interface
5. Establish review workflow
6. Begin content migration