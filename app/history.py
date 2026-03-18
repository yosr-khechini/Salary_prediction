from flask import Blueprint, render_template
from app import db
from app.models import PredictionHistory
from flask_login import login_required, current_user

history_bp = Blueprint('history', __name__)

@history_bp.route('/history')
@login_required
def list_history():
    # Get all history records for the current user, newest first
    histories = PredictionHistory.query.filter_by(user_id=current_user.id).order_by(PredictionHistory.created_at.desc()).all()
    return render_template('history.html', histories=histories)
