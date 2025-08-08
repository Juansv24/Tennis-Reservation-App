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
            from timezone_utils import get_colombia_now
            expires_at = get_colombia_now().replace(tzinfo=None) + timedelta(minutes=10)

            # Limpiar códigos expirados primero
            self.client.table('email_verifications').delete().lt(
                'expires_at', datetime.now().isoformat()
            ).execute()

            result = self.client.table('email_verifications').insert({
                'email': email.strip().lower(),
                'code': code,
                'expires_at': expires_at.isoformat(),
                'is_used': False
            }).execute()
            return len(result.data) > 0
        except Exception as e:
            st.error(f"Error guardando código de verificación: {e}")
            return False

    def verify_email_code(self, email: str, code: str) -> bool:
        """Verificar código de email y marcarlo como usado"""
        try:
            # Buscar código válido
            result = self.client.table('email_verifications').select('id').eq(
                'email', email.strip().lower()
            ).eq('code', code.strip().upper()).eq('is_used', False).gt(
                'expires_at', datetime.now().isoformat()
            ).execute()

            if result.data:
                # Marcar como usado
                self.client.table('email_verifications').update({
                    'is_used': True
                }).eq('id', result.data[0]['id']).execute()
                return True
            return False
        except Exception as e:
            st.error(f"Error verificando código: {e}")
            return False

    def cleanup_expired_data(self):
        """Limpiar datos expirados del sistema"""
        try:
            now = get_colombia_now().replace(tzinfo=None).isoformat()

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


# Instancia global
db_manager = SupabaseManager()