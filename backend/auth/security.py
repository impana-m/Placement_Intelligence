from functools import wraps
from flask import session, redirect, url_for, flash, abort, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from backend.models.database import SessionLocal
from backend.models.models import User, Student, Recruiter

def hash_password(password: str) -> str:
    """Hash password using Werkzeug's default algorithm (scrypt in 3.x)."""
    return generate_password_hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return check_password_hash(hashed, password)

def get_current_user():
    """Get the current authenticated user, cached per-request in flask.g."""
    if 'current_user' in g:
        return g.current_user
    
    user_id = session.get('user_id')
    if not user_id:
        g.current_user = None
        return None
    
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    # Don't close db here - let teardown_appcontext handle it via SessionLocal.remove()
    g.current_user = user
    return user

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.accept_mimetypes.best == 'application/json':
                return jsonify({'error': 'Authentication required'}), 401
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        # Verify user still exists and is active
        user = get_current_user()
        if not user:
            session.clear()
            if request.is_json or request.accept_mimetypes.best == 'application/json':
                return jsonify({'error': 'Session expired'}), 401
            flash('Your session has expired. Please log in again.', 'warning')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json or request.accept_mimetypes.best == 'application/json':
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            # Verify user exists and check role from database
            user = get_current_user()
            if not user:
                session.clear()
                if request.is_json or request.accept_mimetypes.best == 'application/json':
                    return jsonify({'error': 'Session expired'}), 401
                flash('Your session has expired. Please log in again.', 'warning')
                return redirect(url_for('auth.login'))
            
            if user.role not in allowed_roles:
                if request.is_json or request.accept_mimetypes.best == 'application/json':
                    return jsonify({'error': 'Access forbidden: insufficient privileges'}), 403
                flash('Access denied. You do not have permission to view this resource.', 'danger')
                return redirect(url_for('auth.unauthorized'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
