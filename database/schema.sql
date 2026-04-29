-- ============================================================================
-- PromptOps Database Schema
-- ============================================================================
--
-- PostgreSQL schema for storing audit logs, decompositions, executions,
-- context snapshots, and drift events.
--
-- Author: PromptOps Team - Week 11-12
-- Date: 2026-04-29
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Audit Log Table
-- ============================================================================

CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_email VARCHAR(255) NOT NULL,
    command TEXT NOT NULL,
    intent_type VARCHAR(50),
    target_service VARCHAR(100),
    target_env VARCHAR(50),
    status VARCHAR(50) NOT NULL,
    risk_level VARCHAR(20),
    decomposition_id UUID,
    execution_id UUID,
    duration_seconds INT,
    error_message TEXT,
    task_plan JSONB,
    execution_log JSONB DEFAULT '[]',
    approved_by VARCHAR(255),
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for fast queries
CREATE INDEX idx_audit_user ON audit_log(user_email);
CREATE INDEX idx_audit_env ON audit_log(target_env);
CREATE INDEX idx_audit_status ON audit_log(status);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp DESC);
CREATE INDEX idx_audit_intent_type ON audit_log(intent_type);
CREATE INDEX idx_audit_service ON audit_log(target_service);

-- Updated timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_audit_log_updated_at
    BEFORE UPDATE ON audit_log
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE audit_log IS 'Immutable audit trail of all commands and operations';

-- ============================================================================
-- Decompositions Table
-- ============================================================================

CREATE TABLE decompositions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    operation_id VARCHAR(100) UNIQUE NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_email VARCHAR(255) NOT NULL,
    original_command TEXT NOT NULL,
    parsed_intent JSONB NOT NULL,
    total_sub_tasks INT NOT NULL,
    estimated_duration INT,
    risk_assessment JSONB NOT NULL,
    sub_tasks JSONB NOT NULL,
    rollback_plan JSONB,
    current_state JSONB,
    target_state JSONB,
    dependencies_graph JSONB,
    critical_path JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_decomp_user ON decompositions(user_email);
CREATE INDEX idx_decomp_operation ON decompositions(operation_id);
CREATE INDEX idx_decomp_timestamp ON decompositions(timestamp DESC);

COMMENT ON TABLE decompositions IS 'Decomposed task plans with sub-tasks and rollback plans';

-- ============================================================================
-- Executions Table
-- ============================================================================

CREATE TABLE executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id VARCHAR(100) UNIQUE NOT NULL,
    decomposition_id UUID REFERENCES decompositions(id),
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    approved_by VARCHAR(255),
    approved_at TIMESTAMPTZ,
    approval_phrase VARCHAR(100),
    completed_tasks INT DEFAULT 0,
    failed_tasks INT DEFAULT 0,
    current_task_index INT DEFAULT 0,
    current_task_name VARCHAR(255),
    execution_log JSONB DEFAULT '[]',
    error_message TEXT,
    rollback_executed BOOLEAN DEFAULT FALSE,
    rollback_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_exec_decomp ON executions(decomposition_id);
CREATE INDEX idx_exec_status ON executions(status);
CREATE INDEX idx_exec_execution_id ON executions(execution_id);
CREATE INDEX idx_exec_started_at ON executions(started_at DESC);

-- Updated timestamp trigger
CREATE TRIGGER update_executions_updated_at
    BEFORE UPDATE ON executions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE executions IS 'Execution tracking with real-time status and logs';

-- ============================================================================
-- Context Snapshots Table
-- ============================================================================

CREATE TABLE context_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    snapshot_id VARCHAR(100) UNIQUE NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resource_types JSONB NOT NULL,
    total_resources INT NOT NULL,
    collection_duration_ms INT,
    errors JSONB DEFAULT '[]',
    aws_region VARCHAR(50) DEFAULT 'us-east-1',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_snapshot_id ON context_snapshots(snapshot_id);
CREATE INDEX idx_snapshot_timestamp ON context_snapshots(timestamp DESC);

COMMENT ON TABLE context_snapshots IS 'Infrastructure state snapshots for drift detection';

-- ============================================================================
-- Drift Events Table
-- ============================================================================

CREATE TABLE drift_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drift_id VARCHAR(100) UNIQUE NOT NULL,
    snapshot_id VARCHAR(100) NOT NULL,
    previous_snapshot_id VARCHAR(100),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255) NOT NULL,
    resource_name VARCHAR(255),
    field VARCHAR(100) NOT NULL,
    expected_value TEXT,
    actual_value TEXT,
    severity VARCHAR(20) NOT NULL,
    auto_fixable BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(255),
    acknowledged_at TIMESTAMPTZ,
    reverted_by VARCHAR(255),
    reverted_at TIMESTAMPTZ,
    revert_execution_id VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_drift_snapshot ON drift_events(snapshot_id);
CREATE INDEX idx_drift_resource ON drift_events(resource_type, resource_id);
CREATE INDEX idx_drift_severity ON drift_events(severity);
CREATE INDEX idx_drift_acknowledged ON drift_events(acknowledged_by);
CREATE INDEX idx_drift_timestamp ON drift_events(timestamp DESC);
CREATE INDEX idx_drift_id ON drift_events(drift_id);

COMMENT ON TABLE drift_events IS 'Infrastructure drift events with acknowledgement tracking';

-- ============================================================================
-- Users Table (for future authentication)
-- ============================================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'pm',
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- Updated timestamp trigger
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE users IS 'User accounts for authentication and authorization';

-- ============================================================================
-- API Keys Table (for Claude API key rotation)
-- ============================================================================

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_name VARCHAR(100) NOT NULL,
    key_value_encrypted TEXT NOT NULL,
    service VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    usage_count INT DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_api_keys_service ON api_keys(service);
CREATE INDEX idx_api_keys_active ON api_keys(is_active);

-- Updated timestamp trigger
CREATE TRIGGER update_api_keys_updated_at
    BEFORE UPDATE ON api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE api_keys IS 'Encrypted API keys for external services';

-- ============================================================================
-- Views
-- ============================================================================

-- Recent activity view
CREATE VIEW recent_activity AS
SELECT
    a.id,
    a.timestamp,
    a.user_email,
    a.command,
    a.intent_type,
    a.target_service,
    a.target_env,
    a.status,
    a.risk_level,
    a.duration_seconds,
    a.approved_by,
    d.total_sub_tasks,
    e.completed_tasks,
    e.failed_tasks
FROM audit_log a
LEFT JOIN decompositions d ON a.decomposition_id = d.id
LEFT JOIN executions e ON a.execution_id = e.id
ORDER BY a.timestamp DESC
LIMIT 100;

COMMENT ON VIEW recent_activity IS 'Recent command activity with execution details';

-- Critical drift view
CREATE VIEW critical_drift AS
SELECT
    drift_id,
    timestamp,
    resource_type,
    resource_id,
    resource_name,
    field,
    expected_value,
    actual_value,
    severity,
    auto_fixable,
    acknowledged_by
FROM drift_events
WHERE severity IN ('critical', 'high')
  AND acknowledged_by IS NULL
ORDER BY timestamp DESC;

COMMENT ON VIEW critical_drift IS 'Unacknowledged critical and high-severity drift events';

-- Execution statistics view
CREATE VIEW execution_stats AS
SELECT
    DATE(started_at) as date,
    COUNT(*) as total_executions,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
    AVG(completed_tasks) as avg_tasks_completed,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds
FROM executions
WHERE started_at IS NOT NULL
GROUP BY DATE(started_at)
ORDER BY date DESC;

COMMENT ON VIEW execution_stats IS 'Daily execution statistics';

-- ============================================================================
-- Materialized Views (for performance)
-- ============================================================================

-- Audit summary by user
CREATE MATERIALIZED VIEW audit_summary_by_user AS
SELECT
    user_email,
    COUNT(*) as total_commands,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
    AVG(duration_seconds) as avg_duration,
    MAX(timestamp) as last_activity
FROM audit_log
GROUP BY user_email;

CREATE UNIQUE INDEX idx_audit_summary_user ON audit_summary_by_user(user_email);

COMMENT ON MATERIALIZED VIEW audit_summary_by_user IS 'User activity summary (refresh daily)';

-- ============================================================================
-- Functions
-- ============================================================================

-- Function to add audit entry
CREATE OR REPLACE FUNCTION add_audit_entry(
    p_user_email VARCHAR,
    p_command TEXT,
    p_intent_type VARCHAR,
    p_target_service VARCHAR,
    p_target_env VARCHAR,
    p_status VARCHAR,
    p_risk_level VARCHAR
) RETURNS UUID AS $$
DECLARE
    v_id UUID;
BEGIN
    INSERT INTO audit_log (
        user_email,
        command,
        intent_type,
        target_service,
        target_env,
        status,
        risk_level
    ) VALUES (
        p_user_email,
        p_command,
        p_intent_type,
        p_target_service,
        p_target_env,
        p_status,
        p_risk_level
    ) RETURNING id INTO v_id;

    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get unacknowledged drift count
CREATE OR REPLACE FUNCTION get_unacknowledged_drift_count()
RETURNS INT AS $$
BEGIN
    RETURN (
        SELECT COUNT(*)
        FROM drift_events
        WHERE acknowledged_by IS NULL
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Initial Data
-- ============================================================================

-- Insert default admin user
INSERT INTO users (email, full_name, role) VALUES
    ('admin@promptops.com', 'Admin User', 'admin'),
    ('pm@promptops.com', 'Product Manager', 'pm')
ON CONFLICT (email) DO NOTHING;

-- ============================================================================
-- Permissions (adjust based on your setup)
-- ============================================================================

-- Grant permissions to application user
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO promptops_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO promptops_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO promptops_app;

-- ============================================================================
-- Cleanup/Maintenance
-- ============================================================================

-- Function to archive old audit logs (>1 year)
CREATE OR REPLACE FUNCTION archive_old_audit_logs()
RETURNS INT AS $$
DECLARE
    v_count INT;
BEGIN
    -- In production, move to archive table instead of deleting
    DELETE FROM audit_log
    WHERE timestamp < NOW() - INTERVAL '1 year'
    RETURNING COUNT(*) INTO v_count;

    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- Refresh materialized views (schedule this daily)
-- SELECT refresh_materialized_views();
CREATE OR REPLACE FUNCTION refresh_materialized_views()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY audit_summary_by_user;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Schema Version
-- ============================================================================

CREATE TABLE schema_version (
    version VARCHAR(20) PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    description TEXT
);

INSERT INTO schema_version (version, description) VALUES
    ('1.0.0', 'Initial schema with audit, decompositions, executions, snapshots, and drift tables');

-- ============================================================================
-- End of Schema
-- ============================================================================
