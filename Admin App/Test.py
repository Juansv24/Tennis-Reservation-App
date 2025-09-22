import secrets
import string


def generate_salt(length=64):
    """Generate a cryptographically secure salt"""
    # Use letters, digits, and safe symbols
    characters = string.ascii_letters + string.digits + "_-"
    return ''.join(secrets.choice(characters) for _ in range(length))


def generate_multiple_salts():
    """Generate salts of different lengths"""
    print("=== SECURE SALT GENERATOR ===\n")

    # Different lengths for different needs
    lengths = [32, 64, 128]

    for length in lengths:
        salt = generate_salt(length)
        print(f"Salt ({length} chars): {salt}")
        print(f"Length check: {len(salt)} characters")
        print("-" * 50)

    print("\nRECOMMENDED FOR YOUR PROJECT:")
    recommended_salt = generate_salt(64)
    print(f"salt = \"{recommended_salt}\"")
    print(f"\nCopy this to your secrets.toml:")
    print(f'[admin]')
    print(f'default_password = "Tenis_Colina55!"')
    print(f'salt = "{recommended_salt}"')


if __name__ == "__main__":
    generate_multiple_salts()