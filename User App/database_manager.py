"""
Gestor de Base de Datos Supabase para Sistema de Reservas de Cancha de Tenis
"""
import streamlit as st
from supabase import create_client, Client
from supabase.client import ClientOptions  # FIX: Use official ClientOptions class
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Callable, Any
import contextlib
from timezone_utils import get_colombia_now
from database_exceptions import DatabaseConnectionError, DatabaseOperationError, InvalidResponseError, AtomicOperationError
import httpx
import time
from functools import wraps
import random
import errno
import os
import threading
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor, as_completed


def _get_error_details(e: Exception) -> Dict:
    """Extract detailed error information for diagnostics"""
    details = {
        'error_type': type(e).__name__,
        'error_message': str(e),
        'is_timeout': False,
        'is_connection': False,
        'is_resource_exhaustion': False,
        'error_code': None,
        'timestamp': datetime.now().isoformat()
    }

    # Check for specific error types
    if isinstance(e, (TimeoutError, httpx.TimeoutException)):
        details['is_timeout'] = True
    elif isinstance(e, httpx.ConnectError):
        details['is_connection'] = True
    elif isinstance(e, OSError):
        details['error_code'] = e.errno
        if e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
            details['is_resource_exhaustion'] = True
            details['error_message'] = f"EAGAIN/EWOULDBLOCK: OS socket resources exhausted - {str(e)}"
        elif e.errno == errno.EMFILE or e.errno == errno.ENFILE:
            details['is_resource_exhaustion'] = True
            details['error_message'] = f"EMFILE/ENFILE: Too many open files - {str(e)}"

    return details


def execute_parallel(tasks: List[Tuple[Callable, List[Any]]], max_workers: int = 3) -> List[Any]:
    """Execute multiple tasks in parallel using ThreadPoolExecutor

    FIX #5: Parallelize database calls to reduce total query time under concurrent load

    Args:
        tasks: List of (callable, args) tuples where callable(*args) is executed
        max_workers: Maximum number of parallel threads (default 3 to avoid resource exhaustion)

    Returns:
        List of results in the same order as input tasks

    Example:
        results = execute_parallel([
            (db.is_vip_user, ['user@example.com']),
            (db.get_user_credits, ['user@example.com']),
            (db.check_maintenance, [date])
        ])
    """
    results = [None] * len(tasks)

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks and keep track of their positions
            future_to_index = {
                executor.submit(callable_fn, *args): idx
                for idx, (callable_fn, args) in enumerate(tasks)
            }

            # Collect results as they complete (or fail)
            for future in as_completed(future_to_index):
                idx = future_to_index[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    # Log error but don't crash - return None for failed task
                    print(f"Parallel task {idx} failed: {str(e)}")
                    results[idx] = None

    except Exception as e:
        # If ThreadPoolExecutor fails, log error and return all None
        print(f"Parallel execution failed: {str(e)}")
        results = [None] * len(tasks)

    return results


class StreamlitRequestLimiter:
    """Limita solicitudes concurrentes a Supabase para prevenir agotamiento de recursos

    Bajo Streamlit, múltiples reruns pueden causar picos simultáneos de solicitudes.
    Este limitador evita que demasiadas solicitudes golpeen a Supabase/OS al mismo tiempo.
    """
    def __init__(self, max_concurrent=5):
        self.semaphore = threading.Semaphore(max_concurrent)
        self.max_concurrent = max_concurrent
        self.active_requests = 0
        self.lock = threading.Lock()

    def acquire(self, timeout=2.0):
        """Acquire permission to make a request. Returns True if acquired within timeout."""
        acquired = self.semaphore.acquire(timeout=timeout)
        if acquired:
            with self.lock:
                self.active_requests += 1
        return acquired

    def release(self):
        """Release permission after request completes."""
        with self.lock:
            self.active_requests = max(0, self.active_requests - 1)
        self.semaphore.release()

    def get_stats(self) -> Dict:
        """Get current limiter statistics"""
        with self.lock:
            return {
                'active_requests': self.active_requests,
                'max_concurrent': self.max_concurrent,
                'available_slots': self.max_concurrent - self.active_requests
            }


# Global request limiter (5 concurrent requests max prevents OS resource exhaustion)
_request_limiter = StreamlitRequestLimiter(max_concurrent=5)


def limit_concurrent_requests(func):
    """Decorator que limita solicitudes concurrentes a la base de datos

    Esto previene picos de conexiones que causen EAGAIN en Streamlit Cloud.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Wait for a slot to become available (timeout prevents infinite hangs)
        acquired = _request_limiter.acquire(timeout=3.0)

        if not acquired:
            print(f"⚠️ {func.__name__} - conexión saturada, esperando slot...")
            # Retry once after a short wait
            time.sleep(0.5)
            acquired = _request_limiter.acquire(timeout=2.0)

            if not acquired:
                raise DatabaseConnectionError(
                    "Base de datos saturada. Por favor intenta en unos segundos."
                )

        try:
            return func(*args, **kwargs)
        finally:
            _request_limiter.release()

    return wrapper


def retry_on_timeout(max_retries=3, backoff_factor=1.0):
    """Decorator para reintentar operaciones de DB en caso de timeout/resource errors

    Implementa exponential backoff with jitter para prevenir retry storms.
    Ahora captura EAGAIN (Errno 11) y otros errores de recursos del OS.

    Args:
        max_retries: Número máximo de reintentos (default 3)
        backoff_factor: Factor de espera exponencial entre reintentos (default 1.0 = sin espera)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            last_error_details = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (TimeoutError, httpx.TimeoutException, httpx.ConnectError, OSError) as e:
                    last_exception = e
                    error_details = _get_error_details(e)
                    last_error_details = error_details

                    # Determine if we should retry
                    should_retry = (
                        error_details['is_timeout'] or
                        error_details['is_connection'] or
                        error_details['is_resource_exhaustion']
                    )

                    if not should_retry:
                        # OSError that's not a resource issue - don't retry
                        raise

                    if attempt < max_retries - 1:
                        # Exponential backoff with jitter to prevent retry storms
                        base_wait = backoff_factor * (2 ** attempt)
                        jitter = random.uniform(0, 0.5)
                        wait_time = base_wait + jitter

                        # Log detailed diagnostic info
                        st.warning(
                            f"⚠️ {func.__name__} - {error_details['error_message']}\n"
                            f"Reintentando (intento {attempt + 2}/{max_retries}) en {wait_time:.2f}s..."
                        )
                        print(f"[DEBUG] {func.__name__} error details: {error_details}")
                        time.sleep(wait_time)
                    else:
                        # All retries exhausted
                        print(f"❌ {func.__name__} falló después de {max_retries} intentos - {error_details}")
                        st.error(f"❌ Error de conexión: {error_details['error_message']}")
                except Exception as e:
                    # Non-retryable errors
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

    def get_user_info_parallel(self, email: str) -> Dict[str, Any]:
        """Get VIP status and credits in parallel to reduce query time

        FIX #5: Parallelizes two independent database queries that are often made together

        Args:
            email: User email to get info for

        Returns:
            Dict with 'is_vip' and 'credits' keys

        Example:
            info = db_manager.get_user_info_parallel('user@example.com')
            is_vip = info.get('is_vip', False)
            credits = info.get('credits', 0)
        """
        # Execute both queries in parallel instead of sequentially
        results = execute_parallel([
            (self.is_vip_user, [email]),
            (self.get_user_credits, [email])
        ], max_workers=2)

        return {
            'is_vip': results[0] if results[0] is not None else False,
            'credits': results[1] if results[1] is not None else 0
        }

    @limit_concurrent_requests
    @retry_on_timeout(max_retries=2, backoff_factor=0.3)
    def is_vip_user(self, email: str) -> bool:
        """Verificar si un usuario es VIP (tiene horario extendido)

        FIX #3: Aplica retry para manejar timeouts bajo carga
        FIX #4: Implementa caching con TTL de 24 horas (VIP status rarely changes)
        FIX #5: Limita solicitudes concurrentes para prevenir EAGAIN en Streamlit Cloud
        """
        from cache_manager import get_cache

        cache = get_cache()
        cache_key = f"vip:{email.strip().lower()}"

        # Try to get from cache first (24 hour TTL - VIP status rarely changes)
        cached_is_vip = cache.get(cache_key)
        if cached_is_vip is not None:
            return cached_is_vip

        try:
            result = self.client.table('vip_users').select('id').eq(
                'email', email.strip().lower()
            ).execute()
            is_vip = len(result.data) > 0
            # Store in cache with 24 hour TTL
            cache.set(cache_key, is_vip, ttl_seconds=86400)
            return is_vip
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

    @limit_concurrent_requests
    @retry_on_timeout(max_retries=3, backoff_factor=0.5)
    def get_user_credits(self, user_email: str) -> int:
        """Obtener créditos actuales del usuario

        FIX #3: Aplica retry con backoff exponencial para manejar timeouts bajo carga
        FIX #4: Implementa caching con TTL de 5 minutos para reducir carga de DB
        FIX #5: Limita solicitudes concurrentes para prevenir EAGAIN en Streamlit Cloud
        """
        from cache_manager import get_cache

        cache = get_cache()
        cache_key = f"credits:{user_email.strip().lower()}"

        # Try to get from cache first (5 minute TTL)
        cached_credits = cache.get(cache_key)
        if cached_credits is not None:
            return cached_credits

        try:
            result = self.client.table('users').select('credits').eq(
                'email', user_email.strip().lower()
            ).execute()

            if result.data:
                credits = result.data[0]['credits'] or 0
                # Store in cache with 5 minute TTL
                cache.set(cache_key, credits, ttl_seconds=300)
                return credits

            cache.set(cache_key, 0, ttl_seconds=300)
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

    def invalidate_user_cache(self, email: str):
        """Invalidate cached data for a user after reservation

        Should be called after:
        - Credit deduction
        - Reservation creation
        - Profile updates

        Args:
            email: User email to invalidate cache for
        """
        from cache_manager import get_cache
        cache = get_cache()
        # Invalidate credits cache - will be reloaded on next check
        cache.invalidate(f"credits:{email.strip().lower()}")

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

    @limit_concurrent_requests
    @retry_on_timeout(max_retries=3, backoff_factor=0.5)
    def get_date_reservations_summary(self, dates: List[datetime.date], user_email: str) -> Dict:
        """Get all reservation data for multiple dates in one call

        FIX #3: Aplica retry para manejar timeouts bajo carga
        FIX #5: Limita solicitudes concurrentes para prevenir EAGAIN en Streamlit Cloud
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

    @limit_concurrent_requests
    def is_slot_still_available(self, date: datetime.date, hour: int) -> bool:
        """Quick real-time check if slot is still available - single fast query

        FIX #5: Limita solicitudes concurrentes para prevenir EAGAIN en Streamlit Cloud
        """
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