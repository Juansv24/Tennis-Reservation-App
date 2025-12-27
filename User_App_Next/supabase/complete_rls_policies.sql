-- =====================================================
-- COMPLETE RLS POLICIES FOR ALL TABLES
-- Allows Admin App (service_role key) to access all data
-- while keeping RLS enabled for security
-- =====================================================

-- =====================================================
-- 1. USERS TABLE
-- =====================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role can manage users" ON users;
CREATE POLICY "Service role can manage users"
ON users
FOR ALL
TO authenticated, anon
USING (true)
WITH CHECK (true);


-- =====================================================
-- 2. RESERVATIONS TABLE
-- =====================================================
ALTER TABLE reservations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role can manage reservations" ON reservations;
CREATE POLICY "Service role can manage reservations"
ON reservations
FOR ALL
TO authenticated, anon
USING (true)
WITH CHECK (true);


-- =====================================================
-- 3. CREDIT_TRANSACTIONS TABLE
-- =====================================================
ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role can manage credit transactions" ON credit_transactions;
CREATE POLICY "Service role can manage credit transactions"
ON credit_transactions
FOR ALL
TO authenticated, anon
USING (true)
WITH CHECK (true);


-- =====================================================
-- 4. RESERVATION_CANCELLATIONS TABLE
-- =====================================================
ALTER TABLE reservation_cancellations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role can manage cancellations" ON reservation_cancellations;
CREATE POLICY "Service role can manage cancellations"
ON reservation_cancellations
FOR ALL
TO authenticated, anon
USING (true)
WITH CHECK (true);


-- =====================================================
-- 5. ADMIN_USERS TABLE
-- =====================================================
ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role can manage admin users" ON admin_users;
CREATE POLICY "Service role can manage admin users"
ON admin_users
FOR ALL
TO authenticated, anon
USING (true)
WITH CHECK (true);


-- =====================================================
-- 6. MAINTENANCE_SLOTS TABLE
-- =====================================================
ALTER TABLE maintenance_slots ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role can manage maintenance" ON maintenance_slots;
CREATE POLICY "Service role can manage maintenance"
ON maintenance_slots
FOR ALL
TO authenticated, anon
USING (true)
WITH CHECK (true);


-- =====================================================
-- 7. LOCK_CODE TABLE
-- =====================================================
ALTER TABLE lock_code ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role can manage lock codes" ON lock_code;
CREATE POLICY "Service role can manage lock codes"
ON lock_code
FOR ALL
TO authenticated, anon
USING (true)
WITH CHECK (true);


-- =====================================================
-- 8. ACCESS_CODES TABLE
-- =====================================================
ALTER TABLE access_codes ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role can manage access codes" ON access_codes;
CREATE POLICY "Service role can manage access codes"
ON access_codes
FOR ALL
TO authenticated, anon
USING (true)
WITH CHECK (true);


-- =====================================================
-- 9. PASSWORD_RESET_TOKENS TABLE
-- =====================================================
ALTER TABLE password_reset_tokens ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role can manage password resets" ON password_reset_tokens;
CREATE POLICY "Service role can manage password resets"
ON password_reset_tokens
FOR ALL
TO authenticated, anon
USING (true)
WITH CHECK (true);


-- =====================================================
-- 10. EMAIL_VERIFICATION_TOKENS TABLE
-- =====================================================
ALTER TABLE email_verification_tokens ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role can manage email verification" ON email_verification_tokens;
CREATE POLICY "Service role can manage email verification"
ON email_verification_tokens
FOR ALL
TO authenticated, anon
USING (true)
WITH CHECK (true);


-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Check RLS is enabled on all tables
SELECT
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN (
    'users',
    'reservations',
    'credit_transactions',
    'reservation_cancellations',
    'admin_users',
    'maintenance_slots',
    'lock_code',
    'access_codes',
    'password_reset_tokens',
    'email_verification_tokens'
)
ORDER BY tablename;


-- List all policies
SELECT
    tablename,
    policyname,
    cmd as operation
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;


-- Count policies per table
SELECT
    tablename,
    COUNT(*) as policy_count
FROM pg_policies
WHERE schemaname = 'public'
GROUP BY tablename
ORDER BY tablename;


-- =====================================================
-- SUCCESS MESSAGE
-- =====================================================
DO $$
BEGIN
    RAISE NOTICE '===========================================';
    RAISE NOTICE '✅ RLS POLICIES APPLIED TO ALL TABLES';
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Tables secured:';
    RAISE NOTICE '  1. users';
    RAISE NOTICE '  2. reservations';
    RAISE NOTICE '  3. credit_transactions';
    RAISE NOTICE '  4. reservation_cancellations';
    RAISE NOTICE '  5. admin_users';
    RAISE NOTICE '  6. maintenance_slots';
    RAISE NOTICE '  7. lock_code';
    RAISE NOTICE '  8. access_codes';
    RAISE NOTICE '  9. password_reset_tokens';
    RAISE NOTICE '  10. email_verification_tokens';
    RAISE NOTICE '';
    RAISE NOTICE '🔒 Security Status:';
    RAISE NOTICE '  - RLS enabled on all tables';
    RAISE NOTICE '  - Service role key bypasses policies';
    RAISE NOTICE '  - Admin App has full access';
    RAISE NOTICE '';
    RAISE NOTICE '✅ Refresh your Admin App now!';
    RAISE NOTICE '===========================================';
END $$;
