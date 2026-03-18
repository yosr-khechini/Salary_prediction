from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Termination, Employee
from flask_login import login_required
from datetime import datetime

termination_bp = Blueprint('termination', __name__)

@termination_bp.route('/termination')
@login_required
def list_terminations():
    terminations = Termination.query.order_by(Termination.termination_date.desc()).all()
    return render_template('termination/list.html', terminations=terminations)

@termination_bp.route('/termination/add', methods=['GET', 'POST'])
@login_required
def add_termination():
    if request.method == 'POST':
        matricule = request.form.get('matricule')
        termination = Termination(
            matricule=matricule,
            termination_date=datetime.strptime(request.form.get('termination_date'), '%Y-%m-%d').date(),
            grade=request.form.get('grade'),
            corps=request.form.get('corps'),
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            reason=request.form.get('reason')
        )
        db.session.add(termination)
        db.session.commit()
        flash('Départ enregistré avec succès!', 'success')
        return redirect(url_for('termination.list_terminations'))

    employees = Employee.query.all()
    return render_template('termination/add.html', employees=employees)