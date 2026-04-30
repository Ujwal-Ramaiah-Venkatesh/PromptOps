-- ============================================================================
-- Database Migration: Add Discovery & Onboarding Tables
-- ============================================================================
-- Week 16-18: ENHANCEMENT-003
-- Author: PromptOps Team
-- Date: 2026-04-30
-- Description: Tables for AWS resource discovery and bulk onboarding

-- ============================================================================
-- Table: discovery_scans
-- Purpose: Track discovery scan jobs
-- ============================================================================

CREATE TABLE IF NOT EXISTS discovery_scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id VARCHAR(50) NOT NULL UNIQUE,

    -- User who initiated scan
    user_id UUID NOT NULL,
    user_email VARCHAR(255),

    -- Scan configuration
    regions TEXT[],  -- Array of AWS regions scanned
    resource_types TEXT[],  -- Array of resource types scanned

    -- Status tracking
    status VARCHAR(30) NOT NULL CHECK (status IN ('running', 'complete', 'failed')),
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    duration_seconds DECIMAL(10,2),

    -- Results summary
    total_resources INTEGER DEFAULT 0,
    total_dependencies INTEGER DEFAULT 0,
    errors TEXT[],  -- Array of error messages

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for fast lookup
CREATE INDEX idx_discovery_scans_user ON discovery_scans(user_id);
CREATE INDEX idx_discovery_scans_scan_id ON discovery_scans(scan_id);
CREATE INDEX idx_discovery_scans_status ON discovery_scans(status);
CREATE INDEX idx_discovery_scans_started_at ON discovery_scans(started_at DESC);

-- ============================================================================
-- Table: discovered_resources
-- Purpose: Store discovered AWS resources with inferred context
-- ============================================================================

CREATE TABLE IF NOT EXISTS discovered_resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id VARCHAR(50) NOT NULL,

    -- Resource identification
    resource_id VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    region VARCHAR(50) NOT NULL,
    name VARCHAR(500),

    -- Raw AWS state
    aws_state JSONB,  -- Full AWS resource state
    tags JSONB,  -- Resource tags as JSON object

    -- Inferred context
    inferred_environment VARCHAR(50),  -- production, staging, development
    inferred_project VARCHAR(100),
    inferred_owner VARCHAR(255),
    confidence_score DECIMAL(3,2),  -- 0.00 to 1.00
    inference_reasoning TEXT,  -- Why this context was inferred

    -- Import status
    imported BOOLEAN DEFAULT FALSE,
    imported_at TIMESTAMP,
    import_id VARCHAR(50),

    -- Metadata
    discovered_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (scan_id) REFERENCES discovery_scans(scan_id) ON DELETE CASCADE
);

-- Indexes for fast queries
CREATE INDEX idx_discovered_resources_scan ON discovered_resources(scan_id);
CREATE INDEX idx_discovered_resources_resource_id ON discovered_resources(resource_id);
CREATE INDEX idx_discovered_resources_type ON discovered_resources(resource_type);
CREATE INDEX idx_discovered_resources_region ON discovered_resources(region);
CREATE INDEX idx_discovered_resources_environment ON discovered_resources(inferred_environment);
CREATE INDEX idx_discovered_resources_project ON discovered_resources(inferred_project);
CREATE INDEX idx_discovered_resources_imported ON discovered_resources(imported);

-- Composite index for filtering
CREATE INDEX idx_discovered_resources_scan_type_env
    ON discovered_resources(scan_id, resource_type, inferred_environment);

-- ============================================================================
-- Table: resource_dependencies
-- Purpose: Track dependencies between discovered resources
-- ============================================================================

CREATE TABLE IF NOT EXISTS resource_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id VARCHAR(50) NOT NULL,

    -- Dependency relationship
    source_resource_id VARCHAR(255) NOT NULL,
    target_resource_id VARCHAR(255) NOT NULL,
    dependency_type VARCHAR(50) NOT NULL,  -- security_group, network, iam, application
    confidence_score DECIMAL(3,2),  -- 0.00 to 1.00

    -- Metadata
    detected_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (scan_id) REFERENCES discovery_scans(scan_id) ON DELETE CASCADE
);

-- Indexes for dependency queries
CREATE INDEX idx_resource_dependencies_scan ON resource_dependencies(scan_id);
CREATE INDEX idx_resource_dependencies_source ON resource_dependencies(source_resource_id);
CREATE INDEX idx_resource_dependencies_target ON resource_dependencies(target_resource_id);
CREATE INDEX idx_resource_dependencies_type ON resource_dependencies(dependency_type);

-- Composite index for graph queries
CREATE INDEX idx_resource_dependencies_graph
    ON resource_dependencies(scan_id, source_resource_id, target_resource_id);

-- ============================================================================
-- Table: bulk_imports
-- Purpose: Track bulk import operations
-- ============================================================================

CREATE TABLE IF NOT EXISTS bulk_imports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    import_id VARCHAR(50) NOT NULL UNIQUE,
    scan_id VARCHAR(50) NOT NULL,

    -- Import configuration
    user_id UUID NOT NULL,
    environment_filter VARCHAR(50),  -- If specified, only import this environment
    resource_type_filter TEXT[],  -- If specified, only import these types
    dry_run BOOLEAN DEFAULT FALSE,

    -- Status
    status VARCHAR(30) NOT NULL CHECK (status IN ('pending', 'running', 'complete', 'failed')),
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,

    -- Results
    resources_to_import INTEGER DEFAULT 0,
    resources_imported INTEGER DEFAULT 0,
    resources_failed INTEGER DEFAULT 0,
    terraform_generated BOOLEAN DEFAULT FALSE,
    errors TEXT[],

    FOREIGN KEY (scan_id) REFERENCES discovery_scans(scan_id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_bulk_imports_import_id ON bulk_imports(import_id);
CREATE INDEX idx_bulk_imports_scan_id ON bulk_imports(scan_id);
CREATE INDEX idx_bulk_imports_user ON bulk_imports(user_id);
CREATE INDEX idx_bulk_imports_status ON bulk_imports(status);

-- ============================================================================
-- Table: discovery_metrics
-- Purpose: Store metrics and insights from discovery scans
-- ============================================================================

CREATE TABLE IF NOT EXISTS discovery_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id VARCHAR(50) NOT NULL,

    -- Coverage metrics
    total_resources INTEGER NOT NULL,
    environment_coverage_percentage DECIMAL(5,2),  -- 0.00 to 100.00
    project_coverage_percentage DECIMAL(5,2),
    owner_coverage_percentage DECIMAL(5,2),

    -- Confidence metrics
    high_confidence_count INTEGER DEFAULT 0,  -- >= 0.8
    medium_confidence_count INTEGER DEFAULT 0,  -- 0.5 to 0.8
    low_confidence_count INTEGER DEFAULT 0,  -- < 0.5

    -- Tag analysis
    consistent_tags JSONB,  -- Tags found on >80% of resources
    inconsistent_tags JSONB,  -- Tags found on <80% of resources

    -- Naming patterns
    detected_naming_patterns JSONB,  -- Array of detected patterns

    -- Dependency metrics
    total_dependencies INTEGER DEFAULT 0,
    security_group_dependencies INTEGER DEFAULT 0,
    network_dependencies INTEGER DEFAULT 0,
    application_dependencies INTEGER DEFAULT 0,

    -- Risk assessment
    untagged_production_count INTEGER DEFAULT 0,  -- HIGH risk
    resources_no_owner_count INTEGER DEFAULT 0,  -- MEDIUM risk
    resources_default_vpc_count INTEGER DEFAULT 0,  -- MEDIUM risk

    -- Metadata
    generated_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (scan_id) REFERENCES discovery_scans(scan_id) ON DELETE CASCADE
);

-- Index
CREATE INDEX idx_discovery_metrics_scan ON discovery_metrics(scan_id);

-- ============================================================================
-- Views
-- ============================================================================

-- View: Recent scans by user
CREATE OR REPLACE VIEW recent_discovery_scans AS
SELECT
    scan_id,
    user_email,
    status,
    total_resources,
    total_dependencies,
    started_at,
    completed_at,
    duration_seconds,
    ARRAY_LENGTH(regions, 1) as region_count,
    ARRAY_LENGTH(errors, 1) as error_count
FROM discovery_scans
ORDER BY started_at DESC
LIMIT 100;

-- View: Resource summary by environment
CREATE OR REPLACE VIEW resources_by_environment AS
SELECT
    scan_id,
    inferred_environment,
    COUNT(*) as resource_count,
    COUNT(DISTINCT resource_type) as resource_types,
    AVG(confidence_score) as avg_confidence,
    COUNT(CASE WHEN imported THEN 1 END) as imported_count
FROM discovered_resources
GROUP BY scan_id, inferred_environment;

-- View: Dependency summary
CREATE OR REPLACE VIEW dependency_summary AS
SELECT
    scan_id,
    dependency_type,
    COUNT(*) as dependency_count,
    AVG(confidence_score) as avg_confidence
FROM resource_dependencies
GROUP BY scan_id, dependency_type;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE discovery_scans IS 'Track AWS resource discovery scan jobs';
COMMENT ON TABLE discovered_resources IS 'Store discovered AWS resources with inferred context';
COMMENT ON TABLE resource_dependencies IS 'Track dependencies between discovered resources';
COMMENT ON TABLE bulk_imports IS 'Track bulk import operations from discovery scans';
COMMENT ON TABLE discovery_metrics IS 'Store metrics and insights from discovery scans';

COMMENT ON COLUMN discovered_resources.aws_state IS 'Full AWS resource state as JSONB';
COMMENT ON COLUMN discovered_resources.confidence_score IS 'Confidence in inferred context (0.00 to 1.00)';
COMMENT ON COLUMN discovered_resources.inference_reasoning IS 'Human-readable explanation of why context was inferred';

COMMENT ON COLUMN resource_dependencies.dependency_type IS 'Type: security_group, network, iam, application';
COMMENT ON COLUMN resource_dependencies.confidence_score IS 'Confidence in dependency (1.0 = explicit, <1.0 = inferred)';
