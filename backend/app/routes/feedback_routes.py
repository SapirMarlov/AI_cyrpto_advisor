from flask import Blueprint, g, request

from app.db.connection import get_db
from app.services import feedback_service
from app.utils.auth_guard import login_required
from app.utils.response import error_response, success_response
from app.utils.validation import ValidationError, validate_feedback_vote

feedback_bp = Blueprint("feedback", __name__, url_prefix="/api/feedback")


@feedback_bp.post("/vote")
@login_required
def save_vote():
    """Save a thumbs up/down vote for the current user."""
    try:
        vote = validate_feedback_vote(request.get_json(silent=True))
    except ValidationError as exc:
        return error_response("validation_error", exc.message, 400)

    saved = feedback_service.save_vote(
        get_db(),
        g.current_user["id"],
        vote["item_id"],
        vote["item_type"],
        vote["vote_type"],
    )
    return success_response(saved)
