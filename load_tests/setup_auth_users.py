"""
Setup script to create 10 test users in Supabase Auth
Creates both auth users and database users for load testing

IMPORTANT:
- First update the SUPABASE_URL and SUPABASE_KEY with your credentials
- Run this script to create all test users at once
- Make sure users table exists in your database
"""
import os
import sys
from pathlib import Path

# Add parent directory to path to import from User App
sys.path.insert(0, str(Path(__file__).parent.parent / "User App"))

try:
    from supabase import create_client
    from supabase.client import ClientOptions
except ImportError:
    print("❌ Supabase library not installed. Install with: pip install supabase")
    sys.exit(1)

# ============================================================================
# CONFIGURATION - UPDATE THESE
# ============================================================================

# Get from Supabase Dashboard > Project Settings > API
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_SERVICE_KEY = "YOUR_SERVICE_ROLE_KEY"  # Use SERVICE_ROLE key, not anon key

# Test user password (same for all)
TEST_PASSWORD = "TestPassword123!"

# Test users to create
TEST_USERS = [
    ("user1@test.local", "Test User 1"),
    ("user2@test.local", "Test User 2"),
    ("user3@test.local", "Test User 3"),
    ("user4@test.local", "Test User 4"),
    ("user5@test.local", "Test User 5"),
    ("user6@test.local", "Test User 6"),
    ("user7@test.local", "Test User 7"),
    ("user8@test.local", "Test User 8"),
    ("user9@test.local", "Test User 9"),
    ("user10@test.local", "Test User 10"),
]

# ============================================================================

def create_auth_users():
    """Create test users in Supabase Auth"""

    print("\n" + "=" * 80)
    print("SUPABASE TEST USER SETUP")
    print("=" * 80)

    # Validate configuration
    if SUPABASE_URL.startswith("https://YOUR_"):
        print("❌ ERROR: SUPABASE_URL not configured")
        print("   Update SUPABASE_URL in this script with your project URL")
        print("   Find it in: Supabase Dashboard > Project Settings > API")
        return False

    if SUPABASE_SERVICE_KEY.startswith("YOUR_"):
        print("❌ ERROR: SUPABASE_SERVICE_KEY not configured")
        print("   Update SUPABASE_SERVICE_KEY in this script")
        print("   ⚠️  IMPORTANT: Use SERVICE_ROLE key, NOT anon key!")
        print("   Find it in: Supabase Dashboard > Project Settings > API")
        return False

    print(f"✅ Supabase URL: {SUPABASE_URL}")
    print(f"✅ Creating {len(TEST_USERS)} test users...")
    print()

    # Initialize Supabase client with service role
    try:
        client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {str(e)}")
        return False

    created_count = 0
    failed_count = 0

    # Create each user
    for email, full_name in TEST_USERS:
        try:
            print(f"📝 Creating {email}...", end=" ")

            # Create auth user via Supabase admin API
            response = client.auth.admin.create_user({
                "email": email,
                "password": TEST_PASSWORD,
                "email_confirm": True,  # Mark email as verified
                "user_metadata": {
                    "full_name": full_name
                }
            })

            user_id = response.user.id
            print(f"✅ (ID: {user_id})")
            created_count += 1

            # Also create entry in users table if it exists
            try:
                client.table("users").insert({
                    "id": user_id,
                    "email": email,
                    "full_name": full_name,
                    "credits": 10,
                    "is_verified": True,
                }).execute()
                print(f"   ✅ Added to users table")
            except Exception as e:
                if "duplicate" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"   ℹ️  Already exists in users table")
                else:
                    print(f"   ⚠️  Could not add to users table: {str(e)}")

        except Exception as e:
            error_msg = str(e)
            if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                print(f"⚠️  Already exists (skipped)")
            else:
                print(f"❌ Failed: {error_msg}")
                failed_count += 1

    # Print summary
    print("\n" + "=" * 80)
    print("SETUP SUMMARY")
    print("=" * 80)
    print(f"✅ Successfully created: {created_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"Total: {created_count + failed_count}/{len(TEST_USERS)}")
    print()

    if created_count > 0:
        print("✅ Test users ready for load testing!")
        print(f"   Email pattern: user1@test.local through user{len(TEST_USERS)}@test.local")
        print(f"   Password: {TEST_PASSWORD}")
        print()
        print("📝 Next steps:")
        print("   1. Update load_tests/config.py with the test password")
        print("   2. Run: python load_tests/load_test_user_app.py")
        return True
    else:
        print("❌ No users were created. Check configuration and try again.")
        return False


def verify_users():
    """Verify test users exist"""
    print("\n" + "=" * 80)
    print("VERIFY TEST USERS")
    print("=" * 80)

    try:
        client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

        # Check users table
        response = client.table("users").select("id, email, full_name, credits").eq("email", "user1@test.local").execute()

        if response.data:
            print(f"✅ Test users found in database:")
            for user in response.data:
                print(f"   - {user['email']} ({user['full_name']}) - Credits: {user['credits']}")
            return True
        else:
            print("❌ No test users found in database")
            return False

    except Exception as e:
        print(f"❌ Error verifying users: {str(e)}")
        return False


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Setup test users for load testing")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing users")
    args = parser.parse_args()

    if args.verify_only:
        success = verify_users()
    else:
        success = create_auth_users()
        if success:
            verify_users()

    print()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
