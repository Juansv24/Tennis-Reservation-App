-- SQL Script to create 10 test users for load testing
-- Run this in Supabase SQL Editor: Dashboard > SQL Editor > New Query
--
-- IMPORTANT:
-- 1. Make sure your users table and auth.users table exist
-- 2. Adjust column names if your schema is different
-- 3. Password should be hashed in production (this uses plain text for testing)
-- 4. Ensure email verification is marked as complete

-- Test User Credentials:
-- user1@test.local - user10@test.local
-- Password: TestPassword123!

-- First, insert users into your users table
-- Adjust this query based on your actual schema

BEGIN;

-- Insert test users into users table
INSERT INTO public.users (email, full_name, credits, is_verified, created_at)
VALUES
  ('user1@test.local', 'Test User 1', 10, true, NOW()),
  ('user2@test.local', 'Test User 2', 10, true, NOW()),
  ('user3@test.local', 'Test User 3', 10, true, NOW()),
  ('user4@test.local', 'Test User 4', 10, true, NOW()),
  ('user5@test.local', 'Test User 5', 10, true, NOW()),
  ('user6@test.local', 'Test User 6', 10, true, NOW()),
  ('user7@test.local', 'Test User 7', 10, true, NOW()),
  ('user8@test.local', 'Test User 8', 10, true, NOW()),
  ('user9@test.local', 'Test User 9', 10, true, NOW()),
  ('user10@test.local', 'Test User 10', 10, true, NOW())
ON CONFLICT (email) DO NOTHING;

COMMIT;

-- Note: For Supabase auth integration, you'll need to:
-- 1. Create these users through the Supabase Auth API or dashboard
-- 2. Or use a setup script that calls auth.signUpUser()
--
-- Here's how to do it via Supabase CLI (optional):
-- supabase local start
-- supabase db push
-- Then use the setup_auth_users.py script to create auth users

-- Verify users were created
SELECT COUNT(*) as total_test_users
FROM public.users
WHERE email LIKE '%test.local%';

-- View created users
SELECT id, email, full_name, credits, is_verified
FROM public.users
WHERE email LIKE '%test.local%'
ORDER BY email;

-- Optional: If you have a vip_users table and want some test users to be VIP
-- INSERT INTO public.vip_users (email)
-- VALUES
--   ('user1@test.local'),
--   ('user2@test.local')
-- ON CONFLICT (email) DO NOTHING;
