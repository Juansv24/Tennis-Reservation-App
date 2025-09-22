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

            return result.data
        except Exception:
            return []

    def cancel_reservation_with_notification(self, reservation_id: int) -> bool:
        """Cancel a reservation with transaction safety"""
        try:
            # Get reservation data first
            reservation_result = self.client.table('reservations').select('email, date, hour, name').eq('id',
                                                                                                        reservation_id).execute()

            if not reservation_result.data:
                print(f"❌ Reservation {reservation_id} not found")
                return False

            reservation = reservation_result.data[0]
            user_email = reservation['email']

            # Get user data
            user_result = self.client.table('users').select('id, credits').eq('email', user_email).execute()
            if not user_result.data:
                print(f"❌ User {user_email} not found")
                return False

            user = user_result.data[0]
            user_id = user['id']
            current_credits = user['credits'] or 0
            new_credits = current_credits + 1

            print(f"🔄 Starting transaction: Cancel reservation {reservation_id} for {user_email}")

            # TRANSACTION BLOCK - All operations must succeed or all fail
            try:
                # Step 1: Delete the reservation
                delete_result = self.client.table('reservations').delete().eq('id', reservation_id).execute()

                if not delete_result.data:
                    raise Exception("Failed to delete reservation from database")

                print(f"✅ Step 1: Reservation deleted")

                # Step 2: Update user credits
                credit_update_result = self.client.table('users').update({
                    'credits': new_credits
                }).eq('id', user_id).execute()

                if not credit_update_result.data:
                    # ROLLBACK: Re-insert the reservation
                    rollback_result = self.client.table('reservations').insert({
                        'date': reservation['date'],
                        'hour': reservation['hour'],
                        'name': reservation['name'],
                        'email': reservation['email']
                    }).execute()

                    if rollback_result.data:
                        print("🔄 Rollback successful: Reservation restored")
                    else:
                        print("❌ CRITICAL: Rollback failed - manual intervention required")

                    raise Exception("Failed to update user credits")

                print(f"✅ Step 2: Credits updated ({current_credits} → {new_credits})")

                # Step 3: Log the transaction
                transaction_result = self.client.table('credit_transactions').insert({
                    'user_id': user_id,
                    'amount': 1,
                    'transaction_type': 'reservation_refund',
                    'description': f'Refund for admin cancellation - {reservation["date"]} {reservation["hour"]}:00',
                    'admin_user': 'admin',
                    'created_at': datetime.now().isoformat()
                }).execute()

                if not transaction_result.data:
                    print("⚠️ Warning: Transaction logged failed, but reservation and credits updated successfully")
                else:
                    print(f"✅ Step 3: Transaction logged")

                print(f"✅ Transaction completed successfully")
                return True

            except Exception as transaction_error:
                print(f"❌ Transaction failed: {transaction_error}")
                return False

        except Exception as e:
            print(f"❌ Error in cancel_reservation: {e}")
            return False

    def _send_cancellation_notification(self, user_email: str, reservation: Dict):
        """Enviar notificación de cancelación"""
        try:
            from email_config import email_manager

            if email_manager.is_configured():
                subject = "🎾 Reserva Cancelada - Sistema de Reservas"

                html_body = f"""
                <h2>Reserva Cancelada</h2>
                <p>Tu reserva ha sido cancelada por el administrador:</p>
                <ul>
                    <li><strong>Fecha:</strong> {reservation['date']}</li>
                    <li><strong>Hora:</strong> {reservation['hour']}:00</li>
                </ul>
                <p>Se ha reembolsado 1 crédito a tu cuenta.</p>
                <p>Si tienes preguntas, contacta al administrador.</p>
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
            return result.data
        except Exception:
            return []

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
        """Add credits to user with transaction safety"""
        try:
            # Validate inputs
            if credits_amount <= 0 or credits_amount > 100:
                print(f"❌ Invalid credit amount: {credits_amount}")
                return False

            if not reason or len(reason.strip()) < 3:
                print("❌ Reason is required and must be at least 3 characters")
                return False

            # Get user data
            user_result = self.client.table('users').select('id, credits, full_name').eq('email',
                                                                                         email.strip().lower()).execute()

            if not user_result.data:
                print(f"❌ User not found: {email}")
                return False

            user = user_result.data[0]
            user_id = user['id']
            current_credits = user['credits'] or 0
            new_credits = current_credits + credits_amount

            print(f"🔄 Adding {credits_amount} credits to {user['full_name']} ({email})")
            print(f"🔄 Credits: {current_credits} → {new_credits}")

            # TRANSACTION BLOCK
            try:
                # Step 1: Update user credits
                credit_update_result = self.client.table('users').update({
                    'credits': new_credits
                }).eq('id', user_id).execute()

                if not credit_update_result.data:
                    raise Exception("Failed to update user credits")

                print(f"✅ Step 1: User credits updated")

                # Step 2: Log the transaction
                transaction_result = self.client.table('credit_transactions').insert({
                    'user_id': user_id,
                    'amount': credits_amount,
                    'transaction_type': 'admin_grant',
                    'description': reason.strip(),
                    'admin_user': admin_username,
                    'created_at': datetime.now().isoformat()
                }).execute()

                if not transaction_result.data:
                    # ROLLBACK: Restore original credits
                    rollback_result = self.client.table('users').update({
                        'credits': current_credits
                    }).eq('id', user_id).execute()

                    if rollback_result.data:
                        print("🔄 Rollback successful: Credits restored")
                    else:
                        print("❌ CRITICAL: Rollback failed - manual intervention required")

                    raise Exception("Failed to log credit transaction")

                print(f"✅ Step 2: Transaction logged")
                print(f"✅ Credit addition completed successfully")
                return True

            except Exception as transaction_error:
                print(f"❌ Transaction failed: {transaction_error}")
                return False

        except Exception as e:
            print(f"❌ Error in add_credits_to_user: {e}")
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

    def get_user_recent_reservations(self, user_email: str, limit: int = 10) -> List[Dict]:
        """Obtener reservas recientes de un usuario"""
        try:
            result = self.client.table('reservations').select(
                'date, hour, created_at'
            ).eq('email', user_email).order('date', desc=True).limit(limit).execute()

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
                    'Último Login': user['last_login'][:10] if user['last_login'] else 'Nunca',
                    'Fecha Registro': user['created_at'][:10]
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
                    'Fecha Creación': reservation['created_at'][:10]
                })

            return formatted_reservations
        except Exception as e:
            print(f"Error getting reservations for export: {e}")
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
                    'Fecha': transaction['created_at'][:10]
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

# Instancia global
admin_db_manager = AdminDatabaseManager()