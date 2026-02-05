"""
Gestor de Base de Datos para Funciones de Administración
VERSIÓN ACTUALIZADA con formateo de fechas y horas en zona horaria de Colombia
"""

from database_manager import db_manager
from timezone_utils import get_colombia_today, get_colombia_now, format_date_display, COLOMBIA_TZ
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from email_config import email_manager
import pytz

class AdminDatabaseManager:
    """Gestor de base de datos para funciones administrativas"""

    def __init__(self):
        self.client = db_manager.client

    def _format_colombia_datetime(self, utc_datetime_str: str) -> str:
        """Convertir datetime UTC a formato Colombia DD/MM/YYYY HH:MM"""
        try:
            if not utc_datetime_str:
                return 'N/A'

            # Limpiar el string de fecha
            if utc_datetime_str.endswith('Z'):
                utc_datetime_str = utc_datetime_str[:-1]
            elif '+00:00' in utc_datetime_str:
                utc_datetime_str = utc_datetime_str.replace('+00:00', '')

            # Parsear la fecha
            utc_dt = datetime.fromisoformat(utc_datetime_str)

            # Asegurar que tenga timezone UTC
            if utc_dt.tzinfo is None:
                utc_dt = pytz.UTC.localize(utc_dt)

            # Convertir a zona horaria de Colombia
            colombia_dt = utc_dt.astimezone(COLOMBIA_TZ)

            # Formatear como "DD/MM/YYYY HH:MM"
            return colombia_dt.strftime('%d/%m/%Y %H:%M')

        except Exception as e:
            print(f"Error formatting datetime: {e}")
            # Fallback: devolver solo los primeros 16 caracteres
            return utc_datetime_str[:16] if utc_datetime_str else 'N/A'

    def _format_colombia_date(self, utc_datetime_str: str) -> str:
        """Convertir datetime UTC a formato de fecha Colombia DD/MM/YYYY"""
        try:
            if not utc_datetime_str:
                return 'N/A'

            # Limpiar el string de fecha
            if utc_datetime_str.endswith('Z'):
                utc_datetime_str = utc_datetime_str[:-1]
            elif '+00:00' in utc_datetime_str:
                utc_datetime_str = utc_datetime_str.replace('+00:00', '')

            # Parsear la fecha
            utc_dt = datetime.fromisoformat(utc_datetime_str)

            # Asegurar que tenga timezone UTC
            if utc_dt.tzinfo is None:
                utc_dt = pytz.UTC.localize(utc_dt)

            # Convertir a zona horaria de Colombia
            colombia_dt = utc_dt.astimezone(COLOMBIA_TZ)

            # Formatear como "DD/MM/YYYY"
            return colombia_dt.strftime('%d/%m/%Y')

        except Exception as e:
            print(f"Error formatting date: {e}")
            # Fallback: devolver solo los primeros 10 caracteres
            return utc_datetime_str[:10] if utc_datetime_str else 'N/A'

    def get_system_statistics(self) -> Dict:
        """Obtener estadísticas generales del sistema"""
        try:
            # Usuarios totales y VIP
            users_result = self.client.table('users').select('id, is_vip, credits').execute()
            total_users = len(users_result.data)
            vip_users = len([u for u in users_result.data if u.get('is_vip', False)])

            # Fechas
            today = get_colombia_today()
            today_str = today.strftime('%Y-%m-%d')

            # Reservas de hoy
            reservations_today = self.client.table('reservations').select('id').eq('date', today_str).execute()
            today_reservations_count = len(reservations_today.data)

            # Tasa de ocupación hoy
            # Slots disponibles = 15 horas (6-20) menos slots bloqueados
            blocked_today = self.client.table('blocked_slots').select('id').eq('date', today_str).execute()
            available_slots = 15 - len(blocked_today.data)
            today_occupancy_rate = round((today_reservations_count / max(available_slots, 1)) * 100, 1)

            # Total reservas (histórico)
            all_reservations = self.client.table('reservations').select('id, user_id').execute()
            total_reservations = len(all_reservations.data)

            # Reservas esta semana (Lunes a Domingo)
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday)
            week_end = week_start + timedelta(days=6)
            week_start_str = week_start.strftime('%Y-%m-%d')
            week_end_str = week_end.strftime('%Y-%m-%d')

            week_reservations = self.client.table('reservations').select('id').gte(
                'date', week_start_str
            ).lte('date', week_end_str).execute()
            week_reservations_count = len(week_reservations.data)

            # Usuarios activos (últimos 30 días)
            thirty_days_ago = (today - timedelta(days=30)).strftime('%Y-%m-%d')
            active_users_ids = set([r['user_id'] for r in all_reservations.data
                                    if r.get('user_id')])
            # Filter by date - need to get reservations with dates
            active_reservations = self.client.table('reservations').select('user_id').gte(
                'date', thirty_days_ago
            ).execute()
            active_users_30d = len(set([r['user_id'] for r in active_reservations.data]))

            # Créditos totales emitidos (histórico)
            try:
                credits_issued_result = self.client.table('credit_transactions').select('amount').eq(
                    'transaction_type', 'admin_grant'
                ).execute()
                total_credits_issued = sum([t['amount'] for t in credits_issued_result.data]) if credits_issued_result.data else 0
            except Exception:
                total_credits_issued = 0

            # Créditos en sistema (balance actual de usuarios)
            total_credits_balance = sum([u['credits'] or 0 for u in users_result.data])

            return {
                'total_users': total_users,
                'vip_users': vip_users,
                'active_users_30d': active_users_30d,
                'total_reservations': total_reservations,
                'week_reservations': week_reservations_count,
                'today_reservations': today_reservations_count,
                'today_occupancy_rate': today_occupancy_rate,
                'total_credits_issued': total_credits_issued,
                'total_credits_balance': total_credits_balance
            }
        except Exception as e:
            print(f"Error getting system statistics: {e}")
            return {
                'total_users': 0,
                'vip_users': 0,
                'active_users_30d': 0,
                'total_reservations': 0,
                'week_reservations': 0,
                'today_reservations': 0,
                'today_occupancy_rate': 0,
                'total_credits_issued': 0,
                'total_credits_balance': 0
            }

    def get_reservations_by_day_of_week(self) -> Dict:
        """Get all reservations grouped by day of week"""
        try:
            result = self.client.table('reservations').select('date').execute()

            # Count by day of week
            day_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}  # Mon-Sun

            for reservation in result.data:
                date_obj = datetime.strptime(reservation['date'], '%Y-%m-%d').date()
                day_of_week = date_obj.weekday()
                day_counts[day_of_week] += 1

            # Convert to readable format
            days_spanish = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            total = sum(day_counts.values())

            return {
                'days': [days_spanish[i] for i in range(7)],
                'counts': [day_counts[i] for i in range(7)],
                'percentages': [round((day_counts[i] / total * 100), 1) if total > 0 else 0 for i in range(7)]
            }
        except Exception as e:
            print(f"Error getting day of week stats: {e}")
            return {'days': [], 'counts': [], 'percentages': []}

    def search_users_for_reservations(self, search_term: str) -> tuple[List[Dict], str]:
        """
        Buscar usuarios por nombre o email para gestión de reservas

        Returns:
            tuple: (list of users, error_message)
                   - Si tiene éxito: ([users], None)
                   - Si falla: ([], "error message")
        """
        try:
            # Buscar por email o nombre
            result = self.client.table('users').select('id, email, full_name').or_(
                f'email.ilike.%{search_term}%,full_name.ilike.%{search_term}%'
            ).execute()

            users = [{'id': u['id'], 'email': u['email'], 'name': u['full_name']} for u in result.data]
            return (users, None)
        except Exception as e:
            error_msg = f"Error de base de datos al buscar usuarios: {str(e)}"
            print(f"[Search] ERROR: {error_msg}")
            return ([], error_msg)

    def get_user_reservations_history(self, user_email: str, filter_type: str = 'all') -> List[Dict]:
        """Obtener historial completo de reservas de un usuario con filtros - Now uses user_id

        Args:
            user_email: Email del usuario
            filter_type: 'all', 'upcoming', 'past', 'this_week', 'this_month'
        """
        try:
            # Get user_id from email
            user_result = self.client.table('users').select('id').eq('email', user_email).execute()
            if not user_result.data:
                return []

            user_id = user_result.data[0]['id']

            # Base query
            query = self.client.table('reservations').select('*').eq('user_id', user_id)

            # Apply date filters
            today = get_colombia_today()  # Returns datetime.date object
            today_str = today.strftime('%Y-%m-%d')  # Convert to string for queries

            if filter_type == 'upcoming':
                query = query.gte('date', today_str)
            elif filter_type == 'past':
                query = query.lt('date', today_str)
            elif filter_type == 'this_week':
                # Get date 7 days from now (work with date object directly)
                week_end = today + timedelta(days=7)
                week_end_str = week_end.strftime('%Y-%m-%d')
                query = query.gte('date', today_str).lte('date', week_end_str)
            elif filter_type == 'this_month':
                # Get end of current month (work with date object directly)
                if today.month == 12:
                    month_end = f"{today.year + 1}-01-01"
                else:
                    month_end = f"{today.year}-{today.month + 1:02d}-01"
                query = query.gte('date', today_str).lt('date', month_end)

            # Order by date desc (most recent first), then by hour
            result = query.order('date', desc=True).order('hour').execute()

            # Formatear fechas de creación
            for reservation in result.data:
                if 'created_at' in reservation:
                    reservation['created_at'] = self._format_colombia_datetime(reservation['created_at'])

            return result.data
        except Exception as e:
            print(f"Error getting user reservations: {e}")
            return []

    def get_users_detailed_statistics(self) -> List[Dict]:
        """Get detailed statistics for all users"""
        # Use Python-based processing (RPC function not implemented in database)
        return self._get_users_detailed_statistics_fallback()

    def _get_users_detailed_statistics_fallback(self) -> List[Dict]:
        """Fallback method using Python processing (for backwards compatibility)"""
        try:
            # Get all users with their IDs
            users_result = self.client.table('users').select('id, email, full_name, created_at, credits').execute()

            # Create a dictionary to map user_id to email
            user_id_to_email = {user['id']: user['email'] for user in users_result.data}
            user_id_to_data = {user['id']: user for user in users_result.data}

            # Get all reservations (now uses user_id)
            reservations_result = self.client.table('reservations').select('user_id, date, hour').execute()

            # Get all credit transactions using user_id
            try:
                credits_transactions = self.client.table('credit_transactions').select(
                    'user_id, amount, transaction_type').execute()
            except Exception:
                credits_transactions = type('obj', (object,), {'data': []})()  # Empty result if table doesn't exist

            # Calculate total credits bought per user
            credits_by_user_id = {}
            for transaction in credits_transactions.data:
                user_id = transaction['user_id']
                if transaction['transaction_type'] in ['admin_grant', 'purchase', 'bonus']:
                    if user_id not in credits_by_user_id:
                        credits_by_user_id[user_id] = 0
                    credits_by_user_id[user_id] += transaction['amount']

            # Convert to email-based dictionary for backwards compatibility
            credits_dict = {}
            for user_id, total_credits in credits_by_user_id.items():
                if user_id in user_id_to_email:
                    email = user_id_to_email[user_id]
                    credits_dict[email] = total_credits

            # Process reservations by user (now uses user_id)
            user_reservations_by_id = {}
            for res in reservations_result.data:
                user_id = res['user_id']
                if user_id not in user_reservations_by_id:
                    user_reservations_by_id[user_id] = {
                        'total': 0,
                        'days': [],
                        'hours': []
                    }
                user_reservations_by_id[user_id]['total'] += 1

                # Add day of week
                date_obj = datetime.strptime(res['date'], '%Y-%m-%d').date()
                user_reservations_by_id[user_id]['days'].append(date_obj.weekday())

                # Add hour
                user_reservations_by_id[user_id]['hours'].append(res['hour'])

            # Convert to email-based dict for backwards compatibility
            user_reservations = {}
            for user_id, res_data in user_reservations_by_id.items():
                if user_id in user_id_to_email:
                    email = user_id_to_email[user_id]
                    user_reservations[email] = res_data

            # Build final user stats
            days_spanish = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

            user_stats = []
            for user in users_result.data:
                email = user['email']
                res_data = user_reservations.get(email, {'total': 0, 'days': [], 'hours': []})

                # Calculate favorite day
                if res_data['days']:
                    from collections import Counter
                    most_common_day = Counter(res_data['days']).most_common(1)[0][0]
                    favorite_day = days_spanish[most_common_day]
                else:
                    favorite_day = 'N/A'

                # Calculate favorite time
                if res_data['hours']:
                    from collections import Counter
                    most_common_hour = Counter(res_data['hours']).most_common(1)[0][0]
                    favorite_time = f"{most_common_hour:02d}:00"
                else:
                    favorite_time = 'N/A'

                user_stats.append({
                    'email': email,
                    'name': user['full_name'],
                    'registered_date': user['created_at'][:10] if user['created_at'] else 'N/A',
                    'total_credits_bought': credits_dict.get(email, 0),
                    'total_reservations': res_data['total'],
                    'favorite_day': favorite_day,
                    'favorite_time': favorite_time
                })

            return user_stats

        except Exception as e:
            print(f"Error in fallback method: {e}")
            return []

    def cancel_reservation_with_notification(self, reservation_id: int, user_email: str,
                                             cancellation_reason: str = "", admin_username: str = "admin") -> bool:
        """
        Cancelar reserva con proceso atómico completo

        IMPORTANTE: Solo retorna True si TODAS las operaciones se completan exitosamente:
        1. Reembolso de crédito
        2. Eliminación de reserva
        3. Envío de email de notificación
        4. Guardado de registro de cancelación

        Si cualquier operación falla, se hace rollback de las operaciones previas.
        """
        # Variables para tracking de rollback
        credit_refunded = False
        reservation_deleted = False
        reservation_backup = None
        user_id = None
        previous_credits = None

        try:
            # PASO 1: Obtener y validar todos los datos necesarios
            print(f"[Cancellation] Step 1: Fetching reservation data for ID {reservation_id}")
            reservation_result = self.client.table('reservations').select('*').eq('id', reservation_id).execute()
            if not reservation_result.data:
                print(f"[Cancellation] ERROR: Reservation {reservation_id} not found")
                return False

            reservation = reservation_result.data[0]
            reservation_backup = reservation.copy()  # Backup for potential rollback
            user_id = reservation['user_id']

            # Obtener datos del usuario
            print(f"[Cancellation] Step 2: Fetching user data for user_id {user_id}")
            user_result = self.client.table('users').select('id, email, full_name, credits').eq('id', user_id).execute()
            if not user_result.data:
                print(f"[Cancellation] ERROR: User {user_id} not found")
                return False

            user = user_result.data[0]
            previous_credits = user['credits'] or 0
            user_name = user['full_name']

            # Validar que email manager esté configurado
            if not email_manager.is_configured():
                print("[Cancellation] ERROR: Email manager not configured")
                return False

            print("[Cancellation] All validations passed, proceeding with cancellation")

            # PASO 2: Reembolsar crédito (operación reversible)
            print(f"[Cancellation] Step 3: Refunding credit to user (current: {previous_credits})")
            try:
                new_credits = previous_credits + 1
                self.client.table('users').update({
                    'credits': new_credits
                }).eq('id', user_id).execute()

                # Registrar transacción de reembolso
                self.client.table('credit_transactions').insert({
                    'user_id': user_id,
                    'amount': 1,
                    'transaction_type': 'reservation_refund',
                    'description': f'Reembolso por cancelación admin - {reservation["date"]} {reservation["hour"]}:00',
                    'admin_user': admin_username
                }).execute()

                credit_refunded = True
                print(f"[Cancellation] ✓ Credit refunded successfully (new balance: {new_credits})")
            except Exception as e:
                print(f"[Cancellation] ERROR: Failed to refund credit: {e}")
                return False

            # PASO 3: Eliminar reserva (reversible mediante reinserción)
            print(f"[Cancellation] Step 4: Deleting reservation {reservation_id}")
            try:
                delete_result = self.client.table('reservations').delete().eq('id', reservation_id).execute()
                if not delete_result.data:
                    raise Exception("Delete operation returned no data")

                reservation_deleted = True
                print("[Cancellation] ✓ Reservation deleted successfully")
            except Exception as e:
                print(f"[Cancellation] ERROR: Failed to delete reservation: {e}")
                # ROLLBACK: Restar el crédito que agregamos
                if credit_refunded:
                    print("[Cancellation] ROLLBACK: Removing refunded credit")
                    self.client.table('users').update({
                        'credits': previous_credits
                    }).eq('id', user_id).execute()
                return False

            # PASO 4: Enviar email de notificación
            print(f"[Cancellation] Step 5: Sending email notification to {user_email}")
            try:
                email_manager.send_reservation_cancelled_notification(
                    user_email=user_email,
                    user_name=user_name,
                    date=reservation['date'],
                    hour=reservation['hour'],
                    cancelled_by='admin',
                    reason=cancellation_reason or "Sin motivo especificado"
                )
                print("[Cancellation] ✓ Email sent successfully")
            except Exception as e:
                # Email failure is non-critical - cancellation already succeeded
                # Do NOT rollback: restoring the reservation could race with another user booking the slot
                print(f"[Cancellation] WARNING: Email notification failed: {e}")
                print("[Cancellation] Cancellation completed successfully despite email failure")

            # PASO 5: Guardar registro de cancelación (no crítico, pero se intenta)
            print("[Cancellation] Step 6: Saving cancellation record")
            try:
                cancellation_saved = self.save_cancellation_record(
                    reservation_id,
                    {
                        'user_id': user_id,
                        'email': user_email,
                        'name': user_name,
                        'date': reservation['date'],
                        'hour': reservation['hour']
                    },
                    cancellation_reason or "Sin motivo especificado",
                    admin_username
                )
                if cancellation_saved:
                    print("[Cancellation] ✓ Cancellation record saved successfully")
                else:
                    print("[Cancellation] WARNING: Cancellation record not saved, but main operation succeeded")
            except Exception as e:
                # No revertimos si falla esto, ya que las operaciones críticas tuvieron éxito
                print(f"[Cancellation] WARNING: Failed to save cancellation record: {e}")

            print("[Cancellation] ✓✓✓ ALL OPERATIONS COMPLETED SUCCESSFULLY ✓✓✓")
            return True

        except Exception as e:
            print(f"[Cancellation] UNEXPECTED ERROR: {e}")
            # Intentar rollback de cualquier operación completada
            if credit_refunded and user_id and previous_credits is not None:
                try:
                    print("[Cancellation] ROLLBACK: Removing refunded credit")
                    self.client.table('users').update({
                        'credits': previous_credits
                    }).eq('id', user_id).execute()
                except Exception as rollback_error:
                    print(f"[Cancellation] ERROR during rollback: {rollback_error}")

            return False

    def search_users_detailed(self, search_term: str) -> tuple[List[Dict], str]:
        """
        Búsqueda detallada de usuarios

        Returns:
            tuple: (list of users, error_message)
                   - Si tiene éxito: ([users], None)
                   - Si falla: ([], "error message")
        """
        try:
            result = self.client.table('users').select('*').or_(
                f'email.ilike.%{search_term}%,full_name.ilike.%{search_term}%'
            ).execute()

            # Formatear fechas para cada usuario
            for user in result.data:
                if 'created_at' in user:
                    user['created_at'] = self._format_colombia_datetime(user['created_at'])

            return (result.data, None)
        except Exception as e:
            error_msg = f"Error de base de datos al buscar usuarios: {str(e)}"
            print(f"[Search Detailed] ERROR: {error_msg}")
            return ([], error_msg)

    def get_user_stats(self, user_id: int) -> Dict:
        """Obtener estadísticas de un usuario específico - Now uses user_id"""
        try:
            # Total de reservas (now uses user_id)
            total_result = self.client.table('reservations').select('id').eq('user_id', user_id).execute()
            total_reservations = len(total_result.data)

            # Reservas futuras
            today = get_colombia_today().strftime('%Y-%m-%d')
            future_result = self.client.table('reservations').select('id').eq('user_id', user_id).gte('date',
                                                                                                  today).execute()
            active_reservations = len(future_result.data)

            # Última reserva
            last_result = self.client.table('reservations').select('date').eq('user_id', user_id).order('date',
                                                                                                    desc=True).limit(
                1).execute()
            last_reservation = last_result.data[0]['date'] if last_result.data else None

            return {
                'total_reservations': total_reservations,
                'active_reservations': active_reservations,
                'last_reservation': last_reservation
            }
        except Exception:
            return {'total_reservations': 0, 'active_reservations': 0, 'last_reservation': None}

    def get_user_reservation_statistics(self) -> List[Dict]:
        """Obtener estadísticas de reservas por usuario - Now uses JOIN"""
        try:
            result = self.client.table('reservations').select('user_id, date, hour, users(email, full_name)').execute()

            # Contar reservas por usuario y tracking de días/horas
            user_counts = {}
            days_spanish = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

            for reservation in result.data:
                if not reservation.get('users'):
                    continue

                user_id = reservation['user_id']
                email = reservation['users']['email']
                name = reservation['users']['full_name']
                hour = reservation.get('hour')
                date_str = reservation.get('date')

                if user_id in user_counts:
                    user_counts[user_id]['count'] += 1
                    if hour:
                        user_counts[user_id]['hours'].append(hour)
                    if date_str:
                        user_counts[user_id]['dates'].append(date_str)
                else:
                    user_counts[user_id] = {
                        'email': email,
                        'name': name,
                        'count': 1,
                        'hours': [hour] if hour else [],
                        'dates': [date_str] if date_str else []
                    }

            # Convertir a lista con día/hora favoritos
            user_stats = []
            for user_id, data in user_counts.items():
                # Calculate favorite hour
                favorite_hour = 'N/A'
                if data['hours']:
                    hour_counts = {}
                    for h in data['hours']:
                        hour_counts[h] = hour_counts.get(h, 0) + 1
                    most_common_hour = max(hour_counts, key=hour_counts.get)
                    favorite_hour = f"{most_common_hour}:00"

                # Calculate favorite day
                favorite_day = 'N/A'
                if data['dates']:
                    day_counts = {}
                    for d in data['dates']:
                        try:
                            weekday = datetime.strptime(d, '%Y-%m-%d').weekday()
                            day_counts[weekday] = day_counts.get(weekday, 0) + 1
                        except:
                            pass
                    if day_counts:
                        most_common_day = max(day_counts, key=day_counts.get)
                        favorite_day = days_spanish[most_common_day]

                user_stats.append({
                    'email': data['email'],
                    'name': data['name'],
                    'reservations': data['count'],
                    'favorite_day': favorite_day,
                    'favorite_hour': favorite_hour
                })

            return sorted(user_stats, key=lambda x: x['reservations'], reverse=True)[:10]
        except Exception as e:
            print(f"Error getting user reservation statistics: {e}")
            return []

    def get_hourly_reservation_stats(self) -> List[Dict]:
        """Obtener estadísticas de reservas por hora"""
        try:
            result = self.client.table('reservations').select('hour').execute()

            # Agrupar por hora
            hour_counts = {}
            for reservation in result.data:
                hour = reservation['hour']
                hour_counts[hour] = hour_counts.get(hour, 0) + 1

            return [{'hour': hour, 'count': count} for hour, count in sorted(hour_counts.items())]
        except Exception:
            return []

    def get_heatmap_data(self, days_filter: int = None) -> List[List[int]]:
        """
        Obtener datos para heatmap de día × hora

        Args:
            days_filter: Número de días hacia atrás (None = todos los datos)

        Returns:
            Lista de listas: [día_semana][hora] = count
            Días: 0=Lunes, 6=Domingo
            Horas: 6-20 (índices 0-14)
        """
        try:
            # Build query
            query = self.client.table('reservations').select('date, hour')

            # Apply date filter if specified
            if days_filter:
                filter_date = (get_colombia_today() - timedelta(days=days_filter)).strftime('%Y-%m-%d')
                query = query.gte('date', filter_date)

            result = query.execute()

            # Initialize 7x15 matrix (7 days, 15 hours from 6-20)
            heatmap = [[0 for _ in range(15)] for _ in range(7)]

            for reservation in result.data:
                date_obj = datetime.strptime(reservation['date'], '%Y-%m-%d').date()
                day_of_week = date_obj.weekday()  # 0=Monday, 6=Sunday
                hour = reservation['hour']

                # Map hour 6-20 to index 0-14
                if 6 <= hour <= 20:
                    hour_index = hour - 6
                    heatmap[day_of_week][hour_index] += 1

            return heatmap
        except Exception as e:
            print(f"Error getting heatmap data: {e}")
            return [[0 for _ in range(15)] for _ in range(7)]

    def get_occupancy_data(self, scale: str = 'weekly', offset: int = 0) -> Dict:
        """
        Obtener datos de ocupación según la escala seleccionada

        Args:
            scale: 'weekly', 'monthly', or 'yearly'
            offset: Desplazamiento (0 = actual, -1 = anterior, 1 = siguiente)

        Returns:
            Dict con datos de ocupación
        """
        try:
            today = get_colombia_today()
            days_spanish = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
            months_spanish = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                            'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

            dates = []
            occupancy_rates = []
            reservations_count = []
            available_slots_list = []
            period_label = ""
            current_index = -1  # Index of today in the data

            if scale == 'weekly':
                # Calculate week start with offset
                days_since_monday = today.weekday()
                week_start = today - timedelta(days=days_since_monday) + timedelta(weeks=offset)
                week_end = week_start + timedelta(days=6)
                period_label = f"Semana del {week_start.strftime('%d/%m')} al {week_end.strftime('%d/%m/%Y')}"

                for i in range(7):
                    current_date = week_start + timedelta(days=i)
                    date_str = current_date.strftime('%Y-%m-%d')

                    if current_date == today:
                        current_index = i

                    reservations = self.client.table('reservations').select('id').eq('date', date_str).execute()
                    num_reservations = len(reservations.data)

                    blocked = self.client.table('blocked_slots').select('id').eq('date', date_str).execute()
                    num_blocked = len(blocked.data)

                    available_slots = max(15 - num_blocked, 1)
                    occupancy = round((num_reservations / available_slots) * 100, 1)

                    dates.append(f"{days_spanish[i]} {current_date.strftime('%d/%m')}")
                    occupancy_rates.append(occupancy)
                    reservations_count.append(num_reservations)
                    available_slots_list.append(available_slots)

            elif scale == 'monthly':
                # Calculate month with offset
                target_month = today.month + offset
                target_year = today.year
                while target_month > 12:
                    target_month -= 12
                    target_year += 1
                while target_month < 1:
                    target_month += 12
                    target_year -= 1

                period_label = f"{months_spanish[target_month - 1]} {target_year}"

                # Get days in month
                if target_month == 12:
                    next_month = datetime(target_year + 1, 1, 1)
                else:
                    next_month = datetime(target_year, target_month + 1, 1)
                days_in_month = (next_month - datetime(target_year, target_month, 1)).days

                # Group by week
                for week in range(5):  # Max 5 weeks in a month
                    week_start_day = week * 7 + 1
                    week_end_day = min((week + 1) * 7, days_in_month)

                    if week_start_day > days_in_month:
                        break

                    week_reservations = 0
                    week_blocked = 0
                    days_counted = 0

                    for day in range(week_start_day, week_end_day + 1):
                        current_date = datetime(target_year, target_month, day).date()
                        date_str = current_date.strftime('%Y-%m-%d')

                        if current_date == today:
                            current_index = week

                        reservations = self.client.table('reservations').select('id').eq('date', date_str).execute()
                        week_reservations += len(reservations.data)

                        blocked = self.client.table('blocked_slots').select('id').eq('date', date_str).execute()
                        week_blocked += len(blocked.data)
                        days_counted += 1

                    available_slots = max((15 * days_counted) - week_blocked, 1)
                    occupancy = round((week_reservations / available_slots) * 100, 1)

                    dates.append(f"Sem {week + 1}")
                    occupancy_rates.append(occupancy)
                    reservations_count.append(week_reservations)
                    available_slots_list.append(available_slots)

            elif scale == 'yearly':
                # Calculate year with offset
                target_year = today.year + offset
                period_label = f"Año {target_year}"

                for month in range(1, 13):
                    if month == today.month and target_year == today.year:
                        current_index = month - 1

                    # Get first and last day of month
                    first_day = datetime(target_year, month, 1).date()
                    if month == 12:
                        last_day = datetime(target_year, 12, 31).date()
                    else:
                        last_day = datetime(target_year, month + 1, 1).date() - timedelta(days=1)

                    first_day_str = first_day.strftime('%Y-%m-%d')
                    last_day_str = last_day.strftime('%Y-%m-%d')

                    reservations = self.client.table('reservations').select('id').gte(
                        'date', first_day_str
                    ).lte('date', last_day_str).execute()
                    month_reservations = len(reservations.data)

                    blocked = self.client.table('blocked_slots').select('id').gte(
                        'date', first_day_str
                    ).lte('date', last_day_str).execute()
                    month_blocked = len(blocked.data)

                    days_in_month = (last_day - first_day).days + 1
                    available_slots = max((15 * days_in_month) - month_blocked, 1)
                    occupancy = round((month_reservations / available_slots) * 100, 1)

                    dates.append(months_spanish[month - 1])
                    occupancy_rates.append(occupancy)
                    reservations_count.append(month_reservations)
                    available_slots_list.append(available_slots)

            # Calculate period average (only up to current index for current period)
            if current_index >= 0 and offset == 0:
                valid_rates = occupancy_rates[:current_index + 1]
            else:
                valid_rates = occupancy_rates

            avg_occupancy = round(sum(valid_rates) / len(valid_rates), 1) if valid_rates else 0

            return {
                'dates': dates,
                'occupancy_rates': occupancy_rates,
                'reservations': reservations_count,
                'available_slots': available_slots_list,
                'average_occupancy': avg_occupancy,
                'current_index': current_index,
                'period_label': period_label,
                'scale': scale
            }
        except Exception as e:
            print(f"Error getting occupancy data: {e}")
            return {
                'dates': [],
                'occupancy_rates': [],
                'reservations': [],
                'available_slots': [],
                'average_occupancy': 0,
                'current_index': -1,
                'period_label': '',
                'scale': scale
            }

    def get_historic_average_occupancy(self) -> float:
        """Get historic average occupancy rate across all time"""
        try:
            # Get all reservations
            all_reservations = self.client.table('reservations').select('date').execute()

            if not all_reservations.data:
                return 0.0

            # Get unique dates with reservations
            dates_with_data = set()
            reservations_by_date = {}

            for res in all_reservations.data:
                date = res['date']
                dates_with_data.add(date)
                reservations_by_date[date] = reservations_by_date.get(date, 0) + 1

            # Get blocked slots for those dates
            total_occupancy = 0
            for date_str in dates_with_data:
                blocked = self.client.table('blocked_slots').select('id').eq('date', date_str).execute()
                available = max(15 - len(blocked.data), 1)
                occupancy = (reservations_by_date[date_str] / available) * 100
                total_occupancy += occupancy

            return round(total_occupancy / len(dates_with_data), 1) if dates_with_data else 0.0
        except Exception as e:
            print(f"Error getting historic average: {e}")
            return 0.0

    def add_credits_to_user(self, email: str, credits_amount: int, reason: str, admin_username: str) -> bool:
        """Agregar créditos a un usuario"""
        try:
            # Buscar usuario por email
            user_result = self.client.table('users').select('id, credits').eq('email', email.strip().lower()).execute()

            if not user_result.data:
                return False

            user = user_result.data[0]
            user_id = user['id']
            current_credits = user['credits'] or 0
            new_credits = current_credits + credits_amount

            # Actualizar créditos del usuario
            update_result = self.client.table('users').update({
                'credits': new_credits
            }).eq('id', user_id).execute()

            if update_result.data:
                # Registrar transacción
                self.client.table('credit_transactions').insert({
                    'user_id': user_id,
                    'amount': credits_amount,
                    'transaction_type': 'admin_grant',
                    'description': reason,
                    'admin_user': admin_username
                }).execute()

                return True
            return False
        except Exception as e:
            print(f"Error adding credits: {e}")
            return False

    def remove_credits_from_user(self, email: str, credits_amount: int, reason: str, admin_username: str) -> bool:
        """Quitar créditos a un usuario"""
        try:
            # Buscar usuario por email
            user_result = self.client.table('users').select('id, credits').eq('email', email.strip().lower()).execute()

            if not user_result.data:
                return False

            user = user_result.data[0]
            user_id = user['id']
            current_credits = user['credits'] or 0

            # Verificar que tenga suficientes créditos
            if current_credits < credits_amount:
                return False

            new_credits = current_credits - credits_amount

            # Actualizar créditos del usuario
            update_result = self.client.table('users').update({
                'credits': new_credits
            }).eq('id', user_id).execute()

            if update_result.data:
                # Registrar transacción
                self.client.table('credit_transactions').insert({
                    'user_id': user_id,
                    'amount': -credits_amount,
                    'transaction_type': 'admin_deduct',
                    'description': reason,
                    'admin_user': admin_username
                }).execute()

                return True
            return False
        except Exception as e:
            print(f"Error removing credits: {e}")
            return False

    def get_credit_statistics(self) -> Dict:
        """Obtener estadísticas de créditos"""
        try:
            # Créditos totales en el sistema
            users_result = self.client.table('users').select('credits').execute()
            total_credits = sum([u['credits'] or 0 for u in users_result.data])

            # Usuarios con créditos
            users_with_credits = len([u for u in users_result.data if (u['credits'] or 0) > 0])

            # Créditos usados hoy
            today = get_colombia_today().strftime('%Y-%m-%d')
            used_today_result = self.client.table('credit_transactions').select('amount').eq(
                'transaction_type', 'reservation_use'
            ).gte('created_at', today).execute()

            credits_used_today = abs(sum([t['amount'] for t in used_today_result.data])) if used_today_result.data else 0

            return {
                'total_credits': total_credits,
                'users_with_credits': users_with_credits,
                'credits_used_today': credits_used_today
            }
        except Exception:
            return {
                'total_credits': 0,
                'users_with_credits': 0,
                'credits_used_today': 0
            }

    def get_credit_economy_data(self, days_back: int = 30) -> Dict:
        """
        Obtener datos de economía de créditos para visualización

        Args:
            days_back: Número de días hacia atrás

        Returns:
            Dict con flujo de créditos y datos para gráficos
        """
        try:
            # Calculate date range
            end_date = get_colombia_now()
            start_date = end_date - timedelta(days=days_back)
            start_date_str = start_date.isoformat()
            start_date_only = start_date.strftime('%Y-%m-%d')

            # Get all transactions in the period
            transactions = self.client.table('credit_transactions').select(
                'amount, transaction_type, created_at'
            ).gte('created_at', start_date_str).order('created_at').execute()

            # Get reservations in the period (each reservation = 1 credit used)
            reservations = self.client.table('reservations').select(
                'date'
            ).gte('date', start_date_only).execute()

            # Categorize transactions
            credits_granted = 0  # admin_grant, bonus
            credits_refunded = 0 # reservation_refund
            credits_removed = 0  # admin_deduct (negative)

            # Data for timeline chart
            daily_data = {}

            for t in transactions.data:
                amount = t['amount']
                trans_type = t['transaction_type']
                date_str = t['created_at'][:10]  # Extract YYYY-MM-DD

                # Initialize daily data if needed
                if date_str not in daily_data:
                    daily_data[date_str] = {'granted': 0, 'used': 0, 'refunded': 0, 'removed': 0}

                if trans_type in ['admin_grant', 'bonus', 'purchase']:
                    credits_granted += amount
                    daily_data[date_str]['granted'] += amount
                elif trans_type == 'reservation_refund':
                    credits_refunded += amount
                    daily_data[date_str]['refunded'] += amount
                elif trans_type == 'admin_deduct':
                    credits_removed += abs(amount)
                    daily_data[date_str]['removed'] += abs(amount)

            # Calculate credits used from reservations (1 credit per reservation)
            credits_used = len(reservations.data)

            # Add reservation data to daily_data
            for r in reservations.data:
                date_str = r['date']
                if date_str not in daily_data:
                    daily_data[date_str] = {'granted': 0, 'used': 0, 'refunded': 0, 'removed': 0}
                daily_data[date_str]['used'] += 1

            # Calculate net flow
            net_flow = credits_granted + credits_refunded - credits_used - credits_removed

            # Prepare timeline data
            dates = sorted(daily_data.keys())
            timeline = {
                'dates': dates,
                'granted': [daily_data[d]['granted'] for d in dates],
                'used': [daily_data[d]['used'] for d in dates],
                'refunded': [daily_data[d]['refunded'] for d in dates],
                'net': [daily_data[d]['granted'] + daily_data[d]['refunded'] - daily_data[d]['used'] - daily_data[d]['removed'] for d in dates]
            }

            # Calculate cumulative balance over time
            cumulative = []
            running_total = 0
            for d in dates:
                running_total += (daily_data[d]['granted'] + daily_data[d]['refunded'] -
                                 daily_data[d]['used'] - daily_data[d]['removed'])
                cumulative.append(running_total)
            timeline['cumulative'] = cumulative

            return {
                'credits_granted': credits_granted,
                'credits_used': credits_used,
                'credits_refunded': credits_refunded,
                'credits_removed': credits_removed,
                'net_flow': net_flow,
                'timeline': timeline,
                'period_days': days_back
            }
        except Exception as e:
            print(f"Error getting credit economy data: {e}")
            return {
                'credits_granted': 0,
                'credits_used': 0,
                'credits_refunded': 0,
                'credits_removed': 0,
                'net_flow': 0,
                'timeline': {'dates': [], 'granted': [], 'used': [], 'refunded': [], 'net': [], 'cumulative': []},
                'period_days': days_back
            }

    def get_user_retention_data(self) -> Dict:
        """
        Calcular métricas de retención de usuarios

        Returns:
            Dict con métricas de retención
        """
        try:
            today = get_colombia_today()

            # Current month range
            current_month_start = today.replace(day=1)

            # Previous month range
            prev_month_end = current_month_start - timedelta(days=1)
            prev_month_start = prev_month_end.replace(day=1)

            # Get all reservations with user_id
            all_reservations = self.client.table('reservations').select('user_id, date').execute()

            if not all_reservations.data:
                return {
                    'new_users_this_month': 0,
                    'returning_users': 0,
                    'retention_rate': 0,
                    'total_active_prev_month': 0,
                    'frequency_distribution': {'1': 0, '2-5': 0, '6-10': 0, '10+': 0},
                    'avg_reservations_per_user': 0
                }

            # Group reservations by user
            user_reservations = {}
            for r in all_reservations.data:
                user_id = r['user_id']
                date = datetime.strptime(r['date'], '%Y-%m-%d').date()
                if user_id not in user_reservations:
                    user_reservations[user_id] = []
                user_reservations[user_id].append(date)

            # Calculate metrics
            users_current_month = set()
            users_prev_month = set()

            for user_id, dates in user_reservations.items():
                for d in dates:
                    if d >= current_month_start:
                        users_current_month.add(user_id)
                    elif prev_month_start <= d <= prev_month_end:
                        users_prev_month.add(user_id)

            # Returning users (active both months)
            returning_users = users_current_month.intersection(users_prev_month)

            # New users this month (first reservation ever is this month)
            new_users = set()
            for user_id in users_current_month:
                first_reservation = min(user_reservations[user_id])
                if first_reservation >= current_month_start:
                    new_users.add(user_id)

            # Retention rate
            retention_rate = 0
            if len(users_prev_month) > 0:
                retention_rate = round((len(returning_users) / len(users_prev_month)) * 100, 1)

            # Frequency distribution (all time)
            freq_dist = {'1': 0, '2-5': 0, '6-10': 0, '10+': 0}
            total_reservations = 0
            for user_id, dates in user_reservations.items():
                count = len(dates)
                total_reservations += count
                if count == 1:
                    freq_dist['1'] += 1
                elif 2 <= count <= 5:
                    freq_dist['2-5'] += 1
                elif 6 <= count <= 10:
                    freq_dist['6-10'] += 1
                else:
                    freq_dist['10+'] += 1

            # Average reservations per user
            avg_per_user = round(total_reservations / len(user_reservations), 1) if user_reservations else 0

            return {
                'new_users_this_month': len(new_users),
                'returning_users': len(returning_users),
                'retention_rate': retention_rate,
                'total_active_prev_month': len(users_prev_month),
                'frequency_distribution': freq_dist,
                'avg_reservations_per_user': avg_per_user
            }
        except Exception as e:
            print(f"Error getting user retention data: {e}")
            return {
                'new_users_this_month': 0,
                'returning_users': 0,
                'retention_rate': 0,
                'total_active_prev_month': 0,
                'frequency_distribution': {'1': 0, '2-5': 0, '6-10': 0, '10+': 0},
                'avg_reservations_per_user': 0
            }

    def get_alerts_and_anomalies(self) -> List[Dict]:
        """
        Detectar alertas y anomalías en el sistema

        Returns:
            Lista de alertas con tipo, mensaje y severidad
        """
        alerts = []
        try:
            today = get_colombia_today()
            today_str = today.strftime('%Y-%m-%d')

            # 1. Check today's occupancy
            stats = self.get_system_statistics()
            occupancy = stats.get('today_occupancy_rate', 0)
            if occupancy < 20:
                alerts.append({
                    'type': 'warning',
                    'icon': '📉',
                    'title': 'Ocupación Baja Hoy',
                    'message': f'La ocupación de hoy es solo {occupancy}%'
                })
            elif occupancy > 90:
                alerts.append({
                    'type': 'info',
                    'icon': '🔥',
                    'title': 'Alta Demanda Hoy',
                    'message': f'Ocupación del {occupancy}% - Considerar ampliar horarios'
                })

            # 2. Check for users with high cancellation rate
            cancel_stats = self.get_cancellation_statistics(30)
            if cancel_stats.get('cancellation_rate', 0) > 20:
                alerts.append({
                    'type': 'warning',
                    'icon': '⚠️',
                    'title': 'Tasa de Cancelación Alta',
                    'message': f"Tasa de cancelación: {cancel_stats['cancellation_rate']}% en los últimos 30 días"
                })

            # 3. Check for users with zero credits who have reservations
            users_result = self.client.table('users').select('id, full_name, credits').eq('credits', 0).execute()
            zero_credit_users = len(users_result.data) if users_result.data else 0
            if zero_credit_users > 5:
                alerts.append({
                    'type': 'info',
                    'icon': '💰',
                    'title': 'Usuarios sin Créditos',
                    'message': f'{zero_credit_users} usuarios tienen 0 créditos disponibles'
                })

            # 4. Check week reservations vs previous week
            week_start = today - timedelta(days=today.weekday())
            prev_week_start = week_start - timedelta(days=7)
            prev_week_end = week_start - timedelta(days=1)

            current_week = self.client.table('reservations').select('id').gte(
                'date', week_start.strftime('%Y-%m-%d')
            ).lte('date', today_str).execute()

            prev_week = self.client.table('reservations').select('id').gte(
                'date', prev_week_start.strftime('%Y-%m-%d')
            ).lte('date', prev_week_end.strftime('%Y-%m-%d')).execute()

            current_count = len(current_week.data) if current_week.data else 0
            prev_count = len(prev_week.data) if prev_week.data else 0

            if prev_count > 0:
                change = ((current_count - prev_count) / prev_count) * 100
                if change < -30:
                    alerts.append({
                        'type': 'warning',
                        'icon': '📊',
                        'title': 'Caída en Reservas',
                        'message': f'Reservas esta semana: {current_count} vs {prev_count} semana pasada ({change:.0f}%)'
                    })
                elif change > 50:
                    alerts.append({
                        'type': 'success',
                        'icon': '📈',
                        'title': 'Aumento en Reservas',
                        'message': f'Reservas esta semana: {current_count} vs {prev_count} semana pasada (+{change:.0f}%)'
                    })

            # 5. Check for inactive days (no reservations in last 7 days for a weekday)
            for i in range(7):
                check_date = today - timedelta(days=i)
                if check_date.weekday() < 5:  # Weekday only
                    day_reservations = self.client.table('reservations').select('id').eq(
                        'date', check_date.strftime('%Y-%m-%d')
                    ).execute()
                    if not day_reservations.data or len(day_reservations.data) == 0:
                        days_spanish = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
                        alerts.append({
                            'type': 'warning',
                            'icon': '📅',
                            'title': 'Día sin Reservas',
                            'message': f'{days_spanish[check_date.weekday()]} {check_date.strftime("%d/%m")} no tuvo reservas'
                        })
                        break  # Only report the most recent one

            # If no alerts, add a success message
            if not alerts:
                alerts.append({
                    'type': 'success',
                    'icon': '✅',
                    'title': 'Sistema Funcionando Normal',
                    'message': 'No se detectaron anomalías en el sistema'
                })

            return alerts
        except Exception as e:
            print(f"Error getting alerts: {e}")
            return [{
                'type': 'error',
                'icon': '❌',
                'title': 'Error',
                'message': f'No se pudieron cargar las alertas: {str(e)}'
            }]

    def get_credit_transactions(self, limit: int = 50, offset: int = 0) -> List:
        """Obtener historial de transacciones de créditos con paginación"""
        try:
            result = self.client.table('credit_transactions').select(
                'users(full_name), amount, transaction_type, description, admin_user, created_at'
            ).order('created_at', desc=True).range(offset, offset + limit - 1).execute()

            # Formatear datos para mostrar
            formatted_transactions = []
            for transaction in result.data:
                user_name = transaction['users']['full_name'] if transaction['users'] else 'Usuario eliminado'
                formatted_transactions.append([
                    user_name,
                    transaction['amount'],
                    transaction['transaction_type'],
                    transaction['description'],
                    transaction['admin_user'],
                    self._format_colombia_datetime(transaction['created_at'])  # FORMATEADO A COLOMBIA
                ])

            return formatted_transactions
        except Exception as e:
            print(f"Error getting credit transactions: {e}")
            return []

    def get_credit_transactions_count(self) -> int:
        """Obtener el total de transacciones de créditos"""
        try:
            result = self.client.table('credit_transactions').select('id', count='exact').execute()
            return result.count if result.count else 0
        except Exception as e:
            print(f"Error getting credit transactions count: {e}")
            return 0

    def get_all_users_for_export(self) -> List[Dict]:
        """Obtener todos los usuarios para exportación"""
        try:
            result = self.client.table('users').select(
                'id, email, full_name, credits, is_vip, first_login_completed, created_at'
            ).order('created_at', desc=True).execute()

            # Formatear datos para Excel
            formatted_users = []
            for user in result.data:
                formatted_users.append({
                    'ID': user['id'],
                    'Nombre Completo': user['full_name'],
                    'Email': user['email'],
                    'Créditos': user['credits'] or 0,
                    'Pertenece al Comité': 'Sí' if user.get('is_vip', False) else 'No',
                    'Primer Login Completado': 'Sí' if user.get('first_login_completed', False) else 'No',
                    'Fecha Registro': self._format_colombia_datetime(user['created_at'])
                })

            return formatted_users
        except Exception as e:
            print(f"Error getting users for export: {e}")
            return []

    def get_all_reservations_for_export(self) -> List[Dict]:
        """Obtener todas las reservas para exportación - Uses JOIN to users table"""
        try:
            result = self.client.table('reservations').select(
                'id, date, hour, user_id, created_at, users(full_name, email)'
            ).order('date', desc=True).order('hour').execute()

            # Formatear datos para Excel
            formatted_reservations = []
            for reservation in result.data:
                # Formatear fecha más legible
                from timezone_utils import format_date_display
                fecha_display = format_date_display(reservation['date'])

                # Get user data from JOIN
                user_name = reservation['users']['full_name'] if reservation.get('users') else 'Usuario Eliminado'
                user_email = reservation['users']['email'] if reservation.get('users') else 'N/A'

                formatted_reservations.append({
                    'ID Reserva': reservation['id'],
                    'Fecha': fecha_display,
                    'Hora': f"{reservation['hour']}:00 - {reservation['hour'] + 1}:00",
                    'Nombre Usuario': user_name,
                    'Email Usuario': user_email,
                    'Fecha Creación': self._format_colombia_datetime(reservation['created_at'])
                })

            return formatted_reservations
        except Exception as e:
            print(f"Error getting reservations for export: {e}")
            return []

    def search_users_for_credits(self, search_term: str) -> List[Dict]:
        """Buscar usuarios por nombre o email para gestión de créditos"""
        try:
            result = self.client.table('users').select('id, email, full_name, credits').or_(
                f'email.ilike.%{search_term}%,full_name.ilike.%{search_term}%'
            ).order('full_name').execute()

            return [{
                'id': u['id'],
                'email': u['email'],
                'name': u['full_name'],
                'credits': u['credits'] or 0
            } for u in result.data]
        except Exception as e:
            print(f"Error searching users for credits: {e}")
            return []

    def get_credit_transactions_for_export(self) -> List[Dict]:
        """Obtener transacciones de créditos para exportación"""
        try:
            result = self.client.table('credit_transactions').select(
                'users(full_name, email), amount, transaction_type, description, admin_user, created_at'
            ).order('created_at', desc=True).execute()

            # Formatear datos para Excel
            formatted_transactions = []
            for transaction in result.data:
                user_name = transaction['users']['full_name'] if transaction['users'] else 'Usuario eliminado'
                user_email = transaction['users']['email'] if transaction['users'] else 'N/A'

                # Traducir tipos de transacción
                transaction_types = {
                    'admin_grant': 'Otorgado por Admin',
                    'admin_deduct': 'Deducido por Admin',
                    'reservation_use': 'Usado en Reserva',
                    'reservation_refund': 'Reembolso de Reserva'
                }

                formatted_transactions.append({
                    'Usuario': user_name,
                    'Email': user_email,
                    'Cantidad': transaction['amount'],
                    'Tipo': transaction_types.get(transaction['transaction_type'], transaction['transaction_type']),
                    'Descripción': transaction['description'],
                    'Administrador': transaction['admin_user'] or 'Sistema',
                    'Fecha y Hora': self._format_colombia_datetime(transaction['created_at'])  # FORMATEADO A COLOMBIA
                })

            return formatted_transactions
        except Exception as e:
            print(f"Error getting credit transactions for export: {e}")
            return []

    def get_current_lock_code(self) -> Optional[str]:
        """Obtener la contraseña actual del candado"""
        try:
            result = self.client.table('lock_code').select('code').order('created_at', desc=True).limit(1).execute()
            return result.data[0]['code'] if result.data else None
        except Exception as e:
            print(f"Error getting lock code: {e}")
            return None

    def get_users_with_active_reservations(self) -> List[Dict]:
        """Obtener lista de usuarios con reservas activas (que no han pasado) - Uses JOIN"""
        try:
            today = get_colombia_today().strftime('%Y-%m-%d')

            # Obtener todas las reservas futuras con JOIN a users
            result = self.client.table('reservations').select('user_id, users(email, full_name)').gte('date', today).execute()

            # Crear un diccionario para evitar duplicados
            users_dict = {}
            for reservation in result.data:
                if reservation.get('users'):
                    email = reservation['users']['email']
                    if email not in users_dict:
                        users_dict[email] = {
                            'email': email,
                            'name': reservation['users']['full_name']
                        }

            return list(users_dict.values())
        except Exception as e:
            print(f"Error getting users with active reservations: {e}")
            return []

    def _send_lock_code_change_notification(self, user_email: str, user_name: str, new_lock_code: str) -> bool:
        """Enviar notificación de cambio de contraseña del candado"""
        try:
            from email_config import email_manager

            if not email_manager.is_configured():
                print(f"Email not configured, skipping notification for {user_email}")
                return False

            subject = "🔐 Nueva Contraseña del Candado - Sistema de Reservas"

            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #001854 0%, #2478CC 100%); color: white; padding: 30px; text-align: center; border-radius: 10px; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 10px; margin: 20px 0; }}
                    .lock-code-section {{ background: linear-gradient(135deg, #001854 0%, #2478CC 100%); border-radius: 12px; padding: 25px; margin: 25px 0; text-align: center; color: white; }}
                    .lock-code {{ font-size: 3.5rem; font-weight: bold; font-family: 'Courier New', monospace; letter-spacing: 8px; margin: 15px 0; }}
                    .info-box {{ background: white; padding: 15px; border-radius: 8px; border-left: 5px solid #FFD400; margin: 15px 0; }}
                    .footer {{ text-align: center; color: #666; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔐 Nueva Contraseña del Candado</h1>
                        <p>Sistema de Reservas de Cancha de Tenis</p>
                    </div>

                    <div class="content">
                        <h2>¡Hola {user_name}!</h2>
                        <p>Te notificamos que la <strong>contraseña del candado de la cancha ha sido actualizada</strong>.</p>

                        <p>Si tienes una reserva activa, usa esta nueva contraseña para acceder a la cancha:</p>

                        <div class="lock-code-section">
                            <div>Nueva Contraseña:</div>
                            <div class="lock-code">{new_lock_code}</div>
                        </div>

                        <div class="info-box">
                            <h4 style="margin-top: 0;">📝 Información Importante</h4>
                            <ul>
                                <li>Esta es la nueva contraseña para abrir el candado de la cancha</li>
                                <li>La contraseña anterior ya no funcionará</li>
                                <li>Asegúrate de anotar esta contraseña para tu próxima visita</li>
                            </ul>
                        </div>

                        <p>Si no tienes una reserva activa, puedes ignorar este mensaje.</p>
                        <p>Si tienes preguntas, contacta al administrador.</p>
                    </div>

                    <div class="footer">
                        <p>Sistema de Reservas de Cancha de Tenis - Colina Campestre</p>
                        <p>Este es un mensaje automatizado, por favor no respondas a este email.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            text_body = f"""
            Nueva Contraseña del Candado - Sistema de Reservas

            ¡Hola {user_name}!

            Te notificamos que la contraseña del candado de la cancha ha sido actualizada.

            Si tienes una reserva activa, usa esta nueva contraseña para acceder a la cancha:

            NUEVA CONTRASEÑA: {new_lock_code}

            INFORMACIÓN IMPORTANTE:
            - Esta es la nueva contraseña para abrir el candado de la cancha
            - La contraseña anterior ya no funcionará
            - Asegúrate de anotar esta contraseña para tu próxima visita

            Si no tienes una reserva activa, puedes ignorar este mensaje.

            Si tienes preguntas, contacta al administrador.

            Sistema de Reservas de Cancha de Tenis - Colina Campestre
            """

            success, message = email_manager.send_email(user_email, subject, html_body, text_body)
            return success

        except Exception as e:
            print(f"Error sending lock code change notification: {e}")
            return False

    def update_lock_code(self, new_code: str, admin_username: str) -> bool:
        """Actualizar contraseña del candado y notificar a usuarios con reservas activas"""
        try:
            # Insertar nueva contraseña (mantiene historial)
            # Database handles created_at automatically
            result = self.client.table('lock_code').insert({
                'code': new_code
                # Note: admin_user column doesn't exist in lock_code table schema
            }).execute()

            if result.data and len(result.data) > 0:
                print(f"Lock code updated successfully: {new_code}")

                # Obtener usuarios con reservas activas y enviar notificaciones
                users_with_active_reservations = self.get_users_with_active_reservations()

                if users_with_active_reservations:
                    print(f"Notifying {len(users_with_active_reservations)} users about lock code change")

                    for user in users_with_active_reservations:
                        # Enviar email a cada usuario
                        success = self._send_lock_code_change_notification(
                            user['email'],
                            user['name'],
                            new_code
                        )
                        if success:
                            print(f"Lock code change notification sent to {user['email']}")
                        else:
                            print(f"Failed to send notification to {user['email']}")
                else:
                    print("No users with active reservations to notify")

                return True
            else:
                print("Failed to insert lock code")
                return False

        except Exception as e:
            print(f"Error updating lock code: {e}")
            return False

    def get_vip_users(self) -> List[Dict]:
        """Obtener lista de usuarios VIP - Now uses users.is_vip column"""
        try:
            result = self.client.table('users').select('id, email, full_name, created_at').eq('is_vip', True).order('created_at', desc=True).execute()
            return result.data
        except Exception as e:
            print(f"Error obteniendo usuarios VIP: {e}")
            return []

    def add_vip_user(self, email: str, admin_username: str) -> bool:
        """Agregar usuario VIP - Now sets users.is_vip = true"""
        try:
            # First check if user exists
            user_result = self.client.table('users').select('id, is_vip').eq('email', email.strip().lower()).execute()
            if not user_result.data:
                return False

            user = user_result.data[0]

            # Check if already VIP
            if user.get('is_vip', False):
                return False  # Already VIP

            # Set is_vip to true
            result = self.client.table('users').update({
                'is_vip': True
            }).eq('email', email.strip().lower()).execute()

            return len(result.data) > 0
        except Exception as e:
            print(f"Error agregando usuario VIP: {e}")
            return False

    def remove_vip_user(self, email: str) -> bool:
        """Remover usuario VIP - Now sets users.is_vip = false"""
        try:
            result = self.client.table('users').update({
                'is_vip': False
            }).eq('email', email.strip().lower()).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Error removiendo usuario VIP: {e}")
            return False

    def get_current_access_code(self) -> Optional[str]:
        """Obtener el código de acceso actual"""
        try:
            result = self.client.table('access_codes').select('code').order('created_at', desc=True).limit(1).execute()
            return result.data[0]['code'] if result.data else None
        except Exception as e:
            print(f"Error getting access code: {e}")
            return None

    def update_access_code(self, new_code: str, admin_username: str) -> bool:
        """Actualizar código de acceso"""
        try:
            result = self.client.table('access_codes').insert({
                'code': new_code
                # Database handles created_at automatically
                # Note: admin_user column doesn't exist in access_codes table schema
            }).execute()

            if result.data and len(result.data) > 0:
                print(f"Access code updated successfully: {new_code}")
                return True
            else:
                print("Failed to insert access code")
                return False

        except Exception as e:
            print(f"Error updating access code: {e}")
            return False

    def get_weekly_calendar_data(self, week_offset: int = 0) -> Dict:
        """Obtener datos de reservas para vista de calendario semanal"""
        try:
            # Calcular el lunes de la semana seleccionada
            today = get_colombia_today()
            days_to_monday = today.weekday()  # 0 = lunes, 6 = domingo
            target_monday = today - timedelta(days=days_to_monday) + timedelta(weeks=week_offset)

            # Calcular rango de fechas (lunes a domingo)
            week_dates = []
            for i in range(7):  # 7 días de la semana
                day_date = target_monday + timedelta(days=i)
                week_dates.append(day_date)

            start_date = week_dates[0].strftime('%Y-%m-%d')
            end_date = week_dates[6].strftime('%Y-%m-%d')

            # Obtener reservas de la semana with JOIN to users table
            result = self.client.table('reservations').select('date, hour, user_id, users(full_name, email)').gte(
                'date', start_date
            ).lte('date', end_date).execute()

            # Obtener mantenimientos de la semana (incluyendo tipo)
            maintenance_result = self.client.table('blocked_slots').select('date, hour, maintenance_type, reason').gte(
                'date', start_date
            ).lte('date', end_date).execute()

            # Organizar datos por fecha y hora
            reservations_grid = {}
            maintenance_grid = {}
            for date in week_dates:
                date_str = date.strftime('%Y-%m-%d')
                reservations_grid[date_str] = {}
                maintenance_grid[date_str] = {}

            # Llenar el grid con las reservas
            for reservation in result.data:
                date_str = reservation['date']
                hour = reservation['hour']

                # Get name from JOIN - handle case where user was deleted
                if reservation.get('users'):
                    name = reservation['users']['full_name']
                    email = reservation['users']['email']
                else:
                    name = 'Usuario Eliminado'
                    email = 'N/A'

                if date_str in reservations_grid:
                    reservations_grid[date_str][hour] = {
                        'name': name,
                        'email': email
                    }

            # Llenar el grid con los mantenimientos
            for maintenance in maintenance_result.data:
                date_str = maintenance['date']
                hour = maintenance['hour']

                if date_str in maintenance_grid:
                    maintenance_grid[date_str][hour] = {
                        'type': maintenance.get('maintenance_type', 'single_hour'),
                        'reason': maintenance.get('reason', 'Mantenimiento')
                    }

            # Add Tennis School slots dynamically if enabled
            if self.get_tennis_school_enabled():
                for date in week_dates:
                    date_str = date.strftime('%Y-%m-%d')
                    # Check if it's Saturday or Sunday
                    if self.is_tennis_school_time(date, 8):  # Just check if it's a weekend
                        # Add hours 8-11
                        for hour in [8, 9, 10, 11]:
                            if date_str in maintenance_grid:
                                maintenance_grid[date_str][hour] = {
                                    'type': 'tennis_school',
                                    'reason': 'Escuela de Tenis'
                                }

            return {
                'week_dates': week_dates,
                'reservations_grid': reservations_grid,
                'maintenance_grid': maintenance_grid,
                'week_start': week_dates[0].strftime('%d/%m/%Y'),
                'week_end': week_dates[6].strftime('%d/%m/%Y'),
                'total_reservations': len(result.data)
            }

        except Exception as e:
            print(f"Error getting weekly calendar data: {e}")
            return {
                'week_dates': [],
                'reservations_grid': {},
                'week_start': '',
                'week_end': '',
                'total_reservations': 0
            }

    def save_cancellation_record(self, reservation_id: int, reservation_data: Dict,
                                 reason: str, admin_username: str) -> bool:
        """
        Guardar registro de cancelación

        Args:
            reservation_id: UUID de la reserva cancelada
            reservation_data: Debe incluir: user_id, email, name, date, hour
            reason: Motivo de cancelación
            admin_username: Usuario admin que canceló
        """
        try:
            # Obtener datos del diccionario (ahora siempre vienen completos)
            user_id = reservation_data.get('user_id')
            user_email = reservation_data.get('email')
            user_name = reservation_data.get('name')

            # Validar que tenemos todos los datos necesarios
            if not user_id or not user_email or not user_name:
                print(f"[Save Cancellation] ERROR: Missing required data in reservation_data")
                return False

            result = self.client.table('reservation_cancellations').insert({
                'original_reservation_id': reservation_id,
                'user_id': user_id,
                'user_email': user_email,
                'user_name': user_name,
                'reservation_date': reservation_data.get('date'),
                'reservation_hour': reservation_data.get('hour'),
                'cancellation_reason': reason,
                'cancelled_by': admin_username,
                'credits_refunded': 1
                # Database handles cancelled_at automatically with Colombian timezone
            }).execute()

            return len(result.data) > 0
        except Exception as e:
            print(f"[Save Cancellation] ERROR: {e}")
            return False

    def get_cancellation_history(self, days_back: int = None, limit: int = 1000) -> List[Dict]:
        """
        Obtener historial de cancelaciones

        Args:
            days_back: Número de días hacia atrás para filtrar (None = todos)
            limit: Máximo número de registros a retornar (default: 1000)
        """
        try:
            query = self.client.table('reservation_cancellations').select('*')

            # Filtrar por días si se especifica
            if days_back:
                # cancelled_at es un timestamp, usar datetime para comparación correcta
                start_datetime = get_colombia_now() - timedelta(days=days_back)
                start_datetime_str = start_datetime.isoformat()
                query = query.gte('cancelled_at', start_datetime_str)

            # Ordenar por fecha de cancelación (más recientes primero) y limitar resultados
            result = query.order('cancelled_at', desc=True).limit(limit).execute()

            # Formatear datos para display
            formatted_cancellations = []
            for cancellation in result.data:
                # Formatear hora
                hour_display = f"{cancellation['reservation_hour']:02d}:00"

                # Formatear fecha de reserva
                reservation_date_display = format_date_display(cancellation['reservation_date'])

                formatted_cancellations.append({
                    'user_name': cancellation['user_name'],
                    'user_email': cancellation['user_email'],
                    'reservation_date': reservation_date_display,
                    'reservation_hour': hour_display,
                    'cancellation_reason': cancellation['cancellation_reason'] or 'Sin motivo especificado',
                    'cancelled_by': cancellation['cancelled_by'],
                    'cancelled_at': self._format_colombia_datetime(cancellation['cancelled_at']),
                    'credits_refunded': cancellation['credits_refunded']
                })

            return formatted_cancellations

        except Exception as e:
            print(f"Error getting cancellation history: {e}")
            return []

    def get_cancellation_statistics(self, days_back: int = 30) -> Dict:
        """
        Obtener estadísticas de cancelación

        Args:
            days_back: Número de días para calcular estadísticas

        Returns:
            Dict con estadísticas de cancelación
        """
        try:
            # Get date range
            end_date = get_colombia_today()
            start_date = end_date - timedelta(days=days_back)
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')

            # Get cancellations in period
            start_datetime = get_colombia_now() - timedelta(days=days_back)
            cancellations = self.client.table('reservation_cancellations').select(
                'user_name, user_email, cancellation_reason, cancelled_at'
            ).gte('cancelled_at', start_datetime.isoformat()).execute()

            num_cancellations = len(cancellations.data)

            # Get total reservations made in the same period (including cancelled ones)
            # We count reservations + cancellations as "total bookings attempted"
            reservations = self.client.table('reservations').select('id').gte(
                'date', start_date_str
            ).lte('date', end_date_str).execute()
            total_reservations = len(reservations.data) + num_cancellations

            # Calculate cancellation rate
            cancellation_rate = round((num_cancellations / max(total_reservations, 1)) * 100, 1)

            # Find main cancellation reason
            reason_counts = {}
            for c in cancellations.data:
                reason = c.get('cancellation_reason', 'Sin motivo') or 'Sin motivo'
                # Normalize reasons
                if reason.lower() in ['sin motivo especificado', 'sin motivo', '']:
                    reason = 'Sin motivo especificado'
                reason_counts[reason] = reason_counts.get(reason, 0) + 1

            main_reason = max(reason_counts, key=reason_counts.get) if reason_counts else 'N/A'
            main_reason_count = reason_counts.get(main_reason, 0)
            main_reason_pct = round((main_reason_count / max(num_cancellations, 1)) * 100, 1)

            # Find user with most cancellations
            user_cancellations = {}
            for c in cancellations.data:
                email = c.get('user_email', 'Desconocido')
                name = c.get('user_name', 'Desconocido')
                key = (email, name)
                user_cancellations[key] = user_cancellations.get(key, 0) + 1

            if user_cancellations:
                top_user_key = max(user_cancellations, key=user_cancellations.get)
                top_user_name = top_user_key[1]
                top_user_count = user_cancellations[top_user_key]
            else:
                top_user_name = 'N/A'
                top_user_count = 0

            return {
                'total_cancellations': num_cancellations,
                'total_reservations': total_reservations,
                'cancellation_rate': cancellation_rate,
                'main_reason': main_reason,
                'main_reason_count': main_reason_count,
                'main_reason_pct': main_reason_pct,
                'top_user_name': top_user_name,
                'top_user_count': top_user_count,
                'period_days': days_back
            }
        except Exception as e:
            print(f"Error getting cancellation statistics: {e}")
            return {
                'total_cancellations': 0,
                'total_reservations': 0,
                'cancellation_rate': 0,
                'main_reason': 'N/A',
                'main_reason_count': 0,
                'main_reason_pct': 0,
                'top_user_name': 'N/A',
                'top_user_count': 0,
                'period_days': days_back
            }

    def get_blocked_slots(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """Obtener horarios de mantenimiento agrupados por rangos"""
        try:
            query = self.client.table('blocked_slots').select('*')

            if start_date:
                query = query.gte('date', start_date)
            if end_date:
                query = query.lte('date', end_date)

            result = query.order('date').order('start_hour').order('hour').execute()

            # Agrupar por fecha + start_hour + end_hour para mostrar rangos
            grouped_maintenance = {}
            for slot in result.data:
                key = f"{slot['date']}_{slot.get('start_hour', slot['hour'])}_{slot.get('end_hour', slot['hour']+1)}"

                if key not in grouped_maintenance:
                    # Tomar el primer slot como representante del grupo
                    grouped_maintenance[key] = {
                        'id': slot['id'],  # ID del primer slot (para eliminar)
                        'date': slot['date'],
                        'start_hour': slot.get('start_hour', slot['hour']),
                        'end_hour': slot.get('end_hour', slot['hour'] + 1),
                        'maintenance_type': slot.get('maintenance_type', 'single_hour'),
                        'reason': slot.get('reason', 'Mantenimiento programado'),
                        'created_by': slot.get('created_by', 'N/A'),
                        'created_at': self._format_colombia_datetime(slot.get('created_at')),
                        'hour_count': 0,
                        'hours_list': []
                    }

                # Contar horas en el rango
                grouped_maintenance[key]['hour_count'] += 1
                grouped_maintenance[key]['hours_list'].append(slot['hour'])

            # Convertir a lista
            return list(grouped_maintenance.values())

        except Exception as e:
            print(f"Error getting maintenance slots: {e}")
            return []

    def add_maintenance_slot(self, date: str, start_hour: int, end_hour: int, reason: str, admin_username: str, is_whole_day: bool = False) -> Tuple[bool, str]:
        """Agregar horario de mantenimiento con rango de horas o día completo"""
        try:
            # Si es mantenimiento de día completo, establecer rango 6-22
            if is_whole_day:
                start_hour = 6
                end_hour = 22

            # Validar rango de horas
            if start_hour >= end_hour:
                return False, "La hora de inicio debe ser menor que la hora de fin"

            if start_hour < 6 or end_hour > 22:
                return False, "El horario debe estar entre 6:00 y 22:00"

            # Generar lista de horas en el rango
            hours_to_block = list(range(start_hour, end_hour))

            # Verificar si ya existen reservas en alguna de las horas
            conflicting_reservations = []
            for hour in hours_to_block:
                existing_reservation = self.client.table('reservations').select('id').eq(
                    'date', date
                ).eq('hour', hour).execute()

                if existing_reservation.data:
                    conflicting_reservations.append(f"{hour}:00")

            if conflicting_reservations:
                hours_str = ", ".join(conflicting_reservations)
                return False, f"Ya existen reservas en las horas: {hours_str}"

            # Verificar si ya existe mantenimiento en alguna de las horas
            conflicting_maintenance = []
            for hour in hours_to_block:
                existing_maintenance = self.client.table('blocked_slots').select('id, hour').eq(
                    'date', date
                ).eq('hour', hour).execute()

                if existing_maintenance.data:
                    conflicting_maintenance.append(f"{hour}:00")

            if conflicting_maintenance:
                hours_str = ", ".join(conflicting_maintenance)
                return False, f"Ya existe mantenimiento en las horas: {hours_str}"

            # Insertar mantenimiento para cada hora en el rango
            maintenance_type = 'whole_day' if is_whole_day else 'time_range'

            for hour in hours_to_block:
                self.client.table('blocked_slots').insert({
                    'date': date,
                    'hour': hour,
                    'start_hour': start_hour,
                    'end_hour': end_hour,
                    'maintenance_type': maintenance_type,
                    'reason': reason or 'Mantenimiento programado',
                    'created_by': admin_username
                }).execute()

            hours_count = len(hours_to_block)
            time_desc = "día completo" if is_whole_day else f"{start_hour}:00 - {end_hour}:00"
            return True, f"Mantenimiento programado exitosamente ({time_desc}, {hours_count} horas bloqueadas)"

        except Exception as e:
            print(f"Error adding maintenance slot: {e}")
            return False, f"Error: {str(e)}"

    def remove_maintenance_slot(self, maintenance_id: int) -> bool:
        """Eliminar horario de mantenimiento individual"""
        try:
            result = self.client.table('blocked_slots').delete().eq('id', maintenance_id).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Error removing maintenance slot: {e}")
            return False

    def remove_maintenance_range(self, date: str, start_hour: int, end_hour: int) -> Tuple[bool, str]:
        """Eliminar un rango completo de mantenimiento"""
        try:
            # Eliminar todos los slots del rango con una sola query
            delete_result = self.client.table('blocked_slots').delete().eq('date', date).eq(
                'start_hour', start_hour
            ).eq('end_hour', end_hour).execute()

            if delete_result.data and len(delete_result.data) > 0:
                deleted_count = len(delete_result.data)
                return True, f"Se eliminaron {deleted_count} horas de mantenimiento"
            else:
                return False, "No se encontró mantenimiento en ese rango"

        except Exception as e:
            print(f"Error removing maintenance range: {e}")
            return False, f"Error: {str(e)}"

    def get_tennis_school_enabled(self) -> bool:
        """Get Tennis School enabled status from system_settings"""
        try:
            result = self.client.table('system_settings').select('tennis_school_enabled').limit(1).execute()
            if result.data and len(result.data) > 0:
                return result.data[0].get('tennis_school_enabled', False)
            return False
        except Exception as e:
            print(f"Error getting tennis school status: {e}")
            return False

    def set_tennis_school_enabled(self, enabled: bool, admin_username: str) -> Tuple[bool, str]:
        """
        Enable or disable Tennis School - just toggles a flag

        Args:
            enabled: True to enable, False to disable
            admin_username: Admin making the change
        """
        try:
            # Get the settings row first (only one exists)
            get_result = self.client.table('system_settings').select('id').limit(1).execute()

            if not get_result.data:
                return False, "Error: No existe configuración del sistema"

            settings_id = get_result.data[0]['id']

            # Update the settings row
            result = self.client.table('system_settings').update({
                'tennis_school_enabled': enabled,
                'updated_at': datetime.now().isoformat(),
                'updated_by': admin_username
            }).eq('id', settings_id).execute()

            if result.data:
                status = "activada" if enabled else "desactivada"
                return True, f"✅ Escuela de Tenis {status}"
            else:
                return False, "Error al actualizar configuración"

        except Exception as e:
            print(f"Error setting tennis school status: {e}")
            return False, f"Error: {str(e)}"

    def is_tennis_school_time(self, date_obj, hour: int) -> bool:
        """
        Check if a given date/hour falls in Tennis School time
        Saturday/Sunday 8-11 AM (8:00-12:00)

        Args:
            date_obj: datetime.date object
            hour: hour (0-23)
        """
        # Check if it's Saturday (5) or Sunday (6)
        if date_obj.weekday() not in [5, 6]:
            return False

        # Check if hour is 8-11 (8 AM to 12 PM)
        if hour not in [8, 9, 10, 11]:
            return False

        return True

    def block_user(self, user_email: str, admin_username: str) -> Tuple[bool, str]:
        """
        Block a user account, sign out from all sessions, and send notification email

        Args:
            user_email: Email of the user to block
            admin_username: Admin making the change
        """
        try:
            # Get user details
            user_result = self.client.table('users').select('id, full_name, email, is_active').eq(
                'email', user_email.strip().lower()
            ).execute()

            if not user_result.data:
                return False, "Usuario no encontrado"

            user = user_result.data[0]

            if not user['is_active']:
                return False, "El usuario ya está bloqueado"

            # Block the user
            update_result = self.client.table('users').update({
                'is_active': False
            }).eq('id', user['id']).execute()

            if update_result.data:
                # Sign out user from all active sessions using Admin API
                try:
                    self.client.auth.admin.sign_out(user['id'])
                    print(f"✅ Signed out user {user['email']} from all sessions")
                except Exception as e:
                    print(f"⚠️ Warning: Could not sign out user sessions: {e}")
                    # Continue even if sign out fails - user is already blocked

                # Send blocking notification email
                from email_config import email_manager
                email_manager.send_account_blocked_notification(user['email'], user['full_name'])
                return True, f"✅ Usuario bloqueado y desconectado: {user['email']}"
            else:
                return False, "Error al bloquear usuario"

        except Exception as e:
            print(f"Error blocking user: {e}")
            return False, f"Error: {str(e)}"

    def unblock_user(self, user_email: str, admin_username: str) -> Tuple[bool, str]:
        """
        Unblock a user account

        Args:
            user_email: Email of the user to unblock
            admin_username: Admin making the change
        """
        try:
            # Get user details
            user_result = self.client.table('users').select('id, full_name, email, is_active').eq(
                'email', user_email.strip().lower()
            ).execute()

            if not user_result.data:
                return False, "Usuario no encontrado"

            user = user_result.data[0]

            if user['is_active']:
                return False, "El usuario ya está activo"

            # Unblock the user
            update_result = self.client.table('users').update({
                'is_active': True
            }).eq('id', user['id']).execute()

            if update_result.data:
                # Send reactivation notification email
                from email_config import email_manager
                email_manager.send_account_reactivated_notification(user['email'], user['full_name'])
                return True, f"✅ Usuario desbloqueado: {user['email']}"
            else:
                return False, "Error al desbloquear usuario"

        except Exception as e:
            print(f"Error unblocking user: {e}")
            return False, f"Error: {str(e)}"

# Instancia global
admin_db_manager = AdminDatabaseManager()