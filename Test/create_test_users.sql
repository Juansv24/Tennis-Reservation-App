-- SQL Script: Create 10 Test Users for Concurrent Testing
-- Purpose: Simulate multiple users for load testing and race condition validation
-- Run this script in Supabase SQL Editor or via CLI

-- Note: These users will be created in auth.users and public.users tables
-- Password for all test users: TestUser2024!

-- First, we need to use Supabase's auth.users table
-- Since we can't directly insert into auth.users via SQL (it's managed by Supabase Auth),
-- we'll create a function to register test users

-- Create test users using Supabase's user creation
-- You'll need to run this via Supabase Dashboard or API

-- For manual creation via SQL (requires admin privileges):
BEGIN;

-- Insert test users into auth.users (if you have direct access)
-- Otherwise, use the Supabase Dashboard to create these users manually

-- Create public.users entries for test users
-- Note: Replace these UUIDs with actual auth.users IDs after creating them via Supabase Auth

-- Test User 1
INSERT INTO public.users (id, email, full_name, credits, is_vip, first_login_completed)
VALUES
  (gen_random_uuid(), 'testuser1@test.com', 'Test User 1', 10, false, true)
ON CONFLICT (id) DO NOTHING;

-- Test User 2
INSERT INTO public.users (id, email, full_name, credits, is_vip, first_login_completed)
VALUES
  (gen_random_uuid(), 'testuser2@test.com', 'Test User 2', 10, false, true)
ON CONFLICT (id) DO NOTHING;

-- Test User 3
INSERT INTO public.users (id, email, full_name, credits, is_vip, first_login_completed)
VALUES
  (gen_random_uuid(), 'testuser3@test.com', 'Test User 3', 10, false, true)
ON CONFLICT (id) DO NOTHING;

-- Test User 4
INSERT INTO public.users (id, email, full_name, credits, is_vip, first_login_completed)
VALUES
  (gen_random_uuid(), 'testuser4@test.com', 'Test User 4', 10, false, true)
ON CONFLICT (id) DO NOTHING;

-- Test User 5
INSERT INTO public.users (id, email, full_name, credits, is_vip, first_login_completed)
VALUES
  (gen_random_uuid(), 'testuser5@test.com', 'Test User 5', 10, false, true)
ON CONFLICT (id) DO NOTHING;

-- Test User 6 (VIP)
INSERT INTO public.users (id, email, full_name, credits, is_vip, first_login_completed)
VALUES
  (gen_random_uuid(), 'testuser6@test.com', 'Test User 6 VIP', 10, true, true)
ON CONFLICT (id) DO NOTHING;

-- Test User 7 (VIP)
INSERT INTO public.users (id, email, full_name, credits, is_vip, first_login_completed)
VALUES
  (gen_random_uuid(), 'testuser7@test.com', 'Test User 7 VIP', 10, true, true)
ON CONFLICT (id) DO NOTHING;

-- Test User 8
INSERT INTO public.users (id, email, full_name, credits, is_vip, first_login_completed)
VALUES
  (gen_random_uuid(), 'testuser8@test.com', 'Test User 8', 10, false, true)
ON CONFLICT (id) DO NOTHING;

-- Test User 9
INSERT INTO public.users (id, email, full_name, credits, is_vip, first_login_completed)
VALUES
  (gen_random_uuid(), 'testuser9@test.com', 'Test User 9', 10, false, true)
ON CONFLICT (id) DO NOTHING;

-- Test User 10
INSERT INTO public.users (id, email, full_name, credits, is_vip, first_login_completed)
VALUES
  (gen_random_uuid(), 'testuser10@test.com', 'Test User 10', 10, false, true)
ON CONFLICT (id) DO NOTHING;

COMMIT;

-- Verify test users were created
SELECT id, email, full_name, credits, is_vip
FROM public.users
WHERE email LIKE 'testuser%@test.com'
ORDER BY email;

-- Note: You'll need to create the auth.users entries via Supabase Dashboard or API
-- with the same emails and password: TestUser2024!
