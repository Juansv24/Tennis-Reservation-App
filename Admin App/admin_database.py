"""
Gestor de Base de Datos para Funciones de Administración
VERSIÓN ACTUALIZADA con formateo de fechas y horas en zona horaria de Colombia
"""

from database_manager import db_manager
from timezone_utils import get_colombia_today, COLOMBIA_TZ
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
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

    def sync_database(self) -> Dict[str, any]:
        """Sincronizar y limpiar base de datos"""
        try:
            results = {
                'expired_tokens_cleaned': 0,
                'expired_verifications_cleaned': 0,
                'success': True,
                'message': 'Base de datos sincronizada exitosamente'
            }

            now = datetime.utcnow().isoformat()

            # 1. Limpiar tokens de reset expirados
            try:
                expired_tokens = self.client.table('password_reset_tokens').delete().lt('expires_at', now).execute()
                results['expired_tokens_cleaned'] = len(expired_tokens.data) if expired_tokens.data else 0
            except Exception:
                pass  # Table may not exist

            # 2. Limpiar verificaciones de email expiradas (new table name)
            try:
                expired_verifications = self.client.table('email_verification_tokens').delete().lt('expires_at', now).execute()
                results['expired_verifications_cleaned'] = len(
                    expired_verifications.data) if expired_verifications.data else 0
            except Exception:
                pass  # Table may not exist

            return results

        except Exception as e:
            return {
                'success': False,
                'message': f'Error sincronizando base de datos: {str(e)}',
                'expired_tokens_cleaned': 0,
                'expired_verifications_cleaned': 0
            }

    def get_system_statistics(self) -> Dict:
        """Obtener estadísticas generales del sistema"""
        try:
            # Usuarios totales - all users in table are active
            users_result = self.client.table('users').select('id, is_vip, credits').execute()
            total_users = len(users_result.data)
            vip_users = len([u for u in users_result.data if u.get('is_vip', False)])

            # Reservas de hoy
            today = get_colombia_today().strftime('%Y-%m-%d')
            reservations_today = self.client.table('reservations').select('id').eq('date', today).execute()

            # Créditos totales emitidos
            try:
                credits_result = self.client.table('credit_transactions').select('amount').eq('transaction_type', 'admin_grant').execute()
                total_credits_issued = sum([t['amount'] for t in credits_result.data]) if credits_result.data else 0
            except Exception:
                total_credits_issued = 0  # Table may not exist yet

            return {
                'total_users': total_users,
                'vip_users': vip_users,
                'today_reservations': len(reservations_today.data),
                'total_credits_issued': total_credits_issued
            }
        except Exception as e:
            print(f"Error getting system statistics: {e}")
            return {
                'total_users': 0,
                'vip_users': 0,
                'today_reservations': 0,
                'total_credits_issued': 0
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

    def search_users_for_reservations(self, search_term: str) -> List[Dict]:
        """Buscar usuarios por nombre o email para gestión de reservas"""
        try:
            # Buscar por email o nombre
            result = self.client.table('users').select('id, email, full_name').or_(
                f'email.ilike.%{search_term}%,full_name.ilike.%{search_term}%'
            ).execute()

            return [{'id': u['id'], 'email': u['email'], 'name': u['full_name']} for u in result.data]
        except Exception:
            return []

    def get_user_reservations_history(self, user_email: str) -> List[Dict]:
        """Obtener historial completo de reservas de un usuario - Now uses user_id"""
        try:
            # Get user_id from email
            user_result = self.client.table('users').select('id').eq('email', user_email).execute()
            if not user_result.data:
                return []

            user_id = user_result.data[0]['id']

            result = self.client.table('reservations').select('*').eq(
                'user_id', user_id
            ).order('date', desc=True).order('hour').execute()

            # Formatear fechas de creación
            for reservation in result.data:
                if 'created_at' in reservation:
                    reservation['created_at'] = self._format_colombia_datetime(reservation['created_at'])

            return result.data
        except Exception:
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
        """Cancelar reserva, enviar notificación y guardar historial"""
        try:
            # Obtener datos de la reserva ANTES de cancelar
            reservation_result = self.client.table('reservations').select('*').eq('id', reservation_id).execute()
            if not reservation_result.data:
                return False

            reservation = reservation_result.data[0]

            # Cancelar reserva (reutilizar función existente)
            success = self.cancel_reservation(reservation_id)

            if success:
                # Guardar en historial de cancelaciones
                self.save_cancellation_record(
                    reservation_id,
                    reservation,
                    cancellation_reason or "Sin motivo especificado",
                    admin_username
                )

                # Enviar email de notificación con motivo
                self._send_cancellation_notification(user_email, reservation, cancellation_reason)

            return success
        except Exception as e:
            print(f"Error in cancel_reservation_with_notification: {e}")
            return False

    def _send_cancellation_notification(self, user_email: str, reservation: Dict, reason: str = ""):
        """Enviar notificación de cancelación con motivo"""
        try:
            from email_config import email_manager

            if email_manager.is_configured():
                # Get user's full name
                user_result = self.client.table('users').select('full_name').eq(
                    'email', user_email.strip().lower()
                ).execute()

                user_name = user_result.data[0]['full_name'] if user_result.data else 'Usuario'

                # Send cancellation email using the new template with reason
                email_manager.send_reservation_cancelled_notification(
                    user_email=user_email,
                    user_name=user_name,
                    date=reservation['date'],
                    hour=reservation['hour'],
                    cancelled_by='admin',  # Admin cancelled
                    reason=reason  # Include the cancellation reason
                )
        except Exception as e:
            print(f"Error sending cancellation email: {e}")

    def search_users_detailed(self, search_term: str) -> List[Dict]:
        """Búsqueda detallada de usuarios"""
        try:
            result = self.client.table('users').select('*').or_(
                f'email.ilike.%{search_term}%,full_name.ilike.%{search_term}%'
            ).execute()

            # Formatear fechas para cada usuario
            for user in result.data:
                if 'created_at' in user:
                    user['created_at'] = self._format_colombia_datetime(user['created_at'])

            return result.data
        except Exception:
            return []

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
            result = self.client.table('reservations').select('user_id, users(email, full_name)').execute()

            # Contar reservas por usuario
            user_counts = {}
            for reservation in result.data:
                if not reservation.get('users'):
                    continue

                user_id = reservation['user_id']
                email = reservation['users']['email']
                name = reservation['users']['full_name']

                if user_id in user_counts:
                    user_counts[user_id]['count'] += 1
                else:
                    user_counts[user_id] = {'email': email, 'name': name, 'count': 1}

            # Convertir a lista y ordenar
            user_stats = [
                {'email': data['email'], 'name': data['name'], 'reservations': data['count']}
                for user_id, data in user_counts.items()
            ]

            return sorted(user_stats, key=lambda x: x['reservations'], reverse=True)[:10]
        except Exception as e:
            print(f"Error getting user reservation statistics: {e}")
            return []

    def get_daily_reservation_stats(self, days: int = 7) -> List[Dict]:
        """Obtener estadísticas de reservas por día"""
        try:
            start_date = (get_colombia_today() - timedelta(days=days)).strftime('%Y-%m-%d')

            result = self.client.rpc('get_daily_reservation_stats', {
                'start_date': start_date
            }).execute()

            return result.data if result.data else []
        except Exception:
            # Fallback query si la función RPC no existe
            try:
                result = self.client.table('reservations').select('date').gte('date', start_date).execute()
                # Agrupar por fecha manualmente
                date_counts = {}
                for reservation in result.data:
                    date = reservation['date']
                    date_counts[date] = date_counts.get(date, 0) + 1

                return [{'date': date, 'count': count} for date, count in date_counts.items()]
            except Exception:
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

    def get_reservations_for_admin(self, date_filter, status_filter: str) -> List:
        """Obtener reservas para gestión administrativa - Now uses JOIN"""
        try:
            query = self.client.table('reservations').select('id, date, hour, user_id, created_at, users(full_name, email)')

            # Aplicar filtro de fecha si se especifica
            if date_filter:
                query = query.eq('date', date_filter.strftime('%Y-%m-%d'))

            result = query.order('date', desc=True).order('hour').execute()

            # Formatear datos para mantener compatibilidad con código existente
            formatted_data = []
            for reservation in result.data:
                if reservation.get('users'):
                    formatted_reservation = {
                        'id': reservation['id'],
                        'date': reservation['date'],
                        'hour': reservation['hour'],
                        'user_id': reservation['user_id'],
                        'name': reservation['users']['full_name'],
                        'email': reservation['users']['email'],
                        'created_at': self._format_colombia_datetime(reservation['created_at']) if reservation.get('created_at') else 'N/A'
                    }
                    formatted_data.append(formatted_reservation)

            return formatted_data
        except Exception as e:
            print(f"Error getting reservations for admin: {e}")
            return []

    def cancel_reservation(self, reservation_id: int) -> bool:
        """Cancelar una reserva específica - Now uses user_id"""
        try:
            # Obtener datos de la reserva antes de cancelar (now uses user_id)
            reservation_result = self.client.table('reservations').select('user_id, date, hour').eq('id',
                                                                                                  reservation_id).execute()

            if not reservation_result.data:
                return False

            reservation = reservation_result.data[0]
            user_id = reservation['user_id']

            # Eliminar la reserva
            delete_result = self.client.table('reservations').delete().eq('id', reservation_id).execute()

            if delete_result.data:
                # Obtener usuario para reembolso
                user_result = self.client.table('users').select('id, credits').eq('id', user_id).execute()
                if user_result.data:
                    user = user_result.data[0]
                    current_credits = user['credits'] or 0
                    new_credits = current_credits + 1

                    # Actualizar créditos directamente (sin RPC)
                    self.client.table('users').update({
                        'credits': new_credits
                    }).eq('id', user['id']).execute()

                    # Registrar transacción de reembolso
                    self.client.table('credit_transactions').insert({
                        'user_id': user['id'],
                        'amount': 1,
                        'transaction_type': 'reservation_refund',
                        'description': f'Reembolso por cancelación admin - {reservation["date"]} {reservation["hour"]}:00',
                        'admin_user': 'admin'
                    }).execute()

                return True
            return False
        except Exception as e:
            print(f"Error canceling reservation: {e}")
            return False

    def get_all_users(self) -> List:
        """Obtener todos los usuarios del sistema"""
        try:
            result = self.client.table('users').select(
                'id, email, full_name, credits, is_vip, first_login_completed, created_at'
            ).order('created_at', desc=True).execute()

            # Formatear fechas para cada usuario
            for user in result.data:
                if 'created_at' in user:
                    user['created_at'] = self._format_colombia_datetime(user['created_at'])

            return result.data
        except Exception:
            return []

    def toggle_vip_status(self, user_id: int) -> bool:
        """Alternar estado VIP de usuario (replaces toggle_user_status)"""
        try:
            # Obtener estado actual
            user_result = self.client.table('users').select('is_vip').eq('id', user_id).execute()
            if not user_result.data:
                return False

            current_status = user_result.data[0].get('is_vip', False)
            new_status = not current_status

            # Actualizar estado VIP
            update_result = self.client.table('users').update({
                'is_vip': new_status
            }).eq('id', user_id).execute()

            return len(update_result.data) > 0
        except Exception:
            return False

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

    def get_credit_transactions(self, limit: int = 50) -> List:
        """Obtener historial de transacciones de créditos"""
        try:
            result = self.client.table('credit_transactions').select(
                'users(full_name), amount, transaction_type, description, admin_user, created_at'
            ).order('created_at', desc=True).limit(limit).execute()

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

    def get_user_reservation_history(self, user_id: int) -> List:
        """Obtener historial de reservas de un usuario - Now uses user_id"""
        try:
            result = self.client.table('reservations').select(
                'date, hour, created_at'
            ).eq('user_id', user_id).order('date', desc=True).execute()

            # Formatear fechas de creación
            for reservation in result.data:
                if 'created_at' in reservation:
                    reservation['created_at'] = self._format_colombia_datetime(reservation['created_at'])

            return result.data
        except Exception:
            return []

    def get_user_recent_reservations(self, user_email: str, limit: int = 10) -> List[Dict]:
        """Obtener reservas recientes de un usuario - Now uses user_id"""
        try:
            # Get user_id from email
            user_result = self.client.table('users').select('id').eq('email', user_email).execute()
            if not user_result.data:
                return []

            user_id = user_result.data[0]['id']

            result = self.client.table('reservations').select(
                'date, hour, created_at'
            ).eq('user_id', user_id).order('date', desc=True).limit(limit).execute()

            # Formatear fechas de creación
            for reservation in result.data:
                if 'created_at' in reservation:
                    reservation['created_at'] = self._format_colombia_datetime(reservation['created_at'])

            return result.data
        except Exception as e:
            print(f"Error getting user recent reservations: {e}")
            return []

    def use_credit_for_reservation(self, user_email: str, date: str, hour: int) -> bool:
        """Usar un crédito para una reserva (será llamado desde el sistema de reservas)"""
        try:
            # Obtener usuario
            user_result = self.client.table('users').select('id, credits').eq('email', user_email).execute()
            if not user_result.data:
                return False

            user = user_result.data[0]
            if (user['credits'] or 0) < 1:
                return False

            # Descontar crédito
            new_credits = (user['credits'] or 0) - 1
            update_result = self.client.table('users').update({
                'credits': new_credits
            }).eq('id', user['id']).execute()

            if update_result.data:
                # Registrar transacción
                self.client.table('credit_transactions').insert({
                    'user_id': user['id'],
                    'amount': -1,
                    'transaction_type': 'reservation_use',
                    'description': f'Uso de crédito para reserva - {date} {hour}:00'
                }).execute()

                return True
            return False
        except Exception as e:
            print(f"Error using credit: {e}")
            return False

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Obtener información básica de usuario por email"""
        try:
            result = self.client.table('users').select('id, email, full_name, credits').eq(
                'email', email.strip().lower()
            ).execute()

            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None

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
                    'Estado VIP': 'Sí' if user.get('is_vip', False) else 'No',
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
                'code': new_code,
                'admin_user': admin_username  # Audit trail - not a timestamp
            }).execute()

            # Verificar que se insertó correctamente
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

    def verify_access_code(self, code: str) -> bool:
        """Verificar código de acceso"""
        try:
            current_code = self.get_current_access_code()
            return current_code == code.strip().upper() if current_code else False
        except Exception:
            return False

    def mark_user_first_login_complete(self, user_id: int) -> bool:
        """Marcar que el usuario completó su primer login"""
        try:
            result = self.client.table('users').update({
                'first_login_completed': True
            }).eq('id', user_id).execute()
            return len(result.data) > 0
        except Exception:
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

    def get_user_activity_stats(self, days: int = 30) -> List[Dict]:
        """Obtener estadísticas de actividad de usuarios - Uses JOIN"""
        try:
            start_date = (get_colombia_today() - timedelta(days=days)).strftime('%Y-%m-%d')

            # Obtener reservas recientes con JOIN a users
            result = self.client.table('reservations').select('user_id, date, created_at, users(email, full_name)').gte(
                'date', start_date
            ).execute()

            # Obtener datos de usuarios
            users_result = self.client.table('users').select('id, email, full_name, created_at').execute()
            users_dict = {u['id']: u for u in users_result.data}

            # Agrupar actividad por usuario
            user_activity = {}
            for reservation in result.data:
                if not reservation.get('users'):
                    continue

                user_id = reservation['user_id']
                email = reservation['users']['email']

                if user_id not in user_activity:
                    user_info = users_dict.get(user_id, {})
                    user_activity[user_id] = {
                        'name': reservation['users']['full_name'],
                        'email': email,
                        'recent_reservations': 0,
                        'last_reservation': None,
                        'member_since': self._format_colombia_datetime(user_info.get('created_at'))
                    }

                user_activity[user_id]['recent_reservations'] += 1

                # Actualizar última reserva
                if (not user_activity[user_id]['last_reservation'] or
                        reservation['date'] > user_activity[user_id]['last_reservation']):
                    user_activity[user_id]['last_reservation'] = reservation['date']

            # Convertir a lista ordenada por actividad
            return sorted(user_activity.values(),
                          key=lambda x: x['recent_reservations'], reverse=True)[:20]

        except Exception as e:
            print(f"Error getting user activity stats: {e}")
            return []

    def save_cancellation_record(self, reservation_id: int, reservation_data: Dict,
                                 reason: str, admin_username: str) -> bool:
        """Guardar registro de cancelación - Now includes user_id"""
        try:
            # Get user info from reservation_data
            user_id = reservation_data.get('user_id')

            # If we don't have user info in reservation_data, fetch from users table
            if not reservation_data.get('email') or not reservation_data.get('name'):
                if user_id:
                    user_result = self.client.table('users').select('email, full_name').eq('id', user_id).execute()
                    if user_result.data:
                        user_email = user_result.data[0]['email']
                        user_name = user_result.data[0]['full_name']
                    else:
                        user_email = 'Unknown'
                        user_name = 'Unknown'
                else:
                    user_email = 'Unknown'
                    user_name = 'Unknown'
            else:
                user_email = reservation_data.get('email')
                user_name = reservation_data.get('name')

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
            print(f"Error saving cancellation record: {e}")
            return False

    def get_cancellation_history(self, days_back: int = None) -> List[Dict]:
        """Obtener historial de cancelaciones"""
        try:
            query = self.client.table('reservation_cancellations').select('*')

            # Filtrar por días si se especifica
            if days_back:
                start_date = (get_colombia_today() - timedelta(days=days_back)).strftime('%Y-%m-%d')
                query = query.gte('cancelled_at', start_date)

            result = query.order('cancelled_at', desc=True).execute()

            # Formatear datos para display
            formatted_cancellations = []
            for cancellation in result.data:
                # Formatear hora
                hour_display = f"{cancellation['reservation_hour']:02d}:00"

                # Formatear fecha de reserva
                from timezone_utils import format_date_display
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

    def get_maintenance_for_date(self, date: str) -> List[int]:
        """Obtener horas de mantenimiento para una fecha específica"""
        try:
            result = self.client.table('blocked_slots').select('hour').eq('date', date).execute()
            return [row['hour'] for row in result.data]
        except Exception:
            return []

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