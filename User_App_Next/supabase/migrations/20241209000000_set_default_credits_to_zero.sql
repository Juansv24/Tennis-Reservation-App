-- Migration: Set default credits to 0 for new users
-- Date: 2024-12-09
-- Description: Updates the default credits value from 7 to 0 for new user registrations

-- Update the default value for the credits column
ALTER TABLE public.users
ALTER COLUMN credits SET DEFAULT 0;

-- Update the trigger function to set credits to 0 for new users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, email, full_name, credits, is_vip, first_login_completed)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', 'User'),
    0,  -- Changed from 7 to 0
    false,
    false
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Update the comment to reflect the new default
COMMENT ON COLUMN public.users.credits IS 'Number of available reservation credits (default: 0)';
