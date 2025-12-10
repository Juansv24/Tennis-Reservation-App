-- DEBUG: Check actual database state for credits issue
-- Run this in Supabase SQL Editor to gather evidence

-- 1. Check the actual trigger function code currently in database
SELECT
  proname as function_name,
  prosrc as function_source
FROM pg_proc
WHERE proname = 'handle_new_user';

-- 2. Check the default value for credits column
SELECT
  column_name,
  column_default,
  data_type
FROM information_schema.columns
WHERE table_name = 'users'
  AND column_name = 'credits';

-- 3. Check recent users to see their actual credits
SELECT
  id,
  email,
  full_name,
  credits,
  created_at
FROM public.users
ORDER BY created_at DESC
LIMIT 5;

-- 4. Check if there are any other triggers on auth.users
SELECT
  trigger_name,
  event_manipulation,
  event_object_table,
  action_statement
FROM information_schema.triggers
WHERE event_object_table = 'users'
  AND event_object_schema = 'auth';
