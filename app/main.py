from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import html
from .models import Employee, PredictionHistory
from app import db
import json
import os
import pandas as pd
# Blueprint principal
main = Blueprint('main', __name__)

def _sanitize_input(value: str) -> str:
    """Sanitize user input to prevent XSS attacks"""
    if not value:
        return ''
    return html.escape(value.strip())

# --- Home ---
@main.route('/')
def index():
    return render_template('index.html')

@main.route("/home", methods=["GET"])
@login_required
def home():
    return render_template("home.html", user=current_user)

# --- Dashboard ---
@main.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    # Get the base directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Load historical data from the main CSV file
    historical_file = os.path.join(base_dir, 'data', 'historical_data.csv')
    historical_df = pd.read_csv(historical_file)

    # Clean historical data
    historical_df['year'] = pd.to_numeric(historical_df['year'], errors='coerce')
    historical_df = historical_df.dropna(subset=['year'])
    historical_df['year'] = historical_df['year'].astype(int)
    historical_df = historical_df.sort_values(by='year').reset_index(drop=True)

    # Prepare salary data (yearly totals)
    salary_data = {
        'labels': [str(y) for y in historical_df['year'].tolist()],
        'values': historical_df['mass_salary'].tolist()
    }

    # Prepare employees data (yearly)
    employees_data = {
        'labels': [str(y) for y in historical_df['year'].tolist()],
        'values': historical_df['number_employees'].tolist()
    }

    # Prepare departures data (yearly)
    departures_data = {
        'labels': [str(y) for y in historical_df['year'].tolist()],
        'values': historical_df['departures'].tolist()
    }

    # Prepare recruitments data (yearly)
    recruitments_data = {
        'labels': [str(y) for y in historical_df['year'].tolist()],
        'values': historical_df['recruitment'].tolist()
    }

    # Calculate average salary per employee by year
    historical_df['avg_salary'] = historical_df['mass_salary'] / historical_df['number_employees']
    avg_salary_by_year = {
        'labels': [str(y) for y in historical_df['year'].tolist()],
        'values': [round(v, 2) for v in historical_df['avg_salary'].tolist()]
    }

    # Departures by year (same as departures_data for yearly view)
    departures_by_year = {
        'labels': [str(y) for y in historical_df['year'].tolist()],
        'values': historical_df['departures'].tolist()
    }

    # Summary statistics
    total_records = len(historical_df)
    max_employees = int(historical_df['number_employees'].max())
    total_recruitments = int(historical_df['recruitment'].sum())
    total_departures = int(historical_df['departures'].sum())

    return render_template(
        "dashboard.html",
        user=current_user,
        salary_data=json.dumps(salary_data),
        employees_data=json.dumps(employees_data),
        departures_data=json.dumps(departures_data),
        recruitments_data=json.dumps(recruitments_data),
        avg_salary_by_year=json.dumps(avg_salary_by_year),
        departures_by_year=json.dumps(departures_by_year),
        total_records=total_records,
        max_employees=max_employees,
        total_recruitments=total_recruitments,
        total_departures=total_departures
    )

# --- History ---

@main.route("/history", methods=["GET"], strict_slashes=False)
@login_required
def history():
    histories = PredictionHistory.query.filter_by(user_id=current_user.id).order_by(PredictionHistory.created_at.desc()).all()

    for h in histories:
        try:
            h.result_data = json.loads(h.result_json)
        except Exception:
            h.result_data = {}

    return render_template("history.html", user=current_user, histories=histories)

# --- Predict ---
@main.route("/predict", methods=["GET", "POST"], strict_slashes=False)
@login_required
def predict():
    salary = None
    if request.method == "POST":
        try:
            experience_raw = _sanitize_input(request.form.get("experience", "0"))
            experience = float(experience_raw)
        except (TypeError, ValueError):
            flash("Expérience invalide.", "error")
            experience = 0.0

        experience = max(0.0, min(experience, 50.0))  # Limite à 50 ans d'expérience

        education = _sanitize_input(request.form.get("education", "Bachelor")).strip()
        allowed_educations = {"Bachelor", "Master", "PhD"}
        if education not in allowed_educations:
            flash("Niveau d'éducation invalide, utilisation de 'Bachelor'.", "warning")
            education = "Bachelor"

        base_salary = 30000.0
        multiplier = {"Bachelor": 1.0, "Master": 1.2, "PhD": 1.5}
        salary = round(base_salary + experience * 2000.0 * multiplier[education], 2)

    return render_template("prediction.html", user=current_user, salary=salary)

# --- Profile ---
@main.route("/profile", methods=["GET"])
@login_required
def profile():
    employee = Employee.query.filter_by(matricule=current_user.matricule).first()
    if not employee:
        flash("Aucun employe trouve pour cet utilisateur.", "error")
        return render_template('error.html', message="Employee not found"), 404

    return render_template(
        "profile.html",
        username=current_user.username,
        email=current_user.email_adress,
        first_name=employee.first_name,
        last_name=employee.last_name,
    )


@main.route("/change-password", methods=["POST"])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    # Validate current password
    if not current_user.check_password(current_password):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('main.profile'))

    # Validate new password
    if len(new_password) < 8:
        flash('New password must be at least 8 characters.', 'error')
        return redirect(url_for('main.profile'))

    # Check passwords match
    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('main.profile'))

    # Update password
    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()

    flash('Password updated successfully!', 'success')
    return redirect(url_for('main.profile'))


# --- Error handler ---
@main.app_errorhandler(500)
def handle_500(err):
    return render_template('error.html', message=str(err)), 500