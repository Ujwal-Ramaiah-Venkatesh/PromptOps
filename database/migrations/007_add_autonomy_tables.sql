-- Migration 007: Autonomy Tier System
-- Week 13-15: ENHANCEMENT-001
-- Author: PromptOps Team
-- Date: 2026-04-30

-- ============================================================================
-- Autonomy Tier Configuration
-- ============================================================================

-- User-specific autonomy tier settings
CREATE TABLE IF NOT EXISTS autonomy_tiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    risk_level VARCHAR(20) NOT NULL CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    behavior VARCHAR(30) NOT NULL CHECK (behavior IN ('auto_execute', 'require_approval')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, risk_level)
);

-- Create index for fast lookups
CREATE INDEX IF NOT EXISTS idx_autonomy_tiers_user_risk
    ON autonomy_tiers(user_id, risk_level);

-- ============================================================================
-- Action Risk Level Definitions
-- ============================================================================

-- Define default risk levels for action types
CREATE TABLE IF NOT EXISTS action_risk_levels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action_type VARCHAR(100) NOT NULL UNIQUE,
    default_risk_level VARCHAR(20) NOT NULL CHECK (default_risk_level IN ('low', 'medium', 'high', 'critical')),
    description TEXT,
    can_be_overridden BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- Pre-populate Default Action Risk Levels
-- ============================================================================

INSERT INTO action_risk_levels (action_type, default_risk_level, description, can_be_overridden) VALUES
-- LOW RISK ACTIONS
('restart_pod', 'low', 'Restart a Kubernetes pod', TRUE),
('clear_cache', 'low', 'Clear application cache', TRUE),
('disk_cleanup_small', 'low', 'Cleanup disk space under 10GB', TRUE),
('log_rotation', 'low', 'Rotate application logs', TRUE),
('staging_deploy', 'low', 'Deploy to staging environment', TRUE),
('read_only_query', 'low', 'Execute read-only database query', TRUE),
('monitoring_adjust', 'low', 'Adjust monitoring thresholds', TRUE),
('restart_service', 'low', 'Restart application service in dev/staging', TRUE),

-- MEDIUM RISK ACTIONS
('scale_up', 'medium', 'Scale up instances (increase capacity)', TRUE),
('scale_down', 'medium', 'Scale down instances (decrease capacity)', TRUE),
('staging_rollback', 'medium', 'Rollback staging deployment', TRUE),
('config_change_staging', 'medium', 'Change configuration in staging', TRUE),
('database_backup', 'medium', 'Create database backup', TRUE),
('disk_cleanup_large', 'medium', 'Cleanup disk space over 10GB', TRUE),

-- HIGH RISK ACTIONS
('production_deploy', 'high', 'Deploy to production environment', FALSE),
('database_migration', 'high', 'Run database migration', FALSE),
('scale_down_prod', 'high', 'Scale down production instances', TRUE),
('config_change_prod', 'high', 'Change configuration in production', TRUE),
('certificate_renewal', 'high', 'Renew SSL certificates', TRUE),

-- CRITICAL RISK ACTIONS (Always require approval, cannot override)
('database_schema_change', 'critical', 'Modify database schema', FALSE),
('delete_data', 'critical', 'Delete production data', FALSE),
('iam_policy_change', 'critical', 'Modify IAM policies', FALSE),
('security_group_change', 'critical', 'Modify security groups', FALSE),
('production_rollback', 'critical', 'Rollback production deployment', FALSE),
('drop_database', 'critical', 'Drop database', FALSE),
('delete_s3_bucket', 'critical', 'Delete S3 bucket', FALSE)
ON CONFLICT (action_type) DO NOTHING;

-- ============================================================================
-- Auto-Executed Actions Audit Trail
-- ============================================================================

-- Track all actions that were auto-executed (bypassed approval)
CREATE TABLE IF NOT EXISTS auto_executed_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    operation_id VARCHAR(50) NOT NULL,
    action_type VARCHAR(100) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    command TEXT NOT NULL,
    executed_at TIMESTAMP DEFAULT NOW(),
    duration_ms INTEGER,
    success BOOLEAN,
    result_summary TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Indexes for audit queries
CREATE INDEX IF NOT EXISTS idx_auto_executed_user
    ON auto_executed_actions(user_id, executed_at DESC);
CREATE INDEX IF NOT EXISTS idx_auto_executed_operation
    ON auto_executed_actions(operation_id);
CREATE INDEX IF NOT EXISTS idx_auto_executed_action_type
    ON auto_executed_actions(action_type);
CREATE INDEX IF NOT EXISTS idx_auto_executed_timestamp
    ON auto_executed_actions(executed_at DESC);

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE autonomy_tiers IS 'User-specific autonomy tier settings for auto-execution';
COMMENT ON TABLE action_risk_levels IS 'Default risk level definitions for action types';
COMMENT ON TABLE auto_executed_actions IS 'Audit trail of all auto-executed actions';

COMMENT ON COLUMN autonomy_tiers.risk_level IS 'Risk level: low, medium, high, or critical';
COMMENT ON COLUMN autonomy_tiers.behavior IS 'Behavior: auto_execute or require_approval';
COMMENT ON COLUMN action_risk_levels.can_be_overridden IS 'Whether PM can override this default risk level';

-- ============================================================================
-- Sample Data (For Testing/Development)
-- ============================================================================

-- Create sample autonomy settings for test users
-- Note: In production, users start with no settings (defaults to require_approval for all)
-- These are just examples for development/testing

-- Example: Admin user with aggressive auto-execution settings
-- INSERT INTO autonomy_tiers (user_id, risk_level, behavior) VALUES
-- ((SELECT id FROM users WHERE email = 'admin@promptops.com'), 'low', 'auto_execute'),
-- ((SELECT id FROM users WHERE email = 'admin@promptops.com'), 'medium', 'auto_execute'),
-- ((SELECT id FROM users WHERE email = 'admin@promptops.com'), 'high', 'require_approval'),
-- ((SELECT id FROM users WHERE email = 'admin@promptops.com'), 'critical', 'require_approval');

-- ============================================================================
-- Rollback Script (if needed)
-- ============================================================================

-- To rollback this migration:
-- DROP TABLE IF EXISTS auto_executed_actions;
-- DROP TABLE IF EXISTS autonomy_tiers;
-- DROP TABLE IF EXISTS action_risk_levels;
