-- Audit Logging Schema
-- ====================
--
-- Comprehensive audit logging for compliance and security
-- Phase 5B - Enterprise Features
--
-- Author: PromptOps Team
-- Date: 2026-05-02

-- ============================================================================
-- 1. Audit Log Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Actor (who performed the action)
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    user_email VARCHAR(255),
    user_name VARCHAR(200),

    -- Action details
    action VARCHAR(100) NOT NULL,           -- create, update, delete, execute, login, etc.
    resource_type VARCHAR(100) NOT NULL,    -- user, role, budget, resource, etc.
    resource_id VARCHAR(255),               -- ID of affected resource
    resource_name VARCHAR(255),             -- Name of affected resource

    -- Request details
    method VARCHAR(10),                     -- HTTP method (GET, POST, etc.)
    endpoint VARCHAR(500),                  -- API endpoint
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),                -- Request tracking ID

    -- Changes
    old_values JSONB,                       -- Previous state
    new_values JSONB,                       -- New state
    changes JSONB,                          -- Computed diff

    -- Outcome
    status VARCHAR(50) NOT NULL,            -- success, failure, error
    status_code INTEGER,                    -- HTTP status code
    error_message TEXT,

    -- Severity
    severity VARCHAR(20) DEFAULT 'info' CHECK (severity IN ('debug', 'info', 'warning', 'error', 'critical')),

    -- Metadata
    session_id UUID,
    api_key_id UUID,
    additional_data JSONB DEFAULT '{}',

    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Hash chain for tamper detection
    previous_hash VARCHAR(64),
    record_hash VARCHAR(64)
);

-- Indexes for query performance
CREATE INDEX idx_audit_log_tenant_id ON audit_log(tenant_id);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_resource_type ON audit_log(resource_type);
CREATE INDEX idx_audit_log_resource_id ON audit_log(resource_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at DESC);
CREATE INDEX idx_audit_log_status ON audit_log(status);
CREATE INDEX idx_audit_log_severity ON audit_log(severity);
CREATE INDEX idx_audit_log_ip_address ON audit_log(ip_address);

-- Full-text search index for audit log
CREATE INDEX idx_audit_log_search ON audit_log USING gin(
    to_tsvector('english',
        coalesce(action, '') || ' ' ||
        coalesce(resource_type, '') || ' ' ||
        coalesce(resource_name, '') || ' ' ||
        coalesce(user_email, '') || ' ' ||
        coalesce(error_message, '')
    )
);

-- Comments
COMMENT ON TABLE audit_log IS 'Comprehensive audit trail for all system actions';
COMMENT ON COLUMN audit_log.previous_hash IS 'Hash of previous log entry (tamper detection)';
COMMENT ON COLUMN audit_log.record_hash IS 'SHA-256 hash of this entry';


-- ============================================================================
-- 2. Login Attempts Table (Security monitoring)
-- ============================================================================

CREATE TABLE IF NOT EXISTS login_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,

    -- Attempt details
    email VARCHAR(255) NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Outcome
    success BOOLEAN NOT NULL,
    failure_reason VARCHAR(200),            -- invalid_password, account_locked, etc.

    -- Client info
    ip_address INET NOT NULL,
    user_agent TEXT,
    device_type VARCHAR(50),

    -- MFA
    mfa_required BOOLEAN DEFAULT FALSE,
    mfa_success BOOLEAN,

    -- Geolocation (optional)
    country_code VARCHAR(2),
    city VARCHAR(100),

    -- Timestamp
    attempted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Metadata
    metadata JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX idx_login_attempts_email ON login_attempts(email);
CREATE INDEX idx_login_attempts_user_id ON login_attempts(user_id);
CREATE INDEX idx_login_attempts_ip_address ON login_attempts(ip_address);
CREATE INDEX idx_login_attempts_attempted_at ON login_attempts(attempted_at DESC);
CREATE INDEX idx_login_attempts_success ON login_attempts(success);

-- Comments
COMMENT ON TABLE login_attempts IS 'Track all login attempts for security monitoring';


-- ============================================================================
-- 3. Data Access Log (Who accessed what data)
-- ============================================================================

CREATE TABLE IF NOT EXISTS data_access_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Who accessed
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_email VARCHAR(255),

    -- What was accessed
    resource_type VARCHAR(100) NOT NULL,    -- costs, resources, budgets
    resource_id VARCHAR(255),
    record_count INTEGER,                   -- Number of records accessed

    -- How it was accessed
    action VARCHAR(50) NOT NULL,            -- read, export, download
    query_filters JSONB,                    -- Filters applied to query

    -- When
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Client info
    ip_address INET,
    request_id VARCHAR(100),

    -- Performance
    query_duration_ms INTEGER,              -- Query execution time

    -- Metadata
    metadata JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX idx_data_access_log_tenant_id ON data_access_log(tenant_id);
CREATE INDEX idx_data_access_log_user_id ON data_access_log(user_id);
CREATE INDEX idx_data_access_log_resource_type ON data_access_log(resource_type);
CREATE INDEX idx_data_access_log_accessed_at ON data_access_log(accessed_at DESC);

-- Comments
COMMENT ON TABLE data_access_log IS 'Track sensitive data access for compliance';


-- ============================================================================
-- 4. Configuration Changes Log
-- ============================================================================

CREATE TABLE IF NOT EXISTS config_changes_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Who made the change
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    user_email VARCHAR(255),

    -- What changed
    config_type VARCHAR(100) NOT NULL,      -- system, tenant, user
    config_key VARCHAR(255) NOT NULL,
    old_value TEXT,
    new_value TEXT,

    -- Why
    change_reason TEXT,

    -- When
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Approval (for critical changes)
    requires_approval BOOLEAN DEFAULT FALSE,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    metadata JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX idx_config_changes_tenant_id ON config_changes_log(tenant_id);
CREATE INDEX idx_config_changes_user_id ON config_changes_log(user_id);
CREATE INDEX idx_config_changes_config_type ON config_changes_log(config_type);
CREATE INDEX idx_config_changes_changed_at ON config_changes_log(changed_at DESC);

-- Comments
COMMENT ON TABLE config_changes_log IS 'Track all configuration changes';


-- ============================================================================
-- 5. Helper Functions
-- ============================================================================

-- Function to compute hash for audit log entry
CREATE OR REPLACE FUNCTION compute_audit_hash(
    p_id UUID,
    p_tenant_id UUID,
    p_user_id UUID,
    p_action VARCHAR,
    p_resource_type VARCHAR,
    p_created_at TIMESTAMP WITH TIME ZONE,
    p_previous_hash VARCHAR
) RETURNS VARCHAR AS $$
BEGIN
    RETURN encode(
        digest(
            p_id::text || p_tenant_id::text || coalesce(p_user_id::text, '') ||
            p_action || p_resource_type || p_created_at::text || coalesce(p_previous_hash, ''),
            'sha256'
        ),
        'hex'
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to create audit log entry
CREATE OR REPLACE FUNCTION create_audit_log(
    p_tenant_id UUID,
    p_user_id UUID,
    p_user_email VARCHAR,
    p_action VARCHAR,
    p_resource_type VARCHAR,
    p_resource_id VARCHAR DEFAULT NULL,
    p_resource_name VARCHAR DEFAULT NULL,
    p_old_values JSONB DEFAULT NULL,
    p_new_values JSONB DEFAULT NULL,
    p_status VARCHAR DEFAULT 'success',
    p_severity VARCHAR DEFAULT 'info',
    p_ip_address INET DEFAULT NULL,
    p_additional_data JSONB DEFAULT '{}'
) RETURNS UUID AS $$
DECLARE
    v_id UUID;
    v_previous_hash VARCHAR;
    v_record_hash VARCHAR;
    v_changes JSONB;
BEGIN
    v_id := gen_random_uuid();

    -- Get previous hash
    SELECT record_hash INTO v_previous_hash
    FROM audit_log
    WHERE tenant_id = p_tenant_id
    ORDER BY created_at DESC
    LIMIT 1;

    -- Compute changes (diff between old and new)
    IF p_old_values IS NOT NULL AND p_new_values IS NOT NULL THEN
        SELECT jsonb_object_agg(key, value)
        INTO v_changes
        FROM (
            SELECT key, new.value
            FROM jsonb_each(p_new_values) AS new
            LEFT JOIN jsonb_each(p_old_values) AS old ON new.key = old.key
            WHERE old.value IS DISTINCT FROM new.value
        ) AS changes;
    END IF;

    -- Compute this record's hash
    v_record_hash := compute_audit_hash(
        v_id,
        p_tenant_id,
        p_user_id,
        p_action,
        p_resource_type,
        NOW(),
        v_previous_hash
    );

    -- Insert audit log entry
    INSERT INTO audit_log (
        id, tenant_id, user_id, user_email,
        action, resource_type, resource_id, resource_name,
        old_values, new_values, changes,
        status, severity,
        ip_address,
        additional_data,
        previous_hash, record_hash
    ) VALUES (
        v_id, p_tenant_id, p_user_id, p_user_email,
        p_action, p_resource_type, p_resource_id, p_resource_name,
        p_old_values, p_new_values, v_changes,
        p_status, p_severity,
        p_ip_address,
        p_additional_data,
        v_previous_hash, v_record_hash
    );

    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

-- Function to verify audit log integrity (check hash chain)
CREATE OR REPLACE FUNCTION verify_audit_log_integrity(p_tenant_id UUID)
RETURNS TABLE(
    is_valid BOOLEAN,
    total_records BIGINT,
    invalid_records BIGINT,
    first_invalid_id UUID
) AS $$
DECLARE
    v_total_records BIGINT;
    v_invalid_records BIGINT;
    v_first_invalid_id UUID;
BEGIN
    -- Count total records
    SELECT COUNT(*) INTO v_total_records
    FROM audit_log
    WHERE tenant_id = p_tenant_id;

    -- Find invalid records (where computed hash doesn't match stored hash)
    WITH hash_check AS (
        SELECT
            id,
            compute_audit_hash(
                id, tenant_id, user_id, action, resource_type, created_at, previous_hash
            ) AS computed_hash,
            record_hash,
            created_at
        FROM audit_log
        WHERE tenant_id = p_tenant_id
    )
    SELECT COUNT(*), MIN(id)
    INTO v_invalid_records, v_first_invalid_id
    FROM hash_check
    WHERE computed_hash != record_hash;

    RETURN QUERY SELECT
        (v_invalid_records = 0),
        v_total_records,
        v_invalid_records,
        v_first_invalid_id;
END;
$$ LANGUAGE plpgsql;

-- Function to search audit log
CREATE OR REPLACE FUNCTION search_audit_log(
    p_tenant_id UUID,
    p_search_text TEXT,
    p_limit INTEGER DEFAULT 100
) RETURNS TABLE(
    id UUID,
    user_email VARCHAR,
    action VARCHAR,
    resource_type VARCHAR,
    resource_name VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id,
        a.user_email,
        a.action,
        a.resource_type,
        a.resource_name,
        a.created_at,
        ts_rank(
            to_tsvector('english',
                coalesce(a.action, '') || ' ' ||
                coalesce(a.resource_type, '') || ' ' ||
                coalesce(a.resource_name, '') || ' ' ||
                coalesce(a.user_email, '')
            ),
            plainto_tsquery('english', p_search_text)
        ) AS rank
    FROM audit_log a
    WHERE a.tenant_id = p_tenant_id
    AND to_tsvector('english',
            coalesce(a.action, '') || ' ' ||
            coalesce(a.resource_type, '') || ' ' ||
            coalesce(a.resource_name, '') || ' ' ||
            coalesce(a.user_email, '')
        ) @@ plainto_tsquery('english', p_search_text)
    ORDER BY rank DESC, a.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to get user activity summary
CREATE OR REPLACE FUNCTION get_user_activity_summary(
    p_user_id UUID,
    p_days INTEGER DEFAULT 30
) RETURNS TABLE(
    total_actions BIGINT,
    successful_actions BIGINT,
    failed_actions BIGINT,
    most_common_action VARCHAR,
    last_activity TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) AS total_actions,
        COUNT(*) FILTER (WHERE status = 'success') AS successful_actions,
        COUNT(*) FILTER (WHERE status != 'success') AS failed_actions,
        (
            SELECT action
            FROM audit_log
            WHERE user_id = p_user_id
            AND created_at > NOW() - (p_days || ' days')::INTERVAL
            GROUP BY action
            ORDER BY COUNT(*) DESC
            LIMIT 1
        ) AS most_common_action,
        MAX(created_at) AS last_activity
    FROM audit_log
    WHERE user_id = p_user_id
    AND created_at > NOW() - (p_days || ' days')::INTERVAL;
END;
$$ LANGUAGE plpgsql;

-- Function to detect suspicious activity
CREATE OR REPLACE FUNCTION detect_suspicious_activity(p_tenant_id UUID)
RETURNS TABLE(
    user_id UUID,
    user_email VARCHAR,
    issue_type VARCHAR,
    issue_description TEXT,
    occurrences BIGINT,
    last_occurrence TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    -- Multiple failed logins from same IP
    RETURN QUERY
    SELECT
        la.user_id,
        la.email,
        'failed_logins'::VARCHAR,
        'Multiple failed login attempts from ' || la.ip_address::text,
        COUNT(*),
        MAX(la.attempted_at)
    FROM login_attempts la
    WHERE la.tenant_id = p_tenant_id
    AND la.success = FALSE
    AND la.attempted_at > NOW() - INTERVAL '1 hour'
    GROUP BY la.user_id, la.email, la.ip_address
    HAVING COUNT(*) >= 5;

    -- Unusual data access patterns
    RETURN QUERY
    SELECT
        dal.user_id,
        dal.user_email,
        'high_volume_access'::VARCHAR,
        'Unusually high data access: ' || SUM(dal.record_count)::text || ' records',
        COUNT(*),
        MAX(dal.accessed_at)
    FROM data_access_log dal
    WHERE dal.tenant_id = p_tenant_id
    AND dal.accessed_at > NOW() - INTERVAL '1 hour'
    GROUP BY dal.user_id, dal.user_email
    HAVING SUM(dal.record_count) > 10000;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 6. Retention Policy (Cleanup old logs)
-- ============================================================================

-- Function to clean old audit logs (call from cron)
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs(p_retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    DELETE FROM audit_log
    WHERE created_at < NOW() - (p_retention_days || ' days')::INTERVAL;

    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to clean old login attempts
CREATE OR REPLACE FUNCTION cleanup_old_login_attempts(p_retention_days INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    DELETE FROM login_attempts
    WHERE attempted_at < NOW() - (p_retention_days || ' days')::INTERVAL;

    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 7. Row Level Security
-- ============================================================================

ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY audit_log_isolation_policy ON audit_log
    FOR SELECT
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Audit log is append-only (no updates or deletes via RLS)
CREATE POLICY audit_log_append_only ON audit_log
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);


-- ============================================================================
-- 8. Verification Queries
-- ============================================================================

-- Create sample audit log entry
-- SELECT create_audit_log(
--     '00000000-0000-0000-0000-000000000000'::uuid,  -- tenant_id
--     NULL,                                           -- user_id
--     'test@example.com',                            -- user_email
--     'create',                                       -- action
--     'budget',                                       -- resource_type
--     'budget-123',                                   -- resource_id
--     'Q2 Budget',                                    -- resource_name
--     NULL,                                           -- old_values
--     '{"amount": 10000, "period": "quarterly"}'::jsonb,  -- new_values
--     'success',                                      -- status
--     'info'                                          -- severity
-- );

-- Verify audit log integrity
-- SELECT * FROM verify_audit_log_integrity('00000000-0000-0000-0000-000000000000');

-- Search audit logs
-- SELECT * FROM search_audit_log('00000000-0000-0000-0000-000000000000', 'budget create');

-- Get user activity
-- SELECT * FROM get_user_activity_summary('user-uuid-here', 30);

-- Detect suspicious activity
-- SELECT * FROM detect_suspicious_activity('00000000-0000-0000-0000-000000000000');


-- Migration complete!
COMMENT ON SCHEMA public IS 'Audit logging schema version 007 - 2026-05-02';
