from fastapi.testclient import TestClient
from app.dependencies import auth
from app.models.Role import Role
from app.models.User import User
from app.main import app

client = TestClient(app)

mock_user = User(
    user_id=100,
    fullname="Test User",
    email="test@example.com",
    role=Role.student,
)


def _override(user):
    async def _fn():
        return user
    return _fn


# ── update email ──────────────────────────────────────────


def test_update_email_success(mocker):
    app.dependency_overrides[auth.get_current_user] = _override(mock_user)
    try:
        mocker.patch(
            "app.models.User.User.verify_password",
            return_value=True,
        )
        mocker.patch(
            "app.models.User.User.get_by_email",
            return_value=None,
        )
        mocker.patch(
            "app.models.User.User.update_email",
            return_value=None,
        )
        mocker.patch(
            "app.models.User.User.getUserData",
            return_value=User(
                user_id=100,
                fullname="Test User",
                email="new@example.com",
                role=Role.student,
            ),
        )

        response = client.patch(
            "/profile",
            json={
                "current_password": "correctpassword",
                "new_email": "new@example.com",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "new@example.com"
    finally:
        app.dependency_overrides.clear()


# ── update password ───────────────────────────────────────


def test_update_password_success(mocker):
    app.dependency_overrides[auth.get_current_user] = _override(mock_user)
    try:
        mocker.patch(
            "app.models.User.User.verify_password",
            return_value=True,
        )
        mocker.patch(
            "app.models.User.User.update_password",
            return_value=None,
        )
        mocker.patch(
            "app.models.User.User.getUserData",
            return_value=mock_user,
        )

        response = client.patch(
            "/profile",
            json={
                "current_password": "correctpassword",
                "new_password": "newpassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
    finally:
        app.dependency_overrides.clear()


# ── update both ───────────────────────────────────────────


def test_update_both_success(mocker):
    app.dependency_overrides[auth.get_current_user] = _override(mock_user)
    try:
        mocker.patch(
            "app.models.User.User.verify_password",
            return_value=True,
        )
        mocker.patch(
            "app.models.User.User.get_by_email",
            return_value=None,
        )
        mocker.patch(
            "app.models.User.User.update_email",
            return_value=None,
        )
        mocker.patch(
            "app.models.User.User.update_password",
            return_value=None,
        )
        mocker.patch(
            "app.models.User.User.getUserData",
            return_value=User(
                user_id=100,
                fullname="Test User",
                email="new@example.com",
                role=Role.student,
            ),
        )

        response = client.patch(
            "/profile",
            json={
                "current_password": "correctpassword",
                "new_email": "new@example.com",
                "new_password": "newpassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "new@example.com"
    finally:
        app.dependency_overrides.clear()


# ── wrong password ────────────────────────────────────────


def test_update_wrong_password(mocker):
    app.dependency_overrides[auth.get_current_user] = _override(mock_user)
    try:
        mocker.patch(
            "app.models.User.User.verify_password",
            return_value=False,
        )

        response = client.patch(
            "/profile",
            json={
                "current_password": "wrongpassword",
                "new_email": "new@example.com",
            },
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "Incorrect password"
    finally:
        app.dependency_overrides.clear()


# ── duplicate email ───────────────────────────────────────


def test_update_duplicate_email(mocker):
    app.dependency_overrides[auth.get_current_user] = _override(mock_user)
    try:
        mocker.patch(
            "app.models.User.User.verify_password",
            return_value=True,
        )
        mocker.patch(
            "app.models.User.User.get_by_email",
            return_value=User(
                user_id=200,
                fullname="Other User",
                email="taken@example.com",
                role=Role.student,
            ),
        )

        response = client.patch(
            "/profile",
            json={
                "current_password": "correctpassword",
                "new_email": "taken@example.com",
            },
        )
        assert response.status_code == 409
        assert response.json()["detail"] == "Email already in use"
    finally:
        app.dependency_overrides.clear()


# ── same email (no conflict) ──────────────────────────────


def test_update_same_email_no_conflict(mocker):
    app.dependency_overrides[auth.get_current_user] = _override(mock_user)
    try:
        mocker.patch(
            "app.models.User.User.verify_password",
            return_value=True,
        )
        mocker.patch(
            "app.models.User.User.get_by_email",
            return_value=mock_user,
        )
        mocker.patch(
            "app.models.User.User.update_email",
            return_value=None,
        )
        mocker.patch(
            "app.models.User.User.getUserData",
            return_value=mock_user,
        )

        response = client.patch(
            "/profile",
            json={
                "current_password": "correctpassword",
                "new_email": "test@example.com",
            },
        )
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


# ── no fields provided ────────────────────────────────────


def test_update_no_fields_provided():
    app.dependency_overrides[auth.get_current_user] = _override(mock_user)
    try:
        response = client.patch(
            "/profile",
            json={"current_password": "password"},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


# ── unauthenticated ───────────────────────────────────────


def test_update_unauthenticated():
    response = client.patch(
        "/profile",
        json={
            "current_password": "password",
            "new_email": "new@example.com",
        },
    )
    assert response.status_code == 401


# ── empty body ────────────────────────────────────────────


def test_update_empty_body():
    app.dependency_overrides[auth.get_current_user] = _override(mock_user)
    try:
        response = client.patch("/profile", json={})
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()
