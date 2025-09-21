"""
Gestor de Base de Datos para Funciones de Administración
"""

from database_manager import db_manager
from timezone_utils import get_colombia_today
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class AdminDatabaseManager:
    """Gestor de base de datos para funciones administrativas"""

    def __init__(self):
        self.client = db_manager.client

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
            return result.data
        except Exception:
            return []

    def cancel_reservation(self, reservation_id: int) -> bool:
        """Cancelar una reserva específica"""
        try:
            # Obtener datos de la reserva antes de cancelar para reembolso de créditos
            reservation_result = self.client.table('reservations').select('email, date, hour').eq('id', reservation_id).execute()

            if not reservation_result.data:
                return False

            reservation = reservation_result.data[0]

            # Eliminar la reserva
            delete_result = self.client.table('reservations').delete().eq('id', reservation_id).execute()

            if delete_result.data:
                # Reembolsar crédito al usuario
                user_result = self.client.table('users').select('id').eq('email', reservation['email']).execute()
                if user_result.data:
                    user_id = user_result.data[0]['id']

                    # Actualizar créditos del usuario
                    self.client.table('users').update({'credits': db_manager.client.rpc('increment_credits', {'user_id': user_id, 'amount': 1})}).eq('id', user_id).execute()

                    # Registrar transacción de reembolso
                    self.client.table('credit_transactions').insert({
                        'user_id': user_id,
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
                    transaction['created_at']
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

            return result.data
        except Exception:
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

# Instancia global
admin_db_manager = AdminDatabaseManager()