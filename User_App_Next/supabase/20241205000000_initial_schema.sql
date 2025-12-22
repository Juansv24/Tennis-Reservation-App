-- Tennis Reservation App - Initial Database Schema
-- Migration: 20241205000000
-- Description: Creates all tables, RLS policies, indexes, and triggers for the Tennis Reservation App

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- USERS TABLE
-- =====================================================
-- Extends Supabase auth.users with application-specific data
CREATE TABLE public.users (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  full_name TEXT NOT NULL,
  credits INTEGER DEFAULT 0 NOT NULL,
  is_vip BOOLEAN DEFAULT false NOT NULL,
  first_login_completed BOOLEAN DEFAULT false NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Users RLS Policies
CREATE POLICY "Users can view their own profile"
  ON public.users FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
  ON public.users FOR UPDATE
  USING (auth.uid() = id);

-- =====================================================
-- RESERVATIONS TABLE
-- =====================================================
-- Stores court reservations
CREATE TABLE public.reservations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  hour INTEGER NOT NULL CHECK (hour >= 6 AND hour <= 21),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  UNIQUE(date, hour)
);

-- Enable Row Level Security
ALTER TABLE public.reservations ENABLE ROW LEVEL SECURITY;

-- Reservations RLS Policies
CREATE POLICY "Anyone can view reservations"
  ON public.reservations FOR SELECT
  USING (true);

CREATE POLICY "Authenticated users can create reservations"
  ON public.reservations FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own reservations"
  ON public.reservations FOR DELETE
  USING (auth.uid() = user_id);

-- Create indexes for faster queries
CREATE INDEX idx_reservations_date ON public.reservations(date);
CREATE INDEX idx_reservations_user_id ON public.reservations(user_id);

-- =====================================================
-- ACCESS CODES TABLE
-- =====================================================
-- Stores access codes for user registration
CREATE TABLE public.access_codes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  code TEXT NOT NULL UNIQUE,
  is_active BOOLEAN DEFAULT true NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable Row Level Security
ALTER TABLE public.access_codes ENABLE ROW LEVEL SECURITY;

-- Access codes RLS Policies
CREATE POLICY "Anyone can view active access codes"
  ON public.access_codes FOR SELECT
  USING (is_active = true);

-- =====================================================
-- LOCK CODE TABLE
-- =====================================================
-- Stores the lock code for the court
CREATE TABLE public.lock_code (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  code TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable Row Level Security
ALTER TABLE public.lock_code ENABLE ROW LEVEL SECURITY;

-- Lock code RLS Policies
CREATE POLICY "Authenticated users can view lock code"
  ON public.lock_code FOR SELECT
  USING (auth.uid() IS NOT NULL);

-- =====================================================
-- MAINTENANCE SLOTS TABLE
-- =====================================================
-- Stores maintenance/blocked time slots
CREATE TABLE public.blocked_slots (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  date DATE NOT NULL,
  hour INTEGER NOT NULL CHECK (hour >= 6 AND hour <= 21),
  reason TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  UNIQUE(date, hour)
);

-- Enable Row Level Security
ALTER TABLE public.blocked_slots ENABLE ROW LEVEL SECURITY;

-- Maintenance slots RLS Policies
CREATE POLICY "Anyone can view maintenance slots"
  ON public.blocked_slots FOR SELECT
  USING (true);

-- Create index for faster queries
CREATE INDEX idx_blocked_slots_date ON public.blocked_slots(date);

-- =====================================================
-- TRIGGERS
-- =====================================================
-- Function to create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, email, full_name, credits, is_vip, first_login_completed)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', 'User'),
    0,
    false,
    false
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to automatically create user profile when auth user is created
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- =====================================================
-- COMMENTS
-- =====================================================
COMMENT ON TABLE public.users IS 'User profiles extending Supabase auth.users';
COMMENT ON TABLE public.reservations IS 'Court time slot reservations';
COMMENT ON TABLE public.access_codes IS 'Access codes for user registration';
COMMENT ON TABLE public.lock_code IS 'Lock code for court access';
COMMENT ON TABLE public.blocked_slots IS 'Maintenance/blocked time slots';

COMMENT ON COLUMN public.users.credits IS 'Number of available reservation credits (default: 0)';
COMMENT ON COLUMN public.users.is_vip IS 'VIP users have unlimited reservations';
COMMENT ON COLUMN public.users.first_login_completed IS 'Whether user has completed first-time setup';
COMMENT ON COLUMN public.reservations.hour IS 'Hour of reservation (6-21 represents 6am-9pm)';
