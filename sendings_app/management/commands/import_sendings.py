import os
import logging
from django.core.management.base import BaseCommand, CommandError

from sendings_app.services import import_sendings_from_xlsx


DEFAULT_BATCH_SIZE = 500

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Импорт рассылок из XLSX-файла и последующая отправка писем."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "file_path",
            type=str,
            help="Путь к XLSX-файлу с данными рассылок.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=DEFAULT_BATCH_SIZE,
            help=f"Размер батча для bulk_create и проверки external_id (по умолчанию {DEFAULT_BATCH_SIZE}).",
        )

    def handle(self, *args, **options) -> None:
        file_path: str = options["file_path"]
        batch_size: int = options["batch_size"]

        if not os.path.isfile(file_path):
            raise CommandError(f"Файл не найден: {file_path}")

        if not file_path.lower().endswith(".xlsx"):
            raise CommandError("Поддерживается только формат XLSX.")

        logger.info(
            f"Starting import from file: {file_path} with batch size: {batch_size}"
        )

        try:
            result = import_sendings_from_xlsx(file_path, batch_size=batch_size)
        except ValueError as exc:
            logger.warning("Import failed due to invalid data: %s", exc)
            raise CommandError(str(exc)) from exc

        logger.info(
            "Processing completed. Total rows: %d, Created: %d, Skipped: %d, Errors: %d, Ignored: %d",
            result.total_rows,
            result.created,
            result.skipped,
            result.error_count,
            result.ignored,
        )

        if result.errors:
            logger.info("Import completed with errors.")
            for error in result.errors:
                self.stderr.write(self.style.WARNING(f"  • {error}"))
