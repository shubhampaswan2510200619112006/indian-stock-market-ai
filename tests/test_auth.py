"""
Unit Tests for User Authentication, Password Hashing, and Account Persistence.
"""

import pytest
import shutil
from pathlib import Path
from src.auth.service import AuthService


@pytest.fixture
def temp_auth_service(tmp_path):
    db_file = tmp_path / "test_users.db"
    return AuthService(db_path=str(db_file))


def test_user_registration_success(temp_auth_service):
    success, msg, user = temp_auth_service.register(
        username="rahultrader",
        email="rahul@example.com",
        password="SecurePassword123!",
        full_name="Rahul Sharma",
        starting_capital=500000.0,
    )
    assert success is True
    assert user is not None
    assert user.username == "rahultrader"
    assert user.email == "rahul@example.com"
    assert user.starting_capital == 500000.0
    assert user.id.startswith("USR-")


def test_user_registration_duplicate_username_and_email(temp_auth_service):
    # First registration
    temp_auth_service.register(
        username="trader1",
        email="trader1@example.com",
        password="Password123!",
        full_name="Trader One",
    )

    # Duplicate username
    success, msg, user = temp_auth_service.register(
        username="trader1",
        email="different@example.com",
        password="Password123!",
        full_name="Duplicate User",
    )
    assert success is False
    assert "already taken" in msg.lower()

    # Duplicate email
    success, msg, user = temp_auth_service.register(
        username="different_user",
        email="trader1@example.com",
        password="Password123!",
        full_name="Duplicate Email",
    )
    assert success is False
    assert "already registered" in msg.lower()


def test_user_login_success_and_failure(temp_auth_service):
    temp_auth_service.register(
        username="anitasharma",
        email="anita@example.com",
        password="CorrectPassword123!",
        full_name="Anita Sharma",
    )

    # Login by username
    ok_user, _, user_obj = temp_auth_service.login("anitasharma", "CorrectPassword123!")
    assert ok_user is True
    assert user_obj.full_name == "Anita Sharma"

    # Login by email
    ok_email, _, user_obj = temp_auth_service.login("anita@example.com", "CorrectPassword123!")
    assert ok_email is True
    assert user_obj.username == "anitasharma"

    # Invalid password
    fail_pwd, msg, _ = temp_auth_service.login("anitasharma", "WrongPassword!")
    assert fail_pwd is False
    assert "invalid" in msg.lower()

    # Non-existent user
    fail_none, _, _ = temp_auth_service.login("nobody", "anypassword")
    assert fail_none is False
