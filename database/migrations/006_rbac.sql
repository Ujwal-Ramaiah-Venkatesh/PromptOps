-- Role-Based Access Control (RBAC) Schema
-- =========================================
--
-- Adds RBAC and permissions management
-- Phase 5B - Enterprise Features
--
-- Author: PromptOps Team
-- Date: 2026-05-02

-- ============================================================================
-- 1. Permissions Table (Catalog of all available permissions)
-- ============================================================================

CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Permission definition
    name VARCHAR(100) NOT NULL UNIQUE,
    resource VARCHAR(100) NOT NULL,  -- costs, resources, budgets, etc.
    action VARCHAR(50) NOT NULL,     -- read, write, delete, execute
    description TEXT,

    -- Grouping
    category VARCHAR(50),  -- data, management, administration

    -- Metadata
    is_dangerous BOOLEAN DEFAULT FALSE,  -- Requires extra confirmation
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_permissions_resource ON permissions(resource);
CREATE INDEX idx_permissions_action ON permissions(action);
CREATE INDEX idx_permissions_category ON permissions(category);

-- Comments
COMMENT ON TABLE permissions IS 'Catalog of all available permissions';
COMMENT ON COLUMN permissions.is_dangerous IS 'Dangerous permissions (delete, reset, etc.)';


-- ============================================================================
-- 2. Insert Standard Permissions
-- ============================================================================

-- Data Access Permissions
INSERT INTO permissions (name, resource, action, category, description) VALUES
('read:costs', 'costs', 'read', 'data', 'View cost data'),
('write:costs', 'costs', 'write', 'data', 'Edit cost data'),
('delete:costs', 'costs', 'delete', 'data', 'Delete cost data'),

('read:resources', 'resources', 'read', 'data', 'View cloud resources'),
('write:resources', 'resources', 'write', 'data', 'Edit resource metadata'),
('delete:resources', 'resources', 'delete', 'data', 'Delete resource records'),

('read:budgets', 'budgets', 'read', 'data', 'View budgets'),
('write:budgets', 'budgets', 'write', 'data', 'Create and edit budgets'),
('delete:budgets', 'budgets', 'delete', 'data', 'Delete budgets'),

('read:alerts', 'alerts', 'read', 'data', 'View alerts'),
('write:alerts', 'alerts', 'write', 'data', 'Configure alerts'),
('delete:alerts', 'alerts', 'delete', 'data', 'Delete alerts'),

('read:dashboards', 'dashboards', 'read', 'data', 'View dashboards'),
('write:dashboards', 'dashboards', 'write', 'data', 'Create custom dashboards'),

('read:reports', 'reports', 'read', 'data', 'View reports'),
('execute:reports', 'reports', 'execute', 'data', 'Generate reports')

ON CONFLICT (name) DO NOTHING;

-- Operational Permissions
INSERT INTO permissions (name, resource, action, category, description) VALUES
('execute:scans', 'scans', 'execute', 'operations', 'Run cloud resource scans'),
('execute:discovery', 'discovery', 'execute', 'operations', 'Run discovery scans'),
('execute:optimization', 'optimization', 'execute', 'operations', 'Run optimization scans'),

('approve:optimizations', 'optimization', 'approve', 'operations', 'Approve optimization recommendations'),
('execute:rightsizing', 'rightsizing', 'execute', 'operations', 'Execute right-sizing changes'),
('execute:shutdown', 'resources', 'execute', 'operations', 'Shutdown resources')

ON CONFLICT (name) DO NOTHING;

-- Management Permissions
INSERT INTO permissions (name, resource, action, category, description) VALUES
('read:users', 'users', 'read', 'management', 'View users'),
('write:users', 'users', 'write', 'management', 'Create and edit users'),
('delete:users', 'users', 'delete', 'management', 'Delete users'),

('read:roles', 'roles', 'read', 'management', 'View roles'),
('write:roles', 'roles', 'write', 'management', 'Create and edit roles'),
('delete:roles', 'roles', 'delete', 'management', 'Delete roles'),

('read:permissions', 'permissions', 'read', 'management', 'View permissions'),
('assign:roles', 'roles', 'assign', 'management', 'Assign roles to users')

ON CONFLICT (name) DO NOTHING;

-- Administration Permissions
INSERT INTO permissions (name, resource, action, category, description, is_dangerous) VALUES
('read:audit_log', 'audit', 'read', 'administration', 'View audit logs', FALSE),
('read:settings', 'settings', 'read', 'administration', 'View system settings', FALSE),
('write:settings', 'settings', 'write', 'administration', 'Modify system settings', TRUE),

('manage:cloud_accounts', 'cloud_accounts', 'manage', 'administration', 'Add/remove cloud accounts', TRUE),
('manage:integrations', 'integrations', 'manage', 'administration', 'Manage integrations', FALSE),

('admin:system', 'system', 'admin', 'administration', 'Full system administration', TRUE),
('admin:tenant', 'tenant', 'admin', 'administration', 'Tenant administration', TRUE)

ON CONFLICT (name) DO NOTHING;

-- Wildcard permission (superuser)
INSERT INTO permissions (name, resource, action, category, description, is_dangerous) VALUES
('*', 'all', 'all', 'administration', 'All permissions (superuser)', TRUE)
ON CONFLICT (name) DO NOTHING;


-- ============================================================================
-- 3. API Keys Table (For programmatic access)
-- ============================================================================

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- Key details
    name VARCHAR(200) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,  -- bcrypt hash of the key
    key_prefix VARCHAR(20) NOT NULL,        -- First 8 chars for identification

    -- Permissions (can be subset of user's permissions)
    permissions JSONB DEFAULT '[]',

    -- Status
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'revoked')),
    last_used_at TIMESTAMP WITH TIME ZONE,
    last_used_ip INET,

    -- Expiration
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_by UUID REFERENCES users(id),

    -- Metadata
    metadata JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX idx_api_keys_tenant_id ON api_keys(tenant_id);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_status ON api_keys(status);
CREATE INDEX idx_api_keys_expires_at ON api_keys(expires_at);

-- Comments
COMMENT ON TABLE api_keys IS 'API keys for programmatic access';
COMMENT ON COLUMN api_keys.key_hash IS 'bcrypt hash of the API key';
COMMENT ON COLUMN api_keys.key_prefix IS 'First 8 characters for identification';


-- ============================================================================
-- 4. Sessions Table (For web sessions)
-- ============================================================================

CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Session details
    session_token VARCHAR(255) NOT NULL UNIQUE,
    refresh_token VARCHAR(255),

    -- Client info
    ip_address INET,
    user_agent TEXT,
    device_type VARCHAR(50),  -- desktop, mobile, tablet

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Metadata
    metadata JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_tenant_id ON sessions(tenant_id);
CREATE INDEX idx_sessions_session_token ON sessions(session_token);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX idx_sessions_last_activity_at ON sessions(last_activity_at);

-- Comments
COMMENT ON TABLE sessions IS 'User web sessions';


-- ============================================================================
-- 5. Permission Checks Table (For caching permission checks)
-- ============================================================================

CREATE TABLE IF NOT EXISTS permission_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permission VARCHAR(100) NOT NULL,

    -- Cache result
    has_permission BOOLEAN NOT NULL,
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- TTL (cache invalidation)
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '5 minutes',

    UNIQUE(user_id, permission)
);

-- Indexes
CREATE INDEX idx_permission_cache_user_id ON permission_cache(user_id);
CREATE INDEX idx_permission_cache_expires_at ON permission_cache(expires_at);

-- Comments
COMMENT ON TABLE permission_cache IS 'Cached permission check results (5 minute TTL)';


-- ============================================================================
-- 6. Helper Functions
-- ============================================================================

-- Function to check permission (with wildcard support)
CREATE OR REPLACE FUNCTION check_permission(user_uuid UUID, permission_name VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    has_perm BOOLEAN;
    resource_part VARCHAR;
    action_part VARCHAR;
BEGIN
    -- Check cache first
    SELECT has_permission INTO has_perm
    FROM permission_cache
    WHERE user_id = user_uuid
    AND permission = permission_name
    AND expires_at > NOW();

    IF FOUND THEN
        RETURN has_perm;
    END IF;

    -- Check for wildcard permission (*)
    SELECT EXISTS (
        SELECT 1
        FROM user_roles ur
        JOIN roles r ON ur.role_id = r.id
        WHERE ur.user_id = user_uuid
        AND r.permissions @> '["*"]'::jsonb
        AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
    ) INTO has_perm;

    IF has_perm THEN
        -- Cache result
        INSERT INTO permission_cache (user_id, permission, has_permission)
        VALUES (user_uuid, permission_name, TRUE)
        ON CONFLICT (user_id, permission) DO UPDATE
        SET has_permission = TRUE, computed_at = NOW(), expires_at = NOW() + INTERVAL '5 minutes';

        RETURN TRUE;
    END IF;

    -- Check for exact permission match
    SELECT EXISTS (
        SELECT 1
        FROM user_roles ur
        JOIN roles r ON ur.role_id = r.id
        WHERE ur.user_id = user_uuid
        AND r.permissions @> jsonb_build_array(permission_name)
        AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
    ) INTO has_perm;

    IF has_perm THEN
        -- Cache result
        INSERT INTO permission_cache (user_id, permission, has_permission)
        VALUES (user_uuid, permission_name, TRUE)
        ON CONFLICT (user_id, permission) DO UPDATE
        SET has_permission = TRUE, computed_at = NOW(), expires_at = NOW() + INTERVAL '5 minutes';

        RETURN TRUE;
    END IF;

    -- Check for wildcard resource (e.g., "read:*")
    resource_part := split_part(permission_name, ':', 1);
    SELECT EXISTS (
        SELECT 1
        FROM user_roles ur
        JOIN roles r ON ur.role_id = r.id
        WHERE ur.user_id = user_uuid
        AND r.permissions @> jsonb_build_array(resource_part || ':*')
        AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
    ) INTO has_perm;

    IF has_perm THEN
        -- Cache result
        INSERT INTO permission_cache (user_id, permission, has_permission)
        VALUES (user_uuid, permission_name, TRUE)
        ON CONFLICT (user_id, permission) DO UPDATE
        SET has_permission = TRUE, computed_at = NOW(), expires_at = NOW() + INTERVAL '5 minutes';

        RETURN TRUE;
    END IF;

    -- Cache negative result
    INSERT INTO permission_cache (user_id, permission, has_permission)
    VALUES (user_uuid, permission_name, FALSE)
    ON CONFLICT (user_id, permission) DO UPDATE
    SET has_permission = FALSE, computed_at = NOW(), expires_at = NOW() + INTERVAL '5 minutes';

    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Function to invalidate permission cache for a user
CREATE OR REPLACE FUNCTION invalidate_permission_cache(user_uuid UUID)
RETURNS VOID AS $$
BEGIN
    DELETE FROM permission_cache WHERE user_id = user_uuid;
END;
$$ LANGUAGE plpgsql;

-- Function to get all user permissions (expanded)
CREATE OR REPLACE FUNCTION get_user_permissions(user_uuid UUID)
RETURNS TABLE(permission VARCHAR) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT jsonb_array_elements_text(r.permissions)::VARCHAR
    FROM user_roles ur
    JOIN roles r ON ur.role_id = r.id
    WHERE ur.user_id = user_uuid
    AND (ur.expires_at IS NULL OR ur.expires_at > NOW());
END;
$$ LANGUAGE plpgsql;

-- Function to check if user is admin
CREATE OR REPLACE FUNCTION is_admin(user_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN check_permission(user_uuid, '*');
END;
$$ LANGUAGE plpgsql;

-- Function to clean expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM sessions WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to clean expired permission cache
CREATE OR REPLACE FUNCTION cleanup_permission_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM permission_cache WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 7. Triggers
-- ============================================================================

-- Invalidate permission cache when roles change
CREATE OR REPLACE FUNCTION trigger_invalidate_permission_cache()
RETURNS TRIGGER AS $$
BEGIN
    -- Invalidate cache for affected users
    IF TG_OP = 'DELETE' THEN
        PERFORM invalidate_permission_cache(OLD.user_id);
    ELSE
        PERFORM invalidate_permission_cache(NEW.user_id);
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER invalidate_cache_on_role_change
    AFTER INSERT OR UPDATE OR DELETE ON user_roles
    FOR EACH ROW
    EXECUTE FUNCTION trigger_invalidate_permission_cache();

-- Update last_activity_at on session access
CREATE OR REPLACE FUNCTION update_session_activity()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_activity_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_session_last_activity
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    WHEN (OLD.last_activity_at IS DISTINCT FROM NEW.last_activity_at)
    EXECUTE FUNCTION update_session_activity();


-- ============================================================================
-- 8. Scheduled Cleanup Jobs (Call these from cron or background worker)
-- ============================================================================

-- Clean up expired sessions (run daily)
-- SELECT cleanup_expired_sessions();

-- Clean up expired permission cache (run hourly)
-- SELECT cleanup_permission_cache();


-- ============================================================================
-- 9. Row Level Security for API Keys
-- ============================================================================

ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY api_key_isolation_policy ON api_keys
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);


-- ============================================================================
-- 10. Verification Queries
-- ============================================================================

-- List all permissions
-- SELECT * FROM permissions ORDER BY category, resource, action;

-- Get user's permissions
-- SELECT * FROM get_user_permissions('user-uuid-here');

-- Check specific permission
-- SELECT check_permission('user-uuid-here', 'read:costs');

-- Check if user is admin
-- SELECT is_admin('user-uuid-here');

-- List active sessions
-- SELECT u.email, s.ip_address, s.created_at, s.expires_at
-- FROM sessions s
-- JOIN users u ON s.user_id = u.id
-- WHERE s.expires_at > NOW();


-- Migration complete!
COMMENT ON SCHEMA public IS 'RBAC schema version 006 - 2026-05-02';
