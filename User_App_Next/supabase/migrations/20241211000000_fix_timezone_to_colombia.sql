-- Fix ALL timezone issues - Change from UTC to America/Bogota (Colombian timezone)
-- This ensures created_at timestamps are stored in Colombian time

-- 1. Fix users table created_at default
ALTER TABLE public.users
  ALTER COLUMN created_at SET DEFAULT timezone('America/Bogota'::text, now());

-- 2. Fix reservations table created_at default
ALTER TABLE public.reservations
  ALTER COLUMN created_at SET DEFAULT timezone('America/Bogota'::text, now());

-- 3. Fix maintenance_slots table created_at default
ALTER TABLE public.maintenance_slots
  ALTER COLUMN created_at SET DEFAULT timezone('America/Bogota'::text, now());

-- 4. Fix access_codes table created_at default
ALTER TABLE public.access_codes
  ALTER COLUMN created_at SET DEFAULT timezone('America/Bogota'::text, now());

-- 5. Fix email_verification_tokens table created_at default
ALTER TABLE public.email_verification_tokens
  ALTER COLUMN created_at SET DEFAULT timezone('America/Bogota'::text, now());

-- 6. Fix password_reset_tokens table created_at default
ALTER TABLE public.password_reset_tokens
  ALTER COLUMN created_at SET DEFAULT timezone('America/Bogota'::text, now());

-- 7. Fix credit_transactions table created_at default (if exists)
DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'credit_transactions') THEN
    ALTER TABLE public.credit_transactions
      ALTER COLUMN created_at SET DEFAULT timezone('America/Bogota'::text, now());
  END IF;
END $$;

-- Note: This migration fixes the DEFAULT value for new records.
-- Existing records will keep their UTC timestamps.
-- If you need to convert existing timestamps, you would need to update them:
-- UPDATE public.users SET created_at = created_at AT TIME ZONE 'UTC' AT TIME ZONE 'America/Bogota';
