from fastapi.testclient import TestClient
from app.dependencies import auth
from app.models.Role import Role
from app.models.User import User
from app.main import app

client = TestClient(app)

mock_student_user = User(
    user_id=1,
    fullname="John Doe",
    email="john@example.com",
    role=Role.student,
)

mock_mentor_user = User(
    user_id=2,
    fullname="Jane Smith",
    email="jane@example.com",
    role=Role.universityMentor,
)


def _override_user(user):
    async def override():
        return user

    return override


def test_upload_resume_success(mocker):
    app.dependency_overrides[auth.get_current_user] = _override_user(mock_student_user)
    try:
        mocker.patch("os.makedirs")
        mocker.patch("os.path.abspath", return_value="/abs/path/to/resume.pdf")
        mocker.patch("builtins.open", mocker.mock_open())
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            side_effect=[
                [(2, "software engineer", "TP0112233", 999, "none")],
                [("Mentor One", "mentor@example.com", "universityMentor", 999)],
            ],
        )
        mocker.patch("app.dependencies.database_connector.execute_write")
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.post(
            "/resume/upload",
            files={"file": ("resume.pdf", b"%PDF-1.4 fake content", "application/pdf")},
        )

        assert response.status_code == 200
        assert response.json() == {"file_path": "/abs/path/to/resume.pdf"}
    finally:
        app.dependency_overrides.clear()


def test_upload_resume_rejects_non_pdf_content_type(mocker):
    app.dependency_overrides[auth.get_current_user] = _override_user(mock_student_user)
    try:
        response = client.post(
            "/resume/upload",
            files={"file": ("resume.txt", b"not a pdf", "text/plain")},
        )
        assert response.status_code == 400
        assert response.json() == {"detail": "only PDF files are accepted"}
    finally:
        app.dependency_overrides.clear()


def test_upload_resume_rejects_bad_extension(mocker):
    app.dependency_overrides[auth.get_current_user] = _override_user(mock_student_user)
    try:
        response = client.post(
            "/resume/upload",
            files={"file": ("resume.exe", b"not a pdf", "application/pdf")},
        )
        assert response.status_code == 400
        assert response.json() == {"detail": "only PDF files are accepted"}
    finally:
        app.dependency_overrides.clear()


def test_upload_resume_rejects_large_file(mocker):
    app.dependency_overrides[auth.get_current_user] = _override_user(mock_student_user)
    try:
        large_content = b"x" * (5 * 1024 * 1024 + 1)
        response = client.post(
            "/resume/upload",
            files={"file": ("resume.pdf", large_content, "application/pdf")},
        )
        assert response.status_code == 413
        assert response.json() == {"detail": "file exceeds 5MB limit"}
    finally:
        app.dependency_overrides.clear()


def test_upload_resume_not_authenticated():
    response = client.post(
        "/resume/upload",
        files={"file": ("resume.pdf", b"%PDF-1.4 content", "application/pdf")},
    )
    assert response.status_code == 401


def test_upload_resume_not_student(mocker):
    app.dependency_overrides[auth.get_current_user] = _override_user(mock_mentor_user)
    try:
        response = client.post(
            "/resume/upload",
            files={"file": ("resume.pdf", b"%PDF-1.4 content", "application/pdf")},
        )
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


# ─── GET /resume ─────────────────────────────────────────────────────────


def test_get_resume_own_student(mocker):
    app.dependency_overrides[auth.get_current_user] = _override_user(mock_student_user)
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            side_effect=[
                [(2, "software engineer", "TP0112233", 999, "none")],
                [("Mentor One", "mentor@example.com", "universityMentor", 999)],
                [
                    (1, "TP0112233", "/path/to/resume.pdf", False),
                    (2, "TP0112233", "/path/to/second.pdf", False),
                ],
            ],
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.get("/resume")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 2
        assert body[0] == {
            "resume_id": 1,
            "student_id": "TP0112233",
            "file": "/path/to/resume.pdf",
            "verified": False,
        }
        assert body[1] == {
            "resume_id": 2,
            "student_id": "TP0112233",
            "file": "/path/to/second.pdf",
            "verified": False,
        }

    finally:
        app.dependency_overrides.clear()


def test_get_resume_student_empty(mocker):
    app.dependency_overrides[auth.get_current_user] = _override_user(mock_student_user)
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            side_effect=[
                [(2, "software engineer", "TP0112233", 999, "none")],
                [("Mentor One", "mentor@example.com", "universityMentor", 999)],
                [],
            ],
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.get("/resume")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_get_resume_student_cannot_lookup_other(mocker):
    app.dependency_overrides[auth.get_current_user] = _override_user(mock_student_user)
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            side_effect=[
                [(2, "software engineer", "TP0112233", 999, "none")],
                [("Mentor One", "mentor@example.com", "universityMentor", 999)],
            ],
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.get("/resume?request_student_id=TP0999999")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_get_resume_mentor_lookup(mocker):
    app.dependency_overrides[auth.get_current_user] = _override_user(mock_mentor_user)

    def mock_execute_read(connection, query):
        if "WHERE student_id = 'TP0112233'" in query:
            return [(1, "TP0112233", "/path/to/resume.pdf", False)]
        return []

    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            side_effect=mock_execute_read,
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.get("/resume?request_student_id=TP0112233")
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0] == {
            "resume_id": 1,
            "student_id": "TP0112233",
            "file": "/path/to/resume.pdf",
            "verified": False,
        }
    finally:
        app.dependency_overrides.clear()


def test_get_resume_mentor_missing_param(mocker):
    app.dependency_overrides[auth.get_current_user] = _override_user(mock_mentor_user)
    try:
        response = client.get("/resume")
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_get_resume_not_authenticated():
    response = client.get("/resume")
    assert response.status_code == 401


# ─── GET /resume/download/{resume_id} ──────────────────────────────────


def test_download_resume_own_student(mocker, tmp_path):
    pdf_path = tmp_path / "resume.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test content")

    app.dependency_overrides[auth.get_current_user] = _override_user(
        mock_student_user
    )
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            side_effect=[
                [(1, "TP0112233", str(pdf_path), False)],
                [(2, "software engineer", "TP0112233", 999, "none")],
                [("Mentor One", "mentor@example.com", "universityMentor", 999)],
            ],
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.get("/resume/download/1")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
    finally:
        app.dependency_overrides.clear()


def test_download_resume_other_student_forbidden(mocker):
    app.dependency_overrides[auth.get_current_user] = _override_user(
        mock_student_user
    )
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            side_effect=[
                [(1, "TP0999999", "/path/to/other.pdf", False)],
                [(2, "software engineer", "TP0112233", 999, "none")],
                [("Mentor One", "mentor@example.com", "universityMentor", 999)],
            ],
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.get("/resume/download/1")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_download_resume_mentor_lookup(mocker, tmp_path):
    pdf_path = tmp_path / "resume.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test content")

    app.dependency_overrides[auth.get_current_user] = _override_user(
        mock_mentor_user
    )
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            return_value=[(1, "TP0112233", str(pdf_path), False)],
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.get("/resume/download/1")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
    finally:
        app.dependency_overrides.clear()


def test_download_resume_not_found(mocker):
    app.dependency_overrides[auth.get_current_user] = _override_user(
        mock_student_user
    )
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            return_value=[],
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.get("/resume/download/999")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_download_resume_not_authenticated():
    response = client.get("/resume/download/1")
    assert response.status_code == 401
