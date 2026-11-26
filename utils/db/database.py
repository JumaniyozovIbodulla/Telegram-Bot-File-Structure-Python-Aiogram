from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import aiosqlite

UserRole = Literal["guest", "user", "admin"]


@dataclass(slots=True)
class UserRecord:
    """Represents a Telegram user stored in the database."""

    user_id: int
    username: str | None
    full_name: str
    role: UserRole
    is_banned: bool
    guest_requests_today: int
    last_request_date: str
    created_at: str
    updated_at: str

    @property
    def is_guest(self) -> bool:
        return self.role == "guest"

    @property
    def is_registered(self) -> bool:
        return self.role in ("user", "admin")


@dataclass(slots=True)
class BotStats:
    """Aggregated user statistics for the admin panel."""

    total_users: int
    guest_users: int
    registered_users: int
    banned_users: int


class Database:
    """Async SQLite database repository for users, guest mode, and bot settings."""

    def __init__(self, db_path: str = "data/bot.db") -> None:
        self.db_path = db_path
        self._conn: aiosqlite.Connection | None = None
        self._guest_mode_cache: bool | None = None

    async def connect(self) -> None:
        """Open the SQLite connection and initialize tables."""
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL;")
        await self._conn.execute("PRAGMA foreign_keys=ON;")
        await self._create_tables()

    async def close(self) -> None:
        """Close the SQLite connection."""
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database is not connected. Call `await db.connect()` first.")
        return self._conn

    async def _create_tables(self) -> None:
        await self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'guest',
                is_banned INTEGER NOT NULL DEFAULT 0,
                guest_requests_today INTEGER NOT NULL DEFAULT 0,
                last_request_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        await self.conn.commit()

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _today_str() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    @staticmethod
    def _row_to_user(row: aiosqlite.Row) -> UserRecord:
        return UserRecord(
            user_id=row["user_id"],
            username=row["username"],
            full_name=row["full_name"],
            role=row["role"],
            is_banned=bool(row["is_banned"]),
            guest_requests_today=row["guest_requests_today"],
            last_request_date=row["last_request_date"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def get_or_create_user(
        self,
        user_id: int,
        username: str | None,
        full_name: str,
        is_admin: bool = False,
    ) -> UserRecord:
        """Fetch an existing user or create a new one (defaults to 'guest' unless admin)."""
        now = self._now_iso()
        today = self._today_str()

        cursor = await self.conn.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()

        if row is None:
            role: UserRole = "admin" if is_admin else "guest"
            await self.conn.execute(
                """
                INSERT INTO users (
                    user_id, username, full_name, role, is_banned,
                    guest_requests_today, last_request_date, created_at, updated_at
                ) VALUES (?, ?, ?, ?, 0, 0, ?, ?, ?)
                """,
                (user_id, username, full_name, role, today, now, now),
            )
            await self.conn.commit()
            return UserRecord(
                user_id=user_id,
                username=username,
                full_name=full_name,
                role=role,
                is_banned=False,
                guest_requests_today=0,
                last_request_date=today,
                created_at=now,
                updated_at=now,
            )

        # Reset daily guest counter if a new UTC day started
        requests_today = row["guest_requests_today"]
        last_date = row["last_request_date"]
        if last_date != today:
            requests_today = 0
            last_date = today

        new_role: UserRole = "admin" if is_admin else row["role"]
        needs_update = (
            row["username"] != username
            or row["full_name"] != full_name
            or row["role"] != new_role
            or row["last_request_date"] != last_date
        )

        updated_at = row["updated_at"]
        if needs_update:
            updated_at = now
            await self.conn.execute(
                """
                UPDATE users
                SET username = ?, full_name = ?, role = ?,
                    guest_requests_today = ?, last_request_date = ?, updated_at = ?
                WHERE user_id = ?
                """,
                (username, full_name, new_role, requests_today, last_date, now, user_id),
            )
            await self.conn.commit()

        return UserRecord(
            user_id=user_id,
            username=username,
            full_name=full_name,
            role=new_role,
            is_banned=bool(row["is_banned"]),
            guest_requests_today=requests_today,
            last_request_date=last_date,
            created_at=row["created_at"],
            updated_at=updated_at,
        )

    async def set_user_role(self, user_id: int, role: UserRole) -> None:
        """Update a user's role ('guest', 'user', or 'admin')."""
        await self.conn.execute(
            "UPDATE users SET role = ?, updated_at = ? WHERE user_id = ?",
            (role, self._now_iso(), user_id),
        )
        await self.conn.commit()

    async def increment_guest_requests(self, user_id: int) -> int:
        """Increment today's guest request count and return the updated count."""
        today = self._today_str()
        cursor = await self.conn.execute(
            "SELECT guest_requests_today, last_request_date FROM users WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return 0

        count = 1 if row["last_request_date"] != today else row["guest_requests_today"] + 1
        await self.conn.execute(
            """
            UPDATE users
            SET guest_requests_today = ?, last_request_date = ?, updated_at = ?
            WHERE user_id = ?
            """,
            (count, today, self._now_iso(), user_id),
        )
        await self.conn.commit()
        return count

    async def get_setting(self, key: str, default: str | None = None) -> str | None:
        cursor = await self.conn.execute(
            "SELECT value FROM bot_settings WHERE key = ?",
            (key,),
        )
        row = await cursor.fetchone()
        return row["value"] if row is not None else default

    async def set_setting(self, key: str, value: str) -> None:
        await self.conn.execute(
            """
            INSERT INTO bot_settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
        await self.conn.commit()

    async def is_guest_mode_enabled(self, default: bool = True) -> bool:
        if self._guest_mode_cache is not None:
            return self._guest_mode_cache
        raw = await self.get_setting("guest_mode_enabled")
        enabled = default if raw is None else raw.lower() in ("1", "true", "yes", "on")
        self._guest_mode_cache = enabled
        return enabled

    async def set_guest_mode_enabled(self, enabled: bool) -> None:
        self._guest_mode_cache = enabled
        await self.set_setting("guest_mode_enabled", "true" if enabled else "false")

    async def get_stats(self) -> BotStats:
        cursor = await self.conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN role = 'guest' THEN 1 ELSE 0 END) AS guests,
                SUM(CASE WHEN role IN ('user', 'admin') THEN 1 ELSE 0 END) AS registered,
                SUM(CASE WHEN is_banned = 1 THEN 1 ELSE 0 END) AS banned
            FROM users
            """
        )
        row = await cursor.fetchone()
        return BotStats(
            total_users=row["total"] or 0,
            guest_users=row["guests"] or 0,
            registered_users=row["registered"] or 0,
            banned_users=row["banned"] or 0,
        )
