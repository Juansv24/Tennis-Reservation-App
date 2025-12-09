-- SQL function to atomically deduct credits
-- Run this in Supabase SQL Editor

CREATE OR REPLACE FUNCTION deduct_user_credit(user_id_param UUID)
RETURNS TABLE (
  new_credits INTEGER,
  success BOOLEAN
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  current_credits INTEGER;
  is_vip_user BOOLEAN;
BEGIN
  -- Get current credits and VIP status with row lock
  SELECT credits, is_vip INTO current_credits, is_vip_user
  FROM users
  WHERE id = user_id_param
  FOR UPDATE;

  -- Check if user exists
  IF NOT FOUND THEN
    RETURN QUERY SELECT 0, FALSE;
    RETURN;
  END IF;

  -- VIP users don't need credit deduction
  IF is_vip_user THEN
    RETURN QUERY SELECT current_credits, TRUE;
    RETURN;
  END IF;

  -- Check if user has enough credits
  IF current_credits < 1 THEN
    RETURN QUERY SELECT current_credits, FALSE;
    RETURN;
  END IF;

  -- Deduct 1 credit atomically
  UPDATE users
  SET credits = credits - 1
  WHERE id = user_id_param;

  -- Return new credit count
  RETURN QUERY SELECT current_credits - 1, TRUE;
END;
$$;
