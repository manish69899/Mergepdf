"""
💾 Database Module
Stores user preferences, base pdfs, and queue with auto-upgrades.
(Optimized with Threading Locks for Bulk Concurrency)
"""

import os
import sqlite3
import threading
from typing import Dict, Any, List

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        # Lock ensures thread-safety during bulk uploads
        self.lock = threading.Lock()
        self._init_db()
    
    def _get_connection(self):
        """Returns a configured SQLite connection"""
        return sqlite3.connect(self.db_path, timeout=20, check_same_thread=False)

    def _init_db(self):
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Create Users table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT
                    )
                ''')
                
                # Auto-Upgrade Database dynamically
                cursor.execute("PRAGMA table_info(users)")
                existing_columns = [col[1] for col in cursor.fetchall()]
                
                if 'base_pdf_path' not in existing_columns:
                    cursor.execute('ALTER TABLE users ADD COLUMN base_pdf_path TEXT')
                if 'base_pdf_name' not in existing_columns:
                    cursor.execute('ALTER TABLE users ADD COLUMN base_pdf_name TEXT')
                if 'merge_position' not in existing_columns:
                    cursor.execute('ALTER TABLE users ADD COLUMN merge_position TEXT DEFAULT "end"')
                if 'custom_prefix' not in existing_columns:
                    cursor.execute('ALTER TABLE users ADD COLUMN custom_prefix TEXT')
                
                # Queue table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS queue (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        file_id TEXT,
                        file_name TEXT,
                        file_size INTEGER
                    )
                ''')
                
                conn.commit()
    
    def register_user(self, user_id: int, username: str = None):
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (user_id, username)
                    VALUES (?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET username = excluded.username
                ''', (user_id, username))
                conn.commit()
        
    def set_base_pdf(self, user_id: int, file_path: str, file_name: str):
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete old base PDF if it exists to save disk space
                cursor.execute('SELECT base_pdf_path FROM users WHERE user_id = ?', (user_id,))
                res = cursor.fetchone()
                if res and res[0] and os.path.exists(res[0]):
                    try: 
                        os.remove(res[0])
                    except Exception: 
                        pass
                    
                cursor.execute('''
                    UPDATE users SET base_pdf_path = ?, base_pdf_name = ? WHERE user_id = ?
                ''', (file_path, file_name, user_id))
                conn.commit()
        
    def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT base_pdf_path, base_pdf_name, merge_position, custom_prefix 
                FROM users WHERE user_id = ?
            ''', (user_id,))
            res = cursor.fetchone()
            
        if res:
            return {
                "base_pdf_path": res[0],
                "base_pdf_name": res[1],
                "position": res[2] or "end",
                "custom_prefix": res[3] # None if not set
            }
        return {"base_pdf_path": None, "base_pdf_name": None, "position": "end", "custom_prefix": None}
        
    def update_position(self, user_id: int, position: str):
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET merge_position = ? WHERE user_id = ?', (position, user_id))
                conn.commit()
        
    def update_prefix(self, user_id: int, prefix: str):
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET custom_prefix = ? WHERE user_id = ?', (prefix, user_id))
                conn.commit()

    def add_to_queue(self, user_id: int, file_id: str, file_name: str, file_size: int):
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO queue (user_id, file_id, file_name, file_size)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, file_id, file_name, file_size))
                conn.commit()
        
    def get_queue(self, user_id: int) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, file_id, file_name, file_size 
                FROM queue WHERE user_id = ? ORDER BY id ASC
            ''', (user_id,))
            rows = cursor.fetchall()
            
        return [{"id": r[0], "file_id": r[1], "file_name": r[2], "file_size": r[3]} for r in rows]
        
    def remove_from_queue(self, item_id: int):
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM queue WHERE id = ?', (item_id,))
                conn.commit()
        
    def clear_queue(self, user_id: int):
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM queue WHERE user_id = ?', (user_id,))
                conn.commit()

# Late import to avoid circular dependency issues
try:
    from config import config
    db = Database(config.DATABASE_PATH)
except ImportError:
    pass # Allows safe importing in isolated testing environments