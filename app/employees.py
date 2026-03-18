from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
import html
from app import db
from app.models import Employee

employees = Blueprint('employees', __name__, url_prefix='/employees')

def _sanitize_input(value: str) -> str:
    """Sanitize user input to prevent XSS attacks"""
    if not value:
        return ''
    return html.escape(value.strip())

# --- List Employees ---
@employees.route("/")
@login_required
def list_employees():
    search = _sanitize_input(request.args.get('search', ''))
    corps_filter = _sanitize_input(request.args.get('corps', ''))
    grade_filter = _sanitize_input(request.args.get('grade', ''))
    status = _sanitize_input(request.args.get('status', ''))
    year = request.args.get('year', type=int)

    query = Employee.query

    if search:
        query = query.filter(
            (Employee.first_name.ilike(f'%{search}%')) |
            (Employee.last_name.ilike(f'%{search}%')) |
            (Employee.matricule.ilike(f'%{search}%'))
        )

    if corps_filter:
        query = query.filter(Employee.corps == corps_filter)

    if grade_filter:
        query = query.filter(Employee.grade == grade_filter)

    if status == 'active':
        query = query.filter(Employee.date_left.is_(None))
    elif status == 'terminated':
        query = query.filter(Employee.date_left.isnot(None))

    if year:
        query = query.filter(db.extract('year', Employee.date_joined) == year)

    all_employees = query.all()

    # Get distinct corps
    corps_list = db.session.query(
        Employee.corps
    ).distinct().filter(
        Employee.corps.isnot(None)
    ).order_by(Employee.corps).all()
    corps_list = [c[0] for c in corps_list if c[0]]

    # Get distinct grades
    grades = db.session.query(
        Employee.grade
    ).distinct().filter(
        Employee.grade.isnot(None)
    ).order_by(Employee.grade).all()
    grades = [g[0] for g in grades if g[0]]

    # Get distinct years from date_joined
    years = db.session.query(
        db.extract('year', Employee.date_joined).label('year')
    ).distinct().filter(
        Employee.date_joined.isnot(None)
    ).order_by(db.text('year DESC')).all()
    years = [int(year[0]) for year in years]

    return render_template("employees.html",
                         employees=all_employees,
                         corps_list=corps_list,
                         grades=grades,
                         years=years)

# --- Add Employee ---
@employees.route("/add", methods=["GET", "POST"])
@login_required
def add_employee():
    if request.method == "POST":
        try:
            first_name = _sanitize_input(request.form.get("first_name", ""))
            last_name = _sanitize_input(request.form.get("last_name", ""))

            if not first_name or not last_name:
                raise ValueError("First name and last name are required")

            birth_date_raw = _sanitize_input(request.form.get("birth_date", ""))
            birth_date = datetime.strptime(birth_date_raw, "%Y-%m-%d").date() if birth_date_raw else None

            if not birth_date:
                raise ValueError("Birth date is required")

            matricule_raw = _sanitize_input(request.form.get("matricule", ""))
            matricule = int(matricule_raw) if matricule_raw else None
            if not matricule:
                raise ValueError("Matricule is required")

            # INSAF classification fields
            grade = _sanitize_input(request.form.get("grade", "")) or None
            echelon_raw = _sanitize_input(request.form.get("echelon", ""))
            echelon = int(echelon_raw) if echelon_raw else None
            indice_raw = _sanitize_input(request.form.get("indice", ""))
            indice = int(indice_raw) if indice_raw else None
            corps = _sanitize_input(request.form.get("corps", "")) or None

            # Salary components
            salaire_base_raw = _sanitize_input(request.form.get("salaire_base", ""))
            salaire_base = float(salaire_base_raw) if salaire_base_raw else None
            if salaire_base and salaire_base < 0:
                raise ValueError("Salaire de base cannot be negative")

            indemnite_residence_raw = _sanitize_input(request.form.get("indemnite_residence", ""))
            indemnite_residence = float(indemnite_residence_raw) if indemnite_residence_raw else None

            indemnite_transport_raw = _sanitize_input(request.form.get("indemnite_transport", ""))
            indemnite_transport = float(indemnite_transport_raw) if indemnite_transport_raw else None

            # Family situation
            situation_familiale = _sanitize_input(request.form.get("situation_familiale", "")) or None
            nombre_enfants_raw = _sanitize_input(request.form.get("nombre_enfants", ""))
            nombre_enfants = int(nombre_enfants_raw) if nombre_enfants_raw else 0

            # Dates
            date_joined_raw = _sanitize_input(request.form.get("date_joined", ""))
            date_joined = datetime.strptime(date_joined_raw, "%Y-%m-%d").date() if date_joined_raw else None

            date_titularisation_raw = _sanitize_input(request.form.get("date_titularisation", ""))
            date_titularisation = datetime.strptime(date_titularisation_raw, "%Y-%m-%d").date() if date_titularisation_raw else None

            emp = Employee(
                matricule=matricule,
                first_name=first_name,
                last_name=last_name,
                birth_date=birth_date,
                grade=grade,
                echelon=echelon,
                indice=indice,
                corps=corps,
                salaire_base=salaire_base,
                indemnite_residence=indemnite_residence,
                indemnite_transport=indemnite_transport,
                situation_familiale=situation_familiale,
                nombre_enfants=nombre_enfants,
                date_joined=date_joined,
                date_titularisation=date_titularisation
            )

            db.session.add(emp)
            db.session.commit()
            flash("Employee added successfully", "success")
            return redirect(url_for("employees.list_employees"))

        except ValueError as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "error")
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding employee: {str(e)}", "error")

    return render_template("add_employee.html")

# --- Edit Employee ---
@employees.route("/edit/<int:matricule>", methods=["GET", "POST"])
@login_required
def edit_employee(matricule):
    employee = Employee.query.get_or_404(matricule)

    if employee.date_left:
        flash("Cannot edit terminated employee", "error")
        return redirect(url_for("employees.list_employees"))

    if request.method == "POST":
        try:
            first_name = _sanitize_input(request.form.get("first_name", ""))
            last_name = _sanitize_input(request.form.get("last_name", ""))

            if not first_name or not last_name:
                raise ValueError("First name and last name are required")

            employee.first_name = first_name
            employee.last_name = last_name

            birth_date_raw = _sanitize_input(request.form.get("birth_date", ""))
            employee.birth_date = datetime.strptime(birth_date_raw, "%Y-%m-%d").date() if birth_date_raw else None

            # INSAF classification fields
            employee.grade = _sanitize_input(request.form.get("grade", "")) or None
            echelon_raw = _sanitize_input(request.form.get("echelon", ""))
            employee.echelon = int(echelon_raw) if echelon_raw else None
            indice_raw = _sanitize_input(request.form.get("indice", ""))
            employee.indice = int(indice_raw) if indice_raw else None
            employee.corps = _sanitize_input(request.form.get("corps", "")) or None

            # Salary components
            salaire_base_raw = _sanitize_input(request.form.get("salaire_base", ""))
            salaire_base = float(salaire_base_raw) if salaire_base_raw else None
            if salaire_base and salaire_base < 0:
                raise ValueError("Salaire de base cannot be negative")
            employee.salaire_base = salaire_base

            indemnite_residence_raw = _sanitize_input(request.form.get("indemnite_residence", ""))
            employee.indemnite_residence = float(indemnite_residence_raw) if indemnite_residence_raw else None

            indemnite_transport_raw = _sanitize_input(request.form.get("indemnite_transport", ""))
            employee.indemnite_transport = float(indemnite_transport_raw) if indemnite_transport_raw else None

            # Family situation
            employee.situation_familiale = _sanitize_input(request.form.get("situation_familiale", "")) or None
            nombre_enfants_raw = _sanitize_input(request.form.get("nombre_enfants", ""))
            employee.nombre_enfants = int(nombre_enfants_raw) if nombre_enfants_raw else 0

            # Dates
            date_joined_raw = _sanitize_input(request.form.get("date_joined", ""))
            employee.date_joined = datetime.strptime(date_joined_raw, "%Y-%m-%d").date() if date_joined_raw else None

            date_titularisation_raw = _sanitize_input(request.form.get("date_titularisation", ""))
            employee.date_titularisation = datetime.strptime(date_titularisation_raw, "%Y-%m-%d").date() if date_titularisation_raw else None

            date_left_raw = _sanitize_input(request.form.get("date_left", ""))
            employee.date_left = datetime.strptime(date_left_raw, "%Y-%m-%d").date() if date_left_raw else None

            db.session.commit()
            flash("Employee updated successfully", "success")
            return redirect(url_for("employees.list_employees"))

        except ValueError as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "error")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating employee: {str(e)}", "error")

    return render_template("edit_employee.html", employee=employee)

# --- Terminate Employee ---
@employees.route("/terminate/<int:matricule>", methods=["GET", "POST"])
@login_required
def terminate_employee(matricule):
    employee = Employee.query.get_or_404(matricule)

    if employee.date_left:
        flash("Employee is already terminated", "warning")
        return redirect(url_for("employees.list_employees"))

    if request.method == "POST":
        try:
            date_left_raw = _sanitize_input(request.form.get("date_left", ""))
            if not date_left_raw:
                raise ValueError("Termination date is required")

            date_left = datetime.strptime(date_left_raw, "%Y-%m-%d").date()

            if employee.date_joined and date_left < employee.date_joined:
                raise ValueError("Termination date cannot be before hire date")

            employee.date_left = date_left
            db.session.commit()
            flash("Employee terminated successfully", "success")
            return redirect(url_for("employees.list_employees"))

        except ValueError as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "error")
        except Exception as e:
            db.session.rollback()
            flash(f"Error terminating employee: {str(e)}", "error")

    return render_template("terminate_employee.html", employee=employee)