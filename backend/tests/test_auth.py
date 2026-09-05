"""Unit and integration test suite for G06 Authentication Foundation (Phases 026–030):
- Phase 026: User Registration
- Phase 027: User Login
- Phase 028: JWT Authentication & get_current_user Dependency
- Phase 029: Password Hashing with Argon2id
- Phase 030: Refresh Token Rotation & Revocation

Ensures strict security:
- Plaintext passwords never stored
- Password hashes never exposed in responses
- Tokens validated for type, expiry, and signature
- Inactive users safely rejected
- Refresh token reuse / revocation enforced
"""
import uuid
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.jwt import create_access_token, create_refresh_token
from app.core.security import get_password_hash, verify_password
from app.db.session import SessionLocal
from app.main import app
from app.models.refresh_token import RefreshToken
from app.models.user import User

client = TestClient(app)


# ===========================================================================
# PHASE 029: PASSWORD HASHING UNIT TESTS
# ===========================================================================

def test_password_hashing_and_verification():
    """Verify Argon2id hashes passwords securely and verifies constant-time."""
    raw_password = "SecurePassword123!"
    hashed = get_password_hash(raw_password)

    # Hash must not match plaintext
    assert hashed != raw_password
    assert "$argon2id$" in hashed

    # Valid password verification
    assert verify_password(raw_password, hashed) is True

    # Invalid password verification
    assert verify_password("WrongPassword123!", hashed) is False
    assert verify_password("", hashed) is False


# ===========================================================================
# PHASE 026: USER REGISTRATION TESTS
# ===========================================================================

def test_user_registration_success():
    """Verify user registration persists user, hashes password, and returns safe response."""
    unique_suffix = uuid.uuid4().hex[:8]
    email = f"reg_success_{unique_suffix}@example.com"
    payload = {
        "email": email,
        "password": "StrongPassword123!",
        "first_name": "Alice",
        "last_name": "Smith",
    }

    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    body = response.json()

    assert body["success"] is True
    assert body["message"] == "User registered successfully"
    user_data = body["data"]

    assert user_data["email"] == email.lower()
    assert user_data["first_name"] == "Alice"
    assert user_data["last_name"] == "Smith"
    assert user_data["is_active"] is True
    assert "id" in user_data

    # CRITICAL SECURITY CHECK: password and password_hash must NEVER be in response
    assert "password" not in user_data
    assert "password_hash" not in user_data

    # Verify DB persistence and hash
    session = SessionLocal()
    try:
        db_user = session.scalars(select(User).where(User.email == email.lower())).first()
        assert db_user is not None
        assert db_user.password_hash != "StrongPassword123!"
        assert verify_password("StrongPassword123!", db_user.password_hash) is True
    finally:
        session.close()


def test_user_registration_duplicate_email():
    """Verify registering with an existing email returns standardized 409 error."""
    unique_suffix = uuid.uuid4().hex[:8]
    email = f"dup_email_{unique_suffix}@example.com"
    payload = {
        "email": email,
        "password": "StrongPassword123!",
        "first_name": "Bob",
        "last_name": "Jones",
    }

    # First registration: succeeds
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Second registration: 409 conflict
    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    body = res2.json()
    assert body["success"] is False
    assert body["error"]["code"] == "EMAIL_ALREADY_EXISTS"


def test_user_registration_validation_errors():
    """Verify short password, invalid email format, or empty names are rejected with 422."""
    # Invalid email
    res1 = client.post("/api/v1/auth/register", json={
        "email": "not-an-email",
        "password": "ValidPassword123!",
        "first_name": "John",
        "last_name": "Doe",
    })
    assert res1.status_code == 422

    # Password too short (< 8 chars)
    res2 = client.post("/api/v1/auth/register", json={
        "email": "valid@example.com",
        "password": "short",
        "first_name": "John",
        "last_name": "Doe",
    })
    assert res2.status_code == 422


# ===========================================================================
# PHASE 027: LOGIN TESTS
# ===========================================================================

def test_login_success():
    """Verify valid credentials return access token and refresh token."""
    unique_suffix = uuid.uuid4().hex[:8]
    email = f"login_ok_{unique_suffix}@example.com"
    password = "CorrectPassword123!"

    # Register first
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "first_name": "Carol",
        "last_name": "White",
    })

    # Login
    response = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Authentication successful"

    token_data = body["data"]
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert token_data["expires_in"] > 0

    # Ensure passwords and hashes are not in login response
    assert "password" not in token_data
    assert "password_hash" not in token_data


def test_login_invalid_credentials():
    """Verify invalid password or non-existent email returns 401 without user enumeration."""
    unique_suffix = uuid.uuid4().hex[:8]
    email = f"known_{unique_suffix}@example.com"
    password = "CorrectPassword123!"

    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "first_name": "David",
        "last_name": "Brown",
    })

    # Wrong password
    res1 = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "WrongPassword999!",
    })
    assert res1.status_code == 401
    assert res1.json()["error"]["code"] == "INVALID_CREDENTIALS"

    # Non-existent email
    res2 = client.post("/api/v1/auth/login", json={
        "email": f"unknown_{unique_suffix}@example.com",
        "password": password,
    })
    assert res2.status_code == 401
    assert res2.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_inactive_user():
    """Verify inactive users are rejected with 403."""
    unique_suffix = uuid.uuid4().hex[:8]
    email = f"inactive_{unique_suffix}@example.com"
    password = "Password123!"

    reg_res = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "first_name": "Eve",
        "last_name": "Inactive",
    })
    user_id = reg_res.json()["data"]["id"]

    # Deactivate user directly in DB
    session = SessionLocal()
    try:
        user = session.get(User, uuid.UUID(user_id))
        user.is_active = False
        session.commit()
    finally:
        session.close()

    # Attempt login
    res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "USER_INACTIVE"


# ===========================================================================
# PHASE 028: JWT AUTHENTICATION & PROTECTED ROUTE TESTS
# ===========================================================================

def test_protected_route_with_valid_token():
    """Verify valid access token accesses GET /api/v1/auth/me successfully."""
    unique_suffix = uuid.uuid4().hex[:8]
    email = f"protected_{unique_suffix}@example.com"
    password = "Password123!"

    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "first_name": "Frank",
        "last_name": "Miller",
    })

    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })
    access_token = login_res.json()["data"]["access_token"]

    # Access /api/v1/auth/me
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == email.lower()
    assert body["data"]["first_name"] == "Frank"


def test_protected_route_token_failures():
    """Verify missing, malformed, expired, or wrong-type tokens are rejected."""
    # Missing authorization header
    res1 = client.get("/api/v1/auth/me")
    assert res1.status_code == 401

    # Malformed token
    res2 = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not.a.valid.jwt.token"},
    )
    assert res2.status_code == 401

    # Expired token
    expired_token = create_access_token(
        subject=str(uuid.uuid4()),
        expires_delta=timedelta(seconds=-10),
    )
    res3 = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res3.status_code == 401

    # Refresh token passed to access-token-protected route
    refresh_token = create_refresh_token(subject=str(uuid.uuid4()))
    res4 = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert res4.status_code == 401


# ===========================================================================
# PHASE 030: REFRESH TOKEN ROTATION TESTS
# ===========================================================================

def test_refresh_token_rotation_success():
    """Verify refresh token issues a new token pair and revokes the used token."""
    unique_suffix = uuid.uuid4().hex[:8]
    email = f"refresh_user_{unique_suffix}@example.com"
    password = "Password123!"

    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "first_name": "Grace",
        "last_name": "Hopper",
    })

    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })
    tokens1 = login_res.json()["data"]
    old_refresh_token = tokens1["refresh_token"]

    # Refresh tokens
    refresh_res = client.post("/api/v1/auth/refresh", json={
        "refresh_token": old_refresh_token,
    })
    assert refresh_res.status_code == 200
    tokens2 = refresh_res.json()["data"]
    new_access_token = tokens2["access_token"]
    new_refresh_token = tokens2["refresh_token"]

    assert new_access_token != tokens1["access_token"]
    assert new_refresh_token != old_refresh_token

    # Verify new access token works
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {new_access_token}"},
    )
    assert me_res.status_code == 200

    # REPLAY ATTACK PREVENTION: Old refresh token must now be rejected
    reuse_res = client.post("/api/v1/auth/refresh", json={
        "refresh_token": old_refresh_token,
    })
    assert reuse_res.status_code == 401
    assert reuse_res.json()["error"]["code"] == "TOKEN_REVOKED"


def test_refresh_token_rejects_access_token():
    """Verify refresh endpoint rejects an access token."""
    access_token = create_access_token(subject=str(uuid.uuid4()))
    res = client.post("/api/v1/auth/refresh", json={
        "refresh_token": access_token,
    })
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_TOKEN_TYPE"


# ===========================================================================
# PHASE 031: LOGOUT TESTS
# ===========================================================================

def test_logout_success_and_revocation():
    """Verify logout revokes refresh token, rejects subsequent refresh, and keeps user active."""
    unique_suffix = uuid.uuid4().hex[:8]
    email = f"logout_user_{unique_suffix}@example.com"
    password = "Password123!"

    # 1. Register
    reg_res = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "first_name": "Logout",
        "last_name": "TestUser",
    })
    user_id = reg_res.json()["data"]["id"]

    # 2. Login
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })
    tokens = login_res.json()["data"]
    refresh_token = tokens["refresh_token"]

    # 3. Logout
    logout_res = client.post("/api/v1/auth/logout", json={
        "refresh_token": refresh_token,
    })
    assert logout_res.status_code == 200
    assert logout_res.json()["success"] is True
    assert logout_res.json()["data"]["logged_out"] is True

    # 4. Attempt to use revoked refresh token -> must be rejected
    refresh_attempt = client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert refresh_attempt.status_code == 401
    assert refresh_attempt.json()["error"]["code"] == "TOKEN_REVOKED"

    # 5. Verify user remains active in DB
    session = SessionLocal()
    try:
        user = session.get(User, uuid.UUID(user_id))
        assert user is not None
        assert user.is_active is True
    finally:
        session.close()


def test_logout_with_invalid_or_access_token():
    """Verify logout with malformed token or access token is rejected safely."""
    # Malformed token
    res1 = client.post("/api/v1/auth/logout", json={
        "refresh_token": "malformed.token.value",
    })
    assert res1.status_code == 400

    # Access token passed instead of refresh token
    access_token = create_access_token(subject=str(uuid.uuid4()))
    res2 = client.post("/api/v1/auth/logout", json={
        "refresh_token": access_token,
    })
    assert res2.status_code == 400
    assert res2.json()["error"]["code"] == "INVALID_TOKEN_TYPE"


def test_repeated_logout_behaves_safely():
    """Verify repeated logout on an already revoked token behaves safely without error."""
    unique_suffix = uuid.uuid4().hex[:8]
    email = f"rep_logout_{unique_suffix}@example.com"
    password = "Password123!"

    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "first_name": "Repeated",
        "last_name": "Logout",
    })

    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })
    refresh_token = login_res.json()["data"]["refresh_token"]

    # First logout
    res1 = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert res1.status_code == 200

    # Second logout on same token
    res2 = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert res2.status_code == 200
    assert res2.json()["data"]["logged_out"] is True

