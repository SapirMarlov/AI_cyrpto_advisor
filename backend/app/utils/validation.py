import re

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8


class ValidationError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def validate_auth_payload(payload: dict | None, allowed_fields: set[str]) -> dict:
    if payload is None or not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object")

    unexpected = set(payload.keys()) - allowed_fields
    if unexpected:
        raise ValidationError(f"Unexpected fields: {', '.join(sorted(unexpected))}")

    email = payload.get("email")
    password = payload.get("password")

    if not isinstance(email, str) or not email.strip():
        raise ValidationError("Email is required")

    normalized_email = email.strip().lower()
    if not EMAIL_PATTERN.match(normalized_email):
        raise ValidationError("Email format is invalid")

    if not isinstance(password, str) or not password:
        raise ValidationError("Password is required")

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")

    return {"email": normalized_email, "password": password}
