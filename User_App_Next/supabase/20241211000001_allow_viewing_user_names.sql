-- Migration: Allow viewing other users' names for reservation display
-- Description: Adds RLS policy to allow authenticated users to view full_name of all users
-- This is needed to display owner names on taken reservation slots

-- Drop the restrictive policy
DROP POLICY IF EXISTS "Users can view their own profile" ON public.users;

-- Create a new policy that allows users to view all profiles (for full_name display)
CREATE POLICY "Authenticated users can view all user profiles"
  ON public.users FOR SELECT
  USING (auth.uid() IS NOT NULL);

-- Keep the update policy restrictive (users can only update their own profile)
-- This policy already exists, no changes needed
