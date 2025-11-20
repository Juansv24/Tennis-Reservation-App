"""
Gestor de Base de Datos Supabase para Sistema de Reservas de Cancha de Tenis
"""
import streamlit as st
from supabase import create_client, Client
from supabase.client import ClientOptions  # FIX: Use official ClientOptions class
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import contextlib
from timezone_utils import get_colombia_now
from database_exceptions import DatabaseConnectionError, DatabaseOperationError, InvalidResponseError, AtomicOperationError
import httpx
import time
from functools import wraps
import random


def retry_on_timeout(max_retries=3, backoff_factor=1.0):
    """Decorator para reintentar operaciones de DB en caso de timeout

    Implementa exponential backoff with jitter para prevenir retry storms.

    Args:
        max_retries: Número máximo de reintentos (default 3)
        backoff_factor: Factor de espera exponencial entre reintentos (default 1.0 = sin espera)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (TimeoutError, httpx.TimeoutException, httpx.ConnectError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        # Exponential backoff with jitter to prevent retry storms
                        base_wait = backoff_factor * (2 ** attempt)
                        jitter = random.uniform(0, 0.5)  # Random 0-0.5 seconds
                        wait_time = base_wait + jitter
                        print(f"⚠️ Reintentando {func.__name__} (intento {attempt + 2}/{max_retries}) tras {wait_time:.2f}s...")
                        time.sleep(wait_time)
                    else:
                        print(f"❌ {func.__name__} falló después de {max_retries} intentos")
                except Exception as e:
                    # No reintentar otros tipos de errores
                    raise

            # Si llegamos aquí, todos los reintentos fallaron
            raise last_exception
        return wrapper
    return decorator


class SupabaseManager:
    """Gestor de base de datos Supabase para el sistema de reservas"""

    def __init__(self):
        try:
            # Verificar que las credenciales existan
            try:
                self.url = st.secrets["supabase"]["url"]
                self.key = st.secrets["supabase"]["key"]
            except KeyError as e:
                st.error(f"❌ Error de Configuración: Credenciales de Supabase faltantes - {e}")
                st.stop()

            # Validar que las credenciales no estén vacías
            if not self.url or not self.key:
                st.error("❌ Error de Configuración: URL o clave de Supabase está vacía")
                st.stop()

            # FIX #1: Configurar cliente Supabase con timeout, connection pooling y retry
            # Esto previene EAGAIN errors bajo carga concurrente
            # Alineado con supabase-py v2.18.0 official API

            limits = httpx.Limits(
                max_connections=50,           # Increased from 20 for 15-20 concurrent users
                max_keepalive_connections=25  # Proportional increase for connection reuse
            )

            # Crear cliente HTTP con configuración de concurrencia
            httpx_client = httpx.Client(
                limits=limits,
                timeout=httpx.Timeout(30.0, connect=15.0),  # Increased connect timeout from 10 to 15
                http2=True,          # Habilitar HTTP/2 para mejor multiplexing
                verify=True          # Verificar certificados SSL
            )

            # Crear opciones de cliente usando oficial ClientOptions (v2.18.0 recomendado)
            postgrest_timeout = httpx.Timeout(30.0, connect=10.0)
            storage_timeout = httpx.Timeout(30.0, connect=10.0)
            function_timeout = httpx.Timeout(30.0, connect=10.0)

            options = ClientOptions(
                schema="public",
                auto_refresh_token=True,
                persist_session=True,
                httpx_client=httpx_client,
                postgrest_client_timeout=postgrest_timeout,
                storage_client_timeout=storage_timeout,
                function_client_timeout=function_timeout
            )

            # Crear cliente Supabase con ClientOptions oficial
            self.client: Client = create_client(self.url, self.key, options)

            # Verificar que la conexión funciona
            try:
                self.init_tables()
            except Exception as e:
                st.error("❌ Error de Conexión: No se puede conectar a Supabase")
                st.error(f"Detalles: {str(e)}")
                st.stop()

        except Exception as e:
            st.error(f"❌ Error de Inicialización: {str(e)}")
            st.stop()

    def init_tables(self):
        """Verificar que las tablas existan en Supabase"""
        # Las tablas deben crearse en el dashboard de Supabase
        # Este método verifica si existen
        try:
            # Probar conexión
            result = self.client.table('reservations').select('id').limit(1).execute()
            return True
        except Exception as e:
            raise DatabaseConnectionError(f"Tablas no encontradas o error de conexión: {str(e)}")

    def set_session_context(self, session_token: str):
        """Set session token for RLS context"""
        self._current_session_token = session_token
        if session_token:
            try:
                # Set session token in PostgreSQL session
                self.client.rpc('set_session_token', {'token': session_token}).execute()
            except Exception as e:
                print(f"Failed to set session context: {e}")
        else:
            try:
                self.client.rpc('set_session_token', {'token': None}).execute()
            except Exception:
                pass

    def clear_session_context(self):
        """Clear session context"""
        self.set_session_context(None)
        self._current_session_token = None

    @retry_on_timeout(max_retries=2, backoff_factor=0.3)
    def is_vip_user(self, email: str) -> bool:
        """Verificar si un usuario es VIP (tiene horario extendido)

        FIX #3: Aplica retry para manejar timeouts bajo carga
        """
        try:
            result = self.client.table('vip_users').select('id').eq(
                'email', email.strip().lower()
            ).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Error verificando usuario VIP: {e}")
            return False

    def can_user_make_reservation_now(self, email: str) -> Tuple[bool, str]:
        """
        Verificar si un usuario puede hacer reservas en el momento actual
        basado en la hora actual y su tipo de usuario
        Returns: (puede_reservar, mensaje_error)
        """
        try:
            from timezone_utils import get_colombia_now

            # Obtener hora actual en Colombia
            current_hour = get_colombia_now().hour

            # Verificar si es usuario VIP
            is_vip = self.is_vip_user(email)

            if is_vip:
                # Usuarios VIP: pueden reservar de 8 AM - 8 PM (20:00)
                if 8 <= current_hour <= 20:
                    return True, ""
                else:
                    if current_hour < 8:
                        return False, "Las reservas están disponibles a partir de las 8:00 AM"
                    else:
                        return False, "Las reservas están disponibles hasta las 8:00 PM"
            else:
                # Usuarios regulares: pueden reservar de 8 AM - 5 PM (17:00)
                if 8 <= current_hour <= 17:
                    return True, ""
                else:
                    if current_hour < 8:
                        return False, "Las reservas están disponibles a partir de las 8:00 AM"
                    else:
                        return False, "Las reservas están disponibles hasta las 5:00 PM"

        except Exception as e:
            print(f"Error verificando horario de reserva: {e}")
            # En caso de error, permitir como fallback para usuarios regulares
            current_hour = get_colombia_now().hour
            if 8 <= current_hour <= 17:
                return True, ""
            return False, "Error verificando horarios disponibles"

    @retry_on_timeout(max_retries=3, backoff_factor=0.5)
    def get_user_credits(self, user_email: str) -> int:
        """Obtener créditos actuales del usuario

        FIX #3: Aplica retry con backoff exponencial para manejar timeouts bajo carga
        """
        try:
            result = self.client.table('users').select('credits').eq(
                'email', user_email.strip().lower()
            ).execute()

            if result.data:
                return result.data[0]['credits'] or 0
            return 0
        except Exception as e:
            # Distinguish between connection error and no data found
            raise DatabaseConnectionError(f"Failed to fetch user credits: {str(e)}")

    def has_sufficient_credits(self, email: str, required_credits: int) -> bool:
        """Verificar si el usuario tiene suficientes créditos"""
        return self.get_user_credits(email) >= required_credits

    def use_credits_for_reservation(self, email: str, credits_needed: int, date: str, hour: int) -> bool:
        """Usar créditos para una reserva"""
        try:
            # Obtener usuario
            user_result = self.client.table('users').select('id, credits').eq('email', email.strip().lower()).execute()
            if not user_result.data:
                return False

            user = user_result.data[0]
            current_credits = user['credits'] or 0

            if current_credits < credits_needed:
                return False

            # Descontar créditos
            new_credits = current_credits - credits_needed
            update_result = self.client.table('users').update({
                'credits': new_credits
            }).eq('id', user['id']).execute()

            if update_result.data:
                # Registrar transacción
                self.client.table('credit_transactions').insert({
                    'user_id': user['id'],
                    'amount': -credits_needed,
                    'transaction_type': 'reservation_use',
                    'description': f'Reserva {date} {hour}:00',
                    'created_at': datetime.now().isoformat()
                }).execute()
                return True

            return False
        except Exception as e:
            print(f"Error using credits: {e}")
            return False

    def save_reservation(self, date: datetime.date, hour: int, name: str, email: str) -> bool:
        """Guardar nueva reserva"""
        try:
            result = self.client.table('reservations').insert({
                'date': date.strftime('%Y-%m-%d'),
                'hour': hour,
                'name': name.strip(),
                'email': email.strip().lower(),
                'created_at': get_colombia_now().isoformat()
            }).execute()
            return len(result.data) > 0
        except Exception as e:
            # Verificar si es error de clave duplicada
            if 'duplicate' in str(e).lower() or 'unique' in str(e).lower():
                return False
            st.error(f"Error de base de datos: {e}")
            return False

    def is_hour_available(self, date: datetime.date, hour: int) -> bool:
        """Verificar si una hora está disponible"""
        try:
            result = self.client.table('reservations').select('id').eq(
                'date', date.strftime('%Y-%m-%d')
            ).eq('hour', hour).execute()
            return len(result.data) == 0
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to check hour availability: {str(e)}")

    def get_reservations_for_date(self, date: datetime.date) -> List[int]:
        """Obtener horas reservadas para una fecha específica"""
        try:
            result = self.client.table('reservations').select('hour').eq(
                'date', date.strftime('%Y-%m-%d')
            ).order('hour').execute()
            return [row['hour'] for row in result.data]
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to fetch reservations for date: {str(e)}")

    def get_reservations_with_names_for_date(self, date: datetime.date) -> Dict[int, str]:
        """Obtener reservas con nombres de usuarios para una fecha"""
        try:
            result = self.client.table('reservations').select('hour, name').eq(
                'date', date.strftime('%Y-%m-%d')
            ).order('hour').execute()
            return {row['hour']: row['name'] for row in result.data}
        except Exception:
            return {}

    def get_user_reservations_for_date(self, email: str, date: datetime.date) -> List[int]:
        """Obtener reservas de un usuario específico para una fecha"""
        try:
            result = self.client.table('reservations').select('hour').eq(
                'email', email.strip().lower()
            ).eq('date', date.strftime('%Y-%m-%d')).order('hour').execute()
            return [row['hour'] for row in result.data]
        except Exception:
            return []

    def get_all_reservations(self) -> List[tuple]:
        """Obtener todas las reservas del sistema"""
        try:
            result = self.client.table('reservations').select('*').order('date', desc=True).order('hour').execute()
            return [(row['id'], row['date'], row['hour'], row['name'], row['email'], row['created_at']) for row in
                    result.data]
        except Exception:
            return []

    @retry_on_timeout(max_retries=3, backoff_factor=0.5)
    def get_date_reservations_summary(self, dates: List[datetime.date], user_email: str) -> Dict:
        """Get all reservation data for multiple dates in one call

        FIX #3: Aplica retry para manejar timeouts bajo carga
        """
        try:
            date_strings = [d.strftime('%Y-%m-%d') for d in dates]

            # Single query for all reservations across dates
            result = self.client.table('reservations').select(
                'date, hour, name, email'
            ).in_('date', date_strings).order('date, hour').execute()

            # Initialize summary structure
            summary = {
                'all_reservations': {},
                'user_reservations': {},
                'reservation_names': {}
            }

            # Initialize each date
            for date in dates:
                date_str = date.strftime('%Y-%m-%d')
                summary['all_reservations'][date_str] = []
                summary['user_reservations'][date_str] = []
                summary['reservation_names'][date_str] = {}

            # Process results
            for row in result.data:
                date_str = row['date']
                hour = row['hour']

                summary['all_reservations'][date_str].append(hour)
                summary['reservation_names'][date_str][hour] = row['name']

                if row['email'] == user_email.strip().lower():
                    summary['user_reservations'][date_str].append(hour)

            return summary
        except Exception as e:
            st.error(f"Error obteniendo datos de reservas: {e}")
            # Return empty structure on error
            summary = {'all_reservations': {}, 'user_reservations': {}, 'reservation_names': {}}
            for date in dates:
                date_str = date.strftime('%Y-%m-%d')
                summary['all_reservations'][date_str] = []
                summary['user_reservations'][date_str] = []
                summary['reservation_names'][date_str] = {}
            return summary

    def is_slot_still_available(self, date: datetime.date, hour: int) -> bool:
        """Quick real-time check if slot is still available - single fast query"""
        try:
            # Check for active reservations
            result = self.client.table('reservations').select('id').eq(
                'date', date.strftime('%Y-%m-%d')
            ).eq('hour', hour).execute()

            if result.data:
                return False

            # Check for maintenance slots
            maintenance_result = self.client.table('maintenance_slots').select('id').eq(
                'date', date.strftime('%Y-%m-%d')
            ).eq('hour', hour).execute()

            return len(maintenance_result.data) == 0

        except Exception as e:
            print(f"Error checking slot availability: {e}")
            return False  # Safer to assume unavailable on error

    def delete_reservation(self, date: str, hour: int) -> bool:
        """Eliminar una reserva específica"""
        try:
            result = self.client.table('reservations').delete().eq('date', date).eq('hour', hour).execute()
            return len(result.data) > 0
        except Exception:
            return False

    def save_verification_code(self, email: str, code: str) -> bool:
        """Guardar código de verificación de email"""
        try:
            import datetime
            expires_at = datetime.datetime.utcnow() + timedelta(minutes=10)

            # Limpiar códigos expirados primero
            self.client.table('email_verifications').delete().lt(
                'expires_at', datetime.datetime.utcnow().isoformat()
            ).execute()

            result = self.client.table('email_verifications').insert({
                'email': email.strip().lower(),
                'code': code,
                'expires_at': expires_at.isoformat(),
                'is_used': False
            }).execute()

            print(f"DEBUG - Código guardado: {code} para {email}, expira: {expires_at.isoformat()}")
            return len(result.data) > 0
        except Exception as e:
            st.error(f"Error guardando código de verificación: {e}")
            return False

    def verify_email_code(self, email: str, code: str) -> bool:
        """Verificar código de email y marcarlo como usado"""
        try:
            import datetime
            current_time = datetime.datetime.utcnow().isoformat()

            print(f"DEBUG - Verificando código: {code} para email: {email}")
            print(f"DEBUG - Hora actual UTC: {current_time}")

            # Buscar código válido
            result = self.client.table('email_verifications').select('id, expires_at').eq(
                'email', email.strip().lower()
            ).eq('code', code.strip().upper()).eq('is_used', False).gt(
                'expires_at', current_time
            ).execute()

            print(f"DEBUG - Resultados encontrados: {len(result.data)}")
            if result.data:
                print(f"DEBUG - Código expira: {result.data[0]['expires_at']}")

            if result.data:
                # Marcar como usado
                self.client.table('email_verifications').update({
                    'is_used': True
                }).eq('id', result.data[0]['id']).execute()
                return True
            return False
        except Exception as e:
            print(f"DEBUG - Error verificando código: {e}")
            st.error(f"Error verificando código: {e}")
            return False

    def cleanup_expired_data(self):
        """Limpiar datos expirados del sistema"""
        try:
            import datetime
            now = datetime.datetime.utcnow().isoformat()

            # Limpiar códigos de verificación expirados
            self.client.table('email_verifications').delete().lt('expires_at', now).execute()

            # Limpiar tokens de reset expirados
            self.client.table('password_reset_tokens').delete().lt('expires_at', now).execute()

            # Limpiar sesiones expiradas
            self.client.table('user_sessions').update({
                'is_active': False
            }).lt('expires_at', now).eq('is_active', True).execute()

        except Exception as e:
            st.warning(f"Error en limpieza automática: {e}")

    def log_critical_operation(self, operation_type: str, details: dict, success: bool):
        """Log critical database operations for audit trail"""
        try:
            log_entry = {
                'operation_type': operation_type,
                'details': str(details),
                'success': success,
                'timestamp': get_colombia_now().isoformat(),
                'user_agent': 'streamlit_app'
            }

            # Try to log to a system_logs table (create if needed)
            try:
                self.client.table('system_logs').insert(log_entry).execute()
            except Exception:
                # If logging fails, at least print to console
                print(f"🔍 AUDIT: {operation_type} - Success: {success} - Details: {details}")

        except Exception as e:
            print(f"⚠️ Failed to log operation: {e}")

    def create_atomic_reservation(self, date, hour, name, email):
        """Crear reserva usando stored procedure atómica"""
        try:
            result = self.client.rpc('atomic_reservation_request', {
                'p_date': date.strftime('%Y-%m-%d'),
                'p_hour': hour,
                'p_user_email': email,
                'p_user_name': name
            }).execute()

            # Validate response structure
            if not result.data or len(result.data) == 0:
                return False, "Error de base de datos: Sin respuesta del servidor"

            response = result.data[0]

            # Validate response has required keys
            if 'success' not in response or 'message' not in response:
                return False, "Error de base de datos: Respuesta con formato inválido"

            return response['success'], response['message']

        except ConnectionError:
            return False, "Conexión perdida. Por favor intenta de nuevo."
        except TimeoutError:
            return False, "La solicitud expiró. Por favor verifica tu conexión e intenta de nuevo."
        except Exception as e:
            # Log the actual error server-side, return generic to user
            print(f"🔴 RPC Error in atomic_reservation_request: {str(e)}")
            return False, "Error del sistema. Por favor contacta con soporte."

    def create_atomic_double_reservation(self, date, hour1, hour2, name, email):
        """Crear reserva de 2 horas usando stored procedure atómica"""
        try:
            result = self.client.rpc('atomic_double_reservation_request', {
                'p_date': date.strftime('%Y-%m-%d'),
                'p_hour1': hour1,
                'p_hour2': hour2,
                'p_user_email': email,
                'p_user_name': name
            }).execute()

            # Validate response structure
            if not result.data or len(result.data) == 0:
                return False, "Error de base de datos: Sin respuesta del servidor"

            response = result.data[0]

            # Validate response has required keys
            if 'success' not in response or 'message' not in response:
                return False, "Error de base de datos: Respuesta con formato inválido"

            return response['success'], response['message']

        except ConnectionError:
            return False, "Conexión perdida. Por favor intenta de nuevo."
        except TimeoutError:
            return False, "La solicitud expiró. Por favor verifica tu conexión e intenta de nuevo."
        except Exception as e:
            # Log the actual error server-side, return generic to user
            print(f"🔴 RPC Error in atomic_double_reservation_request: {str(e)}")
            return False, "Error del sistema. Por favor contacta con soporte."

    def get_maintenance_slots_for_date(self, date: datetime.date) -> List[int]:
        """Obtener horarios de mantenimiento para una fecha"""
        try:
            result = self.client.table('maintenance_slots').select('hour').eq(
                'date', date.strftime('%Y-%m-%d')
            ).execute()
            return [row['hour'] for row in result.data]
        except Exception as e:
            # Log error but return empty list as safe fallback (no maintenance slots)
            print(f"⚠️ Error getting maintenance slots for date {date}: {str(e)}")
            return []

    def get_current_lock_code(self) -> Optional[str]:
        """Obtener la contraseña actual del candalo"""
        try:
            result = self.client.table('lock_code').select('code').order('created_at', desc=True).limit(1).execute()
            if result.data and len(result.data) > 0:
                lock_code = result.data[0].get('code')
                if lock_code:
                    return lock_code
            # No lock code found
            print("⚠️ No lock code found in database")
            return None
        except Exception as e:
            # Log error but return None as safe fallback
            print(f"⚠️ Error getting lock code: {str(e)}")
            return None

# Instancia global
db_manager = SupabaseManager()