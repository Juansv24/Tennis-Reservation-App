-- Tennis Reservation App - Seed Data
-- Description: Inserts initial data for access codes and lock code
--
-- CONFIGURATION:
-- You can modify the codes below to match your requirements

-- =====================================================
-- ACCESS CODES
-- =====================================================
-- Insert initial access codes for user registration
-- These codes allow users to complete their first-time setup after email verification
--
-- To add more codes, simply add more INSERT statements or add to the VALUES list
-- To deactivate a code, set is_active = false

INSERT INTO public.access_codes (code, is_active) VALUES
  ('TENNIS2024', true),
  ('COLINA2024', true),
  ('RESERVA2024', true)
ON CONFLICT (code) DO NOTHING;

-- =====================================================
-- LOCK CODE
-- =====================================================
-- Insert the initial lock code for court access
-- This is the 4-digit code displayed to authenticated users
--
-- To change the lock code:
-- 1. Update the value below
-- 2. Run this SQL in Supabase
-- OR insert a new code (app shows the most recent one)

INSERT INTO public.lock_code (code) VALUES
  ('1234')
ON CONFLICT DO NOTHING;

-- =====================================================
-- OPTIONAL: CREATE TEST VIP USER
-- =====================================================
-- Uncomment the following section if you want to create a test VIP user
--
-- IMPORTANT: First create the user through Supabase Auth UI or registration flow,
-- then run this SQL to upgrade them to VIP status
--
-- Replace 'your-email@example.com' with the actual email address

-- UPDATE public.users
-- SET
--   is_vip = true,
--   credits = 999,
--   first_login_completed = true
-- WHERE email = 'your-email@example.com';

-- =====================================================
-- OPTIONAL: CREATE SAMPLE MAINTENANCE SLOTS
-- =====================================================
-- Uncomment to add sample maintenance slots
-- Useful for testing the maintenance slot feature
--
-- Replace dates with actual dates you want to block

-- INSERT INTO public.blocked_slots (date, hour, reason) VALUES
--   ('2025-12-10', 8, 'Mantenimiento de cancha'),
--   ('2025-12-10', 9, 'Mantenimiento de cancha'),
--   ('2025-12-15', 14, 'Evento especial')
-- ON CONFLICT (date, hour) DO NOTHING;

-- =====================================================
-- VERIFICATION
-- =====================================================
-- Run these queries to verify the seed data was inserted correctly:

-- Check access codes
-- SELECT * FROM public.access_codes ORDER BY created_at;

-- Check lock code
-- SELECT * FROM public.lock_code ORDER BY created_at DESC LIMIT 1;

-- Check maintenance slots (if any)
-- SELECT * FROM public.blocked_slots ORDER BY date, hour;
