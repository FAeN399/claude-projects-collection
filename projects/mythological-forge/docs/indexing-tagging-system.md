# Indexing and Tagging System

## Overview
The indexing and tagging system for The Mythological Forge provides a multi-dimensional categorization framework that enables powerful search, discovery, and relationship mapping across all mythological content.

## Tag Hierarchy

### Primary Categories

```
Tags/
├── Content-Type/           # What kind of content
├── Culture/               # Cultural tradition
├── Theme/                 # Thematic elements
├── Archetype/            # Archetypal patterns
├── Symbol/               # Symbolic elements
├── Period/               # Historical period
├── Motif/                # Recurring motifs
├── Character-Role/       # Character functions
├── Narrative-Structure/  # Story patterns
└── Scholarly/            # Academic categories
```

## Detailed Tag Taxonomy

### 1. Content-Type Tags

#### Story Types
- `#origin-myth` - Creation and cosmogony stories
- `#hero-journey` - Hero's journey narratives
- `#wisdom-tale` - Didactic and moral stories
- `#transformation-myth` - Metamorphosis stories
- `#cosmic-myth` - Universal/cosmic narratives
- `#flood-myth` - Deluge narratives
- `#underworld-journey` - Katabasis stories
- `#trickster-tale` - Trickster narratives
- `#love-myth` - Romance and love stories
- `#war-epic` - Battle and conflict epics

#### Character Types
- `#deity` - Gods and goddesses
- `#hero` - Hero figures
- `#trickster` - Trickster figures
- `#monster` - Monsters and beasts
- `#guide` - Mentors and guides
- `#mortal` - Human characters
- `#demigod` - Half-divine beings
- `#spirit` - Spirits and supernatural beings
- `#titan` - Primordial beings
- `#demon` - Demonic entities

### 2. Cultural Tags

#### Major Traditions
- `#greek-mythology` - Ancient Greek
- `#roman-mythology` - Ancient Roman
- `#norse-mythology` - Norse/Germanic
- `#egyptian-mythology` - Ancient Egyptian
- `#mesopotamian` - Sumerian/Babylonian/Assyrian
- `#celtic-mythology` - Celtic traditions
- `#chinese-mythology` - Chinese traditions
- `#japanese-mythology` - Japanese traditions
- `#hindu-mythology` - Hindu traditions
- `#native-american` - Indigenous American
- `#african-mythology` - African traditions
- `#slavic-mythology` - Slavic traditions
- `#aztec-mythology` - Aztec traditions
- `#mayan-mythology` - Mayan traditions

### 3. Theme Tags

#### Universal Themes
- `#creation` - Creation and origin
- `#destruction` - Destruction and apocalypse
- `#rebirth` - Death and rebirth
- `#love` - Love and romance
- `#betrayal` - Betrayal and deception
- `#revenge` - Vengeance and retribution
- `#sacrifice` - Sacrifice and offering
- `#wisdom` - Wisdom and knowledge
- `#power` - Power and authority
- `#fate` - Fate and destiny
- `#hubris` - Pride and downfall
- `#redemption` - Redemption and forgiveness
- `#transformation` - Change and metamorphosis
- `#journey` - Quest and journey
- `#conflict` - Conflict and resolution

### 4. Archetype Tags

#### Character Archetypes
- `#hero-archetype` - The Hero
- `#mentor-archetype` - The Wise Old Man/Woman
- `#shadow-archetype` - The Shadow
- `#anima-animus` - Anima/Animus
- `#mother-archetype` - The Great Mother
- `#father-archetype` - The Father
- `#child-archetype` - The Divine Child
- `#maiden-archetype` - The Maiden
- `#warrior-archetype` - The Warrior
- `#magician-archetype` - The Magician
- `#fool-archetype` - The Fool
- `#ruler-archetype` - The Ruler
- `#rebel-archetype` - The Rebel
- `#lover-archetype` - The Lover
- `#creator-archetype` - The Creator

### 5. Symbol Tags

#### Universal Symbols
- `#water` - Water symbolism
- `#fire` - Fire symbolism
- `#earth` - Earth symbolism
- `#air` - Air/wind symbolism
- `#tree` - Tree symbolism (World Tree, etc.)
- `#serpent` - Serpent/dragon symbolism
- `#bird` - Bird symbolism
- `#sun` - Solar symbolism
- `#moon` - Lunar symbolism
- `#star` - Stellar symbolism
- `#mountain` - Mountain symbolism
- `#cave` - Cave symbolism
- `#bridge` - Bridge/crossing symbolism
- `#circle` - Circle/mandala symbolism
- `#cross` - Cross/intersection symbolism

### 6. Period Tags

#### Historical Periods
- `#prehistoric` - Prehistoric/pre-literate
- `#bronze-age` - Bronze Age
- `#iron-age` - Iron Age
- `#classical` - Classical period
- `#hellenistic` - Hellenistic period
- `#late-antiquity` - Late Antiquity
- `#medieval` - Medieval period
- `#renaissance` - Renaissance
- `#modern` - Modern period
- `#contemporary` - Contemporary

### 7. Motif Tags

#### Narrative Motifs
- `#divine-birth` - Miraculous birth
- `#prophecy` - Prophecy and prediction
- `#shapeshifting` - Transformation ability
- `#immortality` - Quest for immortality
- `#forbidden-knowledge` - Forbidden wisdom
- `#divine-punishment` - Divine retribution
- `#sacred-marriage` - Hieros gamos
- `#theft-of-fire` - Prometheus motif
- `#world-tree` - Axis mundi
- `#primordial-chaos` - Chaos before creation
- `#divine-twins` - Twin deities/heroes
- `#dying-god` - Death and resurrection
- `#culture-hero` - Bringer of civilization
- `#threshold-guardian` - Guardian figures
- `#magical-object` - Magical items

## Tagging Rules and Guidelines

### 1. Minimum Tagging Requirements

Every content item MUST have:
- At least one `Content-Type` tag
- At least one `Culture` tag (if culturally specific)
- At least three `Theme` tags
- Status tag (`#draft`, `#reviewed`, `#published`)

### 2. Tagging Best Practices

#### Specificity Levels
1. **Primary Tags** (1-3): Most essential categorization
2. **Secondary Tags** (3-5): Important themes and elements
3. **Tertiary Tags** (5+): Additional searchable elements

#### Tag Application Guidelines
```yaml
Story Tagging:
  Required:
    - content_type: 1 tag
    - culture: 1-2 tags
    - themes: 3-5 tags
    - period: 1 tag
  Recommended:
    - archetypes: 2-3 tags
    - symbols: 2-4 tags
    - motifs: 3-5 tags
    
Character Tagging:
  Required:
    - character_type: 1 tag
    - culture/pantheon: 1 tag
    - archetype: 1-2 tags
  Recommended:
    - domains: 2-4 tags
    - symbols: 2-3 tags
    - themes: 2-3 tags
```

### 3. Tag Relationships

#### Hierarchical Relationships
```
#mythology
  └── #greek-mythology
      ├── #olympian-gods
      ├── #greek-heroes
      └── #greek-monsters
```

#### Associative Relationships
- `#water` ←→ `#purification`
- `#serpent` ←→ `#wisdom` / `#evil`
- `#underworld` ←→ `#death` / `#rebirth`

## Search Index Structure

### Elasticsearch Mapping
```json
{
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "title": { 
        "type": "text",
        "fields": {
          "keyword": { "type": "keyword" },
          "suggest": { "type": "completion" }
        }
      },
      "content": { 
        "type": "text",
        "analyzer": "mythology_analyzer"
      },
      "summary": { "type": "text" },
      "tags": {
        "type": "nested",
        "properties": {
          "name": { "type": "keyword" },
          "category": { "type": "keyword" },
          "weight": { "type": "float" }
        }
      },
      "culture": { "type": "keyword" },
      "type": { "type": "keyword" },
      "themes": { "type": "keyword" },
      "created_date": { "type": "date" },
      "relationships": {
        "type": "nested",
        "properties": {
          "target_id": { "type": "keyword" },
          "type": { "type": "keyword" },
          "strength": { "type": "float" }
        }
      }
    }
  }
}
```

### Custom Analyzers
```json
{
  "analysis": {
    "analyzer": {
      "mythology_analyzer": {
        "tokenizer": "standard",
        "filter": [
          "lowercase",
          "mythology_synonyms",
          "mythology_stopwords",
          "stemmer"
        ]
      }
    },
    "filter": {
      "mythology_synonyms": {
        "type": "synonym",
        "synonyms": [
          "zeus, jupiter",
          "athena, minerva",
          "hero, champion, warrior",
          "journey, quest, adventure"
        ]
      },
      "mythology_stopwords": {
        "type": "stop",
        "stopwords": ["the", "and", "or", "but", "in", "on", "at"]
      }
    }
  }
}
```

## Tag Management

### Tag Lifecycle

1. **Proposal Stage**
   - New tag suggested by curator
   - Review for duplicates
   - Check naming conventions

2. **Approval Stage**
   - Admin review
   - Integration check
   - Documentation update

3. **Active Stage**
   - In use for tagging
   - Usage monitoring
   - Performance tracking

4. **Deprecation Stage**
   - Mark as deprecated
   - Migration plan
   - Replacement mapping

### Tag Quality Metrics

```python
class TagMetrics:
    """Track tag usage and effectiveness"""
    
    def calculate_tag_usage(self, tag_id: str) -> int:
        """Count number of items using this tag"""
        
    def measure_tag_precision(self, tag_id: str) -> float:
        """Measure how precisely tag is used"""
        
    def find_redundant_tags(self) -> List[TagPair]:
        """Identify potentially redundant tags"""
        
    def suggest_tag_mergers(self) -> List[TagMerger]:
        """Suggest tags that could be merged"""
```

## Faceted Search Implementation

### Facet Configuration
```yaml
facets:
  content_type:
    display_name: "Content Type"
    type: "terms"
    size: 10
    order: "count"
    
  culture:
    display_name: "Culture"
    type: "terms"
    size: 20
    order: "alphabetical"
    
  themes:
    display_name: "Themes"
    type: "terms"
    size: 15
    order: "count"
    multi_select: true
    
  period:
    display_name: "Time Period"
    type: "range"
    ranges:
      - key: "ancient"
        from: -3000
        to: 500
      - key: "classical"
        from: -800
        to: 500
      - key: "medieval"
        from: 500
        to: 1500
```

### Search Boosting
```json
{
  "query": {
    "bool": {
      "should": [
        {
          "match": {
            "title": {
              "query": "search term",
              "boost": 3.0
            }
          }
        },
        {
          "match": {
            "tags.name": {
              "query": "search term",
              "boost": 2.0
            }
          }
        },
        {
          "match": {
            "content": {
              "query": "search term",
              "boost": 1.0
            }
          }
        }
      ]
    }
  }
}
```

## Auto-Tagging System

### Machine Learning Pipeline
```python
class AutoTagger:
    """Automated tagging using NLP and ML"""
    
    def __init__(self):
        self.theme_classifier = ThemeClassifier()
        self.archetype_detector = ArchetypeDetector()
        self.symbol_extractor = SymbolExtractor()
        
    def analyze_content(self, text: str) -> TagSuggestions:
        """Analyze content and suggest tags"""
        themes = self.theme_classifier.classify(text)
        archetypes = self.archetype_detector.detect(text)
        symbols = self.symbol_extractor.extract(text)
        
        return TagSuggestions(
            themes=themes,
            archetypes=archetypes,
            symbols=symbols,
            confidence=self.calculate_confidence()
        )
```

### Tag Suggestion Algorithm
1. **Text Analysis**
   - Named entity recognition
   - Theme classification
   - Symbol detection

2. **Pattern Matching**
   - Archetype identification
   - Motif recognition
   - Structure analysis

3. **Contextual Enhancement**
   - Cultural context
   - Historical period
   - Related content

## Tag Visualization

### Network Graph
- Nodes: Tags
- Edges: Co-occurrence
- Node size: Usage frequency
- Edge weight: Relationship strength

### Tag Cloud
- Font size: Frequency
- Color: Category
- Proximity: Relatedness

### Hierarchical Tree
- Root: Category
- Branches: Subcategories
- Leaves: Specific tags

## Performance Optimization

### Caching Strategy
```yaml
tag_cache:
  popular_tags:
    ttl: 3600  # 1 hour
    max_size: 1000
    
  tag_relationships:
    ttl: 86400  # 24 hours
    max_size: 5000
    
  search_facets:
    ttl: 300  # 5 minutes
    max_size: 100
```

### Index Optimization
- Denormalized tag data for fast retrieval
- Pre-computed tag statistics
- Materialized tag relationship views

## Tag Analytics

### Usage Reports
1. **Most Used Tags** - Frequency analysis
2. **Tag Trends** - Usage over time
3. **Tag Effectiveness** - Search success rate
4. **Tag Coverage** - Content without tags

### Quality Metrics
- Tag precision score
- Tag recall score
- Inter-rater reliability
- Tag entropy measure

---
*Last Updated: 2024-01-15*
*Version: 1.0*