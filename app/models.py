from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import UserMixin
from app import db


class Employee(db.Model):
    """
    Employee model based on INSAF (Système d'Information National de
    l'Administration et de la Fonction Publique) data structure.
    """
    __tablename__ = 'employees'

    matricule = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)  # Prénom
    last_name = db.Column(db.String(50), nullable=False)   # Nom
    birth_date = db.Column(db.Date, nullable=False)        # Date de naissance

    # INSAF-specific fields
    grade = db.Column(db.String(20))          # Grade (A1, A2, A3, B, C, D)
    echelon = db.Column(db.Integer)           # Échelon (1-12 typically)
    indice = db.Column(db.Integer)            # Indice (salary index)
    corps = db.Column(db.String(50))          # Corps (Administratif, Technique, etc.)

    # Salary components
    salaire_base = db.Column(db.Numeric(10, 2))      # Salaire de base
    indemnite_residence = db.Column(db.Numeric(10, 2))  # Indemnité de résidence
    indemnite_transport = db.Column(db.Numeric(10, 2))  # Indemnité de transport

    # Family situation (affects allowances)
    situation_familiale = db.Column(db.String(20))  # Célibataire, Marié(e), Divorcé(e), Veuf(ve)
    nombre_enfants = db.Column(db.Integer, default=0)  # Nombre d'enfants à charge

    # Dates
    date_joined = db.Column(db.Date)          # Date de recrutement
    date_titularisation = db.Column(db.Date)  # Date de titularisation
    date_left = db.Column(db.Date)            # Date de départ

    def to_dict(self):
        return {
            'matricule': self.matricule,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'grade': self.grade,
            'echelon': self.echelon,
            'indice': self.indice,
            'corps': self.corps,
            'salaire_base': float(self.salaire_base) if self.salaire_base else None,
            'indemnite_residence': float(self.indemnite_residence) if self.indemnite_residence else None,
            'indemnite_transport': float(self.indemnite_transport) if self.indemnite_transport else None,
            'situation_familiale': self.situation_familiale,
            'nombre_enfants': self.nombre_enfants,
            'date_joined': self.date_joined.isoformat() if self.date_joined else None,
            'date_titularisation': self.date_titularisation.isoformat() if self.date_titularisation else None,
            'date_left': self.date_left.isoformat() if self.date_left else None
        }

    @property
    def salaire_total(self):
        """Calculate total monthly salary"""
        total = 0
        if self.salaire_base:
            total += float(self.salaire_base)
        if self.indemnite_residence:
            total += float(self.indemnite_residence)
        if self.indemnite_transport:
            total += float(self.indemnite_transport)
        return total

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email_adress = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    matricule = db.Column(db.Integer, db.ForeignKey('employees.matricule'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship('Employee', backref='user', lazy=True)

    @property
    def is_active(self):
        """Vérifie si l'utilisateur est actif"""
        if self.employee:
            return self.employee.date_left is None
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Recruitment(db.Model):
    """Recruitment records following INSAF structure"""
    __tablename__ = 'recruitment'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    matricule = db.Column(db.Integer, db.ForeignKey('employees.matricule'), nullable=False)
    recruitment_date = db.Column(db.Date, nullable=False)
    grade = db.Column(db.String(20))      # Grade at recruitment
    corps = db.Column(db.String(50))      # Corps
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.now())

    employee = db.relationship('Employee', backref='recruitment_history')


class Termination(db.Model):
    """Termination/departure records following INSAF structure"""
    __tablename__ = 'termination'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    matricule = db.Column(db.Integer, db.ForeignKey('employees.matricule'), nullable=False)
    termination_date = db.Column(db.Date, nullable=False)
    grade = db.Column(db.String(20))      # Grade at departure
    corps = db.Column(db.String(50))      # Corps
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    reason = db.Column(db.String(200))    # Retraite, Démission, Mutation, Décès, etc.
    created_at = db.Column(db.DateTime, default=db.func.now())

    employee = db.relationship('Employee', backref='termination_history')


class PredictionHistory(db.Model):
    __tablename__ = 'prediction_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Inputs
    start_year = db.Column(db.Integer, nullable=False)
    end_year = db.Column(db.Integer, nullable=False)
    recruitments = db.Column(db.Integer, nullable=False)
    departures = db.Column(db.Integer, nullable=False)
    initial_employees = db.Column(db.Integer, nullable=False)

    # Results (store as JSON string for flexibility)
    result_json = db.Column(db.Text(length=4294967295), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship back to User
    user = db.relationship('User', backref='prediction_history')