from flask import Blueprint, current_app, g

from app.db.connection import get_db
from app.services import dashboard_service
from app.utils.auth_guard import login_required
from app.utils.response import success_response

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.get("/daily")
@login_required
def get_daily_dashboard():
    data = dashboard_service.get_daily_dashboard(
        get_db(),
        g.current_user["id"],
        current_app.config,
    )
    return success_response(data)
