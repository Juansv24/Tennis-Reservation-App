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
                'expired_sessions_cleaned': 0,
                'expired_tokens_cleaned': 0,
                'expired_verifications_cleaned': 0,
                'orphaned_records_cleaned': 0,
                'success': True,
                'message': 'Base de datos sincronizada exitosamente'
            }

            import datetime
            now = datetime.datetime.utcnow().isoformat()

            # 1. Limpiar sesiones expiradas
            expired_sessions = self.client.table('user_sessions').delete().lt('expires_at', now).execute()
            results['expired_sessions_cleaned'] = len(expired_sessions.data) if expired_sessions.data else 0

            # 2. Limpiar tokens de reset expirados
            expired_tokens = self.client.table('password_reset_tokens').delete().lt('expires_at', now).execute()
            results['expired_tokens_cleaned'] = len(expired_tokens.data) if expired_tokens.data else 0

            # 3. Limpiar verificaciones de email expiradas
            expired_verifications = self.client.table('email_verifications').delete().lt('expires_at', now).execute()
            results['expired_verifications_cleaned'] = len(
                expired_verifications.data) if expired_verifications.data else 0

            # 4. Marcar sesiones expiradas como inactivas (por si las anteriores fallan)
            self.client.table('user_sessions').update({
                'is_active': False
            }).lt('expires_at', now).eq('is_active', True).execute()

            return results

        except Exception as e:
            return {
                'success': False,
                'message': f'Error sincronizando base de datos: {str(e)}',
                'expired_sessions_cleaned': 0,
                'expired_tokens_cleaned': 0,
                'expired_verifications_cleaned': 0,
                'orphaned_records_cleaned': 0
            }

    def get_system_statistics(self) -> Dict:
        """Obtener estadísticas generales del sistema"""
        try:
            # Usuarios totales
            users_result = self.client.table('users').select('id, is_active, credits').execute()
            total_users = len(users_result.data)
            active_users = len([u for u in users_result.data if u['is_active']])

            # Reservas de hoy
            today = get_colombia_today().strftime('%Y-%m-%d')
            reservations_today = self.client.table('reservations').select('id').eq('date', today).execute()

            # Créditos totales emitidos
            credits_result = self.client.table('credit_transactions').select('amount').eq('transaction_type', 'admin_grant').execute()
            total_credits_issued = sum([t['amount'] for t in credits_result.data]) if credits_result.data else 0

            return {
                'total_users': total_users,
                'active_users': active_users,
                'today_reservations': len(reservations_today.data),
                'total_credits_issued': total_credits_issued
            }
        except Exception as e:
            print(f"Error getting system statistics: {e}")
            return {
                'total_users': 0,
                'active_users': 0,
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
            ).eq('is_active', True).execute()

            return [{'id': u['id'], 'email': u['email'], 'name': u['full_name']} for u in result.data]
        except Exception:
            return []

    def get_user_reservations_history(self, user_email: str) -> List[Dict]:
        """Obtener historial completo de reservas de un usuario"""
        try:
            result = self.client.table('reservations').select('*').eq(
                'email', user_email
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
        try:
            # Get all users with their IDs
            users_result = self.client.table('users').select('id, email, full_name, created_at, credits').execute()

            # Create a dictionary to map user_id to email
            user_id_to_email = {user['id']: user['email'] for user in users_result.data}
            user_id_to_data = {user['id']: user for user in users_result.data}

            # Get all reservations
            reservations_result = self.client.table('reservations').select('email, date, hour').execute()

            # Get all credit transactions using user_id
            credits_transactions = self.client.table('credit_transactions').select(
                'user_id, amount, transaction_type').execute()

            # Calculate total credits bought per user (by user_id first, then convert to email)
            credits_by_user_id = {}
            for transaction in credits_transactions.data:
                user_id = transaction['user_id']
                # Only count purchases (admin_grant, purchase, etc.)
                if transaction['transaction_type'] in ['admin_grant', 'purchase', 'bonus']:
                    if user_id not in credits_by_user_id:
                        credits_by_user_id[user_id] = 0
                    credits_by_user_id[user_id] += transaction['amount']

            # Convert to email-based dictionary
            credits_dict = {}
            for user_id, total_credits in credits_by_user_id.items():
                if user_id in user_id_to_email:
                    email = user_id_to_email[user_id]
                    credits_dict[email] = total_credits

            # Process reservations by user
            user_reservations = {}
            for res in reservations_result.data:
                email = res['email']
                if email not in user_reservations:
                    user_reservations[email] = {
                        'total': 0,
                        'days': [],
                        'hours': []
                    }
                user_reservations[email]['total'] += 1

                # Add day of week
                date_obj = datetime.strptime(res['date'], '%Y-%m-%d').date()
                user_reservations[email]['days'].append(date_obj.weekday())

                # Add hour
                user_reservations[email]['hours'].append(res['hour'])

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
            print(f"Error getting detailed user statistics: {e}")
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
                subject = "🎾 Reserva Cancelada - Sistema de Reservas"

                reason_section = ""
                if reason and reason != "Sin motivo especificado":
                    reason_section = f"""
                    <div style="background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 15px; margin: 15px 0;">
                        <h4 style="margin: 0; color: #856404;">📋 Motivo de la cancelación:</h4>
                        <p style="margin: 10px 0 0 0; color: #856404;">{reason}</p>
                    </div>
                    """

                html_body = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: linear-gradient(135deg, #001854 0%, #2478CC 100%); color: white; padding: 20px; text-align: center; border-radius: 10px;">
                        <h1>🎾 Reserva Cancelada</h1>
                    </div>

                    <div style="background: #f9f9f9; padding: 20px; border-radius: 10px; margin: 20px 0;">
                        <h2>Tu reserva ha sido cancelada</h2>
                        <p>Lamentamos informarte que tu reserva ha sido <strong>cancelada por el administrador</strong>:</p>

                        <div style="background: white; padding: 15px; border-radius: 8px; border-left: 5px solid #FFD400;">
                            <p><strong>📅 Fecha:</strong> {reservation['date']}</p>
                            <p><strong>🕐 Hora:</strong> {reservation['hour']}:00</p>
                        </div>

                        {reason_section}

                        <p>✅ <strong>Se ha reembolsado 1 crédito</strong> a tu cuenta automáticamente.</p>
                        <p>Si tienes preguntas, contacta al administrador.</p>
                    </div>
                </div>
                """

                email_manager.send_email(user_email, subject, html_body)
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
                if 'last_login' in user:
                    user['last_login'] = self._format_colombia_datetime(user['last_login'])
                if 'created_at' in user:
                    user['created_at'] = self._format_colombia_datetime(user['created_at'])

            return result.data
        except Exception:
            return []

    def get_user_stats(self, user_id: int) -> Dict:
        """Obtener estadísticas de un usuario específico"""
        try:
            user_result = self.client.table('users').select('email').eq('id', user_id).execute()
            if not user_result.data:
                return {'total_reservations': 0, 'active_reservations': 0, 'last_reservation': None}

            email = user_result.data[0]['email']

            # Total de reservas
            total_result = self.client.table('reservations').select('id').eq('email', email).execute()
            total_reservations = len(total_result.data)

            # Reservas futuras
            today = get_colombia_today().strftime('%Y-%m-%d')
            future_result = self.client.table('reservations').select('id').eq('email', email).gte('date',
                                                                                                  today).execute()
            active_reservations = len(future_result.data)

            # Última reserva
            last_result = self.client.table('reservations').select('date').eq('email', email).order('date',
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

    def toggle_user_status_with_notification(self, user_id: int) -> bool:
        """Cambiar estado de usuario y notificar"""
        try:
            # Obtener info del usuario
            user_result = self.client.table('users').select('email, full_name, is_active').eq('id', user_id).execute()
            if not user_result.data:
                return False

            user = user_result.data[0]
            success = self.toggle_user_status(user_id)

            if success:
                # Enviar notificación
                new_status = "activada" if not user['is_active'] else "desactivada"
                self._send_status_change_notification(user['email'], user['full_name'], new_status)

            return success
        except Exception:
            return False

    def _send_status_change_notification(self, email: str, name: str, status: str):
        """Enviar notificación de cambio de estado"""
        try:
            from email_config import email_manager

            if email_manager.is_configured():
                subject = f"🎾 Cuenta {status.title()} - Sistema de Reservas"

                html_body = f"""
                <h2>Estado de Cuenta Actualizado</h2>
                <p>Hola {name},</p>
                <p>Tu cuenta ha sido <strong>{status}</strong> por el administrador.</p>
                <p>Si tienes preguntas, contacta al administrador.</p>
                """

                email_manager.send_email(email, subject, html_body)
        except Exception as e:
            print(f"Error sending status change email: {e}")

    def get_user_reservation_statistics(self) -> List[Dict]:
        """Obtener estadísticas de reservas por usuario"""
        try:
            result = self.client.table('reservations').select('email, name').execute()

            # Contar reservas por usuario
            user_counts = {}
            for reservation in result.data:
                email = reservation['email']
                name = reservation['name']
                if email in user_counts:
                    user_counts[email]['count'] += 1
                else:
                    user_counts[email] = {'name': name, 'count': 1}

            # Convertir a lista y ordenar
            user_stats = [
                {'email': email, 'name': data['name'], 'reservations': data['count']}
                for email, data in user_counts.items()
            ]

            return sorted(user_stats, key=lambda x: x['reservations'], reverse=True)[:10]
        except Exception:
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
        """Obtener reservas para gestión administrativa"""
        try:
            query = self.client.table('reservations').select('id, date, hour, name, email, created_at')

            # Aplicar filtro de fecha si se especifica
            if date_filter:
                query = query.eq('date', date_filter.strftime('%Y-%m-%d'))

            result = query.order('date', desc=True).order('hour').execute()

            # Formatear fechas de creación
            for reservation in result.data:
                if 'created_at' in reservation:
                    reservation['created_at'] = self._format_colombia_datetime(reservation['created_at'])

            return result.data
        except Exception:
            return []

    def cancel_reservation(self, reservation_id: int) -> bool:
        """Cancelar una reserva específica"""
        try:
            # Obtener datos de la reserva antes de cancelar
            reservation_result = self.client.table('reservations').select('email, date, hour').eq('id',
                                                                                                  reservation_id).execute()

            if not reservation_result.data:
                return False

            reservation = reservation_result.data[0]

            # Eliminar la reserva
            delete_result = self.client.table('reservations').delete().eq('id', reservation_id).execute()

            if delete_result.data:
                # Obtener usuario para reembolso
                user_result = self.client.table('users').select('id, credits').eq('email',
                                                                                  reservation['email']).execute()
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
                        'admin_user': 'admin',
                        'created_at': datetime.now().isoformat()
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
                'id, email, full_name, credits, is_active, last_login, created_at'
            ).order('created_at', desc=True).execute()

            # Formatear fechas para cada usuario
            for user in result.data:
                if 'last_login' in user:
                    user['last_login'] = self._format_colombia_datetime(user['last_login'])
                if 'created_at' in user:
                    user['created_at'] = self._format_colombia_datetime(user['created_at'])

            return result.data
        except Exception:
            return []

    def toggle_user_status(self, user_id: int) -> bool:
        """Alternar estado activo/inactivo de usuario"""
        try:
            # Obtener estado actual
            user_result = self.client.table('users').select('is_active').eq('id', user_id).execute()
            if not user_result.data:
                return False

            current_status = user_result.data[0]['is_active']
            new_status = not current_status

            # Actualizar estado
            update_result = self.client.table('users').update({
                'is_active': new_status
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
                    'admin_user': admin_username,
                    'created_at': datetime.now().isoformat()
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
                    'admin_user': admin_username,
                    'created_at': datetime.now().isoformat()
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
        """Obtener historial de reservas de un usuario"""
        try:
            user_result = self.client.table('users').select('email').eq('id', user_id).execute()
            if not user_result.data:
                return []

            email = user_result.data[0]['email']

            result = self.client.table('reservations').select(
                'date, hour, created_at'
            ).eq('email', email).order('date', desc=True).execute()

            # Formatear fechas de creación
            for reservation in result.data:
                if 'created_at' in reservation:
                    reservation['created_at'] = self._format_colombia_datetime(reservation['created_at'])

            return result.data
        except Exception:
            return []

    def get_user_recent_reservations(self, user_email: str, limit: int = 10) -> List[Dict]:
        """Obtener reservas recientes de un usuario"""
        try:
            result = self.client.table('reservations').select(
                'date, hour, created_at'
            ).eq('email', user_email).order('date', desc=True).limit(limit).execute()

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
                    'description': f'Uso de crédito para reserva - {date} {hour}:00',
                    'created_at': datetime.now().isoformat()
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
                'id, email, full_name, credits, is_active, last_login, created_at'
            ).order('created_at', desc=True).execute()

            # Formatear datos para Excel
            formatted_users = []
            for user in result.data:
                formatted_users.append({
                    'ID': user['id'],
                    'Nombre Completo': user['full_name'],
                    'Email': user['email'],
                    'Créditos': user['credits'] or 0,
                    'Estado': 'Activo' if user['is_active'] else 'Inactivo',
                    'Último Login': self._format_colombia_datetime(user['last_login']),  # FORMATEADO A COLOMBIA
                    'Fecha Registro': self._format_colombia_datetime(user['created_at'])  # FORMATEADO A COLOMBIA
                })

            return formatted_users
        except Exception as e:
            print(f"Error getting users for export: {e}")
            return []

    def get_all_reservations_for_export(self) -> List[Dict]:
        """Obtener todas las reservas para exportación"""
        try:
            result = self.client.table('reservations').select(
                'id, date, hour, name, email, created_at'
            ).order('date', desc=True).order('hour').execute()

            # Formatear datos para Excel
            formatted_reservations = []
            for reservation in result.data:
                # Formatear fecha más legible
                try:
                    from datetime import datetime
                    fecha_obj = datetime.strptime(reservation['date'], '%Y-%m-%d')
                    fecha_formateada = fecha_obj.strftime('%d/%m/%Y')
                    dia_semana = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'][fecha_obj.weekday()]
                    fecha_display = f"{dia_semana} {fecha_formateada}"
                except:
                    fecha_display = reservation['date']

                formatted_reservations.append({
                    'ID Reserva': reservation['id'],
                    'Fecha': fecha_display,
                    'Hora': f"{reservation['hour']}:00 - {reservation['hour'] + 1}:00",
                    'Nombre Usuario': reservation['name'],
                    'Email Usuario': reservation['email'],
                    'Fecha Creación': self._format_colombia_datetime(reservation['created_at'])  # FORMATEADO A COLOMBIA
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
            ).eq('is_active', True).order('full_name').execute()

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

    def update_lock_code(self, new_code: str, admin_username: str) -> bool:
        """Actualizar contraseña del candado"""
        try:
            from datetime import datetime

            # Insertar nueva contraseña (mantiene historial)
            result = self.client.table('lock_code').insert({
                'code': new_code,
                'admin_user': admin_username,
                'created_at': datetime.now().isoformat()
            }).execute()

            # Verificar que se insertó correctamente
            if result.data and len(result.data) > 0:
                print(f"Lock code updated successfully: {new_code}")
                return True
            else:
                print("Failed to insert lock code")
                return False

        except Exception as e:
            print(f"Error updating lock code: {e}")
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
            from datetime import datetime

            result = self.client.table('access_codes').insert({
                'code': new_code,
                'admin_user': admin_username,
                'created_at': datetime.now().isoformat()
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
            from datetime import datetime, timedelta

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

            # Obtener reservas de la semana
            result = self.client.table('reservations').select('date, hour, name, email').gte(
                'date', start_date
            ).lte('date', end_date).execute()

            # Organizar datos por fecha y hora
            reservations_grid = {}
            for date in week_dates:
                date_str = date.strftime('%Y-%m-%d')
                reservations_grid[date_str] = {}

            # Llenar el grid con las reservas
            for reservation in result.data:
                date_str = reservation['date']
                hour = reservation['hour']
                name = reservation['name']

                if date_str in reservations_grid:
                    reservations_grid[date_str][hour] = {
                        'name': name,
                        'email': reservation['email']
                    }

            return {
                'week_dates': week_dates,
                'reservations_grid': reservations_grid,
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
        """Obtener estadísticas de actividad de usuarios"""
        try:
            start_date = (get_colombia_today() - timedelta(days=days)).strftime('%Y-%m-%d')

            # Obtener reservas recientes
            result = self.client.table('reservations').select('email, name, date, created_at').gte(
                'date', start_date
            ).execute()

            # Obtener datos de usuarios
            users_result = self.client.table('users').select('email, full_name, last_login, created_at').execute()
            users_dict = {u['email']: u for u in users_result.data}

            # Agrupar actividad por usuario
            user_activity = {}
            for reservation in result.data:
                email = reservation['email']
                if email not in user_activity:
                    user_info = users_dict.get(email, {})
                    user_activity[email] = {
                        'name': reservation['name'],
                        'email': email,
                        'recent_reservations': 0,
                        'last_reservation': None,
                        'last_login': self._format_colombia_datetime(user_info.get('last_login')),
                        'member_since': self._format_colombia_datetime(user_info.get('created_at'))
                    }

                user_activity[email]['recent_reservations'] += 1

                # Actualizar última reserva
                if (not user_activity[email]['last_reservation'] or
                        reservation['date'] > user_activity[email]['last_reservation']):
                    user_activity[email]['last_reservation'] = reservation['date']

            # Convertir a lista ordenada por actividad
            return sorted(user_activity.values(),
                          key=lambda x: x['recent_reservations'], reverse=True)[:20]

        except Exception as e:
            print(f"Error getting user activity stats: {e}")
            return []

    def save_cancellation_record(self, reservation_id: int, reservation_data: Dict,
                                 reason: str, admin_username: str) -> bool:
        """Guardar registro de cancelación"""
        try:
            result = self.client.table('reservation_cancellations').insert({
                'original_reservation_id': reservation_id,
                'user_email': reservation_data.get('email'),
                'user_name': reservation_data.get('name'),
                'reservation_date': reservation_data.get('date'),
                'reservation_hour': reservation_data.get('hour'),
                'cancellation_reason': reason,
                'cancelled_by': admin_username,
                'cancelled_at': datetime.now().isoformat(),
                'credits_refunded': 1
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
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(cancellation['reservation_date'], '%Y-%m-%d')
                    formatted_date = date_obj.strftime('%d/%m/%Y')
                    day_name = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'][date_obj.weekday()]
                    reservation_date_display = f"{day_name} {formatted_date}"
                except:
                    reservation_date_display = cancellation['reservation_date']

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

    def get_maintenance_slots(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """Obtener horarios de mantenimiento"""
        try:
            query = self.client.table('maintenance_slots').select('*')

            if start_date:
                query = query.gte('date', start_date)
            if end_date:
                query = query.lte('date', end_date)

            result = query.order('date').order('hour').execute()

            # Formatear fechas
            for slot in result.data:
                if 'created_at' in slot:
                    slot['created_at'] = self._format_colombia_datetime(slot['created_at'])

            return result.data
        except Exception as e:
            print(f"Error getting maintenance slots: {e}")
            return []

    def add_maintenance_slot(self, date: str, hour: int, reason: str, admin_username: str) -> Tuple[bool, str]:
        """Agregar horario de mantenimiento"""
        try:
            # Verificar si ya existe una reserva
            existing_reservation = self.client.table('reservations').select('id, email').eq(
                'date', date
            ).eq('hour', hour).execute()

            if existing_reservation.data:
                return False, "Ya existe una reserva en este horario"

            # Verificar si ya existe mantenimiento
            existing_maintenance = self.client.table('maintenance_slots').select('id').eq(
                'date', date
            ).eq('hour', hour).execute()

            if existing_maintenance.data:
                return False, "Ya existe mantenimiento programado en este horario"

            # Insertar mantenimiento
            result = self.client.table('maintenance_slots').insert({
                'date': date,
                'hour': hour,
                'reason': reason or 'Mantenimiento programado',
                'created_by': admin_username,
                'created_at': datetime.now().isoformat()
            }).execute()

            return len(result.data) > 0, "Mantenimiento programado exitosamente"
        except Exception as e:
            print(f"Error adding maintenance slot: {e}")
            return False, f"Error: {str(e)}"

    def remove_maintenance_slot(self, maintenance_id: int) -> bool:
        """Eliminar horario de mantenimiento"""
        try:
            result = self.client.table('maintenance_slots').delete().eq('id', maintenance_id).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Error removing maintenance slot: {e}")
            return False

    def get_maintenance_for_date(self, date: str) -> List[int]:
        """Obtener horas de mantenimiento para una fecha específica"""
        try:
            result = self.client.table('maintenance_slots').select('hour').eq('date', date).execute()
            return [row['hour'] for row in result.data]
        except Exception:
            return []

# Instancia global
admin_db_manager = AdminDatabaseManager()