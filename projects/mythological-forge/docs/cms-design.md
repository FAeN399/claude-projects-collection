# Content Management System Design

## Overview
The Mythological Forge CMS is designed to handle the ingestion, processing, storage, and retrieval of mythological content from diverse sources. The system emphasizes scalability, data integrity, and ease of use.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│  (Web Portal, API Endpoints, Admin Dashboard)               │
└─────────────────┬───────────────────────┬───────────────────┘
                  │                       │
┌─────────────────▼─────────┐   ┌────────▼────────────────────┐
│    Content Ingestion      │   │    Search & Discovery       │
│  • Import Queue           │   │  • Full-text Search         │
│  • Format Conversion      │   │  • Faceted Browse           │
│  • Validation Engine      │   │  • Recommendations         │
└─────────────────┬─────────┘   └────────┬────────────────────┘
                  │                       │
┌─────────────────▼───────────────────────▼───────────────────┐
│                    Processing Engine                         │
│  • Metadata Extraction    • Relationship Mapping           │
│  • Content Analysis       • Theme Identification           │
│  • Quality Assurance      • Cross-referencing             │
└─────────────────┬───────────────────────┬───────────────────┘
                  │                       │
┌─────────────────▼─────────┐   ┌────────▼────────────────────┐
│     Storage Layer         │   │    Database Layer           │
│  • File System           │   │  • PostgreSQL               │
│  • Version Control       │   │  • Metadata Storage         │
│  • Media Assets          │   │  • Relationships            │
└───────────────────────────┘   └─────────────────────────────┘
```

## Core Modules

### 1. Content Ingestion Pipeline

#### Purpose
Manages the import and initial processing of new content from various sources.

#### Components

**Import Queue Manager**
```python
class ImportQueueManager:
    """Manages the queue of content awaiting import"""
    
    def add_to_queue(self, file_path: str, metadata: dict) -> str:
        """Add new content to import queue"""
        
    def process_queue(self) -> List[ProcessResult]:
        """Process all pending items in queue"""
        
    def get_queue_status(self) -> QueueStatus:
        """Get current queue statistics"""
```

**Format Converter**
```python
class FormatConverter:
    """Converts between different content formats"""
    
    supported_formats = ['pdf', 'docx', 'txt', 'html', 'epub', 'markdown']
    
    def convert_to_markdown(self, source_path: str) -> str:
        """Convert any supported format to markdown"""
        
    def extract_text(self, file_path: str) -> str:
        """Extract plain text from any format"""
        
    def preserve_formatting(self, content: str) -> dict:
        """Preserve important formatting information"""
```

**Content Validator**
```python
class ContentValidator:
    """Validates content against schemas and rules"""
    
    def validate_metadata(self, metadata: dict, schema_type: str) -> ValidationResult:
        """Validate metadata against JSON schema"""
        
    def check_completeness(self, content: dict) -> List[str]:
        """Check for required fields"""
        
    def verify_relationships(self, content: dict) -> List[str]:
        """Verify referenced entities exist"""
```

#### Workflow
1. Content placed in `/import/queue/`
2. System detects new files
3. Format conversion if needed
4. Metadata extraction/creation
5. Validation checks
6. Move to appropriate storage
7. Update database records
8. Archive original

### 2. Storage Management

#### File Organization
```python
class StorageManager:
    """Manages file system storage"""
    
    def store_content(self, content: Content, content_type: str) -> str:
        """Store content in appropriate directory"""
        
    def generate_path(self, metadata: dict) -> str:
        """Generate storage path based on metadata"""
        
    def ensure_unique_filename(self, proposed_name: str) -> str:
        """Ensure filename is unique"""
        
    def archive_version(self, content_id: str, version: str):
        """Archive previous version"""
```

#### Version Control Integration
```python
class VersionController:
    """Integrates with Git for version control"""
    
    def commit_changes(self, files: List[str], message: str):
        """Commit file changes to repository"""
        
    def tag_release(self, version: str, notes: str):
        """Create tagged release"""
        
    def get_history(self, file_path: str) -> List[Commit]:
        """Get commit history for file"""
        
    def rollback(self, file_path: str, commit_id: str):
        """Rollback file to previous version"""
```

### 3. Processing Engine

#### Content Analyzer
```python
class ContentAnalyzer:
    """Analyzes content for themes, patterns, and relationships"""
    
    def extract_themes(self, text: str) -> List[Theme]:
        """Identify themes using NLP"""
        
    def find_motifs(self, text: str) -> List[Motif]:
        """Detect recurring motifs"""
        
    def identify_archetypes(self, content: dict) -> List[Archetype]:
        """Classify archetypal patterns"""
        
    def suggest_relationships(self, content: dict) -> List[Relationship]:
        """Suggest potential relationships"""
```

#### Relationship Mapper
```python
class RelationshipMapper:
    """Maps relationships between entities"""
    
    def create_relationship(self, source: Entity, target: Entity, rel_type: str):
        """Create new relationship"""
        
    def find_connections(self, entity_id: str, depth: int = 1) -> Graph:
        """Find all connections to specified depth"""
        
    def calculate_similarity(self, entity1: Entity, entity2: Entity) -> float:
        """Calculate similarity score between entities"""
        
    def build_network_graph(self, entities: List[Entity]) -> NetworkGraph:
        """Build complete relationship network"""
```

### 4. Search and Discovery

#### Search Engine
```python
class SearchEngine:
    """Full-text and faceted search capabilities"""
    
    def search(self, query: str, filters: dict = None) -> SearchResults:
        """Perform search with optional filters"""
        
    def build_facets(self, results: List[Content]) -> dict:
        """Build faceted search options"""
        
    def suggest_completions(self, partial_query: str) -> List[str]:
        """Provide search suggestions"""
        
    def find_similar(self, content_id: str) -> List[Content]:
        """Find similar content"""
```

#### Recommendation Engine
```python
class RecommendationEngine:
    """Provides content recommendations"""
    
    def recommend_related(self, content_id: str) -> List[Recommendation]:
        """Recommend related content"""
        
    def recommend_by_theme(self, themes: List[str]) -> List[Recommendation]:
        """Recommend by thematic similarity"""
        
    def personalize_recommendations(self, user_history: List[str]) -> List[Recommendation]:
        """Personalize based on viewing history"""
```

### 5. Export and Publishing

#### Export Manager
```python
class ExportManager:
    """Handles content export in various formats"""
    
    def export_collection(self, collection_id: str, format: str) -> str:
        """Export entire collection"""
        
    def create_ebook(self, content_ids: List[str], metadata: dict) -> str:
        """Create ebook from content"""
        
    def generate_citations(self, content_ids: List[str], style: str) -> List[str]:
        """Generate academic citations"""
        
    def create_api_response(self, content: Content) -> dict:
        """Format content for API response"""
```

## Data Flow

### Import Process
```
1. File Upload/Discovery
   └─> Format Detection
       └─> Conversion (if needed)
           └─> Metadata Extraction
               └─> Validation
                   └─> Storage
                       └─> Indexing
                           └─> Relationship Mapping
                               └─> Publishing
```

### Search Process
```
1. Query Input
   └─> Query Parsing
       └─> Index Search
           └─> Result Ranking
               └─> Facet Building
                   └─> Result Formatting
                       └─> Response Delivery
```

## API Design

### RESTful Endpoints

#### Content Endpoints
```
GET    /api/v1/stories              # List stories
GET    /api/v1/stories/{id}         # Get specific story
POST   /api/v1/stories              # Create new story
PUT    /api/v1/stories/{id}         # Update story
DELETE /api/v1/stories/{id}         # Delete story

GET    /api/v1/characters           # List characters
GET    /api/v1/characters/{id}      # Get specific character
POST   /api/v1/characters           # Create new character
PUT    /api/v1/characters/{id}      # Update character
DELETE /api/v1/characters/{id}      # Delete character
```

#### Search Endpoints
```
GET    /api/v1/search               # Search all content
GET    /api/v1/search/stories       # Search stories
GET    /api/v1/search/characters    # Search characters
GET    /api/v1/search/suggest       # Search suggestions
```

#### Relationship Endpoints
```
GET    /api/v1/relationships/{id}   # Get relationships for entity
POST   /api/v1/relationships        # Create relationship
DELETE /api/v1/relationships/{id}   # Delete relationship
```

#### Collection Endpoints
```
GET    /api/v1/collections          # List collections
GET    /api/v1/collections/{id}     # Get collection
POST   /api/v1/collections          # Create collection
PUT    /api/v1/collections/{id}     # Update collection
DELETE /api/v1/collections/{id}     # Delete collection
```

### GraphQL Schema (Alternative)
```graphql
type Query {
  story(id: ID!): Story
  stories(filter: StoryFilter, limit: Int, offset: Int): [Story!]!
  character(id: ID!): Character
  characters(filter: CharacterFilter, limit: Int, offset: Int): [Character!]!
  search(query: String!, type: ContentType): SearchResults!
}

type Story {
  id: ID!
  title: String!
  type: StoryType!
  culture: String
  characters: [Character!]!
  themes: [Theme!]!
  relatedStories: [Story!]!
}

type Character {
  id: ID!
  name: String!
  type: CharacterType!
  pantheon: String
  stories: [Story!]!
  relationships: [Relationship!]!
}
```

## Security and Access Control

### Authentication
- API key authentication for programmatic access
- OAuth2 for user authentication
- Role-based access control (RBAC)

### Permissions Model
```python
class Permissions:
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    
    ROLES = {
        "viewer": [READ],
        "contributor": [READ, WRITE],
        "editor": [READ, WRITE, DELETE],
        "admin": [READ, WRITE, DELETE, ADMIN]
    }
```

### Data Protection
- Encryption at rest for sensitive content
- HTTPS for all API communications
- Regular backups with encryption
- Audit logging for all modifications

## Performance Optimization

### Caching Strategy
1. **Content Cache**: Frequently accessed content
2. **Search Cache**: Common search queries
3. **Relationship Cache**: Pre-computed relationship graphs
4. **CDN Integration**: Static assets and media

### Database Optimization
- Indexed fields for common queries
- Materialized views for complex aggregations
- Connection pooling
- Query optimization

### Scalability Considerations
- Horizontal scaling for API servers
- Read replicas for database
- Elasticsearch cluster for search
- Object storage for media files

## Monitoring and Analytics

### System Metrics
- API response times
- Database query performance
- Storage utilization
- Error rates

### Content Metrics
- Most viewed content
- Search patterns
- User engagement
- Content gaps

### Health Checks
```python
class HealthChecker:
    def check_database(self) -> HealthStatus
    def check_storage(self) -> HealthStatus
    def check_search_index(self) -> HealthStatus
    def check_api(self) -> HealthStatus
    def get_system_status(self) -> SystemStatus
```

## Maintenance and Operations

### Automated Tasks
1. **Daily**
   - Process import queue
   - Update search indexes
   - Check system health

2. **Weekly**
   - Database optimization
   - Cache cleanup
   - Error log analysis

3. **Monthly**
   - Full backup
   - Performance analysis
   - Security audit

### Manual Procedures
- Content quality review
- Relationship verification
- Metadata enrichment
- Schema updates

## Future Enhancements

### Phase 2 Features
- Machine learning for content classification
- Automated relationship discovery
- Multi-language support
- Advanced visualization tools

### Phase 3 Features
- Collaborative editing
- Community contributions
- API marketplace
- Mobile applications

---
*Last Updated: 2024-01-15*
*Version: 1.0*