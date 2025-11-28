-- Migration: Add database indexes for frequently queried columns
-- Purpose: Optimize query performance for concurrent users (10-15 concurrent)
-- Created: 2024-11-28

-- Users table indexes
-- Reason: email is frequently queried by is_vip_user(), get_user_credits()
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
-- Reason: id is used in joins and user lookups
CREATE INDEX IF NOT EXISTS idx_users_id ON users(id);

-- VIP users table indexes
-- Reason: email is frequently checked for VIP status
CREATE INDEX IF NOT EXISTS idx_vip_users_email ON vip_users(email);

-- Reservations table indexes
-- Reason: date is frequently queried for slot availability checks
CREATE INDEX IF NOT EXISTS idx_reservations_date ON reservations(date);
-- Reason: email is used to filter user's own reservations
CREATE INDEX IF NOT EXISTS idx_reservations_email ON reservations(email);
-- Reason: user_id is used for user-specific queries
CREATE INDEX IF NOT EXISTS idx_reservations_user_id ON reservations(user_id);
-- Reason: Composite index for typical query pattern: WHERE date = ? AND hour = ?
CREATE INDEX IF NOT EXISTS idx_reservations_date_hour ON reservations(date, hour);

-- Maintenance slots table indexes
-- Reason: date is frequently queried for maintenance checks
CREATE INDEX IF NOT EXISTS idx_maintenance_slots_date ON maintenance_slots(date);
-- Reason: Composite index for typical query pattern: WHERE date = ? AND hour = ?
CREATE INDEX IF NOT EXISTS idx_maintenance_slots_date_hour ON maintenance_slots(date, hour);

-- Email verifications table indexes
-- Reason: verification_code is looked up during email verification
CREATE INDEX IF NOT EXISTS idx_email_verifications_code ON email_verifications(verification_code);
-- Reason: email is used to clean up old verification records
CREATE INDEX IF NOT EXISTS idx_email_verifications_email ON email_verifications(email);
-- Reason: expires_at is checked for expired verification codes
CREATE INDEX IF NOT EXISTS idx_email_verifications_expires_at ON email_verifications(expires_at);

-- Notes for manual Supabase application:
-- 1. Copy these CREATE INDEX statements
-- 2. Go to Supabase Dashboard > SQL Editor
-- 3. Create new query and paste the statements
-- 4. Run them in your target database (dev, staging, or production)
-- 5. Verify indexes were created in the "Indexes" tab of each table

-- Performance impact:
-- - Write operations (INSERT, UPDATE, DELETE) will be slightly slower due to index maintenance
-- - Read operations (SELECT with WHERE clauses) will be significantly faster
-- - For tennis reservation app: Overall improvement expected, as reads >> writes
