-- Migration: Fix batch reservations parameter type from TEXT to JSONB
-- This fixes the "invalid input syntax for type json" error

-- Drop the old function
DROP FUNCTION IF EXISTS create_batch_reservations(UUID, TEXT, INTEGER);

-- Recreate with correct JSONB parameter type
CREATE OR REPLACE FUNCTION create_batch_reservations(
  p_user_id UUID,
  p_reservations JSONB, -- Array of {date: 'YYYY-MM-DD', hour: number}
  p_credits_needed INTEGER
) RETURNS JSONB AS $$
DECLARE
  v_user_credits INTEGER;
  v_is_vip BOOLEAN;
  v_reservation JSONB;
  v_date DATE;
  v_hour INTEGER;
  v_existing_count INTEGER;
  v_slot_taken BOOLEAN;
  v_result JSONB;
  v_inserted_ids UUID[] := ARRAY[]::UUID[];
  v_new_reservation_id UUID;
BEGIN
  -- Get user info with row lock to prevent concurrent modifications
  SELECT credits, is_vip INTO v_user_credits, v_is_vip
  FROM users
  WHERE id = p_user_id
  FOR UPDATE; -- Lock this row until transaction completes

  -- Check if user exists
  IF NOT FOUND THEN
    RETURN jsonb_build_object(
      'success', false,
      'error', 'Usuario no encontrado'
    );
  END IF;

  -- Check sufficient credits
  IF v_user_credits < p_credits_needed THEN
    RETURN jsonb_build_object(
      'success', false,
      'error', format('Sin créditos suficientes. Necesitas %s, tienes %s', p_credits_needed, v_user_credits)
    );
  END IF;

  -- PHASE 1: Acquire advisory locks FIRST (prevents phantom reads)
  -- Sort by date and hour to prevent deadlocks
  FOR v_reservation IN
    SELECT DISTINCT (elem->>'date')::DATE as res_date, (elem->>'hour')::INTEGER as res_hour
    FROM jsonb_array_elements(p_reservations) AS elem
    ORDER BY (elem->>'date')::DATE, (elem->>'hour')::INTEGER
  LOOP
    -- Advisory lock: Only ONE transaction can hold this lock at a time
    -- Lock is automatically released at transaction end
    PERFORM pg_advisory_xact_lock(
      hashtext(v_reservation.res_date::TEXT || '-' || v_reservation.res_hour::TEXT)
    );
  END LOOP;

  -- PHASE 2: Validate ALL slots AFTER acquiring locks
  FOR v_reservation IN SELECT * FROM jsonb_array_elements(p_reservations)
  LOOP
    v_date := (v_reservation->>'date')::DATE;
    v_hour := (v_reservation->>'hour')::INTEGER;

    -- Now check if slot is taken (we have exclusive lock, safe to check)
    SELECT EXISTS(
      SELECT 1 FROM reservations
      WHERE date = v_date AND hour = v_hour
    ) INTO v_slot_taken;

    IF v_slot_taken THEN
      RETURN jsonb_build_object(
        'success', false,
        'error', format('El slot %s:00 del %s ya está reservado', v_hour, v_date),
        'slot_taken', jsonb_build_object('date', v_date, 'hour', v_hour)
      );
    END IF;
  END LOOP;

  -- Check daily limit ONCE for all reservations
  -- Group by date and check limits (FIXED: use record dot notation)
  FOR v_reservation IN
    SELECT (elem->>'date')::DATE as check_date, COUNT(*)::INTEGER as new_count
    FROM jsonb_array_elements(p_reservations) AS elem
    GROUP BY (elem->>'date')::DATE
  LOOP
    SELECT COUNT(*) INTO v_existing_count
    FROM reservations
    WHERE user_id = p_user_id AND date = v_reservation.check_date;

    IF v_existing_count + v_reservation.new_count > 2 THEN
      RETURN jsonb_build_object(
        'success', false,
        'error', 'Solo puedes reservar máximo 2 horas por día'
      );
    END IF;
  END LOOP;

  -- PHASE 2: All validations passed - now insert ALL reservations
  FOR v_reservation IN SELECT * FROM jsonb_array_elements(p_reservations)
  LOOP
    v_date := (v_reservation->>'date')::DATE;
    v_hour := (v_reservation->>'hour')::INTEGER;

    -- Insert the reservation
    INSERT INTO reservations (user_id, date, hour)
    VALUES (p_user_id, v_date, v_hour)
    RETURNING id INTO v_new_reservation_id;

    v_inserted_ids := array_append(v_inserted_ids, v_new_reservation_id);
  END LOOP;

  -- Deduct credits atomically
  UPDATE users
  SET credits = credits - p_credits_needed
  WHERE id = p_user_id;

  -- Log credit transaction
  INSERT INTO credit_transactions (user_id, amount, transaction_type, description)
  VALUES (
    p_user_id,
    -p_credits_needed,
    'reservation_use',
    format('Reserva de %s hora(s)', p_credits_needed)
  );

  -- Return success with new credits
  RETURN jsonb_build_object(
    'success', true,
    'new_credits', v_user_credits - p_credits_needed,
    'reservation_ids', to_jsonb(v_inserted_ids)
  );

EXCEPTION
  WHEN OTHERS THEN
    -- Catch any unexpected errors
    RETURN jsonb_build_object(
      'success', false,
      'error', format('Error del sistema: %s', SQLERRM)
    );
END;
$$ LANGUAGE plpgsql;

-- Add comment
COMMENT ON FUNCTION create_batch_reservations IS 'Atomically creates batch reservations with validation, preventing race conditions';
