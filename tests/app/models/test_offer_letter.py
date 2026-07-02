from app.models.Document import Document
from app.models.OfferLetter import OfferLetter


# ─── Basis ───────────────────────────────────────────────────────────────


def test_offer_letter_extends_document():
    assert issubclass(OfferLetter, Document)


def test_offer_letter_class_variables():
    assert OfferLetter._table == "offer_letter"
    assert OfferLetter._id_field == "offer_letter_id"
    assert OfferLetter._upload_dir == "uploads/offer_letters"
    assert OfferLetter._allowed_extensions == {"pdf", "png", "jpg", "jpeg"}
    assert OfferLetter._columns == [
        "offer_letter_id", "application_id", "student_id", "file", "verified",
    ]


def test_offer_letter_inherited_fields():
    ol = OfferLetter(
        offer_letter_id=1, application_id=10,
        student_id="S123", file="/path", verified=True,
    )
    assert ol.offer_letter_id == 1
    assert ol.application_id == 10
    assert ol.student_id == "S123"
    assert ol.file == "/path"
    assert ol.verified is True


# ─── _row_to_instance ────────────────────────────────────────────────────


def test_offer_letter_row_to_instance():
    row = (1, 10, "TP0112233", "/path/to/offer.pdf", False)
    ol = OfferLetter._row_to_instance(row)
    assert ol.offer_letter_id == 1
    assert ol.application_id == 10
    assert ol.student_id == "TP0112233"
    assert ol.file == "/path/to/offer.pdf"
    assert ol.verified is False


# ─── get_by_id ────────────────────────────────────────────────────────────


def test_offer_letter_get_by_id_found(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[(1, 10, "TP0112233", "/path/to/offer.pdf", False)],
    )
    mocker.patch(
        "app.dependencies.database_connector.create_connection",
        return_value=None,
    )

    ol = OfferLetter.get_by_id(1)
    assert ol is not None
    assert ol.offer_letter_id == 1
    assert ol.application_id == 10


def test_offer_letter_get_by_id_not_found(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[],
    )
    mocker.patch(
        "app.dependencies.database_connector.create_connection",
        return_value=None,
    )

    ol = OfferLetter.get_by_id(999)
    assert ol is None


# ─── get_by_student ──────────────────────────────────────────────────────


def test_offer_letter_get_by_student_found(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[
            (2, 20, "TP0112233", "/path/to/second.pdf", False),
            (1, 10, "TP0112233", "/path/to/first.pdf", True),
        ],
    )
    mocker.patch(
        "app.dependencies.database_connector.create_connection",
        return_value=None,
    )

    results = OfferLetter.get_by_student("TP0112233")
    assert len(results) == 2
    assert results[0].offer_letter_id == 2
    assert results[1].offer_letter_id == 1


def test_offer_letter_get_by_student_empty(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[],
    )
    mocker.patch(
        "app.dependencies.database_connector.create_connection",
        return_value=None,
    )

    results = OfferLetter.get_by_student("TP0999999")
    assert results == []


# ─── approve ──────────────────────────────────────────────────────────────


def test_offer_letter_approve(mocker):
    mock_write = mocker.patch("app.dependencies.database_connector.execute_write")
    mocker.patch(
        "app.dependencies.database_connector.create_connection",
        return_value=None,
    )

    OfferLetter.approve(3)

    mock_write.assert_called_once()
    call_query = mock_write.call_args[0][1]
    assert "UPDATE offer_letter" in call_query
    assert "verified = true" in call_query
    assert "offer_letter_id = 3" in call_query


# ─── save_in_db ─────────────────────────────────────────────────────────


def test_offer_letter_save_in_db(mocker):
    mock_write = mocker.patch("app.dependencies.database_connector.execute_write")
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[(7,)],
    )
    mocker.patch(
        "app.dependencies.database_connector.create_connection",
        return_value=None,
    )

    ol_id = OfferLetter.save_in_db(10, "TP0112233", "/path/to/offer.pdf")

    assert ol_id == 7
    mock_write.assert_called_once()
    call_query = mock_write.call_args[0][1]
    assert "INSERT INTO offer_letter" in call_query
    assert "10" in call_query
    assert "TP0112233" in call_query
    assert "/path/to/offer.pdf" in call_query


# ─── upload_in_storage ──────────────────────────────────────────────────


def test_offer_letter_upload_in_storage(mocker):
    mock_makedirs = mocker.patch("os.makedirs")
    mocker.patch("os.path.abspath", return_value="/abs/path/to/offer.pdf")
    mock_open = mocker.patch("builtins.open", mocker.mock_open())

    result = OfferLetter.upload_in_storage("TP0112233", "offer.pdf", b"%PDF-1.4 content")

    assert result == "/abs/path/to/offer.pdf"
    mock_makedirs.assert_called_once_with("uploads/offer_letters", exist_ok=True)
    handle = mock_open()
    handle.write.assert_called_once_with(b"%PDF-1.4 content")


# ─── get_pending_by_mentor ──────────────────────────────────────────────


def test_offer_letter_get_pending_by_mentor_found(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[
            (1, 10, "TP0112233", "/path/to/offer.pdf", False, "John Doe", "Software Engineer Intern"),
            (2, 20, "TP0112234", "/path/to/other.pdf", False, "Jane Smith", "Data Analyst"),
        ],
    )
    mocker.patch(
        "app.dependencies.database_connector.create_connection",
        return_value=None,
    )

    pending = OfferLetter.get_pending_by_mentor(42)

    assert len(pending) == 2
    assert pending[0] == {
        "offer_letter_id": 1,
        "application_id": 10,
        "student_id": "TP0112233",
        "file": "/path/to/offer.pdf",
        "verified": False,
        "student_name": "John Doe",
        "opportunity_title": "Software Engineer Intern",
    }
    assert pending[1] == {
        "offer_letter_id": 2,
        "application_id": 20,
        "student_id": "TP0112234",
        "file": "/path/to/other.pdf",
        "verified": False,
        "student_name": "Jane Smith",
        "opportunity_title": "Data Analyst",
    }


def test_offer_letter_get_pending_by_mentor_empty(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[],
    )
    mocker.patch(
        "app.dependencies.database_connector.create_connection",
        return_value=None,
    )

    pending = OfferLetter.get_pending_by_mentor(99)
    assert pending == []
