from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Recruitment, Employee
from flask_login import login_required
from datetime import datetime

recruitment_bp = Blueprint('recruitment', __name__)

@recruitment_bp.route('/recruitment')
@login_required
def list_recruitments():
    recruitments = Recruitment.query.order_by(Recruitment.recruitment_date.desc()).all()
    return render_template('recruitment/list.html', recruitments=recruitments)

@recruitment_bp.route('/recruitment/add', methods=['GET', 'POST'])
@login_required
def add_recruitment():
    if request.method == 'POST':
        matricule = request.form.get('matricule')
        recruitment = Recruitment(
            matricule=matricule,
            recruitment_date=datetime.strptime(request.form.get('recruitment_date'), '%Y-%m-%d').date(),
            grade=request.form.get('grade'),
            corps=request.form.get('corps'),
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            notes=request.form.get('notes')
        )
        db.session.add(recruitment)
        db.session.commit()
        flash('Recrutement ajouté avec succès!', 'success')
        return redirect(url_for('recruitment.list_recruitments'))

    employees = Employee.query.all()
    return render_template('recruitment/add.html', employees=employees)