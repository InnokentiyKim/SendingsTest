from pathlib import Path
from typing import Callable
from unittest.mock import patch

import openpyxl
import pytest

from sendings_app.models import Sending
from sendings_app.tests.data.test_data import (
    DUPLICATE_ROWS,
    INVALID_EMAIL_ROWS,
    MISSING_FIELDS_ROWS,
    PRE_EXISTING_ROW,
    VALID_ROWS,
    XLSX_HEADERS,
)


def _create_xlsx(
    path: Path,
    rows: list[dict[str, str]],
    headers: list[str] | None = None,
) -> Path:
    """Creates an XLSX file at the given path with the specified rows and headers."""
    wb = openpyxl.Workbook()
    ws = wb.active
    cols = headers or XLSX_HEADERS
    ws.append(cols)
    for row in rows:
        ws.append([row.get(h, "") for h in cols])
    wb.save(str(path))
    return path


@pytest.fixture(autouse=True)
def _mock_send_email():
    """Turn off actual email sending during tests by mocking the send_email function."""
    with patch("sendings_app.tasks.send_email_task.delay") as mock:
        yield mock


@pytest.fixture()
def xlsx_factory(tmp_path) -> Callable[..., str]:
    """
    Fixture that provides a factory function to create XLSX files with specified rows and headers.
    The factory function takes a list of rows (dicts) and optional filename and headers,
    creates an XLSX file in the temporary directory, and returns the file path as a string.
    """
    _counter = 0

    def _factory(
        rows: list[dict[str, str]],
        filename: str | None = None,
        headers: list[str] | None = None,
    ) -> str:
        nonlocal _counter
        _counter += 1
        name = filename or f"test_{_counter}.xlsx"
        path = _create_xlsx(tmp_path / name, rows, headers)
        return str(path)

    return _factory


@pytest.fixture()
def valid_xlsx(xlsx_factory) -> str:
    """XLSX with all valid rows."""
    return xlsx_factory(VALID_ROWS)


@pytest.fixture()
def invalid_email_xlsx(xlsx_factory) -> str:
    """XLSX with all invalid rows."""
    return xlsx_factory(INVALID_EMAIL_ROWS)


@pytest.fixture()
def missing_fields_xlsx(xlsx_factory) -> str:
    """XLSX with rows that have missing required fields (email or message)."""
    return xlsx_factory(MISSING_FIELDS_ROWS)


@pytest.fixture()
def duplicate_xlsx(xlsx_factory) -> str:
    """XLSX with duplicate external_id values to test deduplication within the file."""
    return xlsx_factory(DUPLICATE_ROWS)


@pytest.fixture()
def mixed_xlsx(xlsx_factory) -> str:
    """
    XLSX with a mix of valid rows, rows with invalid emails, rows with missing fields, and duplicate rows.
    Used to test that valid rows are imported while invalid ones are skipped and reported.
    """
    rows = VALID_ROWS + INVALID_EMAIL_ROWS + MISSING_FIELDS_ROWS + DUPLICATE_ROWS
    return xlsx_factory(rows)


@pytest.fixture()
def empty_xlsx(xlsx_factory) -> str:
    """XLSX with only headers and no data rows."""
    return xlsx_factory(rows=[])


@pytest.fixture()
def no_header_xlsx(tmp_path) -> str:
    """Empty XLSX file without headers, to test handling of missing header row."""
    wb = openpyxl.Workbook()
    ws = wb.active

    ws.delete_rows(1)
    path = tmp_path / "no_header.xlsx"
    wb.save(str(path))
    return str(path)


@pytest.fixture()
def missing_columns_xlsx(xlsx_factory) -> str:
    """XLSX with some required columns missing, to test validation of required fields in headers."""
    partial_headers = ["external_id", "user_id", "subject"]
    rows = [{"external_id": "ext-1", "user_id": "u-1", "subject": "Subj"}]
    return xlsx_factory(rows, headers=partial_headers)


@pytest.fixture()
def pre_existing_sending(db) -> Sending:
    """
    Create a Sending record in the database with the same external_id as in PRE_EXISTING_ROW,
    to test that the import command skips it.
    """
    return Sending.objects.create(
        external_id=PRE_EXISTING_ROW["external_id"],
        user_id=PRE_EXISTING_ROW["user_id"],
        email=PRE_EXISTING_ROW["email"],
        subject=PRE_EXISTING_ROW["subject"],
        message=PRE_EXISTING_ROW["message"],
    )


@pytest.fixture()
def xlsx_with_pre_existing(xlsx_factory) -> str:
    """
    XLSX that includes a row with an external_id that already exists in the database (PRE_EXISTING_ROW)
    """
    rows = [PRE_EXISTING_ROW, VALID_ROWS[0]]
    return xlsx_factory(rows)


@pytest.fixture()
def large_xlsx(xlsx_factory) -> str:
    """XLSX with a large number of valid rows (e.g., 50) to test performance and memory usage of the import command."""
    rows = [
        {
            "external_id": f"ext-large-{i}",
            "user_id": f"user-{i}",
            "email": f"user{i}@example.com",
            "subject": f"Subject {i}",
            "message": f"Message body {i}",
        }
        for i in range(50)
    ]
    return xlsx_factory(rows, filename="large.xlsx")
