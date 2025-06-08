# The Mythological Forge - Quick Start Guide

## 🚀 Getting Started

### 1. Set Up Directory Structure
```bash
# Run this command from the project root
mkdir -p content/stories/{by-origin/{greek,norse,egyptian,celtic,modern},by-type/{creation,hero-journey,transformation},by-theme/{consciousness,death-rebirth,power}}
mkdir -p content/{characters/{deities,heroes,monsters},pantheons,collections,media/{images,audio,diagrams}}
mkdir -p metadata/{catalogs,indexes,schemas}
mkdir -p templates tools/{import,validate,index,export}
mkdir -p database/{backups,migrations}
```

### 2. Install Dependencies
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install pyyaml jsonschema pathlib argparse
```

### 3. Your First Story Import

#### Option A: Use the Template
1. Copy the story template:
```bash
cp templates/story-template.md my-first-myth.md
```

2. Fill out the template with your myth's information

3. Import it:
```bash
python tools/import/import_story.py --file my-first-myth.md --auto-fix
```

#### Option B: Quick Import Existing Text
Create a file `perseus-myth.md`:
```markdown
---
title: "Perseus and Medusa"
origin:
  culture: "Greek"
type: "hero-journey"
themes: ["transformation", "divine-assistance", "monster-slaying"]
---

Perseus, son of Zeus and Danaë, was sent by King Polydectes to bring back the head of Medusa...
[Rest of your story here]
```

Import it:
```bash
python tools/import/import_story.py --file perseus-myth.md --auto-fix
```

### 4. Browse Your Collection
After importing, you'll find:
- Story saved in: `content/stories/by-origin/greek/`
- Entry added to: `metadata/catalogs/story-catalog.json`

## 📁 Organization Tips

### Naming Convention
- **Stories**: `[origin]-[type]-[title-slug].md`
  - Example: `greek-hero-perseus-medusa.md`
- **Characters**: `[pantheon]-[role]-[name].md`
  - Example: `olympian-deity-athena.md`

### Essential Metadata Fields
Every story needs:
- `id`: Unique identifier (auto-generated if using --auto-fix)
- `title`: The myth's name
- `origin.culture`: Where it comes from
- `type`: What kind of story it is
- `themes`: Major themes (array)
- `summary`: Brief description
- `status`: draft/review/approved

### Quick Import from External Sources

1. **From a website/book**:
   - Copy the text
   - Create a new `.md` file
   - Add minimal frontmatter:
   ```yaml
   ---
   title: "Story Title"
   origin:
     culture: "Culture Name"
   type: "story-type"
   themes: ["theme1", "theme2"]
   ---
   ```
   - Paste the story text below
   - Run import with `--auto-fix`

2. **Batch import**:
   ```bash
   # Import all .md files from a directory
   python tools/import/import_story.py --directory /path/to/stories/ --auto-fix
   ```

## 🔍 Finding Stories

### View the Catalog
```bash
# Pretty-print the catalog
python -m json.tool metadata/catalogs/story-catalog.json
```

### Search by Theme (coming soon)
```bash
python tools/search.py --theme "transformation"
```

## 📝 Common Tasks

### Add a New Character
```bash
cp templates/character-template.md content/characters/deities/new-deity.md
# Edit the file, then update indexes
```

### Create a Collection
Group related stories:
```json
{
  "id": "consciousness-myths",
  "title": "Myths of Consciousness",
  "description": "Stories exploring awareness and transformation",
  "stories": ["story-id-1", "story-id-2", "story-id-3"],
  "themes": ["consciousness", "transformation"]
}
```

### Tag a Story
Add tags in the metadata:
```yaml
tags: ["medusa", "perseus", "athena", "divine-weapon", "mirror-shield"]
```

## 🛠️ Troubleshooting

### Import Errors
- **Missing required fields**: Use `--auto-fix` flag
- **Invalid culture/type**: Check allowed values in schema
- **File not found**: Use absolute paths or check working directory

### Validation Issues
```bash
# Check what's wrong
python tools/import/import_story.py --file story.md --validate

# Auto-fix common issues
python tools/import/import_story.py --file story.md --auto-fix
```

## 🎯 Next Steps

1. **Import your stories**: Start with 5-10 myths
2. **Organize by preference**: Use by-origin, by-type, or by-theme
3. **Build relationships**: Link characters and stories
4. **Create collections**: Group related content
5. **Explore patterns**: Find archetypal connections

## 💡 Pro Tips

- Use `--auto-fix` for quick imports
- Keep summaries under 500 characters
- Tag liberally for better search
- Version your changes with git
- Backup the database regularly

## 📚 Resources

- [Story Template](templates/story-template.md)
- [Character Template](templates/character-template.md)
- [Content Organization Guide](CONTENT_ORGANIZATION.md)
- [JSON Schema Reference](metadata/schemas/story-schema.json)

---

Happy myth forging! 🔥🔨✨