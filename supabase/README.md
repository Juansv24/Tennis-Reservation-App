# Supabase Migrations

This directory contains SQL migrations for the Tennis Reservation App Supabase database.

## How to Apply Migrations

### Option 1: Manual Application via Supabase Dashboard (Recommended for testing)

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Navigate to **SQL Editor** (left sidebar)
4. Click **New Query**
5. Copy the entire contents of the migration file (e.g., `0001_add_query_indexes.sql`)
6. Paste into the query editor
7. Click **Run**
8. Verify success (no errors)

### Option 2: Using Supabase CLI (For production/automated deployments)

```bash
# Install Supabase CLI (if not already installed)
npm install -g supabase

# Login to Supabase
supabase login

# Link project
supabase link --project-ref YOUR_PROJECT_REF

# Push migrations to remote database
supabase db push

# Pull latest remote schema
supabase db pull
```

## Migration Files

### 0001_add_query_indexes.sql

**Purpose**: Create database indexes for frequently queried columns

**Target**: Production database optimization for 10-15 concurrent users

**Changes**:
- Adds indexes on:
  - `users.email` - VIP status checks, credit queries
  - `reservations.date` - Slot availability checks
  - `reservations.email` - User's own reservations
  - `maintenance_slots.date` - Maintenance slot queries
  - `email_verifications.code` - Email verification lookups
  - Composite indexes on common query patterns (date + hour)

**Impact**:
- SELECT queries: ✅ Much faster (10-100x depending on data size)
- INSERT/UPDATE/DELETE: ⚠️ Slightly slower (index maintenance overhead)
- Overall: ✅ Net positive (reads >> writes in this application)

**Estimated Performance Improvement**:
- Concurrent user capacity: +30-50% improvement
- Query response time: -50-70% for indexed queries

## Database Schema

The application uses these tables:
- `users` - User accounts and credits
- `vip_users` - VIP status mapping
- `reservations` - Court reservations
- `maintenance_slots` - Maintenance schedule
- `email_verifications` - Email verification codes
- `lock_code` - Dynamic lock codes
- `sessions` - User sessions

## Best Practices

1. **Test migrations in development first** before applying to production
2. **Backup your database** before running migrations on production
3. **Review the SQL** before executing
4. **Monitor performance** after migrations are applied
5. **Document any manual changes** you make to the schema

## Troubleshooting

If an index creation fails:

1. Check if the index already exists: Run `SELECT * FROM pg_indexes WHERE indexname = 'idx_name'`
2. If it exists, you can safely skip it
3. Ensure the column exists and has data
4. Check for sufficient disk space
5. Review PostgreSQL error messages in Supabase

## Rollback

If you need to remove an index:

```sql
DROP INDEX IF EXISTS idx_name;
```

Example for all indexes from 0001:

```sql
DROP INDEX IF EXISTS idx_users_email;
DROP INDEX IF EXISTS idx_users_id;
-- ... etc
```
