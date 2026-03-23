import logging
from time import sleep
from random import randint

from celery import shared_task
from typing import TypedDict


logger = logging.getLogger(__name__)


class EmailPayload(TypedDict):
    email: str
    subject: str
    message: str


@shared_task
def send_email_task(email_payload: EmailPayload) -> None:
    """
    Celery task to send emails for a list of sending external IDs.

    Args:
        email_payload: A list of dictionaries containing 'email' and 'subject' keys for each sending.
    """
    try:
        delay_time = randint(5, 20)
        logger.info("Sending EMAIL to %s", email_payload["email"])

        sleep(delay_time)

        logger.info(
            "EMAIL sent to %s, subject: '%s' (delay_time=%ds)",
            email_payload["email"],
            email_payload["subject"],
            delay_time,
        )
    except Exception:
        logger.exception("Failed to send email to %s", email_payload["email"])
