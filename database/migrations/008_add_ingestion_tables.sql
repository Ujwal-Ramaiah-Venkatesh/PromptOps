-- ============================================================================
-- Database Migration: Add Infrastructure Ingestion Tables
-- ============================================================================
-- Week 13-15: ENHANCEMENT-002
-- Author: PromptOps Team
-- Date: 2026-04-30
-- Description: Tables for importing manual AWS Console changes into PromptOps

-- ============================================================================
-- Table: imported_changes
-- Purpose: Track all imported infrastructure changes
-- ============================================================================

CREATE TABLE IF NOT EXISTS imported_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    import_id VARCHAR(50) NOT NULL UNIQUE,
    user_id UUID NOT NULL,
    drift_id VARCHAR(50),  -- Link to drift detection event

    -- Resource info
    resource_id VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,

    -- Change details
    field_changed VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(255),  -- Who made the manual change (if known)
    changed_at TIMESTAMP,  -- When manual change was made

    -- Import metadata
    imported_by UUID NOT NULL,  -- User who imported it
    imported_at TIMESTAMP DEFAULT NOW(),
    reason TEXT,  -- Why was this imported

    -- Terraform
    terraform_code TEXT,  -- Generated Terraform
    terraform_applied BOOLEAN DEFAULT FALSE,

    -- Status
    status VARCHAR(30) NOT NULL CHECK (status IN ('pending', 'generating', 'complete', 'failed', 'rolled_back')),
    error_message TEXT,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for fast lookup
CREATE INDEX idx_imported_changes_user ON imported_changes(user_id);
CREATE INDEX idx_imported_changes_import_id ON imported_changes(import_id);
CREATE INDEX idx_imported_changes_resource ON imported_changes(resource_id);
CREATE INDEX idx_imported_changes_status ON imported_changes(status);
CREATE INDEX idx_imported_changes_imported_at ON imported_changes(imported_at DESC);

-- ============================================================================
-- Table: import_rollbacks
-- Purpose: Track rollback history
-- ============================================================================

CREATE TABLE IF NOT EXISTS import_rollbacks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    import_id VARCHAR(50) NOT NULL,
    rolled_back_by UUID NOT NULL,
    rolled_back_at TIMESTAMP DEFAULT NOW(),
    reason TEXT,
    success BOOLEAN,
    error_message TEXT,

    -- Previous state
    previous_terraform TEXT,
    reverted_to_state TEXT,

    FOREIGN KEY (import_id) REFERENCES imported_changes(import_id) ON DELETE CASCADE
);

CREATE INDEX idx_import_rollbacks_import_id ON import_rollbacks(import_id);
CREATE INDEX idx_import_rollbacks_rolled_back_at ON import_rollbacks(rolled_back_at DESC);

-- ============================================================================
-- Table: terraform_state_history
-- Purpose: Track Terraform state file changes
-- ============================================================================

CREATE TABLE IF NOT EXISTS terraform_state_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    import_id VARCHAR(50),

    -- State snapshot
    state_version INTEGER,
    state_content JSONB,  -- Full Terraform state

    -- Metadata
    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    action VARCHAR(50),  -- import, apply, rollback, manual_edit

    FOREIGN KEY (import_id) REFERENCES imported_changes(import_id) ON DELETE SET NULL
);

CREATE INDEX idx_terraform_state_history_import_id ON terraform_state_history(import_id);
CREATE INDEX idx_terraform_state_history_created_at ON terraform_state_history(created_at DESC);

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE imported_changes IS 'Tracks all manual AWS changes imported into PromptOps';
COMMENT ON TABLE import_rollbacks IS 'History of rolled-back imports';
COMMENT ON TABLE terraform_state_history IS 'Snapshots of Terraform state file changes';

COMMENT ON COLUMN imported_changes.drift_id IS 'Links to drift_detection_events if this import came from drift';
COMMENT ON COLUMN imported_changes.terraform_code IS 'Generated Terraform HCL code for the change';
COMMENT ON COLUMN imported_changes.terraform_applied IS 'Whether Terraform was successfully applied';
COMMENT ON COLUMN imported_changes.reason IS 'Business justification for importing manual change';
