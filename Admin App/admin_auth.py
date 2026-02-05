"""
Sistema de Autenticación Simple para Administradores
"""

import streamlit as st
import bcrypt
from database_manager import db_manager


class AdminAuthManager:
    """Gestor de autenticación para administradores"""

    def __init__(self):
        self.client = db_manager.client

    def _hash_password(self, password: str) -> str:
        """Generate bcrypt hash for password"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against bcrypt hash"""
        return bcrypt.checkpw(password.encode(), stored_hash.encode())

    def update_admin_credentials(self):
        """Update existing admin user with new secure credentials (bcrypt)"""
        try:
            # Get new credentials from secrets
            try:
                new_password = st.secrets["admin"]["default_password"]
            except KeyError:
                st.error("❌ Admin credentials not configured in secrets")
                return False

            # Validate new credentials
            if len(new_password) < 8:
                st.error("❌ New credentials don't meet security requirements")
                return False

            # Generate new bcrypt hash (salt is embedded in bcrypt hash)
            new_hash = self._hash_password(new_password)

            print(f"🔧 Updating admin credentials to bcrypt...")
            print(f"🔧 New hash format: bcrypt")

            # Update the admin user (salt field kept for legacy compatibility but not used for bcrypt)
            update_result = self.client.table('admin_users').update({
                'password_hash': new_hash,
                'salt': 'bcrypt'
            }).eq('username', 'admin').execute()

            if update_result.data:
                print("✅ Admin credentials updated successfully")
                st.success("✅ Admin credentials updated to use secure secrets")
                return True
            else:
                print("❌ Failed to update admin credentials")
                st.error("❌ Failed to update admin credentials")
                return False

        except Exception as e:
            print(f"❌ Error updating admin credentials: {e}")
            st.error(f"Error updating admin credentials: {e}")
            return False

    def ensure_admin_user_exists(self):
        """Ensure default admin user exists with secure credentials"""
        try:
            print("🔍 Checking admin user...")

            # Check if admin user exists
            result = self.client.table('admin_users').select('*').eq('username', 'admin').execute()

            if result.data:
                admin_user = result.data[0]
                stored_salt = admin_user['salt']

                # Check if using old hardcoded credentials
                if stored_salt == 'adminsalt123':
                    st.warning("⚠️ Admin user found with old hardcoded credentials")
                    st.info("🔧 Updating to secure credentials from secrets...")

                    # Update to new secure credentials
                    return self.update_admin_credentials()
                else:
                    print("✅ Admin user exists with secure credentials")
                    return True
            else:
                print("🔍 No admin user found, creating new one...")

                # Create new admin user with secure bcrypt credentials
                try:
                    admin_password = st.secrets["admin"]["default_password"]
                except KeyError:
                    st.error("❌ Credenciales de administrador no configuradas en secretos")
                    st.info("""
                    Para configurar el acceso de administrador, agrega a tus secretos de Streamlit:

                    [admin]
                    default_password = "TuContraseñaSeguraAquí"
                    """)
                    return False

                if len(admin_password) < 8:
                    st.error("❌ Las credenciales de administrador no cumplen los requisitos de seguridad")
                    st.info("""
                    Las credenciales de administrador deben cumplir:
                    - default_password: al menos 8 caracteres
                    """)
                    return False

                password_hash = self._hash_password(admin_password)

                insert_result = self.client.table('admin_users').insert({
                    'username': 'admin',
                    'password_hash': password_hash,
                    'salt': 'bcrypt',
                    'full_name': 'Administrador del Sistema',
                    'is_active': True
                }).execute()

                if insert_result.data:
                    print("✅ New admin user created with secure credentials")
                    return True
                else:
                    st.error("❌ Failed to create admin user")
                    return False

        except Exception as e:
            print(f"❌ Error in ensure_admin_user_exists: {e}")
            st.error(f"Error ensuring admin user exists: {e}")
            return False

    def validate_admin_config(self) -> bool:
        """Validate admin configuration is secure"""
        try:
            admin_password = st.secrets["admin"]["default_password"]

            # Check password strength
            if len(admin_password) < 12:
                st.warning("⚠️ Admin password should be at least 12 characters")

            if not any(c.isupper() for c in admin_password):
                st.warning("⚠️ Admin password should contain uppercase letters")

            if not any(c.islower() for c in admin_password):
                st.warning("⚠️ Admin password should contain lowercase letters")

            if not any(c.isdigit() for c in admin_password):
                st.warning("⚠️ Admin password should contain numbers")

            if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in admin_password):
                st.warning("⚠️ Admin password should contain special characters")

            return True
        except KeyError:
            st.error("❌ Credenciales de administrador no encontradas en secretos")
            st.info("""
            Para configurar el acceso de administrador, agrega a tus secretos de Streamlit:

            [admin]
            default_password = "TuContraseñaSeguraAquí"
            """)
            return False

    def login_admin(self, username: str, password: str) -> bool:
        """Iniciar sesión de administrador"""
        try:
            print(f"Attempting login for username: {username}")

            # Buscar admin en base de datos
            result = self.client.table('admin_users').select('*').eq(
                'username', username.strip()
            ).eq('is_active', True).execute()

            if not result.data:
                print("No admin user found in database")
                return False

            admin = result.data[0]
            print(f"Found admin: {admin['username']}")

            # Verify password with bcrypt
            is_valid = self._verify_password(password, admin['password_hash'])
            print(f"Authentication result: {'SUCCESS' if is_valid else 'FAILED'}")

            if not is_valid:
                return False

            # Guardar sesión de admin
            st.session_state.admin_authenticated = True
            st.session_state.admin_user = {
                'id': admin['id'],
                'username': admin['username'],
                'full_name': admin['full_name']
            }

            return True

        except Exception as e:
            print(f"Login error: {e}")
            st.error(f"Error de autenticación: {e}")
            return False

    def logout_admin(self):
        """Cerrar sesión de administrador"""
        st.session_state.admin_authenticated = False
        st.session_state.admin_user = None
        st.success("✅ Sesión cerrada exitosamente")

    def is_admin_authenticated(self) -> bool:
        """Verificar si hay un administrador autenticado"""
        return st.session_state.get('admin_authenticated', False)


def require_admin_auth() -> bool:
    """Verificar autenticación de administrador"""
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    if 'admin_user' not in st.session_state:
        st.session_state.admin_user = None

    return admin_auth_manager.is_admin_authenticated()


# Instancia global
admin_auth_manager = AdminAuthManager()