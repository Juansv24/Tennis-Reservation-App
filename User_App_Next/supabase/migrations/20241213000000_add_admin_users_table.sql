-- Migration: Add admin_users table for Admin App authentication
-- This table stores admin credentials for the Streamlit Admin App

CREATE TABLE IF NOT EXISTS public.admin_users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  salt TEXT NOT NULL,
  full_name TEXT NOT NULL,
  is_active BOOLEAN DEFAULT true NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('America/Bogota'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('America/Bogota'::text, now()) NOT NULL
);

-- Create index on username for faster lookups
CREATE INDEX IF NOT EXISTS idx_admin_users_username ON public.admin_users(username);

-- Add RLS policies
ALTER TABLE public.admin_users ENABLE ROW LEVEL SECURITY;

-- Admin users table should only be accessible by the service role
-- No policies needed as this will be accessed via service role only

-- Add comment
COMMENT ON TABLE public.admin_users IS 'Admin user credentials for Streamlit Admin App';
