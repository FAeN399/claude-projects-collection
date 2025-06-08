# The Mythological Forge - Organizational System

## Overview
This document outlines the comprehensive organizational system for managing and categorizing external stories and mythological content in The Mythological Forge project.

## 1. Directory Structure

```
The-Mythological-Forge/
│
├── content/                      # All content organized by type
│   ├── stories/                  # External stories collection
│   │   ├── origin/              # Origin myths and creation stories
│   │   ├── hero/                # Hero journeys and epic tales
│   │   ├── wisdom/              # Wisdom literature and parables
│   │   ├── transformation/      # Transformation and metamorphosis tales
│   │   └── cosmic/              # Cosmic and universal myths
│   │
│   ├── characters/              # Character profiles and archetypes
│   │   ├── deities/             # Gods and goddesses
│   │   ├── heroes/              # Heroes and protagonists
│   │   ├── tricksters/          # Trickster figures
│   │   ├── monsters/            # Monsters and antagonists
│   │   └── guides/              # Guides and mentors
│   │
│   ├── pantheons/               # Organized by cultural traditions
│   │   ├── greek/
│   │   ├── norse/
│   │   ├── egyptian/
│   │   ├── mesopotamian/
│   │   ├── celtic/
│   │   ├── eastern/
│   │   └── indigenous/
│   │
│   ├── themes/                  # Thematic collections
│   │   ├── creation/
│   │   ├── destruction/
│   │   ├── love/
│   │   ├── death-rebirth/
│   │   ├── quest/
│   │   └── wisdom/
│   │
│   └── media/                   # Media assets
│       ├── images/
│       ├── audio/
│       ├── maps/
│       └── diagrams/
│
├── metadata/                    # Metadata and indexing
│   ├── catalogs/               # Content catalogs
│   ├── indexes/                # Search indexes
│   └── schemas/                # Schema definitions
│
├── templates/                   # Content templates
│   ├── story/
│   ├── character/
│   ├── pantheon/
│   └── analysis/
│
├── database/                    # Database files
│   ├── migrations/
│   ├── seeds/
│   └── backups/
│
├── import/                      # Staging area for new content
│   ├── queue/                  # Content awaiting processing
│   ├── processing/             # Content being processed
│   └── archive/                # Processed originals
│
├── export/                      # Export configurations
│   ├── formats/
│   └── presets/
│
├── config/                      # Configuration files
│   ├── naming/
│   ├── validation/
│   └── workflows/
│
└── docs/                        # Documentation
    ├── guides/
    ├── api/
    └── schemas/
```

## 2. Metadata Schema

### Story Metadata Schema
```json
{
  "id": "unique-identifier",
  "title": "Story Title",
  "alternate_titles": ["Alt Title 1", "Alt Title 2"],
  "type": "origin|hero|wisdom|transformation|cosmic",
  "source": {
    "culture": "Greek|Norse|Egyptian|etc",
    "tradition": "Specific tradition or text",
    "period": "Historical period",
    "region": "Geographic region",
    "original_language": "Language code",
    "translator": "Translator name if applicable"
  },
  "content": {
    "summary": "Brief summary",
    "full_text": "Path to full text file",
    "format": "markdown|html|txt|pdf",
    "word_count": 1234,
    "reading_time": "5 minutes"
  },
  "characters": [
    {
      "name": "Character Name",
      "role": "protagonist|antagonist|guide|trickster",
      "id": "character-unique-id"
    }
  ],
  "themes": ["creation", "transformation", "wisdom"],
  "motifs": ["journey", "threshold", "mentor"],
  "symbols": ["water", "fire", "tree"],
  "relationships": {
    "related_stories": ["story-id-1", "story-id-2"],
    "variations": ["variation-id-1"],
    "influences": ["influence-id-1"]
  },
  "analysis": {
    "archetypal_patterns": ["hero-journey", "creation-myth"],
    "psychological_themes": ["individuation", "shadow-work"],
    "cultural_significance": "Description of cultural importance"
  },
  "metadata": {
    "created_date": "2024-01-01T00:00:00Z",
    "modified_date": "2024-01-01T00:00:00Z",
    "created_by": "curator-name",
    "status": "draft|review|published|archived",
    "version": "1.0",
    "license": "License information",
    "attribution": "Attribution requirements"
  },
  "tags": ["searchable", "keywords", "topics"],
  "rating": {
    "complexity": 1-5,
    "accessibility": 1-5,
    "scholarly_value": 1-5
  }
}
```

### Character Metadata Schema
```json
{
  "id": "unique-identifier",
  "name": {
    "primary": "Main Name",
    "alternates": ["Alt Name 1", "Alt Name 2"],
    "epithets": ["The Wise", "Storm-Bringer"],
    "etymology": "Name meaning and origin"
  },
  "type": "deity|hero|trickster|monster|guide",
  "pantheon": "Greek|Norse|Egyptian|etc",
  "attributes": {
    "domains": ["wisdom", "war", "harvest"],
    "symbols": ["owl", "spear", "olive tree"],
    "powers": ["shape-shifting", "prophecy"],
    "weaknesses": ["pride", "mortality"]
  },
  "relationships": {
    "parents": ["parent-id-1", "parent-id-2"],
    "siblings": ["sibling-id-1"],
    "consorts": ["consort-id-1"],
    "children": ["child-id-1"],
    "enemies": ["enemy-id-1"],
    "allies": ["ally-id-1"]
  },
  "appearances": {
    "stories": ["story-id-1", "story-id-2"],
    "mentions": ["story-id-3"]
  },
  "evolution": {
    "origins": "Historical development",
    "variations": "Cultural variations",
    "modern_interpretations": "Contemporary relevance"
  },
  "metadata": {
    "created_date": "2024-01-01T00:00:00Z",
    "modified_date": "2024-01-01T00:00:00Z",
    "status": "draft|review|published"
  }
}
```

## 3. Content Management System Design

### Core Components

1. **Content Ingestion Pipeline**
   - Import queue for new content
   - Validation engine
   - Metadata extraction
   - Format conversion
   - Quality assurance

2. **Storage Layer**
   - File-based storage for content
   - Database for metadata and relationships
   - Version control integration
   - Backup and recovery

3. **Processing Engine**
   - Text analysis and tagging
   - Relationship mapping
   - Theme extraction
   - Cross-referencing

4. **Search and Discovery**
   - Full-text search
   - Faceted search by metadata
   - Relationship browsing
   - Recommendation engine

5. **Export and Publishing**
   - Multiple format support
   - API access
   - Batch export
   - Custom collections

## 4. File Naming Conventions

### Stories
Pattern: `[culture]-[type]-[title-slug]-[version].ext`
Example: `greek-hero-odysseus-journey-v1.md`

### Characters
Pattern: `[pantheon]-[type]-[name-slug].ext`
Example: `norse-deity-odin-allfather.json`

### Media Assets
Pattern: `[type]-[subject]-[description]-[size].ext`
Example: `map-greek-odyssey-route-1920x1080.png`

### Metadata Files
Pattern: `[content-type]-metadata-[timestamp].json`
Example: `story-metadata-20240101.json`

## 5. Database Schema

### Stories Table
```sql
CREATE TABLE stories (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    culture VARCHAR(100),
    tradition VARCHAR(100),
    content_path TEXT NOT NULL,
    summary TEXT,
    word_count INTEGER,
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),
    version VARCHAR(10) DEFAULT '1.0'
);
```

### Characters Table
```sql
CREATE TABLE characters (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    pantheon VARCHAR(100),
    attributes JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Relationships Table
```sql
CREATE TABLE relationships (
    id UUID PRIMARY KEY,
    source_id UUID NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    target_id UUID NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    relationship_type VARCHAR(100) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Tags Table
```sql
CREATE TABLE tags (
    id UUID PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Content_Tags Junction Table
```sql
CREATE TABLE content_tags (
    content_id UUID NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    tag_id UUID NOT NULL,
    relevance_score FLOAT DEFAULT 1.0,
    PRIMARY KEY (content_id, tag_id)
);
```

## 6. Content Templates

### Story Template
```markdown
---
id: [generated-uuid]
title: [Story Title]
type: [origin|hero|wisdom|transformation|cosmic]
culture: [Culture Name]
status: draft
---

# [Story Title]

## Summary
[Brief summary of the story]

## Cultural Context
[Historical and cultural background]

## Characters
- **[Character Name]**: [Role and description]

## Narrative
[Full story text]

## Themes and Motifs
- [Theme 1]: [Description]
- [Motif 1]: [Description]

## Analysis
### Archetypal Patterns
[Analysis of archetypal elements]

### Cultural Significance
[Importance within the culture]

### Modern Relevance
[Contemporary interpretations]

## Related Stories
- [Related Story 1]
- [Related Story 2]

## Sources and References
- [Source 1]
- [Reference 1]
```

### Character Template
```markdown
---
id: [generated-uuid]
name: [Character Name]
type: [deity|hero|trickster|monster|guide]
pantheon: [Pantheon Name]
status: draft
---

# [Character Name]

## Overview
[Brief character description]

## Attributes
### Domains
- [Domain 1]
- [Domain 2]

### Symbols
- [Symbol 1]: [Meaning]
- [Symbol 2]: [Meaning]

### Powers and Abilities
- [Power 1]: [Description]
- [Ability 1]: [Description]

## Relationships
### Family
- **Parents**: [Names]
- **Siblings**: [Names]
- **Consorts**: [Names]
- **Children**: [Names]

### Allies and Enemies
- **Allies**: [Names]
- **Enemies**: [Names]

## Major Stories
1. **[Story Title]**: [Role in story]
2. **[Story Title]**: [Role in story]

## Evolution and Variations
[How the character has evolved across cultures and time]

## Modern Interpretations
[Contemporary relevance and adaptations]

## References
- [Source 1]
- [Scholarly Work 1]
```

## 7. Indexing and Tagging System

### Tag Categories

1. **Content Type Tags**
   - `#origin-myth`
   - `#hero-journey`
   - `#wisdom-tale`
   - `#transformation`
   - `#cosmic-myth`

2. **Cultural Tags**
   - `#greek-mythology`
   - `#norse-mythology`
   - `#egyptian-mythology`
   - `#mesopotamian`
   - `#celtic-lore`

3. **Theme Tags**
   - `#creation`
   - `#destruction`
   - `#love-story`
   - `#death-rebirth`
   - `#quest-narrative`
   - `#trickster-tale`

4. **Archetype Tags**
   - `#hero-archetype`
   - `#mentor-guide`
   - `#shadow-figure`
   - `#mother-goddess`
   - `#wise-fool`

5. **Symbol Tags**
   - `#water-symbolism`
   - `#fire-symbolism`
   - `#tree-of-life`
   - `#serpent-dragon`
   - `#sacred-geometry`

6. **Period Tags**
   - `#ancient`
   - `#classical`
   - `#medieval`
   - `#renaissance`
   - `#modern-adaptation`

### Search Index Structure
```json
{
  "content_id": "unique-id",
  "title": "Indexed Title",
  "full_text": "Complete searchable text",
  "tags": ["tag1", "tag2", "tag3"],
  "facets": {
    "type": "story",
    "culture": "greek",
    "period": "classical",
    "themes": ["heroism", "journey"],
    "characters": ["character1", "character2"]
  },
  "relevance_boost": {
    "popular": true,
    "scholarly": true,
    "beginner_friendly": false
  }
}
```

## Implementation Guidelines

1. **Content Import Workflow**
   - Place new content in `/import/queue/`
   - Run validation checks
   - Extract or create metadata
   - Move to appropriate content directory
   - Update database and indexes
   - Archive original in `/import/archive/`

2. **Version Control**
   - Use Git for all text-based content
   - Tag releases for major updates
   - Branch for experimental categorization
   - Maintain change logs

3. **Quality Assurance**
   - Validate metadata completeness
   - Check cross-references
   - Verify file naming conventions
   - Test search functionality
   - Review relationship mappings

4. **Maintenance Schedule**
   - Daily: Process import queue
   - Weekly: Update search indexes
   - Monthly: Audit metadata quality
   - Quarterly: Archive old versions
   - Yearly: Full system review

This organizational system is designed to scale with the collection while maintaining searchability, consistency, and ease of use.