import os
import logging
from flask import Flask, render_template, redirect, url_for, session
from flask_wtf.csrf import CSRFProtect
from config import Config
from backend.models.database import SessionLocal, init_db
from backend.routes.auth_routes import auth_bp
from backend.routes.student_routes import student_bp
from backend.routes.officer_routes import officer_bp
from backend.routes.faculty_routes import faculty_bp
from backend.routes.recruiter_routes import recruiter_bp
from backend.routes.test_routes import test_bp
from backend.routes.interview_routes import interview_bp

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize CSRF protection
    csrf.init_app(app)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Initialize DB tables
    try:
        init_db()
    except Exception as e:
        logger.error(f'Database initialization failed: {e}')

    # Session cleanup on request teardown
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        SessionLocal.remove()

    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(officer_bp)
    app.register_blueprint(faculty_bp)
    app.register_blueprint(recruiter_bp)
    app.register_blueprint(test_bp)
    app.register_blueprint(interview_bp)

    @app.route('/')
    def index():
        if 'user_id' in session:
            role = session.get('role')
            role_dashboards = {
                'student': 'student.dashboard',
                'officer': 'officer.dashboard',
                'faculty': 'faculty.dashboard',
                'recruiter': 'recruiter.dashboard'
            }
            endpoint = role_dashboards.get(role)
            if endpoint:
                return redirect(url_for(endpoint))
        return redirect(url_for('auth.login'))

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('auth/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('auth/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        logger.exception('Internal server error: %s', e)
        return render_template('auth/500.html'), 500

    return app

if __name__ == '__main__':
    app = create_app()
    print('AI Placement & Career Intelligence System running on http://127.0.0.1:5000')
    debug_mode = os.environ.get('FLASK_DEBUG', '0').lower() in {'1', 'true', 'yes'}
    app.run(debug=debug_mode, port=5000, host='127.0.0.1')
