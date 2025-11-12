"""
Gestor de Autenticación Supabase para Sistema de Reservas de Cancha de Tenis
"""
import streamlit as st
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from database_manager import db_manager
from timezone_utils import get_colombia_now

class SupabaseAuthManager:
    """Administrador de autenticación usando Supabase"""

    def __init__(self):
        self.client = db_manager.client

    def _hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """Generar hash de contraseña con salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return password_hash, salt

    def _generate_session_token(self) -> str:
        """Generar token de sesión único"""
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
            db_manager.cleanup_expired_data()
        except Exception:
            pass

    def create_session(self, user_id: int, remember_me: bool = True, user_agent: str = None) -> str:
        """Crear nueva sesión para el usuario"""
        try:
            self._cleanup_expired_sessions()

            # Verificar que el usuario existe
            result = self.client.table('users').select('id').eq('id', user_id).eq('is_active', True).execute()
            if not result.data:
                return None

            # Generar token único
            for attempt in range(5):
                try:
                    session_token = self._generate_session_token()
                    duration_days = 30 if remember_me else 1
                    expires_at = get_colombia_now().replace(tzinfo=None) + timedelta(days=duration_days)

                    result = self.client.table('user_sessions').insert({
                        'user_id': user_id,
                        'session_token': session_token,
                        'expires_at': expires_at.isoformat(),
                        'is_active': True
                    }).execute()

                    if result.data:
                        return session_token

                except Exception:
                    if attempt == 4:
                        return None
                    continue

            return None
        except Exception:
            return None

    def validate_session(self, session_token: str) -> Optional[Dict]:
        """
        Validar sesión existente y configurar contexto RLS

        Args:
            session_token (str): Token de sesión a validar

        Returns:
            Optional[Dict]: Información del usuario si la sesión es válida, None si no
        """
        try:
            # Verificar que el token no esté vacío
            if not session_token:
                return None

            # PASO 1: Configurar contexto de sesión para RLS antes de cualquier consulta
            try:
                self.client.rpc('set_session_token', {'token': session_token}).execute()
            except Exception as e:
                # Si falla el contexto RLS, continuar sin él (para compatibilidad)
                print(f"Advertencia: No se pudo configurar contexto RLS: {e}")

            # PASO 2: Limpiar sesiones expiradas automáticamente
            self._cleanup_expired_sessions()

            # PASO 3: Buscar sesión activa con información del usuario
            result = self.client.table('user_sessions').select(
                'user_id, expires_at, users(email, full_name, is_active)'
            ).eq('session_token', session_token).eq('is_active', True).execute()

            # Verificar que se encontró la sesión
            if not result.data:
                # Sesión no encontrada - limpiar contexto RLS
                try:
                    self.client.rpc('set_session_token', {'token': None}).execute()
                except Exception:
                    pass
                return None

            session = result.data[0]
            user = session['users']

            # PASO 4: Verificar que el usuario esté activo
            if not user['is_active']:
                # Usuario inactivo - limpiar contexto RLS
                try:
                    self.client.rpc('set_session_token', {'token': None}).execute()
                except Exception:
                    pass
                return None

            # PASO 5: Verificar si la sesión ha expirado
            expires_at_str = session['expires_at']

            # Limpiar 'Z' al final si existe (formato UTC)
            if expires_at_str.endswith('Z'):
                expires_at_str = expires_at_str[:-1]

            expires_at = datetime.fromisoformat(expires_at_str)

            # Asegurar que ambas fechas estén en el mismo formato (sin zona horaria)
            if expires_at.tzinfo is not None:
                expires_at = expires_at.replace(tzinfo=None)

            current_time = get_colombia_now().replace(tzinfo=None)

            # Si la sesión expiró, destruirla y retornar None
            if expires_at < current_time:
                self.destroy_session(session_token)
                # Limpiar contexto RLS
                try:
                    self.client.rpc('set_session_token', {'token': None}).execute()
                except Exception:
                    pass
                return None

            # PASO 6: Actualizar timestamp de último uso de la sesión
            try:
                self.client.table('user_sessions').update({
                    'last_used': get_colombia_now().replace(tzinfo=None).isoformat()
                }).eq('session_token', session_token).execute()
            except Exception:
                # No es crítico si falla la actualización del timestamp
                pass

            # PASO 7: Actualizar último login del usuario
            try:
                self.client.table('users').update({
                    'last_login': get_colombia_now().replace(tzinfo=None).isoformat()
                }).eq('id', session['user_id']).execute()
            except Exception:
                # No es crítico si falla la actualización del último login
                pass

            # PASO 8: Retornar información del usuario válida
            # El contexto RLS ya está configurado para futuras operaciones
            return {
                'id': session['user_id'],
                'email': user['email'],
                'full_name': user['full_name'],
                'session_token': session_token
            }

        except ConnectionError as e:
            # Transient network error - don't invalidate session, just warn user
            st.warning("⚠️ Problema de conexión temporal. Por favor recarga la página.")
            print(f"Network error during session validation: {e}")
            return None
        except TimeoutError as e:
            # Timeout - transient network error
            st.warning("⚠️ Tiempo de conexión agotado. Por favor intenta de nuevo.")
            print(f"Timeout during session validation: {e}")
            return None
        except Exception as e:
            # Actual authentication error - invalidate session
            print(f"🔴 Session validation error: {str(e)}")
            try:
                self.client.rpc('set_session_token', {'token': None}).execute()
            except Exception:
                pass
            st.error("Error de sesión. Por favor inicia sesión de nuevo.")
            return None

    def destroy_session(self, session_token: str) -> bool:
        """Destruir sesión específica"""
        try:
            result = self.client.table('user_sessions').update({
                'is_active': False
            }).eq('session_token', session_token).execute()
            return True
        except Exception:
            return False

    def destroy_all_user_sessions(self, user_id: int) -> bool:
        """Destruir todas las sesiones de un usuario"""
        try:
            result = self.client.table('user_sessions').update({
                'is_active': False
            }).eq('user_id', user_id).execute()
            return True
        except Exception:
            return False

    def register_user(self, email: str, password: str, full_name: str, verification_code: str = None) -> Tuple[bool, str]:
        """Registrar nuevo usuario en el sistema"""
        try:
            # Validaciones básicas
            if not email or not self._validate_email(email):
                return False, "Por favor ingresa una dirección de email válida"

            if not full_name or len(full_name.strip()) < 2:
                return False, "Por favor ingresa un nombre válido"

            is_valid_password, password_message = self._validate_password(password)
            if not is_valid_password:
                return False, password_message

            email = email.strip().lower()
            full_name = full_name.strip()

            # Verificar código de verificación si se requiere
            if verification_code and not db_manager.verify_email_code(email, verification_code):
                return False, "Código de verificación inválido o expirado"

            # Verificar si el usuario ya existe
            result = self.client.table('users').select('id').eq('email', email).execute()
            if result.data:
                return False, "Ya existe una cuenta con este email"

            # Crear hash de contraseña
            password_hash, salt = self._hash_password(password)

            # Insertar nuevo usuario
            user_result = self.client.table('users').insert({
                'email': email,
                'password_hash': password_hash,
                'salt': salt,
                'full_name': full_name,
                'is_active': True
            }).execute()

            if user_result.data:
                return True, "Cuenta creada exitosamente"
            return False, "Error al crear cuenta"

        except Exception as e:
            return False, f"Error al crear cuenta: {str(e)}"

    def complete_first_login_with_access_code(self, user_info: Dict, access_code: str, remember_me: bool = True) -> \
    Tuple[bool, str, Optional[Dict]]:
        """Completar primer login con código de acceso"""
        try:
            from admin_database import admin_db_manager

            # Verificar código de acceso
            if not admin_db_manager.verify_access_code(access_code):
                return False, "Código de acceso incorrecto", None

            # Marcar primer login como completado
            if not admin_db_manager.mark_user_first_login_complete(user_info['id']):
                return False, "Error actualizando registro de usuario", None

            # Crear sesión normal
            session_token = self.create_session(user_info['id'], remember_me)
            if not session_token:
                return False, "Error al crear sesión - por favor intenta de nuevo", None

            # Configurar contexto RLS
            try:
                self.client.rpc('set_session_token', {'token': session_token}).execute()
            except Exception as e:
                print(f"Advertencia: No se pudo configurar contexto RLS: {e}")

            # Actualizar último login
            try:
                self.client.table('users').update({
                    'last_login': datetime.now().isoformat()
                }).eq('id', user_info['id']).execute()
            except Exception:
                pass

            # Preparar información del usuario completa
            complete_user_info = {
                'id': user_info['id'],
                'email': user_info['email'],
                'full_name': user_info['full_name'],
                'session_token': session_token
            }

            return True, "Primer acceso completado exitosamente", complete_user_info

        except Exception as e:
            return False, f"Error en primer acceso: {str(e)}", None

    def login_user(self, email: str, password: str, remember_me: bool = True) -> Tuple[bool, str, Optional[Dict]]:
        """Iniciar sesión de usuario con validación mejorada y contexto RLS"""
        try:
            if not email or not password:
                return False, "Por favor ingresa email y contraseña", None

            email = email.strip().lower()

            # Verificar si el correo está registrado
            result = self.client.table('users').select('id').eq('email', email).execute()
            if not result.data:
                return False, "No existe una cuenta con este email", None

            # SEGUNDO: Obtener datos del usuario para validación
            result = self.client.table('users').select('*').eq('email', email).eq('is_active', True).execute()

            if not result.data:
                return False, "Error de acceso. Contacta al administrador", None

            user = result.data[0]

            # TERCERO: Validar contraseña
            password_hash, _ = self._hash_password(password, user['salt'])
            if password_hash != user['password_hash']:
                return False, "Contraseña incorrecta", None

            # Verificar si es primer login
            first_login_completed = user.get('first_login_completed', False)

            if not first_login_completed:
                # Primer login - requerir código de acceso
                user_info = {
                    'id': user['id'],
                    'email': user['email'],
                    'full_name': user['full_name'],
                    'requires_access_code': True  # Flag especial
                }
                return True, "first_login_requires_access_code", user_info


            # CUARTO: Crear sesión si todo está ok
            session_token = self.create_session(user['id'], remember_me)

            if not session_token:
                return False, "Error al crear sesión - por favor intenta de nuevo", None

            # QUINTO: Configurar contexto RLS para futuras operaciones
            try:
                self.client.rpc('set_session_token', {'token': session_token}).execute()
            except Exception as e:
                # Si falla RLS, continuar (para compatibilidad)
                print(f"Advertencia: No se pudo configurar contexto RLS en login: {e}")

            # SEXTO: Actualizar último inicio de sesión
            try:
                self.client.table('users').update({
                    'last_login': datetime.now().isoformat()
                }).eq('id', user['id']).execute()
            except Exception:
                pass  # No crítico si falla

            # SÉPTIMO: Preparar información del usuario
            user_info = {
                'id': user['id'],
                'email': user['email'],
                'full_name': user['full_name'],
                'session_token': session_token
            }

            return True, "Inicio de sesión exitoso", user_info

        except Exception as e:
            # En caso de error, limpiar contexto RLS
            try:
                self.client.rpc('set_session_token', {'token': None}).execute()
            except Exception:
                pass

            return False, f"Error de inicio de sesión: {str(e)}", None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Obtener información de usuario por ID"""
        try:
            result = self.client.table('users').select(
                'id, email, full_name, created_at, last_login'
            ).eq('id', user_id).eq('is_active', True).execute()

            if result.data:
                user = result.data[0]
                return {
                    'id': user['id'],
                    'email': user['email'],
                    'full_name': user['full_name'],
                    'created_at': user['created_at'],
                    'last_login': user['last_login']
                }
            return None
        except Exception:
            return None

    def change_password(self, user_id: int, current_password: str, new_password: str) -> Tuple[bool, str]:
        """Cambiar contraseña de usuario"""
        try:
            # Validar nueva contraseña
            is_valid_password, password_message = self._validate_password(new_password)
            if not is_valid_password:
                return False, password_message

            # Obtener datos actuales del usuario
            result = self.client.table('users').select('password_hash, salt').eq('id', user_id).execute()

            if not result.data:
                return False, "Usuario no encontrado"

            user = result.data[0]

            # Verificar contraseña actual
            current_hash, _ = self._hash_password(current_password, user['salt'])
            if current_hash != user['password_hash']:
                return False, "La contraseña actual es incorrecta"

            # Generar nueva contraseña hash
            new_hash, new_salt = self._hash_password(new_password)

            # Actualizar contraseña
            self.client.table('users').update({
                'password_hash': new_hash,
                'salt': new_salt
            }).eq('id', user_id).execute()

            # Invalidar todas las sesiones por seguridad
            self.destroy_all_user_sessions(user_id)

            return True, "Contraseña cambiada exitosamente. Por favor inicia sesión de nuevo."

        except Exception as e:
            return False, f"Error al cambiar contraseña: {str(e)}"

    def update_user_profile(self, user_id: int, full_name: str) -> Tuple[bool, str]:
        """Actualizar perfil de usuario"""
        try:
            if not full_name or len(full_name.strip()) < 2:
                return False, "Por favor ingresa un nombre válido"

            full_name = full_name.strip()

            result = self.client.table('users').update({
                'full_name': full_name
            }).eq('id', user_id).execute()

            if result.data:
                return True, "Perfil actualizado exitosamente"
            else:
                return False, "Usuario no encontrado"

        except Exception as e:
            return False, f"Error al actualizar perfil: {str(e)}"

    def create_password_reset_token(self, email: str) -> Tuple[bool, str, Optional[str]]:
        """Crear token de recuperación de contraseña"""
        try:
            email = email.strip().lower()

            # Verificar que el usuario existe
            result = self.client.table('users').select('id').eq('email', email).eq('is_active', True).execute()

            if not result.data:
                return False, "Error al procesar solicitud", None

            user_id = result.data[0]['id']

            # FIX: Usar UTC para evitar problemas de timezone
            import datetime
            current_utc = datetime.datetime.utcnow()

            # Limpiar tokens expirados
            self.client.table('password_reset_tokens').delete().lt(
                'expires_at', current_utc.isoformat()
            ).execute()

            # Generar token único
            token = secrets.token_urlsafe(32)
            expires_at = current_utc + timedelta(minutes=30)

            # Guardar token
            token_result = self.client.table('password_reset_tokens').insert({
                'user_id': user_id,
                'token': token,
                'expires_at': expires_at.isoformat(),
                'is_used': False
            }).execute()

            if token_result.data:
                return True, "Token de recuperación creado", token
            return False, "Error creando token", None

        except Exception as e:
            return False, f"Error creando token: {str(e)}", None

    def validate_password_reset_token(self, token: str) -> Tuple[bool, str, Optional[int]]:
        """Validar token de recuperación de contraseña"""
        try:
            result = self.client.table('password_reset_tokens').select(
                'user_id, expires_at, users(email)'
            ).eq('token', token).eq('is_used', False).execute()

            if not result.data:
                return False, "Token inválido o ya usado. Por favor solicita un nuevo enlace de recuperación.", None

            token_data = result.data[0]
            user_email = token_data['users']['email']

            # Verificar expiración usando UTC consistentemente
            try:
                import datetime
                expires_at_str = token_data['expires_at']

                # Remover 'Z' y '+00:00' si existen
                if expires_at_str.endswith('Z'):
                    expires_at_str = expires_at_str[:-1]
                elif '+00:00' in expires_at_str:
                    expires_at_str = expires_at_str.replace('+00:00', '')

                expires_at = datetime.datetime.fromisoformat(expires_at_str)
                current_utc = datetime.datetime.utcnow()

                if expires_at < current_utc:
                    return False, "Token expirado", None

            except ValueError:
                return False, "Token inválido", None

            return True, f"Token válido para {user_email}", token_data['user_id']

        except Exception as e:
            return False, f"Error validando token: {str(e)}", None

    def reset_password_with_token(self, token: str, new_password: str) -> Tuple[bool, str]:
        """Resetear contraseña usando token de recuperación"""
        try:
            # Validar nueva contraseña
            is_valid_password, password_message = self._validate_password(new_password)
            if not is_valid_password:
                return False, password_message

            # Validar token
            token_valid, token_message, user_id = self.validate_password_reset_token(token)
            if not token_valid:
                return False, token_message

            # Generar nueva contraseña hash
            new_hash, new_salt = self._hash_password(new_password)

            # Actualizar contraseña
            self.client.table('users').update({
                'password_hash': new_hash,
                'salt': new_salt
            }).eq('id', user_id).execute()

            # Marcar token como usado
            self.client.table('password_reset_tokens').update({
                'is_used': True
            }).eq('token', token).execute()

            # Invalidar todas las sesiones por seguridad
            self.destroy_all_user_sessions(user_id)

            return True, "Contraseña actualizada exitosamente"

        except Exception as e:
            return False, f"Error reseteando contraseña: {str(e)}"


# Instancia global
auth_manager = SupabaseAuthManager()