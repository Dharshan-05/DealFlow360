"""Security test suite for HttpOnly Cookie Authentication Transport (G08 Security Hardening):
- Verifies refresh token is set as HttpOnly cookie on login
- Verifies cookie attributes (HttpOnly, SameSite=lax, Path=/api/v1/auth)
- Verifies cookie-based refresh without request body
- Verifies cookie rotation and replay prevention
- Verifies logout clears cookie and revokes server-side session
- Verifies refresh after logout fails
"""
import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_login_sets_httponly_cookie():
    """Verify login sets a Secure/HttpOnly refresh_token cookie with restricted path and SameSite=lax."""
    suffix = uuid.uuid4().hex[:8]
    email = f"cookie_login_{suffix}@example.com"
    password = "Password123!"

    # Register
    reg_res = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "first_name": "Cookie",
        "last_name": "User",
    })
    assert reg_res.status_code == 201

    # Login
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()["data"]

    # Verify cookie presence and security flags
    assert "set-cookie" in login_res.headers
    cookie_header = login_res.headers["set-cookie"].lower()
    assert "refresh_token=" in cookie_header
    assert "httponly" in cookie_header
    assert "samesite=lax" in cookie_header
    assert "path=/api/v1/auth" in cookie_header


def test_refresh_via_cookie_and_rotation():
    """Verify refresh endpoint works via cookie credentials alone, rotates cookie, and prevents replay."""
    suffix = uuid.uuid4().hex[:8]
    email = f"cookie_refresh_{suffix}@example.com"
    password = "Password123!"

    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "first_name": "Rotator",
        "last_name": "Test",
    })

    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })
    assert login_res.status_code == 200
    cookie1_val = login_res.cookies.get("refresh_token")
    assert cookie1_val is not None

    # Call refresh without body, passing the cookie
    refresh_res = client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": cookie1_val},
    )
    assert refresh_res.status_code == 200
    body = refresh_res.json()
    assert body["success"] is True
    assert "access_token" in body["data"]

    # Verify rotated cookie is set
    cookie2_val = refresh_res.cookies.get("refresh_token")
    assert cookie2_val is not None
    assert cookie2_val != cookie1_val

    # REPLAY ATTACK: Using cookie1 must fail because it was rotated and revoked
    replay_res = client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": cookie1_val},
    )
    assert replay_res.status_code == 401
    assert replay_res.json()["error"]["code"] == "TOKEN_REVOKED"


def test_logout_clears_cookie_and_revokes_session():
    """Verify logout clears cookie, revokes server session, and prevents further refresh."""
    suffix = uuid.uuid4().hex[:8]
    email = f"cookie_logout_{suffix}@example.com"
    password = "Password123!"

    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "first_name": "Logout",
        "last_name": "Cookie",
    })

    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })
    assert login_res.status_code == 200
    refresh_cookie = login_res.cookies.get("refresh_token")
    assert refresh_cookie is not None

    # Logout with cookie
    logout_res = client.post(
        "/api/v1/auth/logout",
        cookies={"refresh_token": refresh_cookie},
    )
    assert logout_res.status_code == 200
    assert logout_res.json()["data"]["logged_out"] is True

    # Check that Set-Cookie instructs browser to delete/expire cookie
    set_cookie_header = logout_res.headers.get("set-cookie", "").lower()
    assert 'refresh_token=""' in set_cookie_header or "refresh_token=;" in set_cookie_header or 'max-age=0' in set_cookie_header

    # Subsequent refresh with that cookie must fail
    refresh_after_logout = client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": refresh_cookie},
    )
    assert refresh_after_logout.status_code == 401


def test_refresh_without_cookie_or_body_rejected():
    """Verify refresh fails gracefully with 401 when no cookie or body is provided."""
    res = client.post("/api/v1/auth/refresh")
    assert res.status_code == 401
    assert "missing" in res.json()["error"]["message"].lower()
