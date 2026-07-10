from flask import Blueprint, g, request

from app.db.connection import get_db
from app.services import onboarding_service
from app.utils.auth_guard import login_required
from app.utils.response import error_response, success_response
from app.utils.validation import ValidationError, validate_onboarding_answers

onboarding_bp = Blueprint("onboarding", __name__, url_prefix="/api/onboarding")


@onboarding_bp.get("/questions")
@login_required
def get_questions():
    return success_response({"questions": onboarding_service.get_questions()})


@onboarding_bp.post("/answers")
@login_required
def save_answers():
    try:
        answers = validate_onboarding_answers(
            request.get_json(silent=True),
            onboarding_service.get_questions(),
        )
    except ValidationError as exc:
        return error_response("validation_error", exc.message, 400)

    preferences = onboarding_service.save_answers(
        get_db(),
        g.current_user["id"],
        answers,
    )
    return success_response(
        {
            "onboarding_completed": True,
            "preferences": preferences,
        }
    )
