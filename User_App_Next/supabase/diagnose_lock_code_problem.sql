-- =====================================================
-- DIAGNÓSTICO COMPLETO: LOCK_CODE vs ACCESS_CODES
-- =====================================================
-- Ejecuta este SQL completo para ver exactamente qué está pasando
-- =====================================================

-- 1. Ver estructura de ambas tablas
SELECT
    'access_codes' as tabla,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'access_codes'
ORDER BY ordinal_position;

SELECT
    'lock_code' as tabla,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'lock_code'
ORDER BY ordinal_position;

-- 2. Ver políticas RLS actuales
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE tablename IN ('access_codes', 'lock_code')
ORDER BY tablename, policyname;

-- 3. Verificar si RLS está habilitado
SELECT
    schemaname,
    tablename,
    rowsecurity
FROM pg_tables
WHERE tablename IN ('access_codes', 'lock_code');

-- 4. Intentar INSERT de prueba en lock_code
-- IMPORTANTE: Esto intentará insertar. Si falla, verás el error exacto.
INSERT INTO public.lock_code (code)
VALUES ('TEST-9999')
RETURNING id, code, created_at;

-- Si el INSERT anterior funcionó, bórralo:
DELETE FROM public.lock_code WHERE code = 'TEST-9999';

-- 5. Ver registros recientes en ambas tablas
SELECT 'access_codes' as tabla, *
FROM public.access_codes
ORDER BY created_at DESC
LIMIT 5;

SELECT 'lock_code' as tabla, *
FROM public.lock_code
ORDER BY created_at DESC
LIMIT 5;
