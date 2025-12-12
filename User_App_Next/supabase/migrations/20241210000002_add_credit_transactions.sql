-- Add credit_transactions table for audit trail of credit changes
-- This table tracks all credit grants, deductions, and usage

CREATE TABLE IF NOT EXISTS public.credit_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  amount INTEGER NOT NULL,  -- Positive for grants, negative for deductions
  transaction_type TEXT NOT NULL,  -- 'admin_grant', 'admin_deduct', 'reservation_use', 'reservation_refund'
  description TEXT,
  admin_user TEXT,  -- Admin who made the change (from session)
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

-- Add index for faster queries by user_id
CREATE INDEX IF NOT EXISTS idx_credit_transactions_user_id ON public.credit_transactions(user_id);

-- Add index for faster queries by transaction_type
CREATE INDEX IF NOT EXISTS idx_credit_transactions_type ON public.credit_transactions(transaction_type);

-- Add index for faster queries by created_at (for date range queries)
CREATE INDEX IF NOT EXISTS idx_credit_transactions_created_at ON public.credit_transactions(created_at DESC);

-- Enable RLS
ALTER TABLE public.credit_transactions ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only view their own transactions
CREATE POLICY "Users can view own credit transactions"
  ON public.credit_transactions
  FOR SELECT
  USING (auth.uid() = user_id);

-- RLS Policy: Service role can do everything (for admin operations)
CREATE POLICY "Service role can manage all credit transactions"
  ON public.credit_transactions
  FOR ALL
  USING (auth.role() = 'service_role');
