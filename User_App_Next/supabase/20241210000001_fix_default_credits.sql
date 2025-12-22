-- Fix default credits to be 0 for new users
-- This migration ensures the trigger function uses 0 credits

-- Update the table default (in case it wasn't set correctly)
ALTER TABLE public.users
  ALTER COLUMN credits SET DEFAULT 0;

-- Recreate the trigger function to ensure it uses 0 credits
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, email, full_name, credits, is_vip, first_login_completed)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', 'User'),
    0,  -- Explicitly set to 0 credits
    false,
    false
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Comment to document the change
COMMENT ON FUNCTION public.handle_new_user() IS 'Creates user profile with 0 credits on signup (updated 2024-12-10)';
