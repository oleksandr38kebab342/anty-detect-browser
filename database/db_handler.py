"""Database handler module for SQLite operations.

Contains the Database class and helper functions for profile persistence.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional


class Database:
    """SQLite database access layer for profiles and proxies."""

    def __init__(self, db_path: str = "browser_profiles.db"):
        self.db_path = db_path
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        """Create a new database connection.

        Returns:
            SQLite connection instance with Row factory enabled.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self) -> None:
        """Initialize database schema if it doesn't exist."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                profile_id TEXT UNIQUE NOT NULL,
                notes TEXT,
                proxy_id INTEGER,
                tags TEXT,
                os TEXT,
                user_agent TEXT,
                open_tabs TEXT,
                timezone_mode TEXT,
                timezone_value TEXT,
                geolocation_mode TEXT,
                geolocation_lat REAL,
                geolocation_lon REAL,
                language_mode TEXT,
                languages TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (proxy_id) REFERENCES proxies(id)
            )
            """
        )

        cursor.execute(
            """
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
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

        conn.commit()
        conn.close()

        self._ensure_profile_columns()

    def _ensure_profile_columns(self) -> None:
        """Add missing columns to the profiles table for backward compatibility."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(profiles)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        columns_to_add = {
            "os": "TEXT",
            "user_agent": "TEXT",
            "open_tabs": "TEXT",
            "timezone_mode": "TEXT",
            "timezone_value": "TEXT",
            "geolocation_mode": "TEXT",
            "geolocation_lat": "REAL",
            "geolocation_lon": "REAL",
            "language_mode": "TEXT",
            "languages": "TEXT",
        }

        for column, col_type in columns_to_add.items():
            if column not in existing_columns:
                cursor.execute(f"ALTER TABLE profiles ADD COLUMN {column} {col_type}")

        conn.commit()
        conn.close()

    def get_next_profile_number(self) -> int:
        """Get next sequential profile number.

        Returns:
            Next profile number based on max ID in the profiles table.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT IFNULL(MAX(id), 0) + 1 FROM profiles")
        next_id = cursor.fetchone()[0]
        conn.close()
        return int(next_id)

    def create_profile(
        self,
        name: str,
        profile_id: str,
        notes: str = "",
        proxy_id: Optional[int] = None,
        tags: str = "",
        os: str | None = None,
        user_agent: str | None = None,
        open_tabs: str | None = None,
        timezone_mode: str | None = None,
        timezone_value: str | None = None,
        geolocation_mode: str | None = None,
        geolocation_lat: float | None = None,
        geolocation_lon: float | None = None,
        language_mode: str | None = None,
        languages: str | None = None,
    ) -> int:
        """Create a new profile.

        Returns:
            Database row ID of the created profile.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO profiles (
                name, profile_id, notes, proxy_id, tags,
                os, user_agent, open_tabs, timezone_mode, timezone_value,
                geolocation_mode, geolocation_lat, geolocation_lon,
                language_mode, languages, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                profile_id,
                notes,
                proxy_id,
                tags,
                os,
                user_agent,
                open_tabs,
                timezone_mode,
                timezone_value,
                geolocation_mode,
                geolocation_lat,
                geolocation_lon,
                language_mode,
                languages,
                now,
                now,
            ),
        )

        profile_db_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return profile_db_id

    def get_all_profiles(self) -> List[Dict]:
        """Return all profiles with proxy info."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT p.id, p.name, p.profile_id, p.notes, p.proxy_id, p.tags,
                   p.os, p.user_agent, p.open_tabs, p.timezone_mode, p.timezone_value,
                   p.geolocation_mode, p.geolocation_lat, p.geolocation_lon,
                   p.language_mode, p.languages,
                   pr.name as proxy_name, pr.type as proxy_type,
                   pr.host as proxy_host, pr.port as proxy_port
            FROM profiles p
            LEFT JOIN proxies pr ON p.proxy_id = pr.id
            ORDER BY p.created_at DESC
            """
        )

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_profile_by_id(self, profile_id: str) -> Optional[Dict]:
        """Return a profile by profile_id."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT p.id, p.name, p.profile_id, p.notes, p.proxy_id, p.tags,
                   p.os, p.user_agent, p.open_tabs, p.timezone_mode, p.timezone_value,
                   p.geolocation_mode, p.geolocation_lat, p.geolocation_lon,
                   p.language_mode, p.languages,
                   pr.name as proxy_name, pr.type as proxy_type,
                   pr.host as proxy_host, pr.port as proxy_port,
                   pr.username as proxy_username, pr.password as proxy_password
            FROM profiles p
            LEFT JOIN proxies pr ON p.proxy_id = pr.id
            WHERE p.profile_id = ?
            """,
            (profile_id,),
        )

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def update_profile(
        self,
        profile_id: str,
        name: str | None = None,
        notes: str | None = None,
        proxy_id: Optional[int] = None,
        tags: str | None = None,
        os: str | None = None,
        user_agent: str | None = None,
        open_tabs: str | None = None,
        timezone_mode: str | None = None,
        timezone_value: str | None = None,
        geolocation_mode: str | None = None,
        geolocation_lat: float | None = None,
        geolocation_lon: float | None = None,
        language_mode: str | None = None,
        languages: str | None = None,
    ) -> None:
        """Update profile fields by profile_id."""
        conn = self.get_connection()
        cursor = conn.cursor()

        updates: List[str] = []
        params: List[object] = []

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
        if os is not None:
            updates.append("os = ?")
            params.append(os)
        if user_agent is not None:
            updates.append("user_agent = ?")
            params.append(user_agent)
        if open_tabs is not None:
            updates.append("open_tabs = ?")
            params.append(open_tabs)
        if timezone_mode is not None:
            updates.append("timezone_mode = ?")
            params.append(timezone_mode)
        if timezone_value is not None:
            updates.append("timezone_value = ?")
            params.append(timezone_value)
        if geolocation_mode is not None:
            updates.append("geolocation_mode = ?")
            params.append(geolocation_mode)
        if geolocation_lat is not None:
            updates.append("geolocation_lat = ?")
            params.append(geolocation_lat)
        if geolocation_lon is not None:
            updates.append("geolocation_lon = ?")
            params.append(geolocation_lon)
        if language_mode is not None:
            updates.append("language_mode = ?")
            params.append(language_mode)
        if languages is not None:
            updates.append("languages = ?")
            params.append(languages)

        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(profile_id)

        cursor.execute(
            f"""
            UPDATE profiles
            SET {', '.join(updates)}
            WHERE profile_id = ?
            """,
            params,
        )

        conn.commit()
        conn.close()

    def delete_profile(self, profile_id: str) -> None:
        """Delete a profile by profile_id."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM profiles WHERE profile_id = ?", (profile_id,))

        conn.commit()
        conn.close()

    def create_proxy(
        self,
        name: str,
        type: str,
        host: str,
        port: int,
        username: str | None = None,
        password: str | None = None,
    ) -> int:
        """Create a new proxy.

        Returns:
            Database row ID of the created proxy.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO proxies (name, type, host, port, username, password, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name, type, host, port, username, password, now),
        )

        proxy_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return proxy_id

    def get_all_proxies(self) -> List[Dict]:
        """Return all proxies."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM proxies ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_proxy_by_id(self, proxy_id: int) -> Optional[Dict]:
        """Return proxy by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM proxies WHERE id = ?", (proxy_id,))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def update_proxy(
        self,
        proxy_id: int,
        name: str | None = None,
        type: str | None = None,
        host: str | None = None,
        port: int | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        """Update proxy fields by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()

        updates: List[str] = []
        params: List[object] = []

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

        cursor.execute(
            f"""
            UPDATE proxies
            SET {', '.join(updates)}
            WHERE id = ?
            """,
            params,
        )

        conn.commit()
        conn.close()

    def delete_proxy(self, proxy_id: int) -> None:
        """Delete proxy by ID and unlink from profiles."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("UPDATE profiles SET proxy_id = NULL WHERE proxy_id = ?", (proxy_id,))
        cursor.execute("DELETE FROM proxies WHERE id = ?", (proxy_id,))

        conn.commit()
        conn.close()

    def get_setting(self, key: str, default: str | None = None) -> Optional[str]:
        """Get a setting value by key."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()

        return row[0] if row else default

    def set_setting(self, key: str, value: str) -> None:
        """Persist a setting value."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO settings (key, value)
            VALUES (?, ?)
            """,
            (key, value),
        )

        conn.commit()
        conn.close()


def save_profile(
    db: Database,
    *,
    name: str,
    profile_id: str,
    notes: str = "",
    proxy_id: Optional[int] = None,
    tags: str = "",
    os: str | None = None,
    user_agent: str | None = None,
    open_tabs: str | None = None,
    timezone_mode: str | None = None,
    timezone_value: str | None = None,
    geolocation_mode: str | None = None,
    geolocation_lat: float | None = None,
    geolocation_lon: float | None = None,
    language_mode: str | None = None,
    languages: str | None = None,
) -> int:
    """Save a profile using the Database instance.

    Args:
        db: Database instance to use for persistence.
        name: Profile name.
        profile_id: Unique profile identifier.
        notes: Optional notes.
        proxy_id: Optional proxy ID.
        tags: Optional tags.
        os: Operating system name.
        user_agent: User-Agent string.
        open_tabs: JSON string with open tabs.
        timezone_mode: Timezone mode.
        timezone_value: Timezone value if custom.
        geolocation_mode: Geolocation mode.
        geolocation_lat: Latitude if manual.
        geolocation_lon: Longitude if manual.
        language_mode: Language mode.
        languages: JSON string with language list.

    Returns:
        Database row ID of the created profile.

    Raises:
        RuntimeError: If saving the profile fails.
    """
    try:
        return db.create_profile(
            name=name,
            profile_id=profile_id,
            notes=notes,
            proxy_id=proxy_id,
            tags=tags,
            os=os,
            user_agent=user_agent,
            open_tabs=open_tabs,
            timezone_mode=timezone_mode,
            timezone_value=timezone_value,
            geolocation_mode=geolocation_mode,
            geolocation_lat=geolocation_lat,
            geolocation_lon=geolocation_lon,
            language_mode=language_mode,
            languages=languages,
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to save profile: {exc}") from exc
