"""
Setup Test Users via Supabase API
Creates 10 test users for concurrent testing
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

os.chdir('C:/Users/jsval/OneDrive/Documents/Personal/Code/Python Proyects/Tennis-Reservation-App/Test')
# Load environment variables
load_dotenv('credentials.env')

# Supabase configuration
SUPABASE_URL = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Use service role key for admin operations

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ Error: Missing Supabase credentials")
    print("Please set NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env file")
    exit(1)

# Initialize Supabase client with service role
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Test users configuration - All VIP users with 99 credits for extensive testing
TEST_USERS = [
    {"email": "testuser1@test.com", "name": "Test User 1 VIP", "is_vip": True},
    {"email": "testuser2@test.com", "name": "Test User 2 VIP", "is_vip": True},
    {"email": "testuser3@test.com", "name": "Test User 3 VIP", "is_vip": True},
    {"email": "testuser4@test.com", "name": "Test User 4 VIP", "is_vip": True},
    {"email": "testuser5@test.com", "name": "Test User 5 VIP", "is_vip": True},
    {"email": "testuser6@test.com", "name": "Test User 6 VIP", "is_vip": True},
    {"email": "testuser7@test.com", "name": "Test User 7 VIP", "is_vip": True},
    {"email": "testuser8@test.com", "name": "Test User 8 VIP", "is_vip": True},
    {"email": "testuser9@test.com", "name": "Test User 9 VIP", "is_vip": True},
    {"email": "testuser10@test.com", "name": "Test User 10 VIP", "is_vip": True},
]

PASSWORD = "TestUser2024!"

def create_test_users():
    """Create test users via Supabase Admin API"""
    print("🔧 Creating test users...")
    created = 0
    skipped = 0

    for user_config in TEST_USERS:
        try:
            # Create user via Supabase Admin API
            response = supabase.auth.admin.create_user({
                "email": user_config["email"],
                "password": PASSWORD,
                "email_confirm": True,  # Auto-confirm email
                "user_metadata": {
                    "full_name": user_config["name"]
                }
            })

            if response.user:
                user_id = response.user.id

                # Update user profile in public.users table - 99 credits for extensive testing
                supabase.table('users').update({
                    'full_name': user_config["name"],
                    'credits': 99,
                    'is_vip': user_config["is_vip"],
                    'first_login_completed': True
                }).eq('id', user_id).execute()

                print(f"✅ Created: {user_config['email']} (VIP: {user_config['is_vip']}, Credits: 99)")
                created += 1

        except Exception as e:
            if "already registered" in str(e).lower() or "already exists" in str(e).lower():
                print(f"⏭️  Skipped: {user_config['email']} (already exists)")
                skipped += 1
            else:
                print(f"❌ Error creating {user_config['email']}: {e}")

    print(f"\n📊 Summary:")
    print(f"   Created: {created}")
    print(f"   Skipped: {skipped}")
    print(f"   Total: {len(TEST_USERS)}")
    print(f"\n🔑 Password for all test users: {PASSWORD}")

def cleanup_test_users():
    """Delete all test users (use with caution!)"""
    print("🗑️  Cleaning up test users...")

    response = input("⚠️  This will DELETE all test users. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return

    deleted = 0
    for user_config in TEST_USERS:
        try:
            # Get user by email
            users = supabase.auth.admin.list_users()
            user = next((u for u in users if u.email == user_config["email"]), None)

            if user:
                supabase.auth.admin.delete_user(user.id)
                print(f"🗑️  Deleted: {user_config['email']}")
                deleted += 1
        except Exception as e:
            print(f"❌ Error deleting {user_config['email']}: {e}")

    print(f"\n✅ Deleted {deleted} test users")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        cleanup_test_users()
    else:
        create_test_users()
