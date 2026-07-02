import pytest

from app.models.Document import Document
from app.models.Resume import Resume


# ─── Document base class ─────────────────────────────────────────────────


def test_document_save_in_db_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        Document.save_in_db()


def test_resume_extends_document():
    assert issubclass(Resume, Document)


# ─── Resume class variables ──────────────────────────────────────────────


def test_resume_class_variables():
    assert Resume._table == "resume"
    assert Resume._id_field == "resume_id"
    assert Resume._upload_dir == "uploads/resumes"
    assert Resume._allowed_extensions == {"pdf"}
    assert Resume._columns == ["resume_id", "student_id", "file", "verified"]


def test_resume_inherited_fields():
    r = Resume(resume_id=1, student_id="S123", file="/path", verified=True)
    assert r.resume_id == 1
    assert r.student_id == "S123"
    assert r.file == "/path"
    assert r.verified is True


# ─── _row_to_instance ────────────────────────────────────────────────────


def test_resume_row_to_instance():
    row = (1, "TP0112233", "/path/to/resume.pdf", False)
    resume = Resume._row_to_instance(row)
    assert resume.resume_id == 1
    assert resume.student_id == "TP0112233"
    assert resume.file == "/path/to/resume.pdf"
    assert resume.verified is False


def test_resume_row_to_instance_with_true():
    row = (5, "TP0999999", "/another/path.pdf", True)
    resume = Resume._row_to_instance(row)
    assert resume.resume_id == 5
    assert resume.student_id == "TP0999999"
    assert resume.file == "/another/path.pdf"
    assert resume.verified is True


# ─── get_by_id ────────────────────────────────────────────────────────────


def test_resume_get_by_id_found(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[(1, "TP0112233", "/path/to/resume.pdf", False)],
    )
    mocker.patch(
        "app.dependencies.database_connector.create_connection",
        return_value=None,
    )

    resume = Resume.get_by_id(1)
    assert resume is not None
    assert resume.resume_id == 1
    assert resume.student_id == "TP0112233"
    assert resume.file == "/path/to/resume.pdf"
    assert resume.verified is False


def test_resume_get_by_id_not_found(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[],
    )
    mocker.patch(
        "app.dependencies.database_connector.create_connection",
        return_value=None,
    )

    resume = Resume.get_by_id(999)
    assert resume is None


# ─── get_by_student ──────────────────────────────────────────────────────


def test_resume_get_by_student_found(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[
            (2, "TP0112233", "/path/to/second.pdf", False),
            (1, "TP0112233", "/path/to/first.pdf", True),
        ],
    )
    mocker.patch(
        "app.dependencies.database_connector.create_connection",
        return_value=None,
    )

    resumes = Resume.get_by_student("TP0112233")
    assert len(resumes) == 2
    assert resumes[0].resume_id == 2
    assert resumes[0].verified is False
    assert resumes[1].resume_id == 1
    assert resumes[1].verified is True


def test_resume_get_by_student_empty(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[],
    )
    mocker.patch(
        "app.dependencies.database_connector.create_connection",
        return_value=None,
    )

    resumes = Resume.get_by_student("TP0999999")
    assert resumes == []


# ─── approve ──────────────────────────────────────────────────────────────


def test_resume_approve(mocker):
    mock_write = mocker.patch("app.dependencies.database_connector.execute_write")
    mocker.patch(
        "app.dependencies.database_connector.create_connection",
        return_value=None,
    )

    Resume.approve(3)

    mock_write.assert_called_once()
    call_query = mock_write.call_args[0][1]
    assert "UPDATE resume" in call_query
    assert "verified = true" in call_query
    assert "resume_id = 3" in call_query


# ─── save_in_db ─────────────────────────────────────────────────────────


def test_resume_save_in_db(mocker):
    mock_write = mocker.patch("app.dependencies.database_connector.execute_write")
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[(7,)],
    )
    mocker.patch(
        "app.dependencies.database_connector.create_connection",
        return_value=None,
    )

    resume_id = Resume.save_in_db("TP0112233", "/path/to/resume.pdf")

    assert resume_id == 7
    mock_write.assert_called_once()
    call_query = mock_write.call_args[0][1]
    assert "INSERT INTO resume" in call_query
    assert "TP0112233" in call_query
    assert "/path/to/resume.pdf" in call_query


# ─── upload_in_storage ──────────────────────────────────────────────────


def test_resume_upload_in_storage(mocker):
    mock_makedirs = mocker.patch("os.makedirs")
    mock_abspath = mocker.patch("os.path.abspath", return_value="/abs/path/to/file.pdf")
    mock_open = mocker.patch("builtins.open", mocker.mock_open())

    result = Resume.upload_in_storage("TP0112233", "my_resume.pdf", b"%PDF-1.4 content")

    assert result == "/abs/path/to/file.pdf"
    mock_makedirs.assert_called_once_with("uploads/resumes", exist_ok=True)
    mock_open.assert_called_once()
    handle = mock_open()
    handle.write.assert_called_once_with(b"%PDF-1.4 content")


# ─── get_pending_by_mentor ──────────────────────────────────────────────


def test_resume_get_pending_by_mentor_found(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[
            (1, "TP0112233", "/path/to/resume.pdf", False, "John Doe"),
            (2, "TP0112234", "/path/to/other.pdf", False, "Jane Smith"),
        ],
    )
    mocker.patch(
        "app.dependencies.database_connector.create_connection",
        return_value=None,
    )

    pending = Resume.get_pending_by_mentor(42)

    assert len(pending) == 2
    assert pending[0] == {
        "resume_id": 1,
        "student_id": "TP0112233",
        "file": "/path/to/resume.pdf",
        "verified": False,
        "student_name": "John Doe",
    }
    assert pending[1] == {
        "resume_id": 2,
        "student_id": "TP0112234",
        "file": "/path/to/other.pdf",
        "verified": False,
        "student_name": "Jane Smith",
    }


def test_resume_get_pending_by_mentor_empty(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[],
    )
    mocker.patch(
        "app.dependencies.database_connector.create_connection",
        return_value=None,
    )

    pending = Resume.get_pending_by_mentor(99)
    assert pending == []
