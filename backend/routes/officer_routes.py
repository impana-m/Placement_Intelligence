import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file
from sqlalchemy import func
from backend.models.database import SessionLocal
from backend.models.models import (
    Student, Department, Company, Job, Application, Offer, Intervention, User, ActualInterview, Notification
)
from backend.auth.security import login_required, role_required
from backend.analytics.funnel import PlacementAnalytics
from reports.pdf_generator import PlacementReportGenerator

officer_bp = Blueprint('officer', __name__, url_prefix='/officer')

@officer_bp.route('/dashboard')
@login_required
@role_required('officer')
def dashboard():
    db = SessionLocal()
    try:
        total_students = db.query(Student).count()
        placed_students = db.query(Student).filter_by(placement_status='Placed').count()
        placement_rate = round((placed_students / total_students * 100), 1) if total_students > 0 else 0.0

        active_jobs = db.query(Job).filter_by(status='Active').count()
        companies_count = db.query(Company).count()
        total_offers = db.query(Offer).count()

        funnel_data = PlacementAnalytics.get_placement_funnel()
        skill_demand = PlacementAnalytics.get_skill_demand_analytics()
        dept_comparison = PlacementAnalytics.get_department_comparison()
        salary_dist = PlacementAnalytics.get_salary_distribution()
        interventions = db.query(Intervention).filter_by(status='Open').all()

        return render_template(
            'officer/dashboard.html',
            total_students=total_students,
            placed_students=placed_students,
            placement_rate=placement_rate,
            active_jobs=active_jobs,
            companies_count=companies_count,
            total_offers=total_offers,
            funnel=funnel_data,
            skill_demand=skill_demand,
            dept_comparison=dept_comparison,
            salary_dist=salary_dist,
            interventions=interventions
        )
    finally:
        db.close()

from sqlalchemy.orm import joinedload

@officer_bp.route('/students')
@login_required
@role_required('officer')
def students():
    db = SessionLocal()
    try:
        dept_filter = request.args.get('dept')
        query = db.query(Student).options(joinedload(Student.user), joinedload(Student.department))
        if dept_filter:
            query = query.join(Department).filter(Department.code == dept_filter)
        students_list = query.all()
        departments = db.query(Department).all()
        return render_template('officer/students.html', students=students_list, departments=departments, current_dept=dept_filter)
    finally:
        db.close()

@officer_bp.route('/jobs', methods=['GET', 'POST'])
@login_required
@role_required('officer')
def jobs():
    db = SessionLocal()
    try:
        if request.method == 'POST':
            job_id = request.form.get('job_id')
            action = request.form.get('action')
            job = db.query(Job).filter_by(id=job_id).first()
            if job:
                if action == 'toggle_status':
                    if job.status == 'Active':
                        job.status = 'Paused'
                        message = f"'{job.title}' has been paused."
                    elif job.status == 'Paused':
                        job.status = 'Active'
                        message = f"'{job.title}' has been activated."
                    elif job.status == 'Closed':
                        flash('A closed job drive cannot be reactivated. Create a new drive instead.', 'warning')
                        return redirect(url_for('officer.jobs'))
                    elif job.status == 'Draft':
                        flash('A draft job drive cannot be activated using this action.', 'warning')
                        return redirect(url_for('officer.jobs'))
                    flash(message, 'success')
                db.commit()
            return redirect(url_for('officer.jobs'))

        jobs_list = db.query(Job).options(joinedload(Job.company)).all()
        return render_template('officer/jobs.html', jobs=jobs_list)
    finally:
        db.close()

@officer_bp.route('/interventions', methods=['GET', 'POST'])
@login_required
@role_required('officer')
def interventions():
    db = SessionLocal()
    try:
        if request.method == 'POST':
            intervention_id = request.form.get('intervention_id')
            new_status = request.form.get('status')
            notes = request.form.get('notes')
            # Validate status against allowed enum values
            valid_statuses = {'Open', 'In Progress', 'Resolved'}
            if new_status not in valid_statuses:
                flash('Invalid intervention status.', 'danger')
                return redirect(url_for('officer.interventions'))
            inv = db.query(Intervention).filter_by(id=intervention_id).first()
            if inv:
                inv.status = new_status
                if notes:
                    inv.notes = notes
                db.commit()
                flash('Intervention status updated successfully.', 'success')
            return redirect(url_for('officer.interventions'))

        items = db.query(Intervention).options(
            joinedload(Intervention.student).joinedload(Student.user)
        ).order_by(Intervention.created_at.desc()).all()
        return render_template('officer/interventions.html', interventions=items)
    finally:
        db.close()

@officer_bp.route('/analytics')
@login_required
@role_required('officer')
def analytics():
    db = SessionLocal()
    try:
        funnel_data = PlacementAnalytics.get_placement_funnel()
        skill_demand = PlacementAnalytics.get_skill_demand_analytics()
        dept_comparison = PlacementAnalytics.get_department_comparison()
        salary_dist = PlacementAnalytics.get_salary_distribution()
        return render_template(
            'officer/analytics.html',
            funnel=funnel_data,
            skill_demand=skill_demand,
            dept_comparison=dept_comparison,
            salary_dist=salary_dist
        )
    finally:
        db.close()

@officer_bp.route('/reports')
@login_required
@role_required('officer')
def reports():
    return render_template('officer/reports.html')

@officer_bp.route('/broadcast', methods=['GET', 'POST'])
@login_required
@role_required('officer')
def broadcast():
    db = SessionLocal()
    try:
        if request.method == 'POST':
            title = request.form.get('title', 'Upcoming Placement Recruitment Drive')
            message = request.form.get('message', 'A new campus placement recruitment drive has been announced.')
            try:
                min_cgpa = max(0.0, min(10.0, float(request.form.get('min_cgpa', 6.0))))
            except (TypeError, ValueError):
                min_cgpa = 6.0
            
            # Find eligible students and bulk insert notifications
            eligible_students = db.query(Student).filter(Student.cgpa >= min_cgpa).all()
            if eligible_students:
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)
                db.bulk_insert_mappings(Notification, [
                    {
                        'user_id': s.user_id,
                        'title': title,
                        'message': message,
                        'notification_type': 'job',
                        'link': '/student/jobs',
                        'is_read': False,
                        'created_at': now,
                        'updated_at': now
                    }
                    for s in eligible_students
                ])
                db.commit()
            flash(f"Announcement broadcast successfully dispatched to {len(eligible_students)} eligible students!", 'success')
            return redirect(url_for('officer.broadcast'))

        total_students = db.query(Student).count()
        jobs = db.query(Job).filter_by(status='Active').all()
        return render_template('officer/broadcast.html', total_students=total_students, jobs=jobs)
    finally:
        db.close()


@officer_bp.route('/report/download')
@login_required
@role_required('officer')
def download_institutional_report():
    db = SessionLocal()
    try:
        total_students = db.query(Student).count()
        placed = db.query(Student).filter_by(placement_status='Placed').count()
        rate = round((placed / total_students * 100), 1) if total_students > 0 else 0.0

        stats = {
            'total_students': total_students,
            'eligible_students': db.query(Student).filter(Student.cgpa >= 6.0).count(),
            'offers_count': db.query(Offer).count(),
            'placement_rate': rate,
            'highest_package': db.query(func.max(Offer.package_lpa)).scalar() or 0.0,
            'funnel': PlacementAnalytics.get_placement_funnel(),
            'skill_demand': PlacementAnalytics.get_skill_demand_analytics()
        }

        os.makedirs('reports/generated', exist_ok=True)
        pdf_path = os.path.join('reports/generated', "Institutional_Placement_Report_2026.pdf")
        PlacementReportGenerator.generate_institutional_report(pdf_path, stats)

        return send_file(pdf_path, as_attachment=True, download_name="Institutional_Placement_Report_2026.pdf")
    finally:
        db.close()

