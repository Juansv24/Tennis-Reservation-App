-- =====================================================
-- FIX LOCK_CODE TABLE PERMISSIONS
-- =====================================================
-- This script adds the missing INSERT permission policy for lock_code table
-- Replicates the same permissions that access_codes has (which works)
--
-- EXECUTE THIS IN SUPABASE SQL EDITOR
-- =====================================================

-- First, drop existing policies to start fresh
DROP POLICY IF EXISTS "Authenticated users can view lock code" ON public.lock_code;
DROP POLICY IF EXISTS "Service role can manage lock codes" ON public.lock_code;

-- Create comprehensive policy that allows ALL operations
-- This matches the access_codes table permissions
CREATE POLICY "Service role can manage lock codes"
ON public.lock_code
FOR ALL
TO authenticated, anon
USING (true)
WITH CHECK (true);

-- Verify the policy was created
SELECT
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE tablename = 'lock_code';

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Lock code permissions updated successfully!';
    RAISE NOTICE '';
    RAISE NOTICE 'Policy created:';
    RAISE NOTICE '  - Table: lock_code';
    RAISE NOTICE '  - Policy: Service role can manage lock codes';
    RAISE NOTICE '  - Scope: ALL (SELECT, INSERT, UPDATE, DELETE)';
    RAISE NOTICE '  - Roles: authenticated, anon';
    RAISE NOTICE '';
    RAISE NOTICE 'Now the Admin App should be able to INSERT lock codes!';
END $$;
