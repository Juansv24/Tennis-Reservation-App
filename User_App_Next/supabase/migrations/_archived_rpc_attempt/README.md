# Archived RPC Migrations

**Date Archived**: December 19, 2025

## Why These Files Are Archived

These migration files represent an unsuccessful attempt to implement atomic batch reservations using a PostgreSQL RPC function with JSONB array parameters.

The approach encountered persistent "invalid input syntax for type json" errors due to serialization issues between the Supabase JavaScript client and PostgreSQL's JSONB type system.

## Files in This Directory

- `20241218000000_atomic_batch_reservations.sql` - Original RPC function with TEXT parameter
- `20241219000000_fix_batch_reservations_jsonb.sql` - Attempted fix changing to JSONB parameter

## What Happened

Multiple attempts were made to resolve the parameter serialization issue:
1. Changed parameter from TEXT to JSONB
2. Tried explicit client-side serialization
3. Attempted string serialization
4. Tried explicit parsing within the function

None of these approaches succeeded. See `/docs/RPC_JSONB_PARAMETER_ISSUE.md` for complete technical analysis.

## Current Solution

The project now uses a **transaction-based approach** directly in the API route layer, which:
- Avoids JSONB parameter serialization issues
- Uses PostgreSQL transactions with row-level locking
- Provides the same atomicity guarantees
- Is easier to debug and maintain

## Do Not Use These Files

These migrations should **NOT** be applied to any database. They are kept for:
- Historical reference
- Learning purposes
- Troubleshooting similar issues in the future

The RPC function has been dropped via migration `20241219000001_drop_batch_rpc_function.sql`.
