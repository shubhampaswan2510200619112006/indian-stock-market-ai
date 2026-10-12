"""
User Authentication & Trader Account Management Service.

Provides secure registration, authentication, password hashing (PBKDF2-HMAC-SHA256),
and per-user data state isolation for Indian Stock Market AI.
"""

from __future__ import annotations

import hashlib
import re
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from pydantic import BaseModel, Field


class UserAccount(BaseModel):
    """User account model."""
    id: str
    username: str
    email: str
    full_name: str
    starting_capital: float = 1_000_000.0
    created_at: str
    last_login: Optional[str] = None


class AuthService:
    """Manages user persistence, passwords, and user-specific workspace directories."""

    def __init__(self, db_path: str = "data/users.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Create users table if it does not exist."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    starting_capital REAL DEFAULT 1000000.0,
                    created_at TEXT NOT NULL,
                    last_login TEXT
                )
                """
            )
            conn.commit()

    def _hash_password(self, password: str, salt: str) -> str:
        """Computes PBKDF2-HMAC-SHA256 hash."""
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            iterations=100_000,
        ).hex()

    def register(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str,
        starting_capital: float = 1_000_000.0,
    ) -> Tuple[bool, str, Optional[UserAccount]]:
        """
        Registers a new user account.
        Validates email format, username uniqueness, and password strength.
        """
        username = username.strip().lower()
        email = email.strip().lower()
        full_name = full_name.strip()

        if len(username) < 3:
            return False, "Username must be at least 3 characters long.", None
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            return False, "Please enter a valid email address.", None
        if len(password) < 6:
            return False, "Password must be at least 6 characters long.", None

        salt = secrets.token_hex(16)
        pwd_hash = self._hash_password(password, salt)
        user_id = f"USR-{secrets.token_hex(6).upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO users (id, username, email, full_name, salt, password_hash, starting_capital, created_at, last_login)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, username, email, full_name, salt, pwd_hash, starting_capital, now_iso, now_iso),
                )
                conn.commit()
        except sqlite3.IntegrityError as e:
            err_msg = str(e).lower()
            if "username" in err_msg:
                return False, f"Username '{username}' is already taken.", None
            if "email" in err_msg:
                return False, f"Email '{email}' is already registered.", None
            return False, "Account with this username or email already exists.", None

        # Create isolated user directory
        user_state_dir = Path("data/user_state") / user_id
        user_state_dir.mkdir(parents=True, exist_ok=True)

        user = UserAccount(
            id=user_id,
            username=username,
            email=email,
            full_name=full_name,
            starting_capital=starting_capital,
            created_at=now_iso,
            last_login=now_iso,
        )
        return True, "Account registered successfully!", user

    def login(self, username_or_email: str, password: str) -> Tuple[bool, str, Optional[UserAccount]]:
        """
        Authenticates a user by username or email and password.
        """
        ident = username_or_email.strip().lower()
        if not ident or not password:
            return False, "Please enter both credentials.", None

        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM users WHERE username = ? OR email = ?",
                (ident, ident),
            )
            row = cursor.fetchone()

        if not row:
            return False, "Invalid username or password.", None

        salt = row["salt"]
        stored_hash = row["password_hash"]
        computed_hash = self._hash_password(password, salt)

        if not secrets.compare_digest(stored_hash, computed_hash):
            return False, "Invalid username or password.", None

        # Update last login timestamp
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute("UPDATE users SET last_login = ? WHERE id = ?", (now_iso, row["id"]))
            conn.commit()

        user = UserAccount(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            full_name=row["full_name"],
            starting_capital=row["starting_capital"],
            created_at=row["created_at"],
            last_login=now_iso,
        )
        return True, f"Welcome back, {user.full_name}!", user

    def get_user_by_id(self, user_id: str) -> Optional[UserAccount]:
        """Retrieves user account by user ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
        if not row:
            return None
        return UserAccount(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            full_name=row["full_name"],
            starting_capital=row["starting_capital"],
            created_at=row["created_at"],
            last_login=row["last_login"],
        )
