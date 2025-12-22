"""
Gestor de Base de Datos Supabase para Sistema de Reservas de Cancha de Tenis
"""
import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import contextlib
from timezone_utils import get_colombia_now


class SupabaseManager:
    """Gestor de base de datos Supabase para el sistema de reservas"""

    def __init__(self):
        try:
            self.url = st.secrets["supabase"]["url"]
            self.key = st.secrets["supabase"]["key"]
            self.client: Client = create_client(self.url, self.key)
            self.init_tables()
        except Exception as e:
            st.error(f"Error al conectar con Supabase: {e}")
            self.client = None

    def init_tables(self):
        """Verificar que las tablas existan en Supabase"""
        # Las tablas deben crearse en el dashboard de Supabase
        # Este método verifica si existen
        try:
            # Probar conexión
            result = self.client.table('reservations').select('id').limit(1).execute()
            return True
        except Exception:
            st.error("Tablas no encontradas. Por favor ejecuta el SQL de configuración en el dashboard de Supabase.")
            return False

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

    def is_vip_user(self, email: str) -> bool:
        """Verificar si un usuario es VIP (tiene horario extendido)"""
        try:
            # VIP status is now stored in users.is_vip column
            result = self.client.table('users').select('is_vip').eq(
                'email', email.strip().lower()
            ).execute()
            if result.data and len(result.data) > 0:
                return result.data[0].get('is_vip', False)
            return False
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

    def get_user_credits(self, user_email: str) -> int:
        """Obtener créditos actuales del usuario"""
        try:
            result = self.client.table('users').select('credits').eq(
                'email', user_email.strip().lower()
            ).execute()

            if result.data:
                return result.data[0]['credits'] or 0
            return 0
        except Exception as e:
            print(f"Error getting user credits: {e}")
            return 0

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
        """Guardar nueva reserva - NOTE: Now requires user_id instead of name/email"""
        try:
            # Get user_id from email
            user_result = self.client.table('users').select('id').eq('email', email.strip().lower()).execute()
            if not user_result.data:
                st.error(f"Usuario no encontrado: {email}")
                return False

            user_id = user_result.data[0]['id']

            result = self.client.table('reservations').insert({
                'date': date.strftime('%Y-%m-%d'),
                'hour': hour,
                'user_id': user_id,
                'created_at': get_colombia_now().replace(tzinfo=None).isoformat()
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
        except Exception:
            return False

    def get_reservations_for_date(self, date: datetime.date) -> List[int]:
        """Obtener horas reservadas para una fecha específica"""
        try:
            result = self.client.table('reservations').select('hour').eq(
                'date', date.strftime('%Y-%m-%d')
            ).order('hour').execute()
            return [row['hour'] for row in result.data]
        except Exception:
            return []

    def get_reservations_with_names_for_date(self, date: datetime.date) -> Dict[int, str]:
        """Obtener reservas con nombres de usuarios para una fecha - Now uses JOIN"""
        try:
            result = self.client.table('reservations').select(
                'hour, users(full_name)'
            ).eq('date', date.strftime('%Y-%m-%d')).order('hour').execute()
            return {row['hour']: row['users']['full_name'] for row in result.data if row.get('users')}
        except Exception as e:
            print(f"Error getting reservations with names: {e}")
            return {}

    def get_user_reservations_for_date(self, email: str, date: datetime.date) -> List[int]:
        """Obtener reservas de un usuario específico para una fecha - Now uses user_id"""
        try:
            # Get user_id from email
            user_result = self.client.table('users').select('id').eq('email', email.strip().lower()).execute()
            if not user_result.data:
                return []

            user_id = user_result.data[0]['id']

            result = self.client.table('reservations').select('hour').eq(
                'user_id', user_id
            ).eq('date', date.strftime('%Y-%m-%d')).order('hour').execute()
            return [row['hour'] for row in result.data]
        except Exception:
            return []

    def get_all_reservations(self) -> List[tuple]:
        """Obtener todas las reservas del sistema - Now uses JOIN with users"""
        try:
            result = self.client.table('reservations').select(
                'id, date, hour, user_id, created_at, users(full_name, email)'
            ).order('date', desc=True).order('hour').execute()

            # Convert to tuple format (id, date, hour, name, email, created_at)
            reservations = []
            for row in result.data:
                if row.get('users'):
                    reservations.append((
                        row['id'],
                        row['date'],
                        row['hour'],
                        row['users']['full_name'],
                        row['users']['email'],
                        row['created_at']
                    ))
            return reservations
        except Exception as e:
            print(f"Error getting all reservations: {e}")
            return []

    def get_date_reservations_summary(self, dates: List[datetime.date], user_email: str) -> Dict:
        """Get all reservation data for multiple dates in one call - Now uses user_id and JOIN"""
        try:
            date_strings = [d.strftime('%Y-%m-%d') for d in dates]

            # Get user_id from email for filtering user's own reservations
            user_id = None
            if user_email:
                user_result = self.client.table('users').select('id').eq('email', user_email.strip().lower()).execute()
                if user_result.data:
                    user_id = user_result.data[0]['id']

            # Single query for all reservations across dates with user data
            result = self.client.table('reservations').select(
                'date, hour, user_id, users(full_name)'
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

                if row.get('users') and row['users'].get('full_name'):
                    summary['reservation_names'][date_str][hour] = row['users']['full_name']

                if user_id and row['user_id'] == user_id:
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
            maintenance_result = self.client.table('blocked_slots').select('id').eq(
                'date', date.strftime('%Y-%m-%d')
            ).eq('hour', hour).execute()

            if maintenance_result.data:
                return False

            # Check for Tennis School time (if enabled)
            tennis_school_check = self.client.table('system_settings').select('tennis_school_enabled').limit(1).execute()
            if tennis_school_check.data and tennis_school_check.data[0].get('tennis_school_enabled', False):
                # Check if Saturday/Sunday 8-11 AM
                if date.weekday() in [5, 6] and hour in [8, 9, 10, 11]:
                    return False

            return True

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

    # NOTE: Email verification is now handled by Next.js app via email_verification_tokens table
    # These legacy methods are kept for backwards compatibility but should not be used

    def cleanup_expired_data(self):
        """Limpiar datos expirados del sistema"""
        try:
            import datetime
            now = datetime.datetime.utcnow().isoformat()

            # Limpiar tokens de verificación de email expirados (new table)
            try:
                self.client.table('email_verification_tokens').delete().lt('expires_at', now).execute()
            except Exception:
                pass  # Table may not exist in admin context

            # Limpiar tokens de reset expirados
            try:
                self.client.table('password_reset_tokens').delete().lt('expires_at', now).execute()
            except Exception:
                pass  # Table may not exist in admin context

        except Exception as e:
            st.warning(f"Error en limpieza automática: {e}")

    def log_critical_operation(self, operation_type: str, details: dict, success: bool):
        """Log critical database operations for audit trail - Currently logs to console only"""
        try:
            # NOTE: system_logs table doesn't exist in new schema
            # For now, just log to console. Could be added back via migration if needed.
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

            if result.data and len(result.data) > 0:
                response = result.data[0]
                return response['success'], response['message']
            else:
                return False, "Sin respuesta de la base de datos"

        except Exception as e:
            return False, f"Error: {str(e)}"

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

            if result.data and len(result.data) > 0:
                response = result.data[0]
                return response['success'], response['message']
            else:
                return False, "Sin respuesta de la base de datos"

        except Exception as e:
            return False, f"Error: {str(e)}"

    def get_blocked_slots_for_date(self, date: datetime.date) -> List[int]:
        """Obtener horarios de mantenimiento para una fecha"""
        try:
            result = self.client.table('blocked_slots').select('hour').eq(
                'date', date.strftime('%Y-%m-%d')
            ).execute()
            return [row['hour'] for row in result.data]
        except Exception:
            return []



# Instancia global
db_manager = SupabaseManager()