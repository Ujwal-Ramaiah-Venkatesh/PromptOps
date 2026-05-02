-- Multi-Tenancy Database Schema
-- ==============================
--
-- Adds multi-tenant support to PromptOps
-- Phase 5B - Enterprise Features
--
-- Author: PromptOps Team
-- Date: 2026-05-02

-- ============================================================================
-- 1. Tenants Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,

    -- Billing & Plan
    plan VARCHAR(50) DEFAULT 'free' CHECK (plan IN ('free', 'standard', 'enterprise')),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'cancelled')),

    -- Settings
    settings JSONB DEFAULT '{}',

    -- Limits
    max_users INTEGER DEFAULT 5,
    max_cloud_accounts INTEGER DEFAULT 3,
    max_resources_tracked INTEGER DEFAULT 1000,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    suspended_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    created_by UUID,
    metadata JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_tenants_status ON tenants(status);
CREATE INDEX idx_tenants_plan ON tenants(plan);
CREATE INDEX idx_tenants_created_at ON tenants(created_at);

-- Comments
COMMENT ON TABLE tenants IS 'Multi-tenant organizations';
COMMENT ON COLUMN tenants.slug IS 'URL-safe tenant identifier';
COMMENT ON COLUMN tenants.settings IS 'Tenant-specific configuration (JSON)';
COMMENT ON COLUMN tenants.metadata IS 'Additional tenant metadata';


-- ============================================================================
-- 2. Users Table (Enhanced)
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Authentication
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),  -- Null if SSO-only

    -- Profile
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    display_name VARCHAR(200),
    avatar_url TEXT,

    -- Status
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    email_verified BOOLEAN DEFAULT FALSE,

    -- SSO
    sso_provider VARCHAR(50),  -- google, microsoft, github, saml
    sso_id VARCHAR(255),       -- External user ID

    -- Security
    last_login_at TIMESTAMP WITH TIME ZONE,
    last_login_ip INET,
    password_changed_at TIMESTAMP WITH TIME ZONE,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(255),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Constraints
    UNIQUE(tenant_id, email),
    UNIQUE(sso_provider, sso_id)
);

-- Indexes
CREATE INDEX idx_users_tenant_id ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_sso_provider ON users(sso_provider);
CREATE INDEX idx_users_sso_id ON users(sso_id);
CREATE INDEX idx_users_last_login_at ON users(last_login_at);

-- Comments
COMMENT ON TABLE users IS 'User accounts with multi-tenant support';
COMMENT ON COLUMN users.password_hash IS 'bcrypt hash (null for SSO-only users)';
COMMENT ON COLUMN users.sso_provider IS 'SSO identity provider';


-- ============================================================================
-- 3. Roles Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    name VARCHAR(100) NOT NULL,
    description TEXT,

    -- Built-in roles cannot be deleted
    is_system_role BOOLEAN DEFAULT FALSE,

    -- Permissions (JSON array)
    permissions JSONB DEFAULT '[]',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    UNIQUE(tenant_id, name)
);

-- Indexes
CREATE INDEX idx_roles_tenant_id ON roles(tenant_id);
CREATE INDEX idx_roles_is_system_role ON roles(is_system_role);

-- Comments
COMMENT ON TABLE roles IS 'Role definitions with permissions';
COMMENT ON COLUMN roles.permissions IS 'Array of permission strings';
COMMENT ON COLUMN roles.is_system_role IS 'System roles cannot be deleted';


-- ============================================================================
-- 4. User Roles (Many-to-Many)
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,

    -- Assignment metadata
    assigned_by UUID REFERENCES users(id),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    UNIQUE(user_id, role_id)
);

-- Indexes
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);
CREATE INDEX idx_user_roles_expires_at ON user_roles(expires_at);

-- Comments
COMMENT ON TABLE user_roles IS 'User to role assignments';


-- ============================================================================
-- 5. Add tenant_id to Existing Tables
-- ============================================================================

-- Cloud Accounts
ALTER TABLE cloud_accounts
    ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_cloud_accounts_tenant_id ON cloud_accounts(tenant_id);

-- Resources (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'resources') THEN
        ALTER TABLE resources
            ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
        CREATE INDEX IF NOT EXISTS idx_resources_tenant_id ON resources(tenant_id);
    END IF;
END $$;

-- Cost Data (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'cost_data') THEN
        ALTER TABLE cost_data
            ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
        CREATE INDEX IF NOT EXISTS idx_cost_data_tenant_id ON cost_data(tenant_id);
    END IF;
END $$;

-- Budgets (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'budgets') THEN
        ALTER TABLE budgets
            ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
        CREATE INDEX IF NOT EXISTS idx_budgets_tenant_id ON budgets(tenant_id);
    END IF;
END $$;


-- ============================================================================
-- 6. Insert Default Roles
-- ============================================================================

-- Insert default tenant (for migration of existing data)
INSERT INTO tenants (id, name, slug, plan, status)
VALUES ('00000000-0000-0000-0000-000000000000', 'Default Organization', 'default', 'enterprise', 'active')
ON CONFLICT (slug) DO NOTHING;

-- Admin Role
INSERT INTO roles (tenant_id, name, description, is_system_role, permissions)
SELECT
    '00000000-0000-0000-0000-000000000000',
    'Admin',
    'Full system access',
    TRUE,
    '["*"]'::jsonb
WHERE NOT EXISTS (
    SELECT 1 FROM roles
    WHERE tenant_id = '00000000-0000-0000-0000-000000000000'
    AND name = 'Admin'
);

-- Manager Role
INSERT INTO roles (tenant_id, name, description, is_system_role, permissions)
SELECT
    '00000000-0000-0000-0000-000000000000',
    'Manager',
    'Manage resources and budgets, approve optimizations',
    TRUE,
    '[
        "read:*",
        "write:budgets",
        "write:alerts",
        "execute:scans",
        "approve:optimizations",
        "read:reports"
    ]'::jsonb
WHERE NOT EXISTS (
    SELECT 1 FROM roles
    WHERE tenant_id = '00000000-0000-0000-0000-000000000000'
    AND name = 'Manager'
);

-- Analyst Role
INSERT INTO roles (tenant_id, name, description, is_system_role, permissions)
SELECT
    '00000000-0000-0000-0000-000000000000',
    'Analyst',
    'Read-only access, generate reports',
    TRUE,
    '[
        "read:costs",
        "read:resources",
        "read:budgets",
        "read:alerts",
        "read:reports",
        "execute:reports"
    ]'::jsonb
WHERE NOT EXISTS (
    SELECT 1 FROM roles
    WHERE tenant_id = '00000000-0000-0000-0000-000000000000'
    AND name = 'Analyst'
);

-- Viewer Role
INSERT INTO roles (tenant_id, name, description, is_system_role, permissions)
SELECT
    '00000000-0000-0000-0000-000000000000',
    'Viewer',
    'View-only access to dashboards',
    TRUE,
    '[
        "read:costs",
        "read:resources",
        "read:dashboards"
    ]'::jsonb
WHERE NOT EXISTS (
    SELECT 1 FROM roles
    WHERE tenant_id = '00000000-0000-0000-0000-000000000000'
    AND name = 'Viewer'
);


-- ============================================================================
-- 7. Update existing data to use default tenant
-- ============================================================================

UPDATE cloud_accounts
SET tenant_id = '00000000-0000-0000-0000-000000000000'
WHERE tenant_id IS NULL;


-- ============================================================================
-- 8. Row Level Security (Optional but Recommended)
-- ============================================================================

-- Enable RLS on tenants table
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;

-- Create policy: users can only see their own tenant
CREATE POLICY tenant_isolation_policy ON tenants
    FOR ALL
    USING (id = current_setting('app.current_tenant_id', true)::uuid);

-- Enable RLS on users table
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_isolation_policy ON users
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Enable RLS on roles table
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;

CREATE POLICY role_isolation_policy ON roles
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Note: RLS policies can be bypassed by superusers
-- Application should set current_tenant_id for each request


-- ============================================================================
-- 9. Helper Functions
-- ============================================================================

-- Function to get user's roles
CREATE OR REPLACE FUNCTION get_user_roles(user_uuid UUID)
RETURNS TABLE(role_name VARCHAR, permissions JSONB) AS $$
BEGIN
    RETURN QUERY
    SELECT r.name, r.permissions
    FROM user_roles ur
    JOIN roles r ON ur.role_id = r.id
    WHERE ur.user_id = user_uuid
    AND (ur.expires_at IS NULL OR ur.expires_at > NOW());
END;
$$ LANGUAGE plpgsql;

-- Function to check if user has permission
CREATE OR REPLACE FUNCTION user_has_permission(user_uuid UUID, permission_name VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    has_perm BOOLEAN;
BEGIN
    -- Check if user has wildcard permission
    SELECT EXISTS (
        SELECT 1
        FROM user_roles ur
        JOIN roles r ON ur.role_id = r.id
        WHERE ur.user_id = user_uuid
        AND r.permissions @> '["*"]'::jsonb
        AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
    ) INTO has_perm;

    IF has_perm THEN
        RETURN TRUE;
    END IF;

    -- Check for specific permission
    SELECT EXISTS (
        SELECT 1
        FROM user_roles ur
        JOIN roles r ON ur.role_id = r.id
        WHERE ur.user_id = user_uuid
        AND r.permissions @> jsonb_build_array(permission_name)
        AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
    ) INTO has_perm;

    RETURN has_perm;
END;
$$ LANGUAGE plpgsql;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_tenants_updated_at
    BEFORE UPDATE ON tenants
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_roles_updated_at
    BEFORE UPDATE ON roles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- 10. Verification Queries
-- ============================================================================

-- Check tenants
-- SELECT * FROM tenants;

-- Check roles
-- SELECT t.name as tenant, r.name as role, r.permissions
-- FROM roles r
-- JOIN tenants t ON r.tenant_id = t.id;

-- Check user permissions
-- SELECT * FROM get_user_roles('user-uuid-here');

-- Check if user has permission
-- SELECT user_has_permission('user-uuid-here', 'read:costs');


-- Migration complete!
COMMENT ON SCHEMA public IS 'Multi-tenancy schema version 005 - 2026-05-02';
