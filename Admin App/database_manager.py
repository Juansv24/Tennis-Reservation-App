"""
Gestor de Base de Datos Supabase para Sistema de Reservas de Cancha de Tenis
"""
import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta
from typing import Dict, List
from timezone_utils import get_colombia_now, get_colombia_today


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

    def get_activity_timeline_data(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        Get activity data for timeline visualization

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        try:
            # Default to last 7 days if no dates provided
            if not end_date:
                end_date = get_colombia_today().strftime('%Y-%m-%d')
            if not start_date:
                start_dt = datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=7)
                start_date = start_dt.strftime('%Y-%m-%d')

            # Build query with explicit timezone
            start_filter = f"{start_date}T00:00:00+00:00"
            end_filter = f"{end_date}T23:59:59+00:00"

            # Query activity logs with user info
            result = self.client.table('user_activity_logs').select(
                'id, user_id, activity_type, activity_description, created_at, users(full_name, email)'
            ).gte('created_at', start_filter).lte(
                'created_at', end_filter
            ).order('created_at').execute()

            return result.data
        except Exception as e:
            print(f"Error getting timeline data: {e}")
            return []

    def get_activity_stats(self, start_date: str = None, end_date: str = None) -> Dict:
        """Get aggregated activity statistics"""
        try:
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

            # Activity type breakdown
            activity_breakdown = {}
            for item in data:
                act_type = item.get('activity_type', 'unknown')
                activity_breakdown[act_type] = activity_breakdown.get(act_type, 0) + 1

            return {
                'total_activities': total_activities,
                'unique_users': unique_users,
                'unique_sessions': 0,
                'activity_breakdown': activity_breakdown,
                'date_range': {'start': start_date, 'end': end_date}
            }
        except Exception as e:
            print(f"Error getting activity stats: {e}")
            return {}


# Instancia global
db_manager = SupabaseManager()
