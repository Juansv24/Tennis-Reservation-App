-- Seed access codes
INSERT INTO public.access_codes (code, is_active) VALUES
  ('TENNIS2024', true),
  ('COLINA2024', true),
  ('RESERVA2024', true);

-- Seed lock code
INSERT INTO public.lock_code (code) VALUES
  ('1234');

-- Note: Users will be created via Supabase Auth signup
-- Note: Reservations will be created by users via the app
