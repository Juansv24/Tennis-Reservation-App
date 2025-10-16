# Database Migrations - Tennis Reservation System

This folder contains SQL migrations and optimizations for the Supabase database.

## 📋 Available Migrations

### 1. `optimize_user_statistics.sql` - User Statistics Optimization

**Purpose:** Replaces inefficient Python loops with a single optimized SQL query.

**Performance Improvement:**
- **Before:** 3 separate database queries + nested loops in Python
- **After:** 1 optimized SQL query with JOINs and aggregations
- **Speed:** ~10-50x faster depending on data size

**What it does:**
- Calculates total credits bought per user
- Counts total reservations per user
- Finds favorite day of the week for reservations
- Finds favorite time slot for reservations
- All in a single database operation!

---

## 🚀 How to Install a Migration

### Step-by-Step Instructions:

1. **Open Supabase Dashboard**
   - Go to https://supabase.com
   - Select your project: "Tennis Reservation System"

2. **Navigate to SQL Editor**
   - Click on "SQL Editor" in the left sidebar
   - Click "New query"

3. **Copy the SQL File**
   - Open the migration file (e.g., `optimize_user_statistics.sql`)
   - Copy the entire contents

4. **Paste and Run**
   - Paste the SQL into the Supabase SQL Editor
   - Click "Run" (or press Ctrl+Enter / Cmd+Enter)

5. **Verify Success**
   - You should see: "Success. No rows returned"
   - The function is now available!

6. **Test the Function (Optional)**
   ```sql
   SELECT * FROM get_users_detailed_statistics() LIMIT 5;
   ```

---

## ✅ Migration Status

| Migration File | Status | Date Applied | Notes |
|---------------|--------|--------------|-------|
| `optimize_user_statistics.sql` | ⏳ Pending | - | Run this in Supabase! |

---

## 🔄 Rollback (if needed)

If you need to remove the optimization function:

```sql
DROP FUNCTION IF EXISTS get_users_detailed_statistics();
```

The app will automatically fall back to the Python implementation.

---

## 📝 Notes

- All migrations are **backwards compatible**
- If a SQL function doesn't exist, the app uses a fallback method
- No downtime required for applying migrations
- Always test migrations in a development environment first (if available)

---

## 🆘 Troubleshooting

**Error: "function does not exist"**
- Make sure you ran the migration in Supabase SQL Editor
- Check that you selected the correct database/project

**Error: "permission denied"**
- Ensure you have admin/owner access to the Supabase project

**Function not improving performance**
- Clear any caches in your app
- Restart the Streamlit app
- Check Supabase logs for any errors

---

## 📧 Questions?

If you encounter any issues, check:
1. Supabase logs (Dashboard → Logs)
2. Python application logs
3. The fallback method should work even if migration fails
