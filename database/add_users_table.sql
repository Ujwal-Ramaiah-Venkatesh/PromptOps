-- Add users table for authentication
-- Week 13: Security Fixes - Authentication System

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'pm',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login TIMESTAMPTZ,

    CONSTRAINT valid_role CHECK (role IN ('viewer', 'pm', 'engineer', 'lead', 'admin'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- Insert default admin user (password: admin123 - CHANGE THIS!)
-- Password hash for 'admin123'
INSERT INTO users (id, email, hashed_password, full_name, role, is_active)
VALUES (
    'admin-default-001',
    'admin@promptops.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7eU9gS7EVW',
    'System Administrator',
    'admin',
    TRUE
)
ON CONFLICT (email) DO NOTHING;

-- Insert test PM user (password: pm123)
INSERT INTO users (id, email, hashed_password, full_name, role, is_active)
VALUES (
    'pm-test-001',
    'pm@promptops.com',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'Product Manager',
    'pm',
    TRUE
)
ON CONFLICT (email) DO NOTHING;

-- Comments
COMMENT ON TABLE users IS 'User accounts for authentication and authorization';
COMMENT ON COLUMN users.role IS 'User role: viewer, pm, engineer, lead, or admin';
COMMENT ON COLUMN users.is_active IS 'Whether user account is active (soft delete)';
COMMENT ON COLUMN users.last_login IS 'Timestamp of last successful login';
