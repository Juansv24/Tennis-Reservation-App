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

    def ensure_admin_user_exists(self):
        """Ensure default admin user exists in database"""
        try:
            # Check if admin user exists
            result = self.client.table('admin_users').select('id').eq('username', 'admin').execute()

            if not result.data:
                # Create admin user with proper hash
                salt = 'adminsalt123'
                password_hash = self._hash_password('tennis123', salt)

                self.client.table('admin_users').insert({
                    'username': 'admin',
                    'password_hash': password_hash,
                    'salt': salt,
                    'full_name': 'Administrador del Sistema',
                    'is_active': True
                }).execute()

                print("Admin user created successfully")
        except Exception as e:
            print(f"Error ensuring admin user exists: {e}")

    def login_admin(self, username: str, password: str) -> bool:
        """Iniciar sesión de administrador"""
        try:
            print(f"Attempting login for username: {username}")

            # Buscar admin en base de datos
            result = self.client.table('admin_users').select('*').eq(
                'username', username.strip()
            ).eq('is_active', True).execute()

            print(f"Database query result: {result.data}")

            if not result.data:
                print("No admin user found in database")
                return False

            admin = result.data[0]
            print(f"Found admin: {admin['username']}")

            # Verificar contraseña
            password_hash = self._hash_password(password, admin['salt'])
            stored_hash = admin['password_hash']

            print(f"Calculated hash: {password_hash}")
            print(f"Stored hash: {stored_hash}")
            print(f"Hashes match: {password_hash == stored_hash}")

            if password_hash != stored_hash:
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