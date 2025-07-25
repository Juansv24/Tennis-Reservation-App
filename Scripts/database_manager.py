"""
Database Manager for Tennis Court Reservation System

"""

import sqlite3
import datetime
from typing import Dict, List, Optional, Tuple
import contextlib
import os

# Database configuration - identical to original
DATABASE_FILE = "Data/tennis_reservations.db"

class DatabaseManager:
    """Simplified database manager with identical API to original"""
    
    def __init__(self, db_file: str = DATABASE_FILE):
        self.db_file = db_file
        self.init_database()
    
    @contextlib.contextmanager
    def get_connection(self):
        """Context manager for database connections - identical to original"""
        conn = sqlite3.connect(self.db_file)
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        """Create database - simplified without complex migration"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create table with correct structure directly
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reservations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    hour INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, hour)
                )
            ''')
            
            conn.commit()
    
    def save_reservation(self, date: datetime.date, hour: int, name: str, email: str) -> bool:
        """Save reservation - identical API to original"""
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
            # Slot already reserved
            return False
        except Exception:
            return False
    
    def is_hour_available(self, date: datetime.date, hour: int) -> bool:
        """Check availability - identical API to original"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT COUNT(*) FROM reservations 
                    WHERE date = ? AND hour = ?
                ''', (date.strftime('%Y-%m-%d'), hour))
                
                return cursor.fetchone()[0] == 0
        except Exception:
            return False
    
    def get_reservations_for_date(self, date: datetime.date) -> List[int]:
        """Get reserved hours for date - identical API to original"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT hour FROM reservations 
                    WHERE date = ?
                    ORDER BY hour
                ''', (date.strftime('%Y-%m-%d'),))
                
                return [row[0] for row in cursor.fetchall()]
        except Exception:
            return []
    
    def get_reservations_with_names_for_date(self, date: datetime.date) -> Dict[int, str]:
        """Get reservations with names - identical API to original"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT hour, name FROM reservations 
                    WHERE date = ?
                    ORDER BY hour
                ''', (date.strftime('%Y-%m-%d'),))
                
                return {row[0]: row[1] for row in cursor.fetchall()}
        except Exception:
            return {}
    
    def get_user_reservations_for_date(self, email: str, date: datetime.date) -> List[int]:
        """Get user reservations for date - identical API to original"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT hour FROM reservations 
                    WHERE email = ? AND date = ?
                    ORDER BY hour
                ''', (email.strip().lower(), date.strftime('%Y-%m-%d')))
                
                return [row[0] for row in cursor.fetchall()]
        except Exception:
            return []
    
    def get_all_reservations(self) -> List[tuple]:
        """Get all reservations - identical API to original"""
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
        """Delete reservation - identical API to original"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM reservations 
                    WHERE date = ? AND hour = ?
                ''', (date, hour))
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception:
            return False

# Global instance - identical to original
db_manager = DatabaseManager()