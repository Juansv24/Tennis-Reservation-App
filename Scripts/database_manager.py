"""
Gestor de Base de Datos para Sistema de Reservas de Cancha de Tenis
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import contextlib
import os

# Configuración de base de datos
DATABASE_FILE = "Data/tennis_reservations.db"


class DatabaseManager:
    """Gestor de base de datos simplificado"""

    def __init__(self, db_file: str = DATABASE_FILE):
        self.db_file = db_file
        self.init_database()

    @contextlib.contextmanager
    def get_connection(self):
        """Administrador de contexto para conexiones de base de datos"""
        conn = sqlite3.connect(self.db_file)
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def init_database(self):
        """Crear base de datos"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Crear tabla con estructura correcta
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS reservations
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               date
                               TEXT
                               NOT
                               NULL,
                               hour
                               INTEGER
                               NOT
                               NULL,
                               name
                               TEXT
                               NOT
                               NULL,
                               email
                               TEXT
                               NOT
                               NULL,
                               created_at
                               TIMESTAMP
                               DEFAULT
                               CURRENT_TIMESTAMP,
                               UNIQUE
                           (
                               date,
                               hour
                           )
                               )
                           ''')

            conn.commit()

    def save_reservation(self, date: datetime.date, hour: int, name: str, email: str) -> bool:
        """Guardar reserva"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                               INSERT INTO reservations (date, hour, name, email)
                               VALUES (?, ?, ?, ?)
                               ''', (date.strftime('%Y-%m-%d'), hour, name.strip(), email.strip().lower()))

                conn.commit()
                return True

        except sqlite3.IntegrityError:
            # Horario ya reservado
            return False
        except Exception:
            return False

    def is_hour_available(self, date: datetime.date, hour: int) -> bool:
        """Verificar disponibilidad"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                               SELECT COUNT(*)
                               FROM reservations
                               WHERE date = ? AND hour = ?
                               ''', (date.strftime('%Y-%m-%d'), hour))

                return cursor.fetchone()[0] == 0
        except Exception:
            return False

    def get_reservations_for_date(self, date: datetime.date) -> List[int]:
        """Obtener horas reservadas para una fecha"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                               SELECT hour
                               FROM reservations
                               WHERE date = ?
                               ORDER BY hour
                               ''', (date.strftime('%Y-%m-%d'),))

                return [row[0] for row in cursor.fetchall()]
        except Exception:
            return []

    def get_reservations_with_names_for_date(self, date: datetime.date) -> Dict[int, str]:
        """Obtener reservas con nombres"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                               SELECT hour, name
                               FROM reservations
                               WHERE date = ?
                               ORDER BY hour
                               ''', (date.strftime('%Y-%m-%d'),))

                return {row[0]: row[1] for row in cursor.fetchall()}
        except Exception:
            return {}

    def get_user_reservations_for_date(self, email: str, date: datetime.date) -> List[int]:
        """Obtener reservas del usuario para una fecha"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                               SELECT hour
                               FROM reservations
                               WHERE email = ? AND date = ?
                               ORDER BY hour
                               ''', (email.strip().lower(), date.strftime('%Y-%m-%d')))

                return [row[0] for row in cursor.fetchall()]
        except Exception:
            return []

    def get_all_reservations(self) -> List[tuple]:
        """Obtener todas las reservas"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                               SELECT id, date, hour, name, email, created_at
                               FROM reservations
                               ORDER BY date DESC, hour
                               ''')

                return cursor.fetchall()
        except Exception:
            return []

    def delete_reservation(self, date: str, hour: int) -> bool:
        """Eliminar reserva"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                               DELETE
                               FROM reservations
                               WHERE date = ? AND hour = ?
                               ''', (date, hour))

                conn.commit()
                return cursor.rowcount > 0
        except Exception:
            return False

    def save_verification_code(self, email: str, code: str) -> bool:
        """Guardar código de verificación de email"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Crear tabla de verificaciones si no existe
                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS email_verifications
                               (
                                   id
                                   INTEGER
                                   PRIMARY
                                   KEY
                                   AUTOINCREMENT,
                                   email
                                   TEXT
                                   NOT
                                   NULL,
                                   code
                                   TEXT
                                   NOT
                                   NULL,
                                   created_at
                                   TIMESTAMP
                                   DEFAULT
                                   CURRENT_TIMESTAMP,
                                   expires_at
                                   TIMESTAMP
                                   NOT
                                   NULL,
                                   is_used
                                   BOOLEAN
                                   DEFAULT
                                   0
                               )
                               ''')

                # Limpiar códigos expirados
                cursor.execute('''
                               DELETE
                               FROM email_verifications
                               WHERE expires_at < CURRENT_TIMESTAMP
                               ''')

                # Guardar nuevo código (expira en 10 minutos)
                from timezone_utils import get_colombia_now
                expires_at = get_colombia_now().replace(tzinfo=None) + timedelta(minutes=10)

                cursor.execute('''
                               INSERT INTO email_verifications (email, code, expires_at)
                               VALUES (?, ?, ?)
                               ''', (email.strip().lower(), code.upper(), expires_at.isoformat()))

                conn.commit()
                return True

        except Exception:
            return False

    def verify_email_code(self, email: str, code: str) -> bool:
        """Verificar código de email y marcarlo como usado"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Get current time in the same format as stored
                from timezone_utils import get_colombia_now
                current_time = get_colombia_now().replace(tzinfo=None).isoformat()

                cursor.execute('''
                               SELECT id, expires_at
                               FROM email_verifications
                               WHERE email = ?
                                 AND code = ?
                                 AND is_used = 0
                               ORDER BY created_at DESC LIMIT 1
                               ''', (email.strip().lower(), code.strip().upper()))

                result = cursor.fetchone()

                if result:
                    verification_id, expires_at_str = result

                    # Parse the expiration time and compare
                    try:
                        from datetime import datetime
                        expires_at = datetime.fromisoformat(expires_at_str)
                        current_dt = get_colombia_now().replace(tzinfo=None)

                        if current_dt > expires_at:
                            return False  # Expired

                        # Mark as used
                        cursor.execute('''
                                       UPDATE email_verifications
                                       SET is_used = 1
                                       WHERE id = ?
                                       ''', (verification_id,))
                        conn.commit()
                        return True

                    except ValueError:
                        return False

                return False

        except Exception as e:
            print(f"Error in verify_email_code: {str(e)}")  # For debugging
            return False

# Instancia global
db_manager = DatabaseManager()