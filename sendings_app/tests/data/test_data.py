VALID_ROWS: list[dict[str, str]] = [
    {
        "external_id": "ext-001",
        "user_id": "user-1",
        "email": "alice@example.com",
        "subject": "Welcome Alice",
        "message": "Hello Alice, welcome to our platform!",
    },
    {
        "external_id": "ext-002",
        "user_id": "user-2",
        "email": "bob@example.com",
        "subject": "Welcome Bob",
        "message": "Hello Bob, glad to have you!",
    },
    {
        "external_id": "ext-003",
        "user_id": "user-3",
        "email": "charlie@example.com",
        "subject": "Welcome Charlie",
        "message": "Hi Charlie, enjoy your stay!",
    },
]


INVALID_EMAIL_ROWS: list[dict[str, str]] = [
    {
        "external_id": "ext-bad-email-1",
        "user_id": "user-10",
        "email": "not-an-email",
        "subject": "Bad email",
        "message": "This row has an invalid email address.",
    },
    {
        "external_id": "ext-bad-email-2",
        "user_id": "user-11",
        "email": "@missing-local.com",
        "subject": "Bad email 2",
        "message": "Missing local part.",
    },
]


MISSING_FIELDS_ROWS: list[dict[str, str]] = [
    {
        "external_id": "ext-empty-email",
        "user_id": "user-20",
        "email": "",
        "subject": "Empty email field",
        "message": "Email is empty.",
    },
    {
        "external_id": "",
        "user_id": "user-21",
        "email": "valid@example.com",
        "subject": "Empty external_id",
        "message": "external_id is empty.",
    },
    {
        "external_id": "ext-empty-subject",
        "user_id": "user-22",
        "email": "valid2@example.com",
        "subject": "",
        "message": "Subject is empty.",
    },
]


DUPLICATE_ROWS: list[dict[str, str]] = [
    {
        "external_id": "ext-dup-1",
        "user_id": "user-30",
        "email": "dup1@example.com",
        "subject": "Original",
        "message": "First occurrence.",
    },
    {
        "external_id": "ext-dup-1",
        "user_id": "user-31",
        "email": "dup1-copy@example.com",
        "subject": "Duplicate",
        "message": "Second occurrence — should be skipped.",
    },
]


PRE_EXISTING_ROW: dict[str, str] = {
    "external_id": "ext-existing",
    "user_id": "user-99",
    "email": "existing@example.com",
    "subject": "Already in DB",
    "message": "This record was pre-populated.",
}


XLSX_HEADERS: list[str] = ["external_id", "user_id", "email", "subject", "message"]
