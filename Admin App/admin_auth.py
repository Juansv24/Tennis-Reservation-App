"""
Sistema de Autenticación Simple para Administradores
"""

import streamlit as st
import hashlib
from database_manager import db_manager


class AdminAuthManager:
    """Gestor de autenticación para administradores"""

    def __init__(self):
        self.client = db_manager.client

    def _hash_password(self, password: str, salt: str) -> str:
        """Generar hash de contraseña con salt"""
        return hashlib.sha256((password + salt).encode()).hexdigest()

    def update_admin_credentials(self):
        """Update existing admin user with new secure credentials"""
        try:
            # Get new credentials from secrets
            try:
                new_password = st.secrets["admin"]["default_password"]
                new_salt = st.secrets["admin"]["salt"]
            except KeyError:
                st.error("❌ Admin credentials not configured in secrets")
                return False

            # Validate new credentials
            if len(new_password) < 8 or len(new_salt) < 16:
                st.error("❌ New credentials don't meet security requirements")
                return False

            # Generate new hash with new credentials
            new_hash = self._hash_password(new_password, new_salt)

            print(f"🔧 Updating admin credentials...")
            print(f"🔧 New salt: {new_salt[:10]}...")
            print(f"🔧 New hash: {new_hash[:10]}...")

            # Update the admin user
            update_result = self.client.table('admin_users').update({
                'password_hash': new_hash,
                'salt': new_salt
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

                # Create new admin user with secure credentials
                try:
                    admin_password = st.secrets["admin"]["default_password"]
                    salt = st.secrets["admin"]["salt"]
                except KeyError:
                    st.error("❌ Credenciales de administrador no configuradas en secretos")
                    st.info("""
                    Para configurar el acceso de administrador, agrega a tus secretos de Streamlit:

                    [admin]
                    default_password = "TuContraseñaSeguraAquí"
                    salt = "TuSaltSeguroAquíAlMenos16Caracteres"
                    """)
                    return False

                if len(admin_password) < 8 or len(salt) < 16:
                    st.error("❌ Las credenciales de administrador no cumplen los requisitos de seguridad")
                    st.info("""
                    Las credenciales de administrador deben cumplir:
                    - default_password: al menos 8 caracteres
                    - salt: al menos 16 caracteres
                    """)
                    return False

                password_hash = self._hash_password(admin_password, salt)

                insert_result = self.client.table('admin_users').insert({
                    'username': 'admin',
                    'password_hash': password_hash,
                    'salt': salt,
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
            salt = st.secrets["admin"]["salt"]

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

            # Check salt strength
            if len(salt) < 32:
                st.warning("⚠️ Salt should be at least 32 characters for better security")

            return True
        except KeyError:
            st.error("❌ Credenciales de administrador no encontradas en secretos")
            st.info("""
            Para configurar el acceso de administrador, agrega a tus secretos de Streamlit:

            [admin]
            default_password = "TuContraseñaSeguraAquí"
            salt = "TuSaltSeguroAquíAlMenos32Caracteres"
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

            # Verificar contraseña
            password_hash = self._hash_password(password, admin['salt'])
            stored_hash = admin['password_hash']

            # NOTE: DO NOT log password hashes for security reasons
            hashes_match = password_hash == stored_hash
            print(f"Authentication result: {'SUCCESS' if hashes_match else 'FAILED'}")

            if not hashes_match:
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