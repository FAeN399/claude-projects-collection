# File Naming Conventions

## Overview
This document defines the standardized file naming conventions for The Mythological Forge project. Consistent naming ensures easy identification, sorting, and management of files.

## General Rules

1. **Use lowercase letters** for all file names
2. **Use hyphens (-)** to separate words, not underscores or spaces
3. **Avoid special characters** except for hyphens and periods
4. **Keep names descriptive but concise** (max 50 characters recommended)
5. **Include version numbers** where applicable
6. **Use standard file extensions** (.md, .json, .html, .png, etc.)

## Naming Patterns by Content Type

### Stories

#### Pattern
`[culture]-[type]-[title-slug]-[version].[ext]`

#### Components
- `culture`: Cultural tradition (greek, norse, egyptian, etc.)
- `type`: Story type (origin, hero, wisdom, transformation, cosmic)
- `title-slug`: URL-friendly version of the title
- `version`: Version number (v1, v2, etc.) - optional for first version
- `ext`: File extension (md, html, txt)

#### Examples
- `greek-hero-odysseus-journey-v1.md`
- `norse-origin-creation-of-midgard.md`
- `egyptian-wisdom-tale-of-sinuhe-v3.md`

### Characters

#### Pattern
`[pantheon]-[type]-[name-slug].[ext]`

#### Components
- `pantheon`: Cultural pantheon (greek, norse, egyptian, etc.)
- `type`: Character type (deity, hero, trickster, monster, guide)
- `name-slug`: URL-friendly version of the primary name
- `ext`: File extension (md, json)

#### Examples
- `greek-deity-zeus-skyfather.md`
- `norse-trickster-loki.json`
- `egyptian-deity-thoth-wisdom.md`

### Media Assets

#### Images Pattern
`[asset-type]-[subject]-[description]-[dimensions].[ext]`

#### Components
- `asset-type`: Type of asset (portrait, map, diagram, symbol, artifact)
- `subject`: Main subject (character name, location, concept)
- `description`: Brief description
- `dimensions`: Image dimensions (optional)
- `ext`: File extension (png, jpg, svg)

#### Examples
- `portrait-athena-classical-period-800x600.jpg`
- `map-odysseus-journey-mediterranean.png`
- `symbol-ankh-egyptian-life.svg`
- `diagram-yggdrasil-nine-realms.png`

### Metadata Files

#### Pattern
`[content-type]-metadata-[scope]-[date].[ext]`

#### Components
- `content-type`: Type of content (story, character, pantheon, all)
- `scope`: Scope of metadata (full, partial, culture-specific)
- `date`: Date in YYYYMMDD format
- `ext`: File extension (json, yaml)

#### Examples
- `story-metadata-full-20240115.json`
- `character-metadata-greek-20240120.json`
- `all-metadata-partial-20240101.yaml`

### Templates

#### Pattern
`[content-type]-template-[variant].[ext]`

#### Components
- `content-type`: Type of content (story, character, analysis, pantheon)
- `variant`: Template variant (basic, detailed, scholarly)
- `ext`: File extension (md, html)

#### Examples
- `story-template-basic.md`
- `character-template-detailed.md`
- `analysis-template-scholarly.html`

### Database Files

#### Pattern
`[db-type]-[content]-[timestamp].[ext]`

#### Components
- `db-type`: Database operation (migration, seed, backup, export)
- `content`: Content description
- `timestamp`: Timestamp (YYYYMMDD-HHMMSS)
- `ext`: File extension (sql, json, dump)

#### Examples
- `migration-add-themes-table-20240115-143022.sql`
- `seed-initial-tags-20240101-090000.sql`
- `backup-full-database-20240120-180000.dump`

## Special Cases

### Import Queue Files
- Original filename preserved with timestamp prefix
- Pattern: `[timestamp]-[original-filename].[ext]`
- Example: `20240115143022-the-epic-of-gilgamesh.pdf`

### Export Files
- Pattern: `export-[type]-[scope]-[date].[ext]`
- Example: `export-stories-greek-mythology-20240115.zip`

### Collection Files
- Pattern: `collection-[name-slug]-[curator]-[date].[ext]`
- Example: `collection-creation-myths-smith-20240115.json`

## ID Generation Rules

### UUID Format
- Use UUID v4 for all unique identifiers
- Format: `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`
- Example: `550e8400-e29b-41d4-a716-446655440000`

### Readable IDs (Alternative)
- Pattern: `[type]-[culture]-[name]-[random]`
- Example: `story-greek-odyssey-a3f2`
- Example: `char-norse-odin-7b9e`

## Version Control

### Version Numbers
- Format: `v[major].[minor]`
- Start with `v1` or `v1.0`
- Examples: `v1`, `v1.1`, `v2.0`

### Version in Filenames
- Omit version for initial file (implies v1)
- Add version for subsequent versions
- Keep all versions in version control

## Validation Rules

### Length Limits
- Total filename: Max 255 characters
- Title slug: Max 50 characters
- Description: Max 30 characters

### Forbidden Characters
- Spaces (use hyphens instead)
- Special characters: `< > : " / \ | ? * & # % { } $ ! ' @ + =`
- Unicode characters (stick to ASCII)

### Reserved Names
- Avoid system reserved names (con, aux, nul, etc.)
- Don't start with dot (.) except for config files
- Avoid temp, tmp, test in production files

## Migration from Existing Files

### Renaming Strategy
1. Create mapping file of old → new names
2. Batch rename using provided scripts
3. Update all references in metadata
4. Maintain redirect map for URLs

### Legacy File Handling
- Keep originals in `/import/archive/legacy/`
- Document original names in metadata
- Create symbolic links if needed

## Automation Tools

### Validation Script
```bash
# Check if filename follows conventions
./scripts/validate-filename.sh [filename]
```

### Batch Rename Script
```bash
# Rename files according to conventions
./scripts/batch-rename.sh [directory]
```

### Name Generator
```bash
# Generate compliant filename
./scripts/generate-filename.sh --type story --culture greek --title "The Odyssey"
```

## Examples Summary

### Good Examples
- `greek-hero-perseus-medusa-slayer.md` ✓
- `norse-deity-odin-allfather.json` ✓
- `map-ancient-greece-city-states-2048x1536.png` ✓
- `story-metadata-full-20240115.json` ✓

### Bad Examples
- `Greek Hero - Perseus & Medusa.md` ✗ (spaces, capitals, special chars)
- `odin.json` ✗ (missing context)
- `map.png` ✗ (too generic)
- `metadata.json` ✗ (no date or scope)

## Enforcement

1. **Pre-commit hooks** validate filenames
2. **CI/CD pipeline** checks naming compliance
3. **Import process** automatically renames files
4. **Regular audits** identify non-compliant files

---
*Last Updated: 2024-01-15*
*Version: 1.0*