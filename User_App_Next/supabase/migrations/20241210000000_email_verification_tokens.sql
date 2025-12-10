-- Create email_verification_tokens table
CREATE TABLE IF NOT EXISTS public.email_verification_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  token TEXT NOT NULL UNIQUE,
  expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
  used_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create index for faster token lookups
CREATE INDEX IF NOT EXISTS email_verification_tokens_token_idx ON public.email_verification_tokens(token);
CREATE INDEX IF NOT EXISTS email_verification_tokens_user_id_idx ON public.email_verification_tokens(user_id);

-- Create password_reset_tokens table
CREATE TABLE IF NOT EXISTS public.password_reset_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  token TEXT NOT NULL UNIQUE,
  expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
  used_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create index for faster token lookups
CREATE INDEX IF NOT EXISTS password_reset_tokens_token_idx ON public.password_reset_tokens(token);
CREATE INDEX IF NOT EXISTS password_reset_tokens_user_id_idx ON public.password_reset_tokens(user_id);

-- Enable Row Level Security
ALTER TABLE public.email_verification_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.password_reset_tokens ENABLE ROW LEVEL SECURITY;

-- Create policies (only service role can access these tables)
CREATE POLICY "Service role can manage email verification tokens"
  ON public.email_verification_tokens
  FOR ALL
  USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage password reset tokens"
  ON public.password_reset_tokens
  FOR ALL
  USING (auth.role() = 'service_role');
