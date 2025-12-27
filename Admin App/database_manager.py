"""
Gestor de Base de Datos Supabase para Sistema de Reservas de Cancha de Tenis
"""
import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
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
                    'description': f'Reserva {date} {hour}:00'
                }).execute()
                return True

            return False
        except Exception as e:
            print(f"Error using credits: {e}")
            return False

    def save_reservation(self, date: datetime.date, hour: int, name: str, email: str) -> bool:
        """
        Guardar nueva reserva - NOTE: Now requires user_id instead of name/email
        Valida contra reservas existentes, mantenimiento y escuela de tenis
        """
        try:
            # Get user_id from email
            user_result = self.client.table('users').select('id').eq('email', email.strip().lower()).execute()
            if not user_result.data:
                st.error(f"Usuario no encontrado: {email}")
                return False

            user_id = user_result.data[0]['id']

            # Check if the slot is actually available
            slot_status = self.get_slot_status(date, hour)

            if not slot_status['available']:
                # Provide specific error message based on the reason
                if slot_status['reason'] == 'reserved':
                    st.error(f"❌ Esta hora ya está reservada. {slot_status['details']}")
                elif slot_status['reason'] == 'tennis_school':
                    st.error(f"❌ No se puede reservar: {slot_status['details']}")
                elif slot_status['reason'] == 'maintenance':
                    st.error(f"❌ No se puede reservar: {slot_status['details']}")
                else:
                    st.error(f"❌ Esta hora no está disponible: {slot_status['details']}")
                return False

            # Slot is available, proceed with reservation
            result = self.client.table('reservations').insert({
                'date': date.strftime('%Y-%m-%d'),
                'hour': hour,
                'user_id': user_id
            }).execute()
            return len(result.data) > 0
        except Exception as e:
            # Verificar si es error de clave duplicada
            if 'duplicate' in str(e).lower() or 'unique' in str(e).lower():
                st.error("❌ Esta hora ya está reservada")
                return False
            st.error(f"❌ Error de base de datos: {e}")
            return False

    def get_slot_status(self, date: datetime.date, hour: int) -> Dict[str, any]:
        """
        Obtener el estado detallado de un slot
        Retorna información sobre si está disponible y por qué no lo está

        Returns:
            dict: {
                'available': bool,
                'reason': str,  # 'available', 'reserved', 'maintenance', 'tennis_school'
                'details': str  # Mensaje descriptivo
            }
        """
        try:
            # Check if there's already a reservation
            reservation_result = self.client.table('reservations').select(
                'id, users(full_name)'
            ).eq('date', date.strftime('%Y-%m-%d')).eq('hour', hour).execute()

            if reservation_result.data:
                user_name = reservation_result.data[0].get('users', {}).get('full_name', 'Usuario')
                return {
                    'available': False,
                    'reason': 'reserved',
                    'details': f'Ya reservado por {user_name}'
                }

            # Check if the slot is blocked
            blocked_result = self.client.table('blocked_slots').select('id, type, reason').eq(
                'date', date.strftime('%Y-%m-%d')
            ).eq('hour', hour).execute()

            if blocked_result.data:
                block = blocked_result.data[0]
                block_type = block.get('type', 'maintenance')

                if block_type == 'tennis_school':
                    return {
                        'available': False,
                        'reason': 'tennis_school',
                        'details': 'Escuela de Tenis (Sábados y Domingos 8:00-12:00)'
                    }
                else:
                    return {
                        'available': False,
                        'reason': 'maintenance',
                        'details': 'Cancha en mantenimiento'
                    }

            return {
                'available': True,
                'reason': 'available',
                'details': 'Disponible'
            }
        except Exception as e:
            print(f"Error getting slot status: {e}")
            return {
                'available': False,
                'reason': 'error',
                'details': 'Error al verificar disponibilidad'
            }

    def is_hour_available(self, date: datetime.date, hour: int) -> bool:
        """
        Verificar si una hora está disponible
        Chequea:
        1. Reservas normales de usuarios
        2. Slots bloqueados por mantenimiento
        3. Slots bloqueados por escuela de tenis
        """
        status = self.get_slot_status(date, hour)
        return status['available']

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

    def get_blocked_slots_for_date(self, date: datetime.date) -> List[int]:
        """Obtener horarios de mantenimiento para una fecha"""
        try:
            result = self.client.table('blocked_slots').select('hour').eq(
                'date', date.strftime('%Y-%m-%d')
            ).execute()
            return [row['hour'] for row in result.data]
        except Exception:
            return []

    def log_activity(self, user_id: str, activity_type: str, description: str = "",
                     metadata: dict = None) -> bool:
        """
        Log user activity for analytics (simplified - reservations only)

        Args:
            user_id: User's UUID
            activity_type: Type of activity (reservation_create)
            description: Human-readable description
            metadata: Additional context as dict
        """
        try:
            self.client.table('user_activity_logs').insert({
                'user_id': user_id,
                'activity_type': activity_type,
                'activity_description': description,
                'metadata': metadata or {}
            }).execute()
            return True
        except Exception as e:
            print(f"Error logging activity: {e}")
            return False

    def get_activity_timeline_data(self, start_date: str = None, end_date: str = None,
                                   granularity: str = 'hour') -> List[Dict]:
        """
        Get activity data for timeline visualization

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            granularity: 'hour', 'day', or 'month'
        """
        try:
            from datetime import datetime, timedelta

            # Default to last 7 days if no dates provided
            if not end_date:
                end_date = get_colombia_today().strftime('%Y-%m-%d')
            if not start_date:
                start_dt = datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=7)
                start_date = start_dt.strftime('%Y-%m-%d')

            # Build query with explicit timezone
            start_filter = f"{start_date}T00:00:00+00:00"
            end_filter = f"{end_date}T23:59:59+00:00"

            print(f"[DEBUG] Querying activity_logs:")
            print(f"  Start: {start_filter}")
            print(f"  End:   {end_filter}")

            # First, check if we can get ANY records at all (no filters)
            test_result = self.client.table('user_activity_logs').select('id, created_at').limit(5).execute()
            print(f"  Test query (no filters): {len(test_result.data)} records")
            if test_result.data:
                for rec in test_result.data:
                    print(f"    - ID {rec['id']}: {rec['created_at']}")

            # Query activity logs with user info
            result = self.client.table('user_activity_logs').select(
                'id, user_id, activity_type, activity_description, created_at, users(full_name, email)'
            ).gte('created_at', start_filter).lte(
                'created_at', end_filter
            ).order('created_at').execute()

            print(f"  Filtered query: {len(result.data)} records")
            if result.data:
                print(f"  Sample timestamp: {result.data[0]['created_at']}")

            return result.data
        except Exception as e:
            print(f"Error getting timeline data: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_activity_stats(self, start_date: str = None, end_date: str = None) -> Dict:
        """Get aggregated activity statistics"""
        try:
            from datetime import datetime, timedelta

            if not end_date:
                end_date = get_colombia_today().strftime('%Y-%m-%d')
            if not start_date:
                start_dt = datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=30)
                start_date = start_dt.strftime('%Y-%m-%d')

            # Build query with explicit timezone
            start_filter = f"{start_date}T00:00:00+00:00"
            end_filter = f"{end_date}T23:59:59+00:00"

            # Get all activities in date range
            result = self.client.table('user_activity_logs').select(
                'id, user_id, activity_type, created_at'
            ).gte('created_at', start_filter).lte(
                'created_at', end_filter
            ).execute()

            data = result.data

            # Calculate statistics
            total_activities = len(data)
            unique_users = len(set(item['user_id'] for item in data if item.get('user_id')))
            unique_sessions = 0  # Sessions not tracked in simplified version

            # Activity type breakdown
            activity_breakdown = {}
            for item in data:
                act_type = item.get('activity_type', 'unknown')
                activity_breakdown[act_type] = activity_breakdown.get(act_type, 0) + 1

            return {
                'total_activities': total_activities,
                'unique_users': unique_users,
                'unique_sessions': unique_sessions,
                'activity_breakdown': activity_breakdown,
                'date_range': {'start': start_date, 'end': end_date}
            }
        except Exception as e:
            print(f"Error getting activity stats: {e}")
            return {}


# Instancia global
db_manager = SupabaseManager()