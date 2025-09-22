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


    def get_user_credits(self, email: str) -> int:
        """Obtener créditos disponibles del usuario"""
        try:
            result = self.client.table('users').select('credits').eq('email', email.strip().lower()).execute()
            if result.data:
                return result.data[0]['credits'] or 0
            return 0
        except Exception:
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

    def get_date_reservations_summary(self, dates: List[datetime.date], user_email: str) -> Dict:
        """Get all reservation data for multiple dates in one call"""
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


# Instancia global
db_manager = SupabaseManager()