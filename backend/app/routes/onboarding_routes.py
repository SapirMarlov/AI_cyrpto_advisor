from flask import Blueprint

from app.services import onboarding_service
from app.utils.auth_guard import login_required
from app.utils.response import success_response

onboarding_bp = Blueprint("onboarding", __name__, url_prefix="/api/onboarding")


@onboarding_bp.get("/questions")
@login_required
def get_questions():
    return success_response({"questions": onboarding_service.get_questions()})
