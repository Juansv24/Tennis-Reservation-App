"""
Sistema de Autenticación Simplificado para Reservas de Cancha de Tenis
Reemplaza auth_manager.py con funcionalidad idéntica pero código simplificado
Mantiene TODAS las características existentes y compatibilidad de API
"""

import sqlite3
import hashlib
import secrets
import streamlit as st
from typing import Optional, Dict, Tuple
import contextlib
from datetime import datetime, timedelta
from database_manager import DATABASE_FILE
from timezone_utils import get_colombia_now

class AuthManager:
    """Administrador de autenticación simplificado con API idéntica al original"""

    def __init__(self, db_file: str = DATABASE_FILE):
        self.db_file = db_file
        self.init_auth_tables()

    @contextlib.contextmanager
    def get_connection(self):
        """Administrador de contexto para conexiones de base de datos"""
        conn = sqlite3.connect(self.db_file)
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def init_auth_tables(self):
        """Crear tablas de autenticación"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Tabla de usuarios
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

            # Tabla de sesiones (sin complejidad de user_agent)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Crear índices
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_session_token 
                ON user_sessions(session_token)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_session_user_active 
                ON user_sessions(user_id, is_active)
            ''')

            conn.commit()

    def _hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """Generar hash con salt"""
        if salt is None:
            salt = secrets.token_hex(16)

        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return password_hash, salt

    def _generate_session_token(self) -> str:
        """Generar token de sesión"""
        return secrets.token_urlsafe(32)

    def _validate_email(self, email: str) -> bool:
        """Validar formato de email"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.match(pattern, email) is not None

    def _validate_password(self, password: str) -> Tuple[bool, str]:
        """Validar fortaleza de contraseña"""
        if len(password) < 6:
            return False, "La contraseña debe tener al menos 6 caracteres"

        if len(password) > 50:
            return False, "La contraseña debe tener menos de 50 caracteres"

        has_letter = any(c.isalpha() for c in password)
        has_number = any(c.isdigit() for c in password)

        if not (has_letter and has_number):
            return False, "La contraseña debe contener al menos una letra y un número"

        return True, "Contraseña válida"

    def _cleanup_expired_sessions(self):
        """Limpiar sesiones expiradas"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE user_sessions 
                    SET is_active = 0 
                    WHERE expires_at < CURRENT_TIMESTAMP AND is_active = 1
                ''')
                conn.commit()
        except Exception:
            pass

    def create_session(self, user_id: int, remember_me: bool = True, user_agent: str = None) -> str:
        """Crear sesión"""
        try:
            self._cleanup_expired_sessions()

            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Verificar que el usuario existe
                cursor.execute('SELECT id FROM users WHERE id = ? AND is_active = 1', (user_id,))
                if not cursor.fetchone():
                    return None

                # Generar token único
                for attempt in range(5):
                    try:
                        session_token = self._generate_session_token()

                        # Establecer expiración basada en remember_me
                        duration_days = 30 if remember_me else 1
                        expires_at = get_colombia_now().replace(tzinfo=None) + timedelta(days=duration_days)

                        # Crear sesión
                        cursor.execute('''
                            INSERT INTO user_sessions 
                            (user_id, session_token, expires_at)
                            VALUES (?, ?, ?)
                        ''', (user_id, session_token, expires_at.isoformat()))

                        conn.commit()
                        return session_token

                    except sqlite3.IntegrityError:
                        # Colisión de token, reintentar
                        if attempt == 4:
                            return None
                        continue
                    except Exception:
                        return None

                return None

        except Exception:
            return None

    def validate_session(self, session_token: str) -> Optional[Dict]:
        """Validar sesión"""
        if not session_token:
            return None

        try:
            self._cleanup_expired_sessions()

            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Verificar sesión
                cursor.execute('''
                               SELECT s.user_id, s.expires_at, u.email, u.full_name, u.is_active
                               FROM user_sessions s
                                        JOIN users u ON s.user_id = u.id
                               WHERE s.session_token = ?
                                 AND s.is_active = 1
                                 AND u.is_active = 1
                               ''', (session_token,))

                session_data = cursor.fetchone()

                if session_data:
                    user_id, expires_at_str, email, full_name, is_active = session_data

                    # Verificar expiración
                    try:
                        expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                        if expires_at < get_colombia_now().replace(tzinfo=None):
                            cursor.execute('''
                                           UPDATE user_sessions
                                           SET is_active = 0
                                           WHERE session_token = ?
                                           ''', (session_token,))
                            conn.commit()
                            return None
                    except (ValueError, AttributeError):
                        return None

                    # Actualizar último uso
                    cursor.execute('''
                                   UPDATE user_sessions
                                   SET last_used = CURRENT_TIMESTAMP
                                   WHERE session_token = ?
                                   ''', (session_token,))

                    cursor.execute('''
                                   UPDATE users
                                   SET last_login = CURRENT_TIMESTAMP
                                   WHERE id = ?
                                   ''', (user_id,))

                    conn.commit()

                    return {
                        'id': user_id,
                        'email': email,
                        'full_name': full_name,
                        'session_token': session_token
                    }

                return None

        except Exception:
            return None

    def destroy_session(self, session_token: str) -> bool:
        """Destruir sesión"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                               UPDATE user_sessions
                               SET is_active = 0
                               WHERE session_token = ?
                               ''', (session_token,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception:
            return False

    def destroy_all_user_sessions(self, user_id: int) -> bool:
        """Destruir todas las sesiones del usuario"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                               UPDATE user_sessions
                               SET is_active = 0
                               WHERE user_id = ?
                               ''', (user_id,))
                conn.commit()
                return True
        except Exception:
            return False

    def register_user(self, email: str, password: str, full_name: str, verification_code: str = None) -> Tuple[
        bool, str]:
        """Registrar usuario con verificación de email"""
        try:
            if not email or not self._validate_email(email):
                return False, "Por favor ingresa una dirección de email válida"

            if not full_name or len(full_name.strip()) < 2:
                return False, "Por favor ingresa un nombre válido"

            is_valid_password, password_message = self._validate_password(password)
            if not is_valid_password:
                return False, password_message

            email = email.strip().lower()
            full_name = full_name.strip()

            # Si se requiere código de verificación
            if verification_code:
                from database_manager import db_manager
                if not db_manager.verify_email_code(email, verification_code):
                    return False, "Código de verificación inválido o expirado"

            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
                if cursor.fetchone():
                    return False, "Ya existe una cuenta con este email"

                password_hash, salt = self._hash_password(password)

                cursor.execute('''
                               INSERT INTO users (email, password_hash, salt, full_name)
                               VALUES (?, ?, ?, ?)
                               ''', (email, password_hash, salt, full_name))

                conn.commit()
                return True, "Cuenta creada exitosamente"

        except Exception as e:
            return False, f"Error al crear cuenta: {str(e)}"

    def login_user(self, email: str, password: str, remember_me: bool = True) -> Tuple[bool, str, Optional[Dict]]:
        """Iniciar sesión de usuario"""
        try:
            if not email or not password:
                return False, "Por favor ingresa email y contraseña", None

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
                    return False, "Email o contraseña inválidos", None

                user_id, user_email, stored_hash, salt, full_name, is_active = user_data

                if not is_active:
                    return False, "Cuenta desactivada", None

                password_hash, _ = self._hash_password(password, salt)

                if password_hash != stored_hash:
                    return False, "Email o contraseña inválidos", None

                session_token = self.create_session(user_id, remember_me)

                if not session_token:
                    return False, "Error al crear sesión - por favor intenta de nuevo", None

                user_info = {
                    'id': user_id,
                    'email': user_email,
                    'full_name': full_name,
                    'session_token': session_token
                }

                return True, "Inicio de sesión exitoso", user_info

        except Exception as e:
            return False, f"Error de inicio de sesión: {str(e)}", None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Obtener usuario por ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                               SELECT id, email, full_name, created_at, last_login
                               FROM users
                               WHERE id = ?
                                 AND is_active = 1
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
        """Cambiar contraseña"""
        try:
            is_valid_password, password_message = self._validate_password(new_password)
            if not is_valid_password:
                return False, password_message

            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                               SELECT password_hash, salt
                               FROM users
                               WHERE id = ?
                               ''', (user_id,))

                user_data = cursor.fetchone()
                if not user_data:
                    return False, "Usuario no encontrado"

                stored_hash, salt = user_data

                current_hash, _ = self._hash_password(current_password, salt)
                if current_hash != stored_hash:
                    return False, "La contraseña actual es incorrecta"

                new_hash, new_salt = self._hash_password(new_password)

                cursor.execute('''
                               UPDATE users
                               SET password_hash = ?,
                                   salt          = ?
                               WHERE id = ?
                               ''', (new_hash, new_salt, user_id))

                cursor.execute('''
                               UPDATE user_sessions
                               SET is_active = 0
                               WHERE user_id = ?
                               ''', (user_id,))

                conn.commit()
                return True, "Contraseña cambiada exitosamente. Por favor inicia sesión de nuevo."

        except Exception as e:
            return False, f"Error al cambiar contraseña: {str(e)}"

    def update_user_profile(self, user_id: int, full_name: str) -> Tuple[bool, str]:
        """Actualizar perfil de usuario"""
        try:
            if not full_name or len(full_name.strip()) < 2:
                return False, "Por favor ingresa un nombre válido"

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
                    return True, "Perfil actualizado exitosamente"
                else:
                    return False, "Usuario no encontrado"

        except Exception as e:
            return False, f"Error al actualizar perfil: {str(e)}"

    def create_password_reset_token(self, email: str) -> Tuple[bool, str, Optional[str]]:
        """Crear token de recuperación de contraseña"""
        try:
            email = email.strip().lower()

            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Verificar que el usuario existe
                cursor.execute('SELECT id FROM users WHERE email = ? AND is_active = 1', (email,))
                user = cursor.fetchone()

                if not user:
                    # Retornar falso sin revelar que el email no existe
                    return False, "Error al procesar solicitud", None

                # Crear tabla de tokens de recuperación si no existe
                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS password_reset_tokens
                               (
                                   id
                                   INTEGER
                                   PRIMARY
                                   KEY
                                   AUTOINCREMENT,
                                   user_id
                                   INTEGER
                                   NOT
                                   NULL,
                                   token
                                   TEXT
                                   UNIQUE
                                   NOT
                                   NULL,
                                   created_at
                                   TIMESTAMP
                                   DEFAULT
                                   CURRENT_TIMESTAMP,
                                   expires_at
                                   TIMESTAMP
                                   NOT
                                   NULL,
                                   is_used
                                   BOOLEAN
                                   DEFAULT
                                   0,
                                   FOREIGN
                                   KEY
                               (
                                   user_id
                               ) REFERENCES users
                               (
                                   id
                               )
                                   )
                               ''')

                # Limpiar tokens expirados
                cursor.execute('DELETE FROM password_reset_tokens WHERE expires_at < CURRENT_TIMESTAMP')

                # Generar token único
                import secrets
                token = secrets.token_urlsafe(32)

                # Establecer expiración (30 minutos)
                expires_at = get_colombia_now().replace(tzinfo=None) + timedelta(minutes=30)

                # Guardar token
                cursor.execute('''
                               INSERT INTO password_reset_tokens (user_id, token, expires_at)
                               VALUES (?, ?, ?)
                               ''', (user[0], token, expires_at.isoformat()))

                conn.commit()
                return True, "Token de recuperación creado", token

        except Exception as e:
            return False, f"Error creando token: {str(e)}", None

    def validate_password_reset_token(self, token: str) -> Tuple[bool, str, Optional[int]]:
        """Validar token de recuperación de contraseña"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                               SELECT prt.user_id, prt.expires_at, u.email
                               FROM password_reset_tokens prt
                                        JOIN users u ON prt.user_id = u.id
                               WHERE prt.token = ?
                                 AND prt.is_used = 0
                                 AND u.is_active = 1
                               ''', (token,))

                result = cursor.fetchone()

                if not result:
                    return False, "Token inválido o ya usado ingrese a https://reservas-tenis-colina.streamlit.app para volver a iniciar sesión", None

                user_id, expires_at_str, email = result

                # Verificar expiración
                try:
                    expires_at = datetime.fromisoformat(expires_at_str)
                    if expires_at < get_colombia_now().replace(tzinfo=None):
                        return False, "Token expirado", None
                except ValueError:
                    return False, "Token inválido", None

                return True, f"Token válido para {email}", user_id

        except Exception as e:
            return False, f"Error validando token: {str(e)}", None


    def reset_password_with_token(self, token: str, new_password: str) -> Tuple[bool, str]:
        """Resetear contraseña usando token"""
        try:
            # Validar contraseña
            is_valid_password, password_message = self._validate_password(new_password)
            if not is_valid_password:
                return False, password_message

            # Validar token
            token_valid, token_message, user_id = self.validate_password_reset_token(token)
            if not token_valid:
                return False, token_message

            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Generar nueva contraseña hash
                new_hash, new_salt = self._hash_password(new_password)

                # Actualizar contraseña
                cursor.execute('''
                               UPDATE users
                               SET password_hash = ?,
                                   salt          = ?
                               WHERE id = ?
                               ''', (new_hash, new_salt, user_id))

                # Marcar token como usado
                cursor.execute('UPDATE password_reset_tokens SET is_used = 1 WHERE token = ?', (token,))

                # Invalidar todas las sesiones del usuario por seguridad
                cursor.execute('UPDATE user_sessions SET is_active = 0 WHERE user_id = ?', (user_id,))

                conn.commit()
                return True, "Contraseña actualizada exitosamente"

        except Exception as e:
            return False, f"Error reseteando contraseña: {str(e)}"
# Instancia global
auth_manager = AuthManager()