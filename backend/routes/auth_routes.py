from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from urllib.parse import urlparse
from backend.models.database import SessionLocal
from backend.models.models import User, Student, Department, Recruiter, Company
from backend.auth.security import hash_password, verify_password

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect_by_role(session.get('role'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please provide both email and password.', 'danger')
            return render_template('auth/login.html', email=email)

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email, User.is_active == True).first()
            if user and verify_password(password, user.password_hash):
                session.clear()
                session['user_id'] = user.id
                session['email'] = user.email
                session['full_name'] = user.full_name
                session['role'] = user.role
                session['department_id'] = user.department_id

                if user.role == 'student' and user.student_profile:
                    session['student_id'] = user.student_profile.id
                elif user.role == 'recruiter' and user.recruiter_profile:
                    session['recruiter_id'] = user.recruiter_profile.id
                    session['company_id'] = user.recruiter_profile.company_id

                flash(f'Welcome back, {user.full_name}!', 'success')
                next_page = request.args.get('next')
                if next_page:
                    parsed = urlparse(next_page)
                    if parsed.scheme == '' and parsed.netloc == '' and next_page.startswith('/') and not next_page.startswith('//'):
                        return redirect(next_page)
                return redirect_by_role(user.role)
            else:
                flash('Invalid email or password. Please try again.', 'danger')
        finally:
            db.close()

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect_by_role(session.get('role'))

    db = SessionLocal()
    try:
        departments = db.query(Department).all()
        if request.method == 'POST':
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            role = 'student'  # Public registration may only create student accounts.
            dept_id = request.form.get('department_id')
            usn = request.form.get('usn', '').strip().upper()
            batch = request.form.get('batch_year', 2026)

            if not full_name or not email or not password:
                flash('All basic fields are required.', 'danger')
                return render_template('auth/register.html', departments=departments)

            if len(password) < 8:
                flash('Password must be at least 8 characters long.', 'danger')
                return render_template('auth/register.html', departments=departments)

            existing = db.query(User).filter(User.email == email).first()
            if existing:
                flash('An account with this email already exists.', 'danger')
                return render_template('auth/register.html', departments=departments)

            new_user = User(
                email=email,
                password_hash=hash_password(password),
                full_name=full_name,
                role=role,
                department_id=int(dept_id) if dept_id else None
            )
            db.add(new_user)
            db.flush()

            if role == 'student':
                if not usn:
                    usn = f'USN{new_user.id:04d}'
                student = Student(
                    user_id=new_user.id,
                    usn=usn,
                    department_id=int(dept_id) if dept_id else departments[0].id,
                    batch_year=int(batch) if batch else 2026,
                    cgpa=7.5
                )
                db.add(student)

            try:
                db.commit()
                flash('Registration successful! You can now log in.', 'success')
                return redirect(url_for('auth.login'))
            except Exception:
                db.rollback()
                flash('An account with this email or USN already exists.', 'danger')
                return render_template('auth/register.html', departments=departments)
        return render_template('auth/register.html', departments=departments)
    finally:
        db.close()

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/unauthorized')
def unauthorized():
    return render_template('auth/403.html'), 403

def redirect_by_role(role):
    if role == 'student':
        return redirect(url_for('student.dashboard'))
    elif role == 'officer':
        return redirect(url_for('officer.dashboard'))
    elif role == 'faculty':
        return redirect(url_for('faculty.dashboard'))
    elif role == 'recruiter':
        return redirect(url_for('recruiter.dashboard'))
    return redirect(url_for('auth.login'))
