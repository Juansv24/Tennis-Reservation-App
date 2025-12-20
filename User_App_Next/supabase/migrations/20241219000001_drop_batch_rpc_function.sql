-- Migration: Drop RPC batch reservations function
-- Reverting to transaction-based approach due to JSONB parameter serialization issues
-- See docs/RPC_JSONB_PARAMETER_ISSUE.md for details

-- Drop all versions of the function
DROP FUNCTION IF EXISTS create_batch_reservations(UUID, TEXT, INTEGER);
DROP FUNCTION IF EXISTS create_batch_reservations(UUID, JSONB, INTEGER);

-- Note: This migration removes the atomic RPC approach.
-- Batch reservations will now be handled via transactions in the API layer.
