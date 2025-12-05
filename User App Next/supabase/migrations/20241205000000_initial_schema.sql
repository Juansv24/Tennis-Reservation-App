-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (extends auth.users)
CREATE TABLE public.users (
  id uuid REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
  email text UNIQUE NOT NULL,
  full_name text NOT NULL,
  credits integer DEFAULT 7 NOT NULL CHECK (credits >= 0),
  is_vip boolean DEFAULT false NOT NULL,
  first_login_completed boolean DEFAULT false NOT NULL,
  created_at timestamp with time zone DEFAULT now() NOT NULL
);

-- Reservations table
CREATE TABLE public.reservations (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
  date date NOT NULL,
  hour integer NOT NULL CHECK (hour >= 6 AND hour <= 21),
  created_at timestamp with time zone DEFAULT now() NOT NULL,
  UNIQUE(date, hour)
);

-- Access codes table
CREATE TABLE public.access_codes (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  code text UNIQUE NOT NULL,
  is_active boolean DEFAULT true NOT NULL,
  created_at timestamp with time zone DEFAULT now() NOT NULL
);

-- Lock code table
CREATE TABLE public.lock_code (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  code text NOT NULL,
  created_at timestamp with time zone DEFAULT now() NOT NULL
);

-- Maintenance slots table
CREATE TABLE public.maintenance_slots (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  date date NOT NULL,
  hour integer NOT NULL CHECK (hour >= 6 AND hour <= 21),
  reason text,
  created_at timestamp with time zone DEFAULT now() NOT NULL,
  UNIQUE(date, hour)
);

-- Indexes for performance
CREATE INDEX idx_reservations_date ON public.reservations(date);
CREATE INDEX idx_reservations_user_id ON public.reservations(user_id);
CREATE INDEX idx_maintenance_date ON public.maintenance_slots(date);

-- RLS Policies
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reservations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.access_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lock_code ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.maintenance_slots ENABLE ROW LEVEL SECURITY;

-- Users: Users can read their own profile
CREATE POLICY "Users can view own profile"
  ON public.users FOR SELECT
  USING (auth.uid() = id);

-- Users: Users can update their own profile
CREATE POLICY "Users can update own profile"
  ON public.users FOR UPDATE
  USING (auth.uid() = id);

-- Reservations: Users can view all reservations
CREATE POLICY "Anyone can view reservations"
  ON public.reservations FOR SELECT
  TO authenticated
  USING (true);

-- Reservations: Users can create their own reservations
CREATE POLICY "Users can create own reservations"
  ON public.reservations FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

-- Reservations: Users can delete their own reservations
CREATE POLICY "Users can delete own reservations"
  ON public.reservations FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

-- Access codes: Authenticated users can read active codes
CREATE POLICY "Authenticated users can view access codes"
  ON public.access_codes FOR SELECT
  TO authenticated
  USING (is_active = true);

-- Lock code: Authenticated users can view lock code
CREATE POLICY "Authenticated users can view lock code"
  ON public.lock_code FOR SELECT
  TO authenticated
  USING (true);

-- Maintenance: Anyone can view maintenance slots
CREATE POLICY "Anyone can view maintenance slots"
  ON public.maintenance_slots FOR SELECT
  TO authenticated
  USING (true);

-- Function: Auto-create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.users (id, email, full_name, credits, is_vip, first_login_completed)
  VALUES (
    new.id,
    new.email,
    COALESCE(new.raw_user_meta_data->>'full_name', 'User'),
    7,
    false,
    false
  );
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger: Create user profile on auth.users insert
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
