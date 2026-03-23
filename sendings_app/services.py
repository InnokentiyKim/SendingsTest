from dataclasses import dataclass, field
from typing import Generator

import openpyxl
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from sendings_app.models import Sending
from sendings_app.tasks import send_email_task, EmailPayload


REQUIRED_COLUMNS: set[str] = {"external_id", "user_id", "email", "subject", "message"}


@dataclass
class ImportResult:
    """The result of the import process, accumulating statistics and errors."""

    total_rows: int = 0
    created: int = 0
    skipped: int = 0
    ignored: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return len(self.errors)


def send_emails(sendings: list[EmailPayload]) -> None:
    """
    Simulates sending emails for a list of sendings by invoking the Celery task.

    Args:
        sendings: A list of EmailPayload dictionaries containing 'email' and 'subject' keys.
    """
    for email_payload in sendings:
        send_email_task.delay(email_payload)


def _validate_row(row_data: dict[str, str], row_number: int) -> str | None:
    """
    Validates a single row of data from the XLSX file.
    Checks for presence of required fields and validates the email format.

    Args:
        row_data: A dictionary mapping column names to their values for the current row.
        row_number: The line number in the XLSX file (for error reporting).

    Returns:
        An error message string if validation fails, or None if the row is valid.
    """
    for col in REQUIRED_COLUMNS:
        value = row_data.get(col)
        if value is None or str(value).strip() == "":
            return f"Строка {row_number}: пустое обязательное поле '{col}'"

    try:
        validate_email(str(row_data["email"]).strip())
    except ValidationError:
        return f"Строка {row_number} имеет невалидный email '{row_data['email']}'"


def _iter_xlsx_rows(
    file_path: str,
) -> Generator[tuple[int, dict[str, str]], None, None]:
    """
    Generates rows from the XLSX file one by one, yielding a tuple of (row_number, row_data_dict).

    Args:
        file_path: The path to the XLSX file to read.

    Yields:
        A tuple containing the line number (starting from 2, since 1 is for headers
    """
    wb = openpyxl.load_workbook(file_path, read_only=True)
    ws = wb.active

    try:
        rows_iter = ws.iter_rows(values_only=True)

        raw_headers = next(rows_iter, None)
        if raw_headers is None:
            raise ValueError("XLSX-файл пуст — нет строки заголовков.")

        headers: list[str] = [
            str(h).strip().lower() for h in raw_headers if h is not None
        ]

        missing = REQUIRED_COLUMNS - set(headers)
        if missing:
            raise ValueError(
                f"В файле отсутствуют обязательные колонки: {', '.join(sorted(missing))}"
            )

        for row_number, row in enumerate(rows_iter, start=2):
            row_dict = {
                headers[i]: (row[i] if i < len(row) else None)
                for i in range(len(headers))
            }
            yield row_number, row_dict
    finally:
        wb.close()


def _process_batch(
    batch: list[dict[str, str]],
    result: ImportResult,
    batch_size: int,
) -> list[Sending]:
    """
    Processes a batch of rows: performs deduplication against the database and within the file,
    creates Sending instances for valid rows, and updates the ImportResult with statistics.

    Args:
        batch: A list of dictionaries, each representing a row of data to process.
        result: The ImportResult instance to update with statistics about created and skipped records.
        batch_size: The size of the batch for bulk_create and database queries.

    Returns:
        A list of Sending instances that were created in the database for this batch.
    """
    batch_ext_ids = [str(r["external_id"]).strip() for r in batch]
    existing_ids: set[str] = set(
        Sending.objects.filter(external_id__in=batch_ext_ids).values_list(
            "external_id", flat=True
        )
    )

    sendings_to_create: list[Sending] = []
    for row_data in batch:
        ext_id = str(row_data["external_id"]).strip()

        if ext_id in existing_ids:
            result.skipped += 1
            continue

        sendings_to_create.append(
            Sending(
                external_id=ext_id,
                user_id=str(row_data["user_id"]).strip(),
                email=str(row_data["email"]).strip(),
                subject=str(row_data["subject"]).strip(),
                message=str(row_data["message"]).strip(),
            )
        )

    Sending.objects.bulk_create(
        sendings_to_create, batch_size=batch_size, ignore_conflicts=True
    )
    ext_ids = [s.external_id for s in sendings_to_create]
    created = list(Sending.objects.filter(external_id__in=ext_ids))

    result.created += len(created)
    result.ignored += len(sendings_to_create) - len(created)

    return created


def import_sendings_from_xlsx(
    file_path: str,
    batch_size: int = 500,
) -> ImportResult:
    """
    Imports sendings from an XLSX file, validates the data, creates Sending instances in the database,
    and simulates sending emails for the created records.

    Args:
        file_path: The path to the XLSX file to import.
        batch_size: The number of records to process in each batch for database operations.

    Returns:
        An ImportResult instance containing statistics about the import process and any errors encountered.
    """
    result = ImportResult()
    current_batch: list[dict[str, str]] = []

    for row_number, row_data in _iter_xlsx_rows(file_path):
        result.total_rows += 1

        error = _validate_row(row_data, row_number)
        if error:
            result.errors.append(error)
            continue

        current_batch.append(row_data)

        if len(current_batch) >= batch_size:
            created = _process_batch(current_batch, result, batch_size)
            sendings: list[EmailPayload] = [
                {"email": s.email, "subject": s.subject, "message": s.message}
                for s in created
            ]
            send_emails(sendings)

            current_batch = []

    if current_batch:
        created = _process_batch(current_batch, result, batch_size)
        sendings: list[EmailPayload] = [
            {"email": s.email, "subject": s.subject, "message": s.message}
            for s in created
        ]
        send_emails(sendings)

    return result
