import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from sendings_app.models import Sending
from sendings_app.tests.data.test_data import (
    DUPLICATE_ROWS,
    VALID_ROWS,
)


@pytest.mark.django_db
class TestSuccessfulImport:
    """Tests for successful import of valid rows."""

    def test_creates_all_records(self, valid_xlsx):
        """Checks that all valid rows from the XLSX file are created in the database."""
        call_command("import_sendings", valid_xlsx)
        assert Sending.objects.count() == len(VALID_ROWS)

    def test_records_have_correct_data(self, valid_xlsx):
        """Checks that the created records have the correct data as per the input rows."""
        call_command("import_sendings", valid_xlsx)
        for row in VALID_ROWS:
            sending = Sending.objects.get(external_id=row["external_id"])
            assert sending.user_id == row["user_id"]
            assert sending.email == row["email"]
            assert sending.subject == row["subject"]
            assert sending.message == row["message"]


@pytest.mark.django_db
class TestInvalidEmail:
    """Tests for rows with invalid email addresses."""

    def test_no_records_created(self, invalid_email_xlsx):
        """Checks that no records are created for rows with invalid email addresses."""
        call_command("import_sendings", invalid_email_xlsx)
        assert Sending.objects.count() == 0


@pytest.mark.django_db
class TestMissingFields:
    """Tests for rows with missing required fields (external_id, user_id, email, subject, message)."""

    def test_no_records_created(self, missing_fields_xlsx):
        """Checks that no records are created for rows with missing required fields."""
        call_command("import_sendings", missing_fields_xlsx)
        assert Sending.objects.count() == 0


@pytest.mark.django_db
class TestDuplicateInFile:
    """Tests for rows with duplicate external_id within the same XLSX file. Only the first occurrence should be created."""

    def test_only_first_occurrence_created(self, duplicate_xlsx):
        """Checks that when there are duplicate external_id in the file, only the first one is created."""
        call_command("import_sendings", duplicate_xlsx)
        assert Sending.objects.count() == 1
        sending = Sending.objects.get(external_id=DUPLICATE_ROWS[0]["external_id"])
        assert sending.email == DUPLICATE_ROWS[0]["email"]


@pytest.mark.django_db
class TestDuplicateInDB:
    """Tests for rows with external_id that already exists in the database before import."""

    def test_existing_record_skipped(
        self, pre_existing_sending, xlsx_with_pre_existing
    ):
        """
        Checks that if a record with the same external_id already exists in the database,
        it is skipped and not duplicated.
        """
        call_command("import_sendings", xlsx_with_pre_existing)
        # Одна запись уже была, одна новая — итого 2.
        assert Sending.objects.count() == 2


@pytest.mark.django_db
class TestMixedFile:
    """
    Tests for a file that contains a mix of valid rows, rows with invalid emails,
    rows with missing fields, and duplicate rows.
    """

    def test_mixed_import(self, mixed_xlsx):
        """Checks that in a mixed file, valid rows are created, duplicates are skipped, and errors are reported."""
        call_command("import_sendings", mixed_xlsx)

        valid_rows_count = (
            len(VALID_ROWS) + len(DUPLICATE_ROWS) - 1
        )  # 1 дубликат не создаётся
        assert Sending.objects.count() == valid_rows_count


@pytest.mark.django_db
class TestEmptyFile:
    """
    Tests for an XLSX file that has no data rows (only headers).
    No records should be created, but no errors should occur.
    """

    def test_no_records_created(self, empty_xlsx):
        """Checks that if the XLSX file has no data rows (only headers), no records are created and no errors occur."""
        call_command("import_sendings", empty_xlsx)
        assert Sending.objects.count() == 0


@pytest.mark.django_db
class TestBrokenStructure:
    """
    Tests for XLSX files that have structural issues,
    such as missing header row or missing required columns in the header.
    """

    def test_no_header_raises_error(self, no_header_xlsx):
        """Checks that if the XLSX file has no header row, a CommandError is raised indicating missing headers."""
        with pytest.raises(CommandError, match="пуст"):
            call_command("import_sendings", no_header_xlsx)

    def test_missing_columns_raises_error(self, missing_columns_xlsx):
        """Checks that if the XLSX file is missing required columns."""
        with pytest.raises(CommandError, match="обязательные колонки"):
            call_command("import_sendings", missing_columns_xlsx)


@pytest.mark.django_db
class TestReimport:
    """Tests for importing the same valid XLSX file multiple times."""

    def test_second_import_creates_nothing(self, valid_xlsx):
        """
        Checks that if the same valid XLSX file is imported twice,
        the second import does not create duplicate records.
        """
        call_command("import_sendings", valid_xlsx)
        assert Sending.objects.count() == len(VALID_ROWS)

        call_command("import_sendings", valid_xlsx)
        assert Sending.objects.count() == len(VALID_ROWS)


@pytest.mark.django_db
class TestBatching:
    """Tests for the batch processing logic of the import command."""

    def test_small_batch_size(self, large_xlsx):
        """Checks that the command correctly processes the case when the batch_size is smaller than the total number of rows."""
        call_command("import_sendings", large_xlsx, batch_size=7)
        assert Sending.objects.count() == 50

    def test_batch_size_one(self, valid_xlsx):
        """Checks that the command works correctly when batch_size is set to 1"""
        call_command("import_sendings", valid_xlsx, batch_size=1)
        assert Sending.objects.count() == len(VALID_ROWS)


class TestCommandErrors:
    """Tests for error handling in the import command."""

    def test_nonexistent_file(self):
        """Checks that if the specified XLSX file does not exist, a CommandError is raised indicating the file was not found."""
        with pytest.raises(CommandError, match="Файл не найден"):
            call_command("import_sendings", "/nonexistent/path/file.xlsx")

    def test_non_xlsx_file(self, tmp_path):
        """Checks that if the specified file is not an XLSX file, a CommandError is raised indicating that only XLSX format is supported."""
        txt_file = tmp_path / "data.csv"
        txt_file.write_text("a,b,c")
        with pytest.raises(CommandError, match="только формат XLSX"):
            call_command("import_sendings", str(txt_file))


@pytest.mark.django_db
class TestSendEmailCalled:
    """Tests to verify that the send_email function is called for each created Sending record."""

    def test_send_email_called_for_each_created(self, valid_xlsx, _mock_send_email):
        """Checks that the send_email function is called for each created Sending record after import."""
        call_command("import_sendings", valid_xlsx)

        total_sent = _mock_send_email.call_count
        assert total_sent == len(VALID_ROWS)

    def test_send_email_not_called_for_skipped(
        self, pre_existing_sending, xlsx_with_pre_existing, _mock_send_email
    ):
        """Checks that the send_email function is not called for rows that are skipped due to existing external_id in the database."""
        call_command("import_sendings", xlsx_with_pre_existing)

        total_sent = _mock_send_email.call_count
        assert total_sent == 1

    def test_send_email_not_called_for_errors(
        self, invalid_email_xlsx, _mock_send_email
    ):
        """Checks that the send_email function is not called for rows that have validation errors."""
        call_command("import_sendings", invalid_email_xlsx)

        total_sent = _mock_send_email.call_count
        assert total_sent == 0
