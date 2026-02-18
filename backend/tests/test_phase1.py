"""
Phase 1 Tests - User Management & Admin Setup

Run with: pytest tests/test_phase1.py -v
"""

import pytest
from httpx import AsyncClient
from fastapi import status

from src.main import backend_app


@pytest.fixture
def test_app():
    return backend_app


@pytest.mark.asyncio
async def test_signup_creates_user_with_default_role(test_app):
    """Test that signup creates a user with 'user' role by default"""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/signup",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["authorizedAccount"]["role"] == "user"
        assert "token" in data["authorizedAccount"]


@pytest.mark.asyncio
async def test_signin_returns_role_in_response(test_app):
    """Test that signin returns role in the response"""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        # First signup
        await client.post(
            "/api/auth/signup",
            json={
                "username": "signintest",
                "email": "signintest@example.com",
                "password": "testpassword123",
            },
        )

        # Then signin
        response = await client.post(
            "/api/auth/signin",
            json={
                "username": "signintest",
                "email": "signintest@example.com",
                "password": "testpassword123",
            },
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert "role" in data["authorizedAccount"]


@pytest.mark.asyncio
async def test_get_current_user_profile(test_app):
    """Test getting current user profile"""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        # Signup and get token
        signup_response = await client.post(
            "/api/auth/signup",
            json={
                "username": "profiletest",
                "email": "profiletest@example.com",
                "password": "testpassword123",
            },
        )
        token = signup_response.json()["authorizedAccount"]["token"]

        # Get profile
        response = await client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "profiletest"
        assert data["email"] == "profiletest@example.com"
        assert data["role"] == "user"


@pytest.mark.asyncio
async def test_update_user_profile(test_app):
    """Test updating user profile"""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        # Signup and get token
        signup_response = await client.post(
            "/api/auth/signup",
            json={
                "username": "updatetest",
                "email": "updatetest@example.com",
                "password": "testpassword123",
            },
        )
        token = signup_response.json()["authorizedAccount"]["token"]

        # Update profile
        response = await client.patch(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "fullName": "Test User",
                "phone": "+1234567890",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["fullName"] == "Test User"
        assert data["phone"] == "+1234567890"


@pytest.mark.asyncio
async def test_admin_access_denied_for_regular_user(test_app):
    """Test that regular users cannot access admin endpoints"""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        # Signup as regular user
        signup_response = await client.post(
            "/api/auth/signup",
            json={
                "username": "regularuser",
                "email": "regular@example.com",
                "password": "testpassword123",
            },
        )
        token = signup_response.json()["authorizedAccount"]["token"]

        # Try to access admin endpoint
        response = await client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_otp_send(test_app):
    """Test sending OTP"""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/otp/send",
            json={
                "email": "otptest@example.com",
                "purpose": "login",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "expiresInSeconds" in data


@pytest.mark.asyncio
async def test_forgot_password(test_app):
    """Test forgot password flow"""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        # First create a user
        await client.post(
            "/api/auth/signup",
            json={
                "username": "forgottest",
                "email": "forgottest@example.com",
                "password": "testpassword123",
            },
        )

        # Request password reset
        response = await client.post(
            "/api/auth/forgot-password",
            json={
                "email": "forgottest@example.com",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data


# Admin tests (require admin user to be seeded first)
@pytest.mark.asyncio
async def test_admin_can_list_users(test_app):
    """Test that admin can list users"""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        # Login as admin (assuming admin is seeded)
        signin_response = await client.post(
            "/api/auth/signin",
            json={
                "username": "admin",
                "email": "admin@zoniq.com",
                "password": "admin123!",
            },
        )

        if signin_response.status_code != status.HTTP_202_ACCEPTED:
            pytest.skip("Admin user not seeded")

        token = signin_response.json()["authorizedAccount"]["token"]

        # List users
        response = await client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "users" in data
        assert "total" in data


@pytest.mark.asyncio
async def test_admin_can_get_stats(test_app):
    """Test that admin can get user stats"""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        # Login as admin
        signin_response = await client.post(
            "/api/auth/signin",
            json={
                "username": "admin",
                "email": "admin@zoniq.com",
                "password": "admin123!",
            },
        )

        if signin_response.status_code != status.HTTP_202_ACCEPTED:
            pytest.skip("Admin user not seeded")

        token = signin_response.json()["authorizedAccount"]["token"]

        # Get stats
        response = await client.get(
            "/api/admin/users/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "totalUsers" in data
        assert "totalAdmins" in data
        assert "blockedUsers" in data


@pytest.mark.asyncio
async def test_admin_can_block_user(test_app):
    """Test that admin can block a user"""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        # Login as admin
        signin_response = await client.post(
            "/api/auth/signin",
            json={
                "username": "admin",
                "email": "admin@zoniq.com",
                "password": "admin123!",
            },
        )

        if signin_response.status_code != status.HTTP_202_ACCEPTED:
            pytest.skip("Admin user not seeded")

        admin_token = signin_response.json()["authorizedAccount"]["token"]

        # Create a user to block
        signup_response = await client.post(
            "/api/auth/signup",
            json={
                "username": "blockme",
                "email": "blockme@example.com",
                "password": "testpassword123",
            },
        )
        user_id = signup_response.json()["id"]

        # Block the user
        response = await client.post(
            f"/api/admin/users/{user_id}/block",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"reason": "Test block"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["isBlocked"] == True
        assert data["blockedReason"] == "Test block"


@pytest.mark.asyncio
async def test_blocked_user_cannot_login(test_app):
    """Test that blocked user cannot login"""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        # Login as admin and block a user first (from previous test)
        signin_response = await client.post(
            "/api/auth/signin",
            json={
                "username": "admin",
                "email": "admin@zoniq.com",
                "password": "admin123!",
            },
        )

        if signin_response.status_code != status.HTTP_202_ACCEPTED:
            pytest.skip("Admin user not seeded")

        admin_token = signin_response.json()["authorizedAccount"]["token"]

        # Create and block a user
        signup_response = await client.post(
            "/api/auth/signup",
            json={
                "username": "blockeduser",
                "email": "blockeduser@example.com",
                "password": "testpassword123",
            },
        )
        user_id = signup_response.json()["id"]

        await client.post(
            f"/api/admin/users/{user_id}/block",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"reason": "Test block"},
        )

        # Try to login as blocked user
        response = await client.post(
            "/api/auth/signin",
            json={
                "username": "blockeduser",
                "email": "blockeduser@example.com",
                "password": "testpassword123",
            },
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
