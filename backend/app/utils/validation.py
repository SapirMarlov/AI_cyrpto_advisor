import re

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8
VALID_FEEDBACK_ITEM_TYPES = {"news", "insight", "meme"}
VALID_FEEDBACK_VOTE_TYPES = {"up", "down"}
ALLOWED_FEEDBACK_VOTE_FIELDS = {"item_id", "item_type", "vote_type"}


class ValidationError(Exception):
    """Raised when a request payload fails validation."""

    def __init__(self, message: str):
        """Store the validation error message."""
        super().__init__(message)
        self.message = message


def validate_auth_payload(payload: dict | None, allowed_fields: set[str]) -> dict:
    """Validate signup/login JSON and return cleaned fields."""
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


def validate_onboarding_answers(payload: dict | None, questions: list[dict]) -> dict:
    """Validate onboarding answers against the quiz questions."""
    if payload is None or not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object")

    unexpected = set(payload.keys()) - {"answers"}
    if unexpected:
        raise ValidationError(f"Unexpected fields: {', '.join(sorted(unexpected))}")

    answers = payload.get("answers")
    if answers is None or not isinstance(answers, dict):
        raise ValidationError("Answers must be an object")

    question_by_id = {question["id"]: question for question in questions}
    unexpected_answers = set(answers.keys()) - set(question_by_id.keys())
    if unexpected_answers:
        raise ValidationError(
            f"Unexpected answer fields: {', '.join(sorted(unexpected_answers))}"
        )

    validated: dict = {}
    for question in questions:
        question_id = question["id"]
        if question_id not in answers:
            raise ValidationError(f"Answer for '{question_id}' is required")

        value = answers[question_id]
        allowed_ids = {option["id"] for option in question["options"]}

        if question["type"] == "single":
            if not isinstance(value, str) or not value:
                raise ValidationError(f"Answer for '{question_id}' must be a string")
            if value not in allowed_ids:
                raise ValidationError(f"Invalid option for '{question_id}'")
            validated[question_id] = value
            continue

        if question["type"] == "multi":
            if not isinstance(value, list) or not value:
                raise ValidationError(
                    f"Answer for '{question_id}' must be a non-empty list"
                )
            if not all(isinstance(item, str) and item for item in value):
                raise ValidationError(
                    f"Answer for '{question_id}' must contain only option ids"
                )
            if len(value) != len(set(value)):
                raise ValidationError(
                    f"Answer for '{question_id}' must not contain duplicates"
                )
            invalid = set(value) - allowed_ids
            if invalid:
                raise ValidationError(f"Invalid option for '{question_id}'")
            validated[question_id] = value
            continue

        raise ValidationError(f"Unsupported question type for '{question_id}'")

    return validated


def validate_feedback_vote(payload: dict | None) -> dict:
    """Validate feedback vote JSON and return cleaned fields."""
    if payload is None or not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object")

    unexpected = set(payload.keys()) - ALLOWED_FEEDBACK_VOTE_FIELDS
    if unexpected:
        raise ValidationError(f"Unexpected fields: {', '.join(sorted(unexpected))}")

    item_id = payload.get("item_id")
    item_type = payload.get("item_type")
    vote_type = payload.get("vote_type")

    if not isinstance(item_id, str) or not item_id.strip():
        raise ValidationError("item_id must be a non-empty string")

    if item_type not in VALID_FEEDBACK_ITEM_TYPES:
        raise ValidationError("item_type must be one of: news, insight, meme")

    if vote_type not in VALID_FEEDBACK_VOTE_TYPES:
        raise ValidationError("vote_type must be one of: up, down")

    return {
        "item_id": item_id.strip(),
        "item_type": item_type,
        "vote_type": vote_type,
    }
