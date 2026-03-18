from flask import Blueprint, request, redirect, url_for, flash, render_template
from werkzeug.security import check_password_hash
from flask_login import login_user, logout_user
from urllib.parse import urlparse, urljoin
import html
from app.models import User

auth = Blueprint('auth', __name__)

def _is_safe_next_url(target: str) -> bool:
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target or ''))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def _is_valid_email(email: str) -> bool:
    return bool(email) and '@' in email and '.' in email.split('@')[-1]

def _is_valid_username(username: str) -> bool:
    return bool(username) and 3 <= len(username) <= 64

def _is_strong_password(password: str) -> bool:
    return bool(password) and len(password) >= 8

def _sanitize_input(value: str) -> str:
    """Sanitize user input to prevent XSS attacks"""
    if not value:
        return ''
    return html.escape(value.strip())


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        print(f"Tentative de connexion : username={username}")  # Debug

        user = User.query.filter_by(username=username).first()

        print(f"Utilisateur trouvé : {user}")  # Debug

        if user:
            print(f"Hash stocké : {user.password_hash}")  # Debug
            print(f"Vérification : {user.check_password(password)}")  # Debug

        if user and user.check_password(password):
            login_user(user, remember=True)
            return redirect(url_for('main.home'))
        else:
            flash('Identifiants invalides')

    return render_template('login.html')


@auth.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    #return redirect(url_for('auth.login'))
    return redirect(url_for('main.index'))



@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup is disabled - only admin can access the system"""
    flash('Registration is disabled. Please contact the administrator.')
    return redirect(url_for('auth.login'))
