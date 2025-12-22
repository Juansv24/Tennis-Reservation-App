-- =====================================================
-- CREATE ADMIN_USERS TABLE
-- Required for Admin App authentication
-- =====================================================

CREATE TABLE IF NOT EXISTS admin_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users(username);
CREATE INDEX IF NOT EXISTS idx_admin_users_is_active ON admin_users(is_active);

-- Add comments
COMMENT ON TABLE admin_users IS 'Admin users for the Admin App authentication';
COMMENT ON COLUMN admin_users.password_hash IS 'SHA256 hash of password + salt';
COMMENT ON COLUMN admin_users.salt IS 'Unique salt for password hashing';

-- Verification
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'admin_users'
ORDER BY ordinal_position;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '===========================================';
    RAISE NOTICE '✅ admin_users TABLE CREATED';
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '  1. Configure admin credentials in Streamlit secrets';
    RAISE NOTICE '  2. Restart the Admin App';
    RAISE NOTICE '  3. Admin user will be auto-created on first run';
    RAISE NOTICE '===========================================';
END $$;
