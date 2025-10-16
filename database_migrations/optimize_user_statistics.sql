-- ============================================================================
-- OPTIMIZACIÓN: Estadísticas Detalladas de Usuarios
-- ============================================================================
-- Esta función reemplaza las consultas múltiples y loops en Python con una
-- sola consulta SQL optimizada que usa JOINs y agregaciones nativas.
--
-- INSTRUCCIONES DE INSTALACIÓN:
-- 1. Abre tu proyecto en Supabase Dashboard (https://supabase.com)
-- 2. Ve a SQL Editor
-- 3. Copia y pega este script completo
-- 4. Haz clic en "Run" para ejecutar
-- 5. La función estará disponible inmediatamente
-- ============================================================================

CREATE OR REPLACE FUNCTION get_users_detailed_statistics()
RETURNS TABLE (
    email TEXT,
    full_name TEXT,
    registered_date TEXT,
    total_credits_bought INTEGER,
    total_reservations BIGINT,
    favorite_day TEXT,
    favorite_time TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH
    -- Calcular créditos comprados por usuario
    user_credits AS (
        SELECT
            ct.user_id,
            COALESCE(SUM(ct.amount), 0)::INTEGER as credits_bought
        FROM credit_transactions ct
        WHERE ct.transaction_type IN ('admin_grant', 'purchase', 'bonus')
        GROUP BY ct.user_id
    ),

    -- Calcular estadísticas de reservas por usuario
    reservation_stats AS (
        SELECT
            r.email,
            COUNT(*)::BIGINT as total_res,
            MODE() WITHIN GROUP (ORDER BY EXTRACT(DOW FROM r.date::date)) as fav_day_num,
            MODE() WITHIN GROUP (ORDER BY r.hour) as fav_hour
        FROM reservations r
        GROUP BY r.email
    ),

    -- Mapear números de día a nombres en español
    day_names AS (
        SELECT 0 as day_num, 'Domingo' as day_name
        UNION ALL SELECT 1, 'Lunes'
        UNION ALL SELECT 2, 'Martes'
        UNION ALL SELECT 3, 'Miércoles'
        UNION ALL SELECT 4, 'Jueves'
        UNION ALL SELECT 5, 'Viernes'
        UNION ALL SELECT 6, 'Sábado'
    )

    -- Consulta principal con JOINs
    SELECT
        u.email,
        u.full_name,
        TO_CHAR(u.created_at, 'YYYY-MM-DD') as registered_date,
        COALESCE(uc.credits_bought, 0) as total_credits_bought,
        COALESCE(rs.total_res, 0) as total_reservations,
        COALESCE(dn.day_name, 'N/A') as favorite_day,
        CASE
            WHEN rs.fav_hour IS NOT NULL THEN LPAD(rs.fav_hour::TEXT, 2, '0') || ':00'
            ELSE 'N/A'
        END as favorite_time
    FROM users u
    LEFT JOIN user_credits uc ON u.id = uc.user_id
    LEFT JOIN reservation_stats rs ON u.email = rs.email
    LEFT JOIN day_names dn ON rs.fav_day_num = dn.day_num
    ORDER BY u.created_at DESC;
END;
$$;

-- ============================================================================
-- COMENTARIO DE LA FUNCIÓN
-- ============================================================================
COMMENT ON FUNCTION get_users_detailed_statistics() IS
'Obtiene estadísticas detalladas de todos los usuarios con una sola consulta optimizada.
Reemplaza múltiples queries y loops en Python. Usa JOINs y agregaciones SQL nativas.
Retorna: email, nombre, fecha registro, créditos comprados, total reservas, día favorito, hora favorita.';

-- ============================================================================
-- PRUEBA DE LA FUNCIÓN (Opcional - descomentar para probar)
-- ============================================================================
-- SELECT * FROM get_users_detailed_statistics() LIMIT 5;

-- ============================================================================
-- FIN DEL SCRIPT
-- ============================================================================
