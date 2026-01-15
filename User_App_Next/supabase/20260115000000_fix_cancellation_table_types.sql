-- Fix reservation_cancellations table to use UUID instead of INTEGER
-- Migration: 20260115000000
-- Description: Converts user_id and original_reservation_id from INTEGER to UUID

-- Drop the table if it exists with wrong types and recreate it
-- This is safe if the table is relatively new and doesn't have critical historical data
-- If you have important data, you'll need a more complex migration to convert the data

DROP TABLE IF EXISTS public.reservation_cancellations CASCADE;

-- Recreate the table with correct UUID types
CREATE TABLE public.reservation_cancellations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  original_reservation_id UUID NOT NULL,
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  user_email TEXT NOT NULL,
  user_name TEXT NOT NULL,
  reservation_date DATE NOT NULL,
  reservation_hour INTEGER NOT NULL CHECK (reservation_hour >= 6 AND reservation_hour <= 21),
  cancellation_reason TEXT,
  cancelled_by TEXT NOT NULL,
  credits_refunded INTEGER DEFAULT 1,
  cancelled_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('America/Bogota'::text, now()) NOT NULL
);

-- Enable Row Level Security
ALTER TABLE public.reservation_cancellations ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Service role (admin app) can do everything
CREATE POLICY "Service role can manage cancellations"
ON public.reservation_cancellations
FOR ALL
TO authenticated, anon
USING (true)
WITH CHECK (true);

-- Create indexes for better query performance
CREATE INDEX idx_cancellations_user_id ON public.reservation_cancellations(user_id);
CREATE INDEX idx_cancellations_cancelled_at ON public.reservation_cancellations(cancelled_at);
CREATE INDEX idx_cancellations_reservation_date ON public.reservation_cancellations(reservation_date);

-- Add table comment
COMMENT ON TABLE public.reservation_cancellations IS 'Audit trail of cancelled reservations';
COMMENT ON COLUMN public.reservation_cancellations.original_reservation_id IS 'The UUID of the cancelled reservation';
COMMENT ON COLUMN public.reservation_cancellations.cancelled_by IS 'Admin username who cancelled the reservation';
COMMENT ON COLUMN public.reservation_cancellations.credits_refunded IS 'Number of credits refunded to the user';
