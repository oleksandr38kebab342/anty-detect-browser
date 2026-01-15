"""
Модуль для роботи з базою даних SQLite.
Зберігає метадані профілів та проксі.
"""
import sqlite3
import os
from typing import List, Dict, Optional
from datetime import datetime


class Database:
    def __init__(self, db_path: str = "browser_profiles.db"):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        """Створює з'єднання з базою даних."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """Ініціалізує базу даних, створюючи необхідні таблиці."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Таблиця профілів
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                profile_id TEXT UNIQUE NOT NULL,
                notes TEXT,
                proxy_id INTEGER,
                tags TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (proxy_id) REFERENCES proxies(id)
            )
        """)

        # Таблиця проксі
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proxies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                username TEXT,
                password TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # Таблиця налаштувань
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    # Профілі
    def create_profile(self, name: str, profile_id: str, notes: str = "", 
                      proxy_id: Optional[int] = None, tags: str = "") -> int:
        """Створює новий профіль."""
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO profiles (name, profile_id, notes, proxy_id, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, profile_id, notes, proxy_id, tags, now, now))
        
        profile_db_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return profile_db_id

    def get_all_profiles(self) -> List[Dict]:
        """Отримує всі профілі з інформацією про проксі."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.id, p.name, p.profile_id, p.notes, p.proxy_id, p.tags,
                   pr.name as proxy_name, pr.type as proxy_type, 
                   pr.host as proxy_host, pr.port as proxy_port
            FROM profiles p
            LEFT JOIN proxies pr ON p.proxy_id = pr.id
            ORDER BY p.created_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def get_profile_by_id(self, profile_id: str) -> Optional[Dict]:
        """Отримує профіль за profile_id."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.id, p.name, p.profile_id, p.notes, p.proxy_id, p.tags,
                   pr.name as proxy_name, pr.type as proxy_type,
                   pr.host as proxy_host, pr.port as proxy_port,
                   pr.username as proxy_username, pr.password as proxy_password
            FROM profiles p
            LEFT JOIN proxies pr ON p.proxy_id = pr.id
            WHERE p.profile_id = ?
        """, (profile_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None

    def update_profile(self, profile_id: str, name: str = None, notes: str = None,
                      proxy_id: Optional[int] = None, tags: str = None):
        """Оновлює профіль."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)
        if proxy_id is not None:
            updates.append("proxy_id = ?")
            params.append(proxy_id)
        if tags is not None:
            updates.append("tags = ?")
            params.append(tags)
        
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(profile_id)
        
        cursor.execute(f"""
            UPDATE profiles
            SET {', '.join(updates)}
            WHERE profile_id = ?
        """, params)
        
        conn.commit()
        conn.close()

    def delete_profile(self, profile_id: str):
        """Видаляє профіль."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM profiles WHERE profile_id = ?", (profile_id,))
        
        conn.commit()
        conn.close()

    # Проксі
    def create_proxy(self, name: str, type: str, host: str, port: int,
                    username: str = None, password: str = None) -> int:
        """Створює новий проксі."""
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO proxies (name, type, host, port, username, password, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, type, host, port, username, password, now))
        
        proxy_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return proxy_id

    def get_all_proxies(self) -> List[Dict]:
        """Отримує всі проксі."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM proxies ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def get_proxy_by_id(self, proxy_id: int) -> Optional[Dict]:
        """Отримує проксі за ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM proxies WHERE id = ?", (proxy_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None

    def update_proxy(self, proxy_id: int, name: str = None, type: str = None,
                    host: str = None, port: int = None,
                    username: str = None, password: str = None):
        """Оновлює проксі."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if type is not None:
            updates.append("type = ?")
            params.append(type)
        if host is not None:
            updates.append("host = ?")
            params.append(host)
        if port is not None:
            updates.append("port = ?")
            params.append(port)
        if username is not None:
            updates.append("username = ?")
            params.append(username)
        if password is not None:
            updates.append("password = ?")
            params.append(password)
        
        if not updates:
            conn.close()
            return
        
        params.append(proxy_id)
        
        cursor.execute(f"""
            UPDATE proxies
            SET {', '.join(updates)}
            WHERE id = ?
        """, params)
        
        conn.commit()
        conn.close()

    # Налаштування
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Отримує значення налаштування."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        
        return row['value'] if row else default

    def set_setting(self, key: str, value: str):
        """Зберігає значення налаштування."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO settings (key, value) 
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = ?
        """, (key, value, value))
        
        conn.commit()
        conn.close()

    def delete_proxy(self, proxy_id: int):
        """Видаляє проксі."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Спочатку видаляємо посилання на проксі з профілів
        cursor.execute("UPDATE profiles SET proxy_id = NULL WHERE proxy_id = ?", (proxy_id,))
        
        # Потім видаляємо сам проксі
        cursor.execute("DELETE FROM proxies WHERE id = ?", (proxy_id,))
        
        conn.commit()
        conn.close()

