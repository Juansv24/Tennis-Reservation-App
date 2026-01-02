-- Migration: Add admin_user column to lock_code table for audit trail
-- This is OPTIONAL - uncomment and run if you want to track which admin changed the password
-- After running this migration, uncomment the admin_user line in Admin App/admin_database.py line 1059

/*
ALTER TABLE public.lock_code
ADD COLUMN admin_user TEXT;

COMMENT ON COLUMN public.lock_code.admin_user IS 'Username of admin who updated the lock code';
*/

-- NOTE: This migration is currently commented out. The app will work without it.
-- To enable audit trail:
-- 1. Uncomment the SQL above and run it in Supabase SQL Editor
-- 2. Uncomment line 1059 in Admin App/admin_database.py
-- 3. Comment out line 1058 in Admin App/admin_database.py
