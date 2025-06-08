-- The Mythological Forge Database Schema
-- Version 1.0
-- Description: Complete database schema for mythological content management

-- Enable UUID extension if using PostgreSQL
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- CORE CONTENT TABLES
-- =====================================================

-- Stories table for mythological narratives
CREATE TABLE stories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('origin', 'hero', 'wisdom', 'transformation', 'cosmic')),
    culture VARCHAR(100),
    tradition VARCHAR(100),
    period VARCHAR(100),
    region VARCHAR(100),
    original_language VARCHAR(10),
    translator VARCHAR(255),
    content_path TEXT NOT NULL,
    summary TEXT,
    word_count INTEGER,
    reading_time VARCHAR(50),
    complexity_rating INTEGER CHECK (complexity_rating BETWEEN 1 AND 5),
    accessibility_rating INTEGER CHECK (accessibility_rating BETWEEN 1 AND 5),
    scholarly_value_rating INTEGER CHECK (scholarly_value_rating BETWEEN 1 AND 5),
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'review', 'published', 'archived')),
    version VARCHAR(10) DEFAULT '1.0',
    license TEXT,
    attribution TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    CONSTRAINT unique_story_title_culture UNIQUE (title, culture)
);

-- Characters table for mythological figures
CREATE TABLE characters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    primary_name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('deity', 'hero', 'trickster', 'monster', 'guide', 'mortal', 'demigod')),
    pantheon VARCHAR(100),
    culture VARCHAR(100),
    etymology TEXT,
    appearance_description TEXT,
    personality_description TEXT,
    attributes JSONB,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'review', 'published', 'archived')),
    version VARCHAR(10) DEFAULT '1.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    CONSTRAINT unique_character_name_pantheon UNIQUE (primary_name, pantheon)
);

-- Pantheons table for organizing cultural mythologies
CREATE TABLE pantheons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    culture VARCHAR(100) NOT NULL,
    region VARCHAR(100),
    period VARCHAR(100),
    description TEXT,
    characteristics TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Themes table for thematic categorization
CREATE TABLE themes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50),
    description TEXT,
    parent_theme_id UUID REFERENCES themes(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- RELATIONSHIP TABLES
-- =====================================================

-- Generic relationships table for all entity relationships
CREATE TABLE relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL,
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('story', 'character', 'pantheon', 'theme')),
    target_id UUID NOT NULL,
    target_type VARCHAR(50) NOT NULL CHECK (target_type IN ('story', 'character', 'pantheon', 'theme')),
    relationship_type VARCHAR(100) NOT NULL,
    relationship_subtype VARCHAR(100),
    strength INTEGER DEFAULT 1 CHECK (strength BETWEEN 1 AND 10),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_relationship UNIQUE (source_id, target_id, relationship_type),
    CONSTRAINT no_self_reference CHECK (source_id != target_id)
);

-- Story-Character junction table
CREATE TABLE story_characters (
    story_id UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    role VARCHAR(50) CHECK (role IN ('protagonist', 'antagonist', 'guide', 'trickster', 'supporting')),
    importance INTEGER DEFAULT 1 CHECK (importance BETWEEN 1 AND 5),
    first_appearance INTEGER, -- Chapter or section number
    notes TEXT,
    PRIMARY KEY (story_id, character_id)
);

-- Character alternate names
CREATE TABLE character_names (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    name_type VARCHAR(50) CHECK (name_type IN ('alternate', 'epithet', 'title', 'translation')),
    language VARCHAR(10),
    context TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TAGGING AND CATEGORIZATION
-- =====================================================

-- Tags table for flexible categorization
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50),
    description TEXT,
    color VARCHAR(7), -- Hex color for UI
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_count INTEGER DEFAULT 0
);

-- Content-Tags junction table
CREATE TABLE content_tags (
    content_id UUID NOT NULL,
    content_type VARCHAR(50) NOT NULL CHECK (content_type IN ('story', 'character', 'pantheon')),
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    relevance_score FLOAT DEFAULT 1.0 CHECK (relevance_score BETWEEN 0 AND 1),
    added_by VARCHAR(100),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (content_id, tag_id)
);

-- Motifs table for recurring elements
CREATE TABLE motifs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Story-Motifs junction table
CREATE TABLE story_motifs (
    story_id UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    motif_id UUID NOT NULL REFERENCES motifs(id) ON DELETE CASCADE,
    occurrences INTEGER DEFAULT 1,
    significance VARCHAR(20) CHECK (significance IN ('minor', 'moderate', 'major', 'central')),
    notes TEXT,
    PRIMARY KEY (story_id, motif_id)
);

-- =====================================================
-- CONTENT MANAGEMENT
-- =====================================================

-- Import queue for new content
CREATE TABLE import_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_path TEXT NOT NULL,
    file_type VARCHAR(50),
    source_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'archived')),
    metadata JSONB,
    error_message TEXT,
    imported_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Content versions for tracking changes
CREATE TABLE content_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID NOT NULL,
    content_type VARCHAR(50) NOT NULL CHECK (content_type IN ('story', 'character', 'pantheon')),
    version_number VARCHAR(10) NOT NULL,
    change_summary TEXT,
    content_snapshot JSONB,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_content_version UNIQUE (content_id, version_number)
);

-- =====================================================
-- SEARCH AND DISCOVERY
-- =====================================================

-- Search index for full-text search
CREATE TABLE search_index (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID NOT NULL,
    content_type VARCHAR(50) NOT NULL CHECK (content_type IN ('story', 'character', 'pantheon')),
    title VARCHAR(255),
    searchable_text TEXT,
    facets JSONB,
    boost_score FLOAT DEFAULT 1.0,
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_search_entry UNIQUE (content_id, content_type)
);

-- User collections for organizing content
CREATE TABLE collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(50) CHECK (type IN ('personal', 'public', 'scholarly', 'thematic')),
    visibility VARCHAR(20) DEFAULT 'private' CHECK (visibility IN ('private', 'public', 'restricted')),
    metadata JSONB,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Collection items junction table
CREATE TABLE collection_items (
    collection_id UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    content_id UUID NOT NULL,
    content_type VARCHAR(50) NOT NULL CHECK (content_type IN ('story', 'character', 'pantheon')),
    position INTEGER,
    notes TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (collection_id, content_id)
);

-- =====================================================
-- ANALYTICS AND METRICS
-- =====================================================

-- Content metrics for tracking popularity and usage
CREATE TABLE content_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID NOT NULL,
    content_type VARCHAR(50) NOT NULL CHECK (content_type IN ('story', 'character', 'pantheon')),
    view_count INTEGER DEFAULT 0,
    export_count INTEGER DEFAULT 0,
    citation_count INTEGER DEFAULT 0,
    last_viewed TIMESTAMP,
    avg_time_spent INTEGER, -- in seconds
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_content_metrics UNIQUE (content_id, content_type)
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Stories indexes
CREATE INDEX idx_stories_type ON stories(type);
CREATE INDEX idx_stories_culture ON stories(culture);
CREATE INDEX idx_stories_status ON stories(status);
CREATE INDEX idx_stories_created_at ON stories(created_at DESC);
CREATE INDEX idx_stories_title_trgm ON stories USING gin(title gin_trgm_ops);

-- Characters indexes
CREATE INDEX idx_characters_type ON characters(type);
CREATE INDEX idx_characters_pantheon ON characters(pantheon);
CREATE INDEX idx_characters_culture ON characters(culture);
CREATE INDEX idx_characters_name_trgm ON characters USING gin(primary_name gin_trgm_ops);

-- Relationships indexes
CREATE INDEX idx_relationships_source ON relationships(source_id, source_type);
CREATE INDEX idx_relationships_target ON relationships(target_id, target_type);
CREATE INDEX idx_relationships_type ON relationships(relationship_type);

-- Tags indexes
CREATE INDEX idx_content_tags_content ON content_tags(content_id, content_type);
CREATE INDEX idx_content_tags_tag ON content_tags(tag_id);

-- Search index
CREATE INDEX idx_search_fulltext ON search_index USING gin(to_tsvector('english', searchable_text));
CREATE INDEX idx_search_content ON search_index(content_id, content_type);

-- =====================================================
-- TRIGGERS FOR AUTOMATED UPDATES
-- =====================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to tables with updated_at
CREATE TRIGGER update_stories_updated_at BEFORE UPDATE ON stories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_characters_updated_at BEFORE UPDATE ON characters
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_collections_updated_at BEFORE UPDATE ON collections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Update tag usage count
CREATE OR REPLACE FUNCTION update_tag_usage_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE tags SET usage_count = usage_count + 1 WHERE id = NEW.tag_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE tags SET usage_count = usage_count - 1 WHERE id = OLD.tag_id;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tag_usage_after_insert AFTER INSERT ON content_tags
    FOR EACH ROW EXECUTE FUNCTION update_tag_usage_count();

CREATE TRIGGER update_tag_usage_after_delete AFTER DELETE ON content_tags
    FOR EACH ROW EXECUTE FUNCTION update_tag_usage_count();

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- Story overview with counts
CREATE VIEW story_overview AS
SELECT 
    s.id,
    s.title,
    s.type,
    s.culture,
    s.status,
    s.created_at,
    COUNT(DISTINCT sc.character_id) as character_count,
    COUNT(DISTINCT sm.motif_id) as motif_count,
    COUNT(DISTINCT ct.tag_id) as tag_count
FROM stories s
LEFT JOIN story_characters sc ON s.id = sc.story_id
LEFT JOIN story_motifs sm ON s.id = sm.story_id
LEFT JOIN content_tags ct ON s.id = ct.content_id AND ct.content_type = 'story'
GROUP BY s.id;

-- Character overview with relationship counts
CREATE VIEW character_overview AS
SELECT 
    c.id,
    c.primary_name,
    c.type,
    c.pantheon,
    c.culture,
    c.status,
    COUNT(DISTINCT sc.story_id) as story_count,
    COUNT(DISTINCT cn.id) as alternate_name_count,
    COUNT(DISTINCT r.id) as relationship_count
FROM characters c
LEFT JOIN story_characters sc ON c.id = sc.character_id
LEFT JOIN character_names cn ON c.id = cn.character_id
LEFT JOIN relationships r ON (c.id = r.source_id OR c.id = r.target_id)
GROUP BY c.id;

-- =====================================================
-- SAMPLE DATA FOR TAGS
-- =====================================================

INSERT INTO tags (name, category, description) VALUES
-- Content Type Tags
('origin-myth', 'content-type', 'Stories about the creation of the world or universe'),
('hero-journey', 'content-type', 'Stories following the hero''s journey pattern'),
('wisdom-tale', 'content-type', 'Stories meant to impart wisdom or moral lessons'),
('transformation-myth', 'content-type', 'Stories involving transformation or metamorphosis'),
('cosmic-myth', 'content-type', 'Stories about cosmic events and universal themes'),

-- Cultural Tags
('greek-mythology', 'culture', 'Greek mythological tradition'),
('norse-mythology', 'culture', 'Norse/Germanic mythological tradition'),
('egyptian-mythology', 'culture', 'Ancient Egyptian mythological tradition'),
('mesopotamian-mythology', 'culture', 'Mesopotamian mythological traditions'),
('celtic-mythology', 'culture', 'Celtic mythological traditions'),

-- Theme Tags
('creation', 'theme', 'Creation and origin themes'),
('destruction', 'theme', 'Destruction and ending themes'),
('love-story', 'theme', 'Love and romance themes'),
('death-rebirth', 'theme', 'Death and rebirth cycles'),
('quest-narrative', 'theme', 'Quest and journey themes'),

-- Archetype Tags
('hero-archetype', 'archetype', 'The hero figure'),
('mentor-guide', 'archetype', 'The wise mentor or guide'),
('shadow-figure', 'archetype', 'The shadow or dark aspect'),
('trickster-archetype', 'archetype', 'The trickster figure'),
('mother-goddess', 'archetype', 'The mother or goddess figure');