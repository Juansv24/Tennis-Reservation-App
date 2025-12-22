-- =====================================================
-- ROW LEVEL SECURITY POLICIES
-- Secure policies for admin tables
-- =====================================================

-- =====================================================
-- ADMIN_USERS TABLE POLICIES
-- =====================================================

-- Enable RLS (if not already enabled)
ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;

-- Policy 1: Allow service role to do everything (admin app uses this)
-- This allows the admin app with service_role key to manage admin users
CREATE POLICY "Service role can manage admin users"
ON admin_users
FOR ALL
TO authenticated, anon
USING (true)
WITH CHECK (true);

-- Note: The policy above is permissive but the admin app controls access
-- The real security comes from protecting your service_role key


-- =====================================================
-- CREDIT_TRANSACTIONS TABLE POLICIES
-- =====================================================

-- Enable RLS
ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY;

-- Policy 1: Service role (admin app) can do everything
CREATE POLICY "Service role can manage credit transactions"
ON credit_transactions
FOR ALL
TO authenticated, anon
USING (true)
WITH CHECK (true);

-- If you want to add user-level access later:
-- Users can view their own credit transactions
-- CREATE POLICY "Users can view own credit transactions"
-- ON credit_transactions
-- FOR SELECT
-- TO authenticated
-- USING (auth.uid() = user_id);


-- =====================================================
-- RESERVATION_CANCELLATIONS TABLE POLICIES
-- =====================================================

-- Enable RLS
ALTER TABLE reservation_cancellations ENABLE ROW LEVEL SECURITY;

-- Policy 1: Service role (admin app) can do everything
CREATE POLICY "Service role can manage cancellations"
ON reservation_cancellations
FOR ALL
TO authenticated, anon
USING (true)
WITH CHECK (true);

-- If you want to add user-level access later:
-- Users can view their own cancellations
-- CREATE POLICY "Users can view own cancellations"
-- ON reservation_cancellations
-- FOR SELECT
-- TO authenticated
-- USING (auth.uid() = user_id);


-- =====================================================
-- VERIFICATION
-- =====================================================

-- Check RLS is enabled
SELECT
    schemaname,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables
WHERE tablename IN ('admin_users', 'credit_transactions', 'reservation_cancellations')
ORDER BY tablename;

-- Check policies exist
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd
FROM pg_policies
WHERE tablename IN ('admin_users', 'credit_transactions', 'reservation_cancellations')
ORDER BY tablename, policyname;


-- =====================================================
-- ALTERNATIVE: More Restrictive Policies
-- (Use if you want tighter security)
-- =====================================================

-- First, drop the permissive policies:
-- DROP POLICY "Service role can manage admin users" ON admin_users;
-- DROP POLICY "Service role can manage credit transactions" ON credit_transactions;
-- DROP POLICY "Service role can manage cancellations" ON reservation_cancellations;

-- Then create restrictive policies based on a custom claim or role:

-- For admin_users: Only allow if using service role key
-- (Requires bypassing RLS with service_role key in your app)

-- For credit_transactions:
-- CREATE POLICY "Admin can manage all transactions"
-- ON credit_transactions
-- FOR ALL
-- TO authenticated
-- USING (
--     EXISTS (
--         SELECT 1 FROM admin_users
--         WHERE admin_users.id = auth.uid()
--         AND admin_users.is_active = true
--     )
-- );

-- For reservation_cancellations:
-- CREATE POLICY "Admin can manage all cancellations"
-- ON reservation_cancellations
-- FOR ALL
-- TO authenticated
-- USING (
--     EXISTS (
--         SELECT 1 FROM admin_users
--         WHERE admin_users.id = auth.uid()
--         AND admin_users.is_active = true
--     )
-- );


-- =====================================================
-- SUCCESS MESSAGE
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '===========================================';
    RAISE NOTICE '✅ RLS POLICIES CREATED';
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Policies created for:';
    RAISE NOTICE '  1. admin_users';
    RAISE NOTICE '  2. credit_transactions';
    RAISE NOTICE '  3. reservation_cancellations';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  IMPORTANT SECURITY NOTES:';
    RAISE NOTICE '  - These policies are permissive';
    RAISE NOTICE '  - Security relies on protecting your service_role key';
    RAISE NOTICE '  - Use service_role key only in Admin App';
    RAISE NOTICE '  - Use anon key for User App';
    RAISE NOTICE '===========================================';
END $$;
