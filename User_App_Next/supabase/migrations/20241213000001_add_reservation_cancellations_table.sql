-- Migration: Add reservation_cancellations table
-- This table stores history of cancelled reservations for audit purposes

CREATE TABLE IF NOT EXISTS public.reservation_cancellations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  original_reservation_id UUID,  -- Original reservation ID (may no longer exist)
  user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
  user_name TEXT NOT NULL,  -- Denormalized for historical record
  user_email TEXT NOT NULL,  -- Denormalized for historical record
  reservation_date DATE NOT NULL,
  reservation_hour INTEGER NOT NULL CHECK (reservation_hour >= 6 AND reservation_hour <= 21),
  cancellation_reason TEXT,
  cancelled_by TEXT NOT NULL,  -- Admin username who cancelled
  cancelled_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('America/Bogota'::text, now()) NOT NULL,
  credits_refunded INTEGER DEFAULT 1 NOT NULL
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_reservation_cancellations_user_id ON public.reservation_cancellations(user_id);
CREATE INDEX IF NOT EXISTS idx_reservation_cancellations_date ON public.reservation_cancellations(reservation_date);
CREATE INDEX IF NOT EXISTS idx_reservation_cancellations_cancelled_at ON public.reservation_cancellations(cancelled_at);

-- Add RLS policies
ALTER TABLE public.reservation_cancellations ENABLE ROW LEVEL SECURITY;

-- Service role only - no user access needed
-- Admins will access via service role in Streamlit app

-- Add comment
COMMENT ON TABLE public.reservation_cancellations IS 'Historical record of cancelled reservations for audit trail';
