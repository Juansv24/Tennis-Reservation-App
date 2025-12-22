-- Migration: Single-payload RPC approach for batch reservations
-- Uses a single JSONB parameter to avoid serialization issues
-- Based on PostgREST pattern for single JSON parameter functions

CREATE OR REPLACE FUNCTION confirm_batch_reservation(payload JSONB)
RETURNS JSONB AS $$
DECLARE
  v_user_id UUID := (payload->>'user_id')::UUID;
  v_credits_needed INTEGER := (payload->>'credits_needed')::INTEGER;
  v_user_credits INTEGER;
  v_is_vip BOOLEAN;
  v_slot RECORD;
  v_inserted_ids UUID[] := ARRAY[]::UUID[];
  v_new_reservation_id UUID;
  v_existing_count INTEGER;
  v_date DATE;
  v_hour INTEGER;
BEGIN
  -- Validate payload structure
  IF payload->>'user_id' IS NULL THEN
    RETURN jsonb_build_object(
      'success', false,
      'error_code', 'INVALID_PAYLOAD',
      'error', 'Missing user_id'
    );
  END IF;

  IF payload->'slots' IS NULL THEN
    RETURN jsonb_build_object(
      'success', false,
      'error_code', 'INVALID_PAYLOAD',
      'error', 'Missing slots array'
    );
  END IF;

  -- SECURITY: Validate user_id matches authenticated user (defense-in-depth)
  -- This protects against API bugs sending wrong user_id
  -- Note: RLS policies also enforce this, but defense-in-depth is important
  IF current_setting('request.jwt.claims', true) IS NOT NULL THEN
    DECLARE
      v_authenticated_user_id TEXT;
    BEGIN
      v_authenticated_user_id := current_setting('request.jwt.claims', true)::jsonb->>'sub';

      IF v_authenticated_user_id IS NOT NULL AND v_user_id::TEXT != v_authenticated_user_id THEN
        RETURN jsonb_build_object(
          'success', false,
          'error_code', 'UNAUTHORIZED',
          'error', 'No autorizado para reservar en nombre de otro usuario'
        );
      END IF;
    END;
  END IF;

  -- VALIDATION: All slots must be for the same date
  DECLARE
    v_unique_dates INTEGER;
  BEGIN
    SELECT COUNT(DISTINCT res_date) INTO v_unique_dates
    FROM jsonb_to_recordset(payload->'slots') AS x(res_date DATE, res_hour INTEGER);

    IF v_unique_dates > 1 THEN
      RETURN jsonb_build_object(
        'success', false,
        'error_code', 'MULTIPLE_DATES',
        'error', 'Solo puedes hacer reservas para un día a la vez'
      );
    END IF;
  END;

  -- VALIDATION: If 2 slots, they must be consecutive hours
  DECLARE
    v_slot_count INTEGER;
    v_hours INTEGER[];
  BEGIN
    SELECT COUNT(*), array_agg(res_hour ORDER BY res_hour)
    INTO v_slot_count, v_hours
    FROM jsonb_to_recordset(payload->'slots') AS x(res_date DATE, res_hour INTEGER);

    IF v_slot_count = 2 THEN
      IF v_hours[2] - v_hours[1] != 1 THEN
        RETURN jsonb_build_object(
          'success', false,
          'error_code', 'NON_CONSECUTIVE_HOURS',
          'error', 'Las 2 horas reservadas deben ser consecutivas (una después de la otra)'
        );
      END IF;
    ELSIF v_slot_count > 2 THEN
      RETURN jsonb_build_object(
        'success', false,
        'error_code', 'TOO_MANY_SLOTS',
        'error', 'Máximo 2 horas por reserva'
      );
    END IF;
  END;

  -- 1. LOCK THE USER: Prevents concurrent credit modifications
  SELECT credits, is_vip INTO v_user_credits, v_is_vip
  FROM users
  WHERE id = v_user_id
  FOR UPDATE; -- This lock prevents race conditions on credits

  -- Check if user exists
  IF NOT FOUND THEN
    RETURN jsonb_build_object(
      'success', false,
      'error_code', 'USER_NOT_FOUND',
      'error', 'Usuario no encontrado'
    );
  END IF;

  -- 2. VALIDATE CREDITS
  IF v_user_credits < v_credits_needed THEN
    RETURN jsonb_build_object(
      'success', false,
      'error_code', 'INSUFFICIENT_CREDITS',
      'error', format('Sin créditos suficientes. Necesitas %s, tienes %s', v_credits_needed, v_user_credits)
    );
  END IF;

  -- 3. VALIDATE DAILY LIMITS (before inserting anything)
  -- Check each unique date in the payload
  FOR v_slot IN
    SELECT DISTINCT x.res_date as res_date
    FROM jsonb_to_recordset(payload->'slots') AS x(res_date DATE, res_hour INTEGER)
  LOOP
    v_date := v_slot.res_date;

    -- Count existing reservations for this date
    SELECT COUNT(*) INTO v_existing_count
    FROM reservations
    WHERE user_id = v_user_id AND date = v_date;

    -- Count new reservations for this date in the payload
    DECLARE
      v_new_count_for_date INTEGER;
    BEGIN
      SELECT COUNT(*) INTO v_new_count_for_date
      FROM jsonb_to_recordset(payload->'slots') AS x(res_date DATE, res_hour INTEGER)
      WHERE x.res_date = v_date;

      IF v_existing_count + v_new_count_for_date > 2 THEN
        RETURN jsonb_build_object(
          'success', false,
          'error_code', 'DAILY_LIMIT_EXCEEDED',
          'error', 'Solo puedes reservar máximo 2 horas por día'
        );
      END IF;
    END;
  END LOOP;

  -- 3b. VALIDATE NO SAME HOUR ON CONSECUTIVE DAYS
  -- Check if user is trying to book the same hour they have on previous/next day
  FOR v_slot IN
    SELECT x.res_date, x.res_hour
    FROM jsonb_to_recordset(payload->'slots') AS x(res_date DATE, res_hour INTEGER)
  LOOP
    -- Check if user has this hour reserved on the day before or after
    IF EXISTS (
      SELECT 1 FROM reservations
      WHERE user_id = v_user_id
        AND hour = v_slot.res_hour
        AND (date = v_slot.res_date - INTERVAL '1 day'
             OR date = v_slot.res_date + INTERVAL '1 day')
    ) THEN
      RETURN jsonb_build_object(
        'success', false,
        'error_code', 'CONSECUTIVE_DAY_SAME_HOUR',
        'error', format('No puedes reservar a las %s:00 en este día porque ya lo tienes reservado en el día anterior o siguiente', v_slot.res_hour)
      );
    END IF;
  END LOOP;

  -- 4. INSERT ALL SLOTS (after validation passed)
  -- Using jsonb_to_recordset to extract slot data
  BEGIN
    FOR v_slot IN
      SELECT * FROM jsonb_to_recordset(payload->'slots')
      AS x(res_date DATE, res_hour INTEGER)
    LOOP
      v_date := v_slot.res_date;
      v_hour := v_slot.res_hour;

      -- Insert reservation (will fail on unique constraint if slot taken)
      INSERT INTO reservations (user_id, date, hour)
      VALUES (v_user_id, v_date, v_hour)
      RETURNING id INTO v_new_reservation_id;

      v_inserted_ids := array_append(v_inserted_ids, v_new_reservation_id);
    END LOOP;

  EXCEPTION
    WHEN unique_violation THEN
      -- First-Click-Wins: Someone else booked the slot first
      RETURN jsonb_build_object(
        'success', false,
        'error_code', 'SLOT_ALREADY_TAKEN',
        'error', 'Uno o más horarios ya están reservados'
      );
  END;

  -- 5. DEDUCT CREDITS (only if all reservations succeeded)
  UPDATE users
  SET credits = credits - v_credits_needed
  WHERE id = v_user_id;

  -- Success! Return new credits and reservation IDs
  RETURN jsonb_build_object(
    'success', true,
    'new_credits', v_user_credits - v_credits_needed,
    'reservation_ids', to_jsonb(v_inserted_ids)
  );

EXCEPTION
  WHEN OTHERS THEN
    -- Catch any unexpected errors
    RETURN jsonb_build_object(
      'success', false,
      'error_code', 'SYSTEM_ERROR',
      'error', format('Error del sistema: %s', SQLERRM)
    );
END;
$$ LANGUAGE plpgsql;

-- Add comment
COMMENT ON FUNCTION confirm_batch_reservation IS
  'Atomically creates batch reservations using single JSONB payload parameter. Prevents race conditions with FOR UPDATE lock and unique constraints.';
