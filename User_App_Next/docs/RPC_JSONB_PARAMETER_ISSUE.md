# Technical Analysis: RPC JSONB Parameter Issue

## Document Information
- **Date**: December 19, 2025
- **Project**: Tennis Reservation App (User_App_Next)
- **Issue**: PostgreSQL RPC function failing with "invalid input syntax for type json"
- **Severity**: Critical - Blocking atomic batch reservations feature
- **Status**: Unresolved - Pivoted to alternative solution

---

## Executive Summary

An attempt to implement atomic batch reservations using a PostgreSQL RPC function encountered a persistent "invalid input syntax for type json" error when passing array parameters from the Supabase JavaScript client to a JSONB function parameter. Despite multiple attempts to resolve the parameter serialization issue, the problem remained unresolved, leading to a pivot toward a transaction-based approach without custom RPC functions.

---

## Background

### Objective
Implement atomic batch reservations to eliminate race conditions when multiple users attempt to reserve the same court time slots simultaneously.

### Initial Approach
Created a PostgreSQL function `create_batch_reservations` that would:
1. Accept an array of reservation objects (date + hour)
2. Use advisory locks to prevent concurrent reservations
3. Validate all slots in a single transaction
4. Insert all reservations atomically
5. Deduct credits from user account

### Technology Stack
- **Frontend/API**: Next.js 16.0.7, TypeScript 5
- **Database Client**: @supabase/supabase-js v2.86.2
- **Database**: PostgreSQL (via Supabase)
- **API Layer**: PostgREST (Supabase's REST API layer)

---

## Timeline of Errors and Attempted Fixes

### Phase 1: Initial Implementation - TEXT Parameter Type

#### Migration File
`supabase/migrations/20241218000000_atomic_batch_reservations.sql`

#### Function Signature
```sql
CREATE OR REPLACE FUNCTION create_batch_reservations(
  p_user_id UUID,
  p_reservations TEXT, -- Array of {date: 'YYYY-MM-DD', hour: number} as JSON string
  p_credits_needed INTEGER
) RETURNS JSONB
```

#### Error Encountered
```
Error del sistema: invalid input syntax for type json
```

#### Client Code
```typescript
const { data: result, error: rpcError } = await supabase
  .rpc('create_batch_reservations', {
    p_user_id: user.id,
    p_reservations: reservations, // JavaScript array
    p_credits_needed: creditsNeeded
  })
```

#### Debug Output
```
reservations: [
  {
    "date": "2025-12-20",
    "hour": 13
  },
  {
    "date": "2025-12-20",
    "hour": 14
  }
]
reservations type: object
reservations isArray: true
creditsNeeded: 2
```

#### Root Cause Analysis
The function parameter was declared as `TEXT`, but the Supabase JavaScript client automatically serializes JavaScript objects/arrays to JSON format. When PostgreSQL received the JSON-formatted data, it expected TEXT but received JSON type data. The subsequent cast `p_reservations::jsonb` on line 47 failed because:

1. Parameter type is TEXT
2. Supabase client sends JavaScript array → auto-converts to JSON
3. PostgreSQL receives JSON type, but function expects TEXT
4. Cast from JSON → JSONB fails with "invalid input syntax for type json"

#### SQL Function Usage
```sql
FROM jsonb_array_elements(p_reservations::jsonb) AS elem
```

This cast failed because the data received wasn't in TEXT format that could be cast to JSONB.

---

### Phase 2: First Fix Attempt - JSONB Parameter Type

#### Migration File
`supabase/migrations/20241219000000_fix_batch_reservations_jsonb.sql`

#### Changes Made
1. Changed parameter type from `TEXT` to `JSONB`
```sql
CREATE OR REPLACE FUNCTION create_batch_reservations(
  p_user_id UUID,
  p_reservations JSONB, -- Array of {date: 'YYYY-MM-DD', hour: number}
  p_credits_needed INTEGER
) RETURNS JSONB
```

2. Removed all `::jsonb` casts since parameter is already JSONB
```sql
FROM jsonb_array_elements(p_reservations) AS elem
-- Previously: jsonb_array_elements(p_reservations::jsonb)
```

#### Expected Outcome
With JSONB parameter type, PostgreSQL should accept JSON data directly from the client, and the `jsonb_array_elements()` function should work without additional casting.

#### Actual Result
**Error persisted**: Same "invalid input syntax for type json" error

#### Verification
Function signature confirmed in database:
```sql
SELECT pg_get_function_arguments(p.oid) as arguments
FROM pg_proc p
WHERE p.proname = 'create_batch_reservations';

-- Result:
-- arguments: "p_user_id uuid, p_reservations jsonb, p_credits_needed integer"
```

Function signature was correct, but error continued.

#### Error Details
```
Error del sistema: invalid input syntax for type json (State: 22P02)
```

SQL State Code: **22P02** - `invalid_text_representation`
- Indicates PostgreSQL is trying to parse text as JSON and failing
- Suggests the JSONB parameter is receiving data in an unexpected format

---

### Phase 3: Client-Side Serialization Attempt

#### Hypothesis
Maybe the Supabase JavaScript client needs explicit serialization of the array parameter.

#### Code Changes
```typescript
// Attempt 1: Deep clone (no effect expected)
const reservationsJson = JSON.parse(JSON.stringify(reservations))

const { data: result, error: rpcError } = await supabase
  .rpc('create_batch_reservations', {
    p_user_id: user.id,
    p_reservations: reservationsJson,
    p_credits_needed: creditsNeeded
  })
```

#### Result
No change - this was essentially a no-op since it just created a deep clone of the same JavaScript array.

---

### Phase 4: String Serialization Attempt

#### Hypothesis
Based on PostgREST issues and Supabase discussions, some configurations require JSONB parameters to be sent as stringified JSON.

#### Code Changes
```typescript
// Explicitly stringify the array
const reservationsString = JSON.stringify(reservations)
console.log('reservationsString:', reservationsString)

const { data: result, error: rpcError } = await supabase
  .rpc('create_batch_reservations', {
    p_user_id: user.id,
    p_reservations: reservationsString, // Now a string
    p_credits_needed: creditsNeeded
  })
```

#### Error Encountered
```
Error del sistema: cannot extract elements from a scalar (State: 22023)
```

SQL State Code: **22023** - `invalid_parameter_value`

#### Root Cause
When passing a stringified JSON to a JSONB parameter, PostgreSQL performs the following:

1. Receives string: `"[{\"date\":\"2025-12-20\",\"hour\":9}...]"`
2. Parses it as JSONB → Creates JSONB **string value** (a scalar)
3. The JSONB type now contains: `"[...]"` as a string literal, not as an array
4. When `jsonb_array_elements(p_reservations)` is called, it fails because:
   - `p_reservations` is a JSONB string (scalar)
   - `jsonb_array_elements()` requires a JSONB array
   - Error: "cannot extract elements from a scalar"

#### Diagram: Double-Serialization Problem
```
JavaScript Array → JSON.stringify() → JSON String
                                         ↓
                               Supabase Client sends
                                         ↓
                            PostgreSQL JSONB parameter
                                         ↓
                            Parses as JSONB String (scalar)
                                         ↓
                            jsonb_array_elements() fails
                            (expects array, got string)
```

---

### Phase 5: TEXT Parameter with Explicit Parsing

#### Hypothesis
Accept TEXT parameter and explicitly control the parsing to JSONB within the function.

#### Migration File
`supabase/FIX_batch_reservations.sql`

#### Function Signature
```sql
CREATE OR REPLACE FUNCTION create_batch_reservations(
  p_user_id UUID,
  p_reservations TEXT, -- JSON string to be parsed
  p_credits_needed INTEGER
) RETURNS JSONB
```

#### Implementation
```sql
DECLARE
  v_reservations_array JSONB;
BEGIN
  -- Parse the TEXT parameter to JSONB
  BEGIN
    v_reservations_array := p_reservations::JSONB;
  EXCEPTION
    WHEN OTHERS THEN
      RETURN jsonb_build_object(
        'success', false,
        'error', format('Invalid JSON format: %s', SQLERRM)
      );
  END;

  -- Validate it's an array
  IF jsonb_typeof(v_reservations_array) != 'array' THEN
    RETURN jsonb_build_object(
      'success', false,
      'error', 'Reservations must be an array'
    );
  END IF;

  -- Use v_reservations_array for all subsequent operations
  FOR v_reservation IN SELECT * FROM jsonb_array_elements(v_reservations_array)
  LOOP
    -- ...
  END LOOP;
END;
```

#### Client Code
```typescript
const reservationsString = JSON.stringify(reservations)

const { data: result, error: rpcError } = await supabase
  .rpc('create_batch_reservations', {
    p_user_id: user.id,
    p_reservations: reservationsString,
    p_credits_needed: creditsNeeded
  })
```

#### Result
**Not working** - Specific error not provided, but approach failed.

---

## Debugging Attempts

### Added Debug Logging to SQL Function
Created `DEBUG_batch_reservations.sql` with extensive RAISE NOTICE statements:

```sql
BEGIN
  -- DEBUG: Log what we received
  RAISE NOTICE 'DEBUG: p_reservations type: %', pg_typeof(p_reservations);
  RAISE NOTICE 'DEBUG: p_reservations value: %', p_reservations;
  RAISE NOTICE 'DEBUG: p_reservations is array: %', jsonb_typeof(p_reservations);

  -- ... more debug statements throughout

  RAISE NOTICE 'DEBUG: About to acquire locks';
  -- ... lock acquisition
  RAISE NOTICE 'DEBUG: Locks acquired, validating slots';

EXCEPTION
  WHEN OTHERS THEN
    RAISE NOTICE 'DEBUG: Exception caught: % %', SQLSTATE, SQLERRM;
END;
```

### Result
User did not provide Postgres logs output. Debug messages would have appeared in Supabase Dashboard → Logs → Postgres Logs, but were not retrieved.

---

## Possible Root Causes (Unconfirmed)

### 1. PostgREST Content-Type Handling
PostgREST (Supabase's REST API layer) may be setting specific Content-Type headers that affect how parameters are serialized. The JavaScript client might not be setting the correct headers for JSONB arrays.

### 2. Supabase Client Library Serialization
The `@supabase/supabase-js` v2.86.2 client library may have specific behavior for how it serializes array/object parameters when calling RPC functions.

**Known issues from research:**
- "Invalid input syntax for type json" can occur with Unicode encoding issues
- PostgREST has issues with `Prefer: params=single-object` header and empty bodies
- Some users report needing to stringify JSONB parameters, others report needing to pass objects directly

### 3. PostgreSQL Extension or Configuration
There may be a PostgreSQL extension or configuration setting in the Supabase instance that affects JSON/JSONB parsing.

### 4. Type Coercion Ambiguity
PostgreSQL might be unable to determine the correct type coercion path from the received data type to the expected JSONB parameter type.

---

## Research Findings

### Supabase/PostgREST Issues
Multiple GitHub discussions found with similar issues:

1. **[POST randomly started failing: invalid input syntax for type json](https://github.com/orgs/supabase/discussions/7319)**
   - Users experiencing similar errors
   - Often related to Unicode encoding or malformed JSON

2. **[POST with no body calls RPC function with json argument; crashes](https://github.com/PostgREST/postgrest/issues/2399)**
   - Issue with `Prefer: params=single-object` header
   - Empty POST bodies cause crashes
   - Workaround: Omit the header for parameterless calls

3. **[Invalid input syntax for type json](https://github.com/orgs/supabase/discussions/33779)**
   - Similar error reported
   - No resolution provided in thread

### PostgreSQL Best Practices
From official documentation:

1. **JSONB vs TEXT for JSON Data**
   - JSONB provides automatic validation
   - JSONB stores data in binary format (faster processing)
   - TEXT requires manual parsing with `::jsonb` cast
   - **Recommendation**: Use JSONB for function parameters receiving JSON

2. **JSON Type Casting**
   - TEXT → JSONB: `text_value::jsonb`
   - JSONB → TEXT: `jsonb_value::text`
   - JSON → JSONB: Implicit cast available
   - String literal → JSONB: Creates JSONB string, not parsed object

---

## What We Learned

### 1. PostgreSQL Type System Complexity
- TEXT, JSON, and JSONB are distinct types with different casting rules
- Passing stringified JSON to JSONB parameter creates a JSONB string (scalar), not a parsed structure
- Type coercion doesn't always work intuitively across client-server boundaries

### 2. Supabase/PostgREST Layer Abstraction
- The JavaScript client abstracts away HTTP details
- Unclear how parameters are serialized before sending to PostgREST
- PostgREST adds another layer of type handling before reaching PostgreSQL
- Debugging requires access to multiple layers: Client → PostgREST → PostgreSQL

### 3. Limited Debugging Visibility
- RAISE NOTICE messages only appear in Postgres logs (not client-side)
- Error messages are caught by EXCEPTION handlers and returned as JSONB
- Difficult to see actual parameter values received by PostgreSQL
- No visibility into PostgREST's parameter transformation

### 4. Version-Specific Behavior
- Different Supabase client library versions may handle RPC parameters differently
- PostgREST versions may have different JSONB handling behavior
- Documentation may not reflect actual behavior in specific version combinations

---

## Attempted Workarounds Summary

| Attempt | Parameter Type | Client Sends | Result | Error Code |
|---------|---------------|--------------|--------|------------|
| 1 | TEXT | JavaScript Array | Failed | 22P02 (invalid_text_representation) |
| 2 | JSONB | JavaScript Array | Failed | 22P02 (invalid_text_representation) |
| 3 | JSONB | Deep Cloned Array | Failed | 22P02 (invalid_text_representation) |
| 4 | JSONB | JSON.stringify(array) | Failed | 22023 (cannot extract elements from scalar) |
| 5 | TEXT | JSON.stringify(array) | Failed | Unknown |

---

## Alternative Solutions Considered

### 1. Direct Database Transactions (Chosen Approach)
Instead of using RPC functions, implement atomic operations using:
- PostgreSQL transactions in the API route
- `SELECT ... FOR UPDATE` for row-level locking
- Sequential operations within a single transaction
- Automatic rollback on any failure

**Advantages:**
- Avoids JSONB parameter serialization issues entirely
- More transparent - all logic visible in TypeScript
- Easier to debug
- No RPC function maintenance required

**Disadvantages:**
- More verbose code in API route
- Business logic in application layer instead of database
- Requires multiple round-trips to database (within transaction)

### 2. Single-Reservation RPC Function
Create an RPC function that accepts a single reservation, call it multiple times:

```sql
CREATE FUNCTION create_single_reservation(
  p_user_id UUID,
  p_date DATE,
  p_hour INTEGER
) RETURNS JSONB
```

**Advantages:**
- No array/JSONB parameter issues
- Simpler function signature
- Primitive types only (UUID, DATE, INTEGER)

**Disadvantages:**
- Loses atomicity (can't lock all slots before inserting)
- Race conditions still possible
- Multiple database round-trips

### 3. Use PostgreSQL Arrays Instead of JSONB
```sql
CREATE TYPE reservation_slot AS (
  res_date DATE,
  res_hour INTEGER
);

CREATE FUNCTION create_batch_reservations(
  p_user_id UUID,
  p_reservations reservation_slot[], -- Array of composite type
  p_credits_needed INTEGER
) RETURNS JSONB
```

**Advantages:**
- Native PostgreSQL array type
- Strongly typed
- No JSON parsing required

**Disadvantages:**
- Client serialization still unclear
- More complex type definition
- May encounter similar serialization issues

### 4. Queue-Based Approach
Use a reservation queue table:
1. Insert reservation requests into queue
2. Background worker processes queue atomically
3. Notify client of success/failure

**Advantages:**
- Decouples client from atomic operations
- Can handle high concurrency
- Retry logic built-in

**Disadvantages:**
- Added complexity
- Requires background worker
- Delayed response to user
- Over-engineered for current scale

---

## Recommendations for Future

### 1. Avoid Complex RPC Parameters
When using Supabase RPC functions:
- Prefer primitive types (UUID, INTEGER, TEXT, DATE, BOOLEAN)
- Avoid JSONB parameters for complex structures
- If JSONB is necessary, thoroughly test serialization in target environment

### 2. Test in Production-Like Environment Early
- Local development may behave differently than production Supabase
- Test RPC functions with actual client library early in development
- Don't assume parameter serialization works as documented

### 3. Implement Comprehensive Logging
- Add extensive RAISE NOTICE statements to functions
- Log parameter types and values on entry
- Check Postgres logs regularly during development

### 4. Consider Transaction-Based Approaches First
- PostgreSQL transactions with row locking are well-understood
- Easier to debug than RPC parameter serialization
- More portable across different client libraries

### 5. Document Known Issues
- Maintain a document like this for future reference
- Record version numbers when encountering issues
- Share findings with team and community

---

## References

### Documentation
- [PostgreSQL JSON Functions and Operators](https://www.postgresql.org/docs/current/functions-json.html)
- [PostgreSQL JSON Types](https://www.postgresql.org/docs/current/datatype-json.html)
- [Supabase JavaScript API Reference - RPC](https://supabase.com/docs/reference/javascript/rpc)
- [PostgREST Functions as RPC](https://docs.postgrest.org/en/v12/references/api/functions.html)

### Related Issues
- [Supabase Discussion #7319: POST randomly started failing: invalid input syntax for type json](https://github.com/orgs/supabase/discussions/7319)
- [Supabase Discussion #33779: Invalid input syntax for type json](https://github.com/orgs/supabase/discussions/33779)
- [PostgREST Issue #2399: POST with no body calls RPC function with json argument; crashes](https://github.com/PostgREST/postgrest/issues/2399)

### Articles
- [JSON vs. JSONB in PostgreSQL: A Complete Comparison](https://www.dbvis.com/thetable/json-vs-jsonb-in-postgresql-a-complete-comparison/)
- [Caveat when using the RPC function with Supabase](https://iamjeremie.me/post/2025-03/caveat-when-using-the-rpc-function-with-supabase/)

---

## Conclusion

Despite following PostgreSQL and Supabase best practices, the JSONB parameter serialization issue remained unresolved after five different approaches. The root cause likely lies in the interaction between the Supabase JavaScript client (v2.86.2), PostgREST, and PostgreSQL's type system, but could not be definitively identified without deeper access to PostgREST's parameter handling and network-level debugging.

The decision to pivot to a transaction-based approach without RPC functions was made to:
1. Unblock feature development
2. Avoid further time investment in debugging opaque serialization issues
3. Implement a more maintainable solution with clearer debugging paths

This document serves as a reference for future developers who may encounter similar issues and as a case study in the complexity of type serialization across multi-layer architectures.

---

**Last Updated**: December 19, 2025
**Author**: Development Team
**Status**: Issue Unresolved - Alternative Solution Implemented
