import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file
from datetime import datetime, timedelta
from backend.models.database import SessionLocal
from backend.models.models import Recruiter, Company, Job, Application, ActualInterview, Offer, Student, Notification
from backend.auth.security import login_required, role_required
from reports.pdf_generator import PlacementReportGenerator

recruiter_bp = Blueprint('recruiter', __name__, url_prefix='/recruiter')

from sqlalchemy.orm import joinedload

@recruiter_bp.route('/dashboard')
@login_required
@role_required('recruiter')
def dashboard():
    company_id = session.get('company_id')
    db = SessionLocal()
    try:
        company = db.query(Company).filter_by(id=company_id).first()
        jobs = db.query(Job).filter_by(company_id=company_id).all()
        job_ids = [j.id for j in jobs]

        applications = db.query(Application).options(
            joinedload(Application.student).joinedload(Student.user),
            joinedload(Application.job)
        ).filter(Application.job_id.in_(job_ids)).all() if job_ids else []
        
        shortlisted = [a for a in applications if a.status in ['Shortlisted', 'Test', 'Technical Interview', 'HR Interview', 'Selected', 'Offer Received', 'Offer Accepted']]
        interviews = db.query(ActualInterview).options(
            joinedload(ActualInterview.student).joinedload(Student.user),
            joinedload(ActualInterview.application).joinedload(Application.job)
        ).join(Application).filter(Application.job_id.in_(job_ids)).all() if job_ids else []

        return render_template(
            'recruiter/dashboard.html',
            company=company,
            jobs=jobs,
            applications=applications,
            shortlisted=shortlisted,
            interviews=interviews
        )
    finally:
        db.close()

@recruiter_bp.route('/jobs')
@login_required
@role_required('recruiter')
def jobs():
    company_id = session.get('company_id')
    db = SessionLocal()
    try:
        jobs_list = db.query(Job).filter_by(company_id=company_id).all()
        return render_template('recruiter/jobs.html', jobs=jobs_list)
    finally:
        db.close()

@recruiter_bp.route('/jobs/create', methods=['GET', 'POST'])
@login_required
@role_required('recruiter')
def create_job():
    company_id = session.get('company_id')
    db = SessionLocal()
    try:
        if request.method == 'POST':
            title = request.form.get('title')
            role_type = request.form.get('role_type', 'Full-Time')
            location = request.form.get('location')
            salary_pkg = request.form.get('salary_package')
            salary_num = float(request.form.get('salary_numeric', 6.0))
            min_cgpa = float(request.form.get('min_cgpa', 6.0))
            req_skills = request.form.get('required_skills')
            pref_skills = request.form.get('preferred_skills')
            desc = request.form.get('description')

            new_job = Job(
                company_id=company_id,
                title=title,
                role_type=role_type,
                location=location,
                salary_package=salary_pkg,
                salary_numeric=salary_num,
                min_cgpa=min_cgpa,
                required_skills=req_skills,
                preferred_skills=pref_skills,
                description=desc,
                selection_process='Assessment -> Technical Round -> HR',
                deadline=datetime.utcnow() + timedelta(days=30),
                status='Active'
            )
            db.add(new_job)
            db.commit()
            flash(f"Job posting '{title}' published successfully!", 'success')
            return redirect(url_for('recruiter.dashboard'))

        return render_template('recruiter/create_job.html')
    finally:
        db.close()

@recruiter_bp.route('/applicants')
@login_required
@role_required('recruiter')
def applicants():
    company_id = session.get('company_id')
    db = SessionLocal()
    try:
        jobs = db.query(Job).filter_by(company_id=company_id).all()
        job_ids = [j.id for j in jobs]
        applications = db.query(Application).options(
            joinedload(Application.student).joinedload(Student.user),
            joinedload(Application.job)
        ).filter(Application.job_id.in_(job_ids)).all() if job_ids else []

        return render_template('recruiter/applicants.html', applications=applications)
    finally:
        db.close()

@recruiter_bp.route('/interviews')
@login_required
@role_required('recruiter')
def interviews():
    company_id = session.get('company_id')
    db = SessionLocal()
    try:
        jobs = db.query(Job).filter_by(company_id=company_id).all()
        job_ids = [j.id for j in jobs]
        interviews_list = db.query(ActualInterview).options(
            joinedload(ActualInterview.student).joinedload(Student.user),
            joinedload(ActualInterview.application).joinedload(Application.job)
        ).join(Application).filter(Application.job_id.in_(job_ids)).all() if job_ids else []

        return render_template('recruiter/interviews.html', interviews=interviews_list)
    finally:
        db.close()

@recruiter_bp.route('/applications/<int:app_id>/status', methods=['POST'])
@login_required
@role_required('recruiter')
def update_application_status(app_id):
    db = SessionLocal()
    try:
        company_id = session.get('company_id')
        app = db.query(Application).join(Job).filter(
            Application.id == app_id,
            Job.company_id == company_id
        ).first()
        if not app:
            flash('Application not found or it does not belong to your company.', 'danger')
            return redirect(url_for('recruiter.applicants'))

        allowed_statuses = {
            'Applied', 'Shortlisted', 'Test', 'Technical Interview',
            'HR Interview', 'Selected', 'Rejected', 'Offer Received', 'Offer Accepted'
        }
        new_status = request.form.get('status')
        if new_status not in allowed_statuses:
            flash('Invalid application status.', 'danger')
            return redirect(url_for('recruiter.applicants'))

        app.status = new_status
        if new_status == 'Selected':
            existing_offer = db.query(Offer).filter_by(application_id=app.id).first()
            if not existing_offer:
                db.add(Offer(
                    application_id=app.id,
                    student_id=app.student_id,
                    company_name=app.job.company.name,
                    job_title=app.job.title,
                    package_lpa=app.job.salary_numeric,
                    status='Offered'
                ))
            student_user_id = app.student.user_id
            db.add(Notification(
                user_id=student_user_id,
                title='Placement Selection Update',
                message=f'You have been selected for {app.job.title} at {app.job.company.name}.',
                notification_type='offer',
                link='/student/applications'
            ))
        db.commit()
        flash(f"Candidate status updated to {new_status}.", 'success')
        return redirect(url_for('recruiter.applicants'))
    finally:
        db.close()

