-- Migration: Create atomic batch reservation function
-- This eliminates race conditions when multiple users try to reserve the same slots simultaneously

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

  -- Validate and insert each reservation atomically
  FOR v_reservation IN SELECT * FROM jsonb_array_elements(p_reservations)
  LOOP
    v_date := (v_reservation->>'date')::DATE;
    v_hour := (v_reservation->>'hour')::INTEGER;

    -- Check if slot is already taken (with row lock)
    SELECT EXISTS(
      SELECT 1 FROM reservations
      WHERE date = v_date AND hour = v_hour
      FOR UPDATE -- Lock to prevent concurrent inserts
    ) INTO v_slot_taken;

    IF v_slot_taken THEN
      -- Rollback will happen automatically
      RETURN jsonb_build_object(
        'success', false,
        'error', format('El slot %s:00 del %s ya está reservado', v_hour, v_date),
        'slot_taken', jsonb_build_object('date', v_date, 'hour', v_hour)
      );
    END IF;

    -- Check daily limit (max 2 hours per day)
    SELECT COUNT(*) INTO v_existing_count
    FROM reservations
    WHERE user_id = p_user_id AND date = v_date;

    -- Count how many we're trying to add for this date
    DECLARE
      v_new_for_date INTEGER;
    BEGIN
      SELECT COUNT(*) INTO v_new_for_date
      FROM jsonb_array_elements(p_reservations) AS r
      WHERE (r->>'date')::DATE = v_date;

      IF v_existing_count + v_new_for_date > 2 THEN
        RETURN jsonb_build_object(
          'success', false,
          'error', 'Solo puedes reservar máximo 2 horas por día'
        );
      END IF;
    END;

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
