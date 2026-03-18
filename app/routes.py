from flask import Blueprint, request, jsonify
from app.models import db, Employee
from datetime import datetime

employees_bp = Blueprint('employees', __name__, url_prefix='/api/employees')

# GET tous les employés
@employees_bp.route('', methods=['GET'])
def get_employees():
    employees = Employee.query.all()
    return jsonify([emp.to_dict() for emp in employees]), 200

# GET un employé par matricule
@employees_bp.route('/<int:matricule>', methods=['GET'])
def get_employee(matricule):
    employee = Employee.query.get_or_404(matricule)
    return jsonify(employee.to_dict()), 200

# POST créer un employé
@employees_bp.route('', methods=['POST'])
def create_employee():
    data = request.get_json()

    employee = Employee(
        matricule=data.get('matricule'),
        first_name=data['first_name'],
        last_name=data['last_name'],
        birth_date=datetime.strptime(data['birth_date'], '%Y-%m-%d').date() if data.get('birth_date') else None,
        grade=data.get('grade'),
        echelon=data.get('echelon'),
        indice=data.get('indice'),
        corps=data.get('corps'),
        salaire_base=data.get('salaire_base'),
        indemnite_residence=data.get('indemnite_residence'),
        indemnite_transport=data.get('indemnite_transport'),
        situation_familiale=data.get('situation_familiale'),
        nombre_enfants=data.get('nombre_enfants', 0),
        date_joined=datetime.strptime(data['date_joined'], '%Y-%m-%d').date() if data.get('date_joined') else None,
        date_titularisation=datetime.strptime(data['date_titularisation'], '%Y-%m-%d').date() if data.get('date_titularisation') else None
    )

    db.session.add(employee)
    db.session.commit()

    return jsonify(employee.to_dict()), 201

# PUT mettre à jour un employé
@employees_bp.route('/<int:matricule>', methods=['PUT'])
def update_employee(matricule):
    employee = Employee.query.get_or_404(matricule)
    data = request.get_json()

    employee.first_name = data.get('first_name', employee.first_name)
    employee.last_name = data.get('last_name', employee.last_name)
    employee.birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date() if data.get('birth_date') else employee.birth_date
    employee.grade = data.get('grade', employee.grade)
    employee.echelon = data.get('echelon', employee.echelon)
    employee.indice = data.get('indice', employee.indice)
    employee.corps = data.get('corps', employee.corps)
    employee.salaire_base = data.get('salaire_base', employee.salaire_base)
    employee.indemnite_residence = data.get('indemnite_residence', employee.indemnite_residence)
    employee.indemnite_transport = data.get('indemnite_transport', employee.indemnite_transport)
    employee.situation_familiale = data.get('situation_familiale', employee.situation_familiale)
    employee.nombre_enfants = data.get('nombre_enfants', employee.nombre_enfants)
    employee.date_titularisation = datetime.strptime(data['date_titularisation'], '%Y-%m-%d').date() if data.get('date_titularisation') else employee.date_titularisation

    db.session.commit()

    return jsonify(employee.to_dict()), 200

# PATCH terminer un employé (date de départ)
@employees_bp.route('/<int:matricule>/terminate', methods=['PATCH'])
def terminate_employee(matricule):
    employee = Employee.query.get_or_404(matricule)
    data = request.get_json()

    employee.date_left = datetime.strptime(data['date_left'], '%Y-%m-%d').date() if data.get('date_left') else datetime.now().date()

    db.session.commit()

    return jsonify(employee.to_dict()), 200

# DELETE supprimer un employé
@employees_bp.route('/<int:matricule>', methods=['DELETE'])
def delete_employee(matricule):
    employee = Employee.query.get_or_404(matricule)
    db.session.delete(employee)
    db.session.commit()

    return jsonify({'message': 'Employé supprimé'}), 200