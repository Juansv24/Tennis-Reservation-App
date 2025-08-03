"""
Simplified Authentication System for Tennis Court Reservation
Removed session token functionality - only basic email/password authentication
"""

import sqlite3
import hashlib
import secrets
from typing import Optional, Dict, Tuple
import contextlib
from database_manager import DATABASE_FILE

class AuthManager:
    """Simplified authentication manager without session tokens"""

    def __init__(self, db_file: str = DATABASE_FILE):
        self.db_file = db_file
        self.init_auth_tables()

    @contextlib.contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_file)
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def init_auth_tables(self):
        """Create auth tables - simplified without sessions"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')

            conn.commit()

    def _hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """Generate hash with salt"""
        if salt is None:
            salt = secrets.token_hex(16)

        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return password_hash, salt

    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def _validate_password(self, password: str) -> Tuple[bool, str]:
        """Validate password strength"""
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"

        if len(password) > 50:
            return False, "Password must be less than 50 characters"

        has_letter = any(c.isalpha() for c in password)
        has_number = any(c.isdigit() for c in password)

        if not (has_letter and has_number):
            return False, "Password must contain at least one letter and one number"

        return True, "Password is valid"

    def register_user(self, email: str, password: str, full_name: str) -> Tuple[bool, str]:
        """Register user"""
        try:
            if not email or not self._validate_email(email):
                return False, "Please enter a valid email address"

            if not full_name or len(full_name.strip()) < 2:
                return False, "Please enter a valid full name"

            is_valid_password, password_message = self._validate_password(password)
            if not is_valid_password:
                return False, password_message

            email = email.strip().lower()
            full_name = full_name.strip()

            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
                if cursor.fetchone():
                    return False, "An account with this email already exists"

                password_hash, salt = self._hash_password(password)

                cursor.execute('''
                    INSERT INTO users (email, password_hash, salt, full_name)
                    VALUES (?, ?, ?, ?)
                ''', (email, password_hash, salt, full_name))

                conn.commit()
                return True, "Account created successfully"

        except Exception as e:
            return False, f"Error creating account: {str(e)}"

    def login_user(self, email: str, password: str, remember_me: bool = False) -> Tuple[bool, str, Optional[Dict]]:
        """Login user - remember_me parameter kept for compatibility but ignored"""
        try:
            if not email or not password:
                return False, "Please enter both email and password", None

            email = email.strip().lower()

            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT id, email, password_hash, salt, full_name, is_active
                    FROM users 
                    WHERE email = ?
                ''', (email,))

                user_data = cursor.fetchone()

                if not user_data:
                    return False, "Invalid email or password", None

                user_id, user_email, stored_hash, salt, full_name, is_active = user_data

                if not is_active:
                    return False, "Account is deactivated", None

                password_hash, _ = self._hash_password(password, salt)

                if password_hash != stored_hash:
                    return False, "Invalid email or password", None

                # Update last login
                cursor.execute('''
                    UPDATE users 
                    SET last_login = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (user_id,))
                conn.commit()

                user_info = {
                    'id': user_id,
                    'email': user_email,
                    'full_name': full_name
                    # No session_token in simplified version
                }

                return True, "Login successful", user_info

        except Exception as e:
            return False, f"Login error: {str(e)}", None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT id, email, full_name, created_at, last_login
                    FROM users 
                    WHERE id = ? AND is_active = 1
                ''', (user_id,))

                user_data = cursor.fetchone()

                if user_data:
                    return {
                        'id': user_data[0],
                        'email': user_data[1],
                        'full_name': user_data[2],
                        'created_at': user_data[3],
                        'last_login': user_data[4]
                    }

                return None

        except Exception:
            return None

    def change_password(self, user_id: int, current_password: str, new_password: str) -> Tuple[bool, str]:
        """Change password"""
        try:
            is_valid_password, password_message = self._validate_password(new_password)
            if not is_valid_password:
                return False, password_message

            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT password_hash, salt FROM users WHERE id = ?
                ''', (user_id,))

                user_data = cursor.fetchone()
                if not user_data:
                    return False, "User not found"

                stored_hash, salt = user_data

                current_hash, _ = self._hash_password(current_password, salt)
                if current_hash != stored_hash:
                    return False, "Current password is incorrect"

                new_hash, new_salt = self._hash_password(new_password)

                cursor.execute('''
                    UPDATE users 
                    SET password_hash = ?, salt = ?
                    WHERE id = ?
                ''', (new_hash, new_salt, user_id))

                conn.commit()
                return True, "Password changed successfully. Please sign in again."

        except Exception as e:
            return False, f"Error changing password: {str(e)}"

    def update_user_profile(self, user_id: int, full_name: str) -> Tuple[bool, str]:
        """Update user profile"""
        try:
            if not full_name or len(full_name.strip()) < 2:
                return False, "Please enter a valid full name"

            full_name = full_name.strip()

            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    UPDATE users 
                    SET full_name = ?
                    WHERE id = ?
                ''', (full_name, user_id))

                if cursor.rowcount > 0:
                    conn.commit()
                    return True, "Profile updated successfully"
                else:
                    return False, "User not found"

        except Exception as e:
            return False, f"Error updating profile: {str(e)}"

    # Session methods kept for compatibility but do nothing
    def validate_session(self, session_token: str) -> Optional[Dict]:
        """Compatibility method - returns None as sessions not supported"""
        return None

    def destroy_session(self, session_token: str) -> bool:
        """Compatibility method - returns True but does nothing"""
        return True

    def destroy_all_user_sessions(self, user_id: int) -> bool:
        """Compatibility method - returns True but does nothing"""
        return True

# Global instance
auth_manager = AuthManager()