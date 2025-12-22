-- =====================================================
-- CREATE MISSING TABLES FOR ADMIN APP
-- Run this in Supabase SQL Editor
-- =====================================================

-- =====================================================
-- TABLE 1: credit_transactions
-- Purpose: Track all credit operations (add, remove, use)
-- =====================================================

CREATE TABLE IF NOT EXISTS credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    description TEXT,
    admin_user VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_credit_transactions_user_id ON credit_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_created_at ON credit_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_type ON credit_transactions(transaction_type);

-- Add comment for documentation
COMMENT ON TABLE credit_transactions IS 'Tracks all credit operations: grants, deductions, usage, and refunds';
COMMENT ON COLUMN credit_transactions.transaction_type IS 'Values: admin_grant, admin_deduct, reservation_use, reservation_refund';


-- =====================================================
-- TABLE 2: reservation_cancellations
-- Purpose: Historical record of cancelled reservations
-- =====================================================

CREATE TABLE IF NOT EXISTS reservation_cancellations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_reservation_id INTEGER,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    user_email VARCHAR(255) NOT NULL,
    user_name VARCHAR(255) NOT NULL,
    reservation_date DATE NOT NULL,
    reservation_hour INTEGER NOT NULL,
    cancellation_reason TEXT,
    cancelled_by VARCHAR(255) NOT NULL,
    cancelled_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    credits_refunded INTEGER DEFAULT 1
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_reservation_cancellations_user_id ON reservation_cancellations(user_id);
CREATE INDEX IF NOT EXISTS idx_reservation_cancellations_date ON reservation_cancellations(reservation_date DESC);
CREATE INDEX IF NOT EXISTS idx_reservation_cancellations_cancelled_at ON reservation_cancellations(cancelled_at DESC);

-- Add comment for documentation
COMMENT ON TABLE reservation_cancellations IS 'Historical audit trail of all cancelled reservations';
COMMENT ON COLUMN reservation_cancellations.original_reservation_id IS 'ID of the original reservation before deletion';
COMMENT ON COLUMN reservation_cancellations.cancelled_by IS 'Username of admin who cancelled, or "user" if self-cancelled';


-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Check that tables were created
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('credit_transactions', 'reservation_cancellations')
ORDER BY table_name;

-- Check columns for credit_transactions
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'credit_transactions'
ORDER BY ordinal_position;

-- Check columns for reservation_cancellations
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'reservation_cancellations'
ORDER BY ordinal_position;

-- Check indexes were created
SELECT tablename, indexname
FROM pg_indexes
WHERE tablename IN ('credit_transactions', 'reservation_cancellations')
ORDER BY tablename, indexname;

-- Check foreign key constraints
SELECT
    tc.table_name,
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name IN ('credit_transactions', 'reservation_cancellations')
AND tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name;


-- =====================================================
-- SUCCESS MESSAGE
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '===========================================';
    RAISE NOTICE '✅ TABLES CREATED SUCCESSFULLY';
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Tables added:';
    RAISE NOTICE '  1. credit_transactions';
    RAISE NOTICE '  2. reservation_cancellations';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '  1. Run verification queries above';
    RAISE NOTICE '  2. Test Admin App - Credits tab';
    RAISE NOTICE '  3. Test Admin App - Reservas tab';
    RAISE NOTICE '===========================================';
END $$;
