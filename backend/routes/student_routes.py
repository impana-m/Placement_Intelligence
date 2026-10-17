import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from werkzeug.utils import secure_filename
from backend.models.database import SessionLocal
from backend.models.models import (
    Student, User, StudentSkill, Skill, Project, Certification, Internship,
    Resume, Job, Application, TestAttempt, MockInterviewSession, RoadmapTask,
    Intervention, ReadinessHistory, Offer, Notification, Department, ActualInterview
)
from backend.auth.security import login_required, role_required
from ai.job_matching.matcher import LocalJobMatchingEngine
from ai.skill_gap.engine import SkillGapEngine
from ai.readiness.scorer import CareerReadinessScorer
from ai.resume.parser import ResumeParser
from ai.simulation.simulator import CareerSimulator
from reports.pdf_generator import PlacementReportGenerator
from config import Config

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
@login_required
@role_required('student')
def dashboard():
    student_id = session.get('student_id')
    db = SessionLocal()
    try:
        student = db.query(Student).filter_by(id=student_id).first()
        if not student:
            flash('Student record not found.', 'danger')
            return redirect(url_for('auth.logout'))

        # Fetch active jobs
        jobs = db.query(Job).filter_by(status='Active').all()

        # Compute AI match scores on active jobs
        matcher = LocalJobMatchingEngine()
        student_data = {
            'skills': [{'name': s.skill.name, 'proficiency': s.proficiency} for s in student.student_skills],
            'cgpa': student.cgpa,
            'projects': [{'title': p.title, 'technologies': p.technologies, 'description': p.description} for p in student.projects],
            'internships': [{'role': i.role, 'description': i.description} for i in student.internships],
            'bio': student.bio
        }

        matched_jobs = []
        for j in jobs:
            j_dict = {
                'title': j.title,
                'description': j.description,
                'required_skills': j.required_skills,
                'preferred_skills': j.preferred_skills,
                'min_cgpa': j.min_cgpa
            }
            m_res = matcher.compute_match(student_data, j_dict)
            matched_jobs.append({
                'job': j,
                'match': m_res
            })

        matched_jobs.sort(key=lambda x: x['match']['overall_match'], reverse=True)

        # Career Readiness
        scorer = CareerReadinessScorer()
        resume_comp = student.resumes[0].completeness_score if student.resumes else 0.0
        readiness_input = dict(student_data)
        readiness_input['attendance'] = student.attendance_percentage
        readiness_input['resume_completeness'] = resume_comp
        readiness_input['test_attempts'] = [{'percentage': t.percentage} for t in student.test_attempts]
        readiness_input['mock_interviews'] = [{'overall_score': m.overall_score} for m in student.mock_interviews]
        readiness = scorer.compute_readiness(readiness_input)

        # Roadmap progress
        tasks = student.roadmap_tasks
        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.status == 'Completed')
        roadmap_pct = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0

        # Notifications
        notifications = db.query(Notification).filter_by(user_id=student.user_id).order_by(Notification.created_at.desc()).limit(5).all()
        unread_notifications = db.query(Notification).filter_by(user_id=student.user_id, is_read=False).count()
        upcoming_interviews = db.query(ActualInterview).filter_by(student_id=student.id, status='Scheduled').order_by(ActualInterview.scheduled_at.asc()).limit(5).all()
        qt_attempts = db.query(TestAttempt).filter_by(student_id=student.id).order_by(TestAttempt.created_at.desc()).limit(5).all()
        mock_sessions = db.query(MockInterviewSession).filter_by(student_id=student.id).order_by(MockInterviewSession.created_at.desc()).limit(5).all()

        weak_topics = []
        for attempt in qt_attempts:
            for topic, stats in (attempt.answers_data or {}).get('topic_stats', {}).items():
                if stats.get('total') and stats.get('correct', 0) / stats['total'] < 0.6:
                    weak_topics.append(topic)
        weak_topics = list(dict.fromkeys(weak_topics))[:4]

        return render_template(
            'student/dashboard.html',
            student=student,
            matched_jobs=matched_jobs[:4],
            readiness=readiness,
            roadmap_pct=roadmap_pct,
            tasks=tasks,
            applications=student.applications,
            notifications=notifications,
            unread_notifications=unread_notifications,
            upcoming_interviews=upcoming_interviews,
            qt_attempts=qt_attempts,
            mock_sessions=mock_sessions,
            weak_topics=weak_topics
        )
    finally:
        db.close()

@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('student')
def profile():
    student_id = session.get('student_id')
    db = SessionLocal()
    try:
        student = db.query(Student).filter_by(id=student_id).first()
        all_skills = db.query(Skill).all()

        if request.method == 'POST':
            student.phone = request.form.get('phone', student.phone)
            student.preferred_roles = request.form.get('preferred_roles', student.preferred_roles)
            student.preferred_locations = request.form.get('preferred_locations', student.preferred_locations)
            student.bio = request.form.get('bio', student.bio)

            # Update skills
            skill_ids = request.form.getlist('skill_ids')
            proficiencies = request.form.getlist('proficiencies')

            # Clear existing skills and replace
            db.query(StudentSkill).filter_by(student_id=student.id).delete()
            for sid, prof in zip(skill_ids, proficiencies):
                if sid:
                    db.add(StudentSkill(
                        student_id=student.id,
                        skill_id=int(sid),
                        proficiency=prof,
                        verified=False
                    ))

            db.commit()
            flash('Profile and skills updated successfully!', 'success')
            return redirect(url_for('student.profile'))

        return render_template('student/profile.html', student=student, all_skills=all_skills)
    finally:
        db.close()

@student_bp.route('/resume', methods=['GET', 'POST'])
@login_required
@role_required('student')
def resume_management():
    student_id = session.get('student_id')
    db = SessionLocal()
    try:
        student = db.query(Student).filter_by(id=student_id).first()
        resume_record = student.resumes[0] if student.resumes else None

        if request.method == 'POST':
            if 'resume_file' not in request.files:
                flash('No file part provided.', 'danger')
                return redirect(request.url)
            file = request.files['resume_file']
            if file.filename == '':
                flash('No file selected.', 'warning')
                return redirect(request.url)

            ext = file.filename.rsplit('.', 1)[-1].lower()
            if ext not in Config.ALLOWED_EXTENSIONS:
                flash('Only PDF and DOCX documents are accepted.', 'danger')
                return redirect(request.url)

            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
            safe_fname = secure_filename(f"resume_std_{student.id}_{file.filename}")
            save_path = os.path.join(Config.UPLOAD_FOLDER, safe_fname)
            file.save(save_path)

            # Parse locally using PyMuPDF / python-docx
            parser = ResumeParser()
            parse_res = parser.parse_resume(save_path)

            if resume_record:
                resume_record.file_path = save_path
                resume_record.filename = safe_fname
                resume_record.extracted_text = parse_res['raw_text']
                resume_record.detected_skills = parse_res['detected_skills']
                resume_record.detected_sections = parse_res['detected_sections']
                resume_record.completeness_score = parse_res['completeness_score']
            else:
                resume_record = Resume(
                    student_id=student.id,
                    file_path=save_path,
                    filename=safe_fname,
                    extracted_text=parse_res['raw_text'],
                    detected_skills=parse_res['detected_skills'],
                    detected_sections=parse_res['detected_sections'],
                    completeness_score=parse_res['completeness_score'],
                    is_active=True
                )
                db.add(resume_record)

            db.commit()
            flash('Resume uploaded and analyzed successfully with local intelligence!', 'success')
            return redirect(url_for('student.resume_management'))

        return render_template('student/resume.html', student=student, resume=resume_record)
    finally:
        db.close()

@student_bp.route('/jobs')
@login_required
@role_required('student')
def jobs_list():
    student_id = session.get('student_id')
    db = SessionLocal()
    try:
        student = db.query(Student).filter_by(id=student_id).first()
        jobs = db.query(Job).filter_by(status='Active').all()

        matcher = LocalJobMatchingEngine()
        student_data = {
            'skills': [{'name': s.skill.name, 'proficiency': s.proficiency} for s in student.student_skills],
            'cgpa': student.cgpa,
            'projects': [{'title': p.title, 'technologies': p.technologies, 'description': p.description} for p in student.projects],
            'internships': [{'role': i.role, 'description': i.description} for i in student.internships],
            'bio': student.bio
        }

        # Check existing applications
        applied_job_ids = {a.job_id: a.status for a in student.applications}

        job_items = []
        for j in jobs:
            j_dict = {
                'title': j.title,
                'description': j.description,
                'required_skills': j.required_skills,
                'preferred_skills': j.preferred_skills,
                'min_cgpa': j.min_cgpa
            }
            m_res = matcher.compute_match(student_data, j_dict)
            job_items.append({
                'job': j,
                'match': m_res,
                'applied_status': applied_job_ids.get(j.id)
            })

        job_items.sort(key=lambda x: x['match']['overall_match'], reverse=True)

        return render_template('student/jobs.html', jobs=job_items, student=student)
    finally:
        db.close()

@student_bp.route('/jobs/<int:job_id>/apply', methods=['POST'])
@login_required
@role_required('student')
def apply_job(job_id):
    student_id = session.get('student_id')
    db = SessionLocal()
    try:
        student = db.query(Student).filter_by(id=student_id).first()
        job = db.query(Job).filter_by(id=job_id).first()
        if not job:
            flash('Job not found.', 'danger')
            return redirect(url_for('student.jobs_list'))

        if job.status != 'Active':
            flash(f"This job drive is currently {job.status.lower()} and is not accepting applications.", 'warning')
            return redirect(url_for('student.jobs_list'))
        if job.deadline and datetime.utcnow() > job.deadline:
            flash('The application deadline for this job has passed.', 'warning')
            return redirect(url_for('student.jobs_list'))
        if student.cgpa < job.min_cgpa:
            flash(f'You are not eligible. Minimum CGPA required: {job.min_cgpa}.', 'warning')
            return redirect(url_for('student.jobs_list'))

        existing = db.query(Application).filter_by(student_id=student.id, job_id=job.id).first()
        if existing:
            flash('You have already applied for this position.', 'warning')
            return redirect(url_for('student.jobs_list'))

        # Calculate AI match score
        matcher = LocalJobMatchingEngine()
        student_data = {
            'skills': [{'name': s.skill.name, 'proficiency': s.proficiency} for s in student.student_skills],
            'cgpa': student.cgpa,
            'projects': [{'title': p.title, 'technologies': p.technologies, 'description': p.description} for p in student.projects],
            'internships': [{'role': i.role, 'description': i.description} for i in student.internships],
            'bio': student.bio
        }
        j_dict = {
            'title': job.title,
            'description': job.description,
            'required_skills': job.required_skills,
            'preferred_skills': job.preferred_skills,
            'min_cgpa': job.min_cgpa
        }
        match_res = matcher.compute_match(student_data, j_dict)

        new_app = Application(
            student_id=student.id,
            job_id=job.id,
            status='Applied',
            ai_match_score=match_res['overall_match'],
            match_breakdown=match_res,
            notes='Candidate submitted application via portal.'
        )
        db.add(new_app)
        db.commit()
        flash(f'Successfully applied for {job.title} at {job.company.name}!', 'success')
        return redirect(url_for('student.applications_list'))
    finally:
        db.close()

@student_bp.route('/applications')
@login_required
@role_required('student')
def applications_list():
    student_id = session.get('student_id')
    db = SessionLocal()
    try:
        student = db.query(Student).filter_by(id=student_id).first()
        return render_template('student/applications.html', student=student, applications=student.applications)
    finally:
        db.close()

@student_bp.route('/skill-gap/<int:job_id>')
@login_required
@role_required('student')
def skill_gap_analysis(job_id):
    student_id = session.get('student_id')
    db = SessionLocal()
    try:
        student = db.query(Student).filter_by(id=student_id).first()
        job = db.query(Job).filter_by(id=job_id).first()
        if not job:
            flash('Job not found.', 'danger')
            return redirect(url_for('student.jobs_list'))

        student_skills = [{'name': s.skill.name, 'proficiency': s.proficiency} for s in student.student_skills]
        engine = SkillGapEngine()
        gap_res = engine.analyze_gaps(student_skills, job.required_skills, job.preferred_skills)

        return render_template('student/skill_gap.html', student=student, job=job, gap=gap_res)
    finally:
        db.close()

@student_bp.route('/simulator', methods=['GET', 'POST'])
@login_required
@role_required('student')
def simulator():
    student_id = session.get('student_id')
    db = SessionLocal()
    try:
        student = db.query(Student).filter_by(id=student_id).first()
        sim_engine = CareerSimulator()

        base_data = {
            'cgpa': student.cgpa,
            'attendance': student.attendance_percentage,
            'skills': [{'name': s.skill.name, 'proficiency': s.proficiency} for s in student.student_skills],
            'projects': [{'title': p.title} for p in student.projects],
            'certifications': [{'name': c.name} for c in student.certifications],
            'internships': [{'role': i.role} for i in student.internships],
            'test_attempts': [{'percentage': t.percentage} for t in student.test_attempts],
            'mock_interviews': [{'overall_score': m.overall_score} for m in student.mock_interviews],
            'resume_completeness': student.resumes[0].completeness_score if student.resumes else 60.0
        }

        sim_result = None
        if request.method == 'POST':
            scenario = {
                'upgraded_skills': {},
                'added_projects': int(request.form.get('added_projects', 0)),
                'added_certifications': int(request.form.get('added_certifications', 0)),
                'added_internship': request.form.get('added_internship') == 'on',
                'simulated_aptitude_pct': float(request.form.get('sim_aptitude', 85.0)),
                'simulated_interview_score': float(request.form.get('sim_interview', 80.0)),
                'simulated_resume_score': float(request.form.get('sim_resume', 90.0))
            }
            if request.form.get('upgrade_python'):
                scenario['upgraded_skills']['python'] = 'Advanced'
            if request.form.get('upgrade_sql'):
                scenario['upgraded_skills']['sql'] = 'Advanced'
            if request.form.get('add_docker'):
                scenario['added_skills'] = [{'name': 'Docker', 'proficiency': 'Intermediate'}]

            sim_result = sim_engine.simulate_what_if(base_data, scenario)

        return render_template('student/simulator.html', student=student, sim_result=sim_result)
    finally:
        db.close()

@student_bp.route('/roadmap', methods=['GET', 'POST'])
@login_required
@role_required('student')
def roadmap():
    student_id = session.get('student_id')
    db = SessionLocal()
    try:
        student = db.query(Student).filter_by(id=student_id).first()
        if request.method == 'POST':
            task_id = request.form.get('task_id')
            new_status = request.form.get('status')
            new_prog = int(request.form.get('progress', 0))
            task = db.query(RoadmapTask).filter_by(id=task_id, student_id=student.id).first()
            if task:
                task.status = new_status
                task.progress_percentage = new_prog
                db.commit()
                flash('Roadmap task updated!', 'success')
            return redirect(url_for('student.roadmap'))

        return render_template('student/roadmap.html', student=student, tasks=student.roadmap_tasks)
    finally:
        db.close()

@student_bp.route('/report/download')
@login_required
@role_required('student')
def download_student_report():
    student_id = session.get('student_id')
    db = SessionLocal()
    try:
        student = db.query(Student).filter_by(id=student_id).first()
        scorer = CareerReadinessScorer()
        student_data = {
            'full_name': student.user.full_name,
            'usn': student.usn,
            'department': student.department.name,
            'cgpa': student.cgpa,
            'skills': [{'name': s.skill.name, 'proficiency': s.proficiency} for s in student.student_skills],
            'projects': student.projects,
            'internships': student.internships
        }
        readiness_input = dict(student_data)
        readiness_input['attendance'] = student.attendance_percentage
        readiness_input['resume_completeness'] = student.resumes[0].completeness_score if student.resumes else 70.0
        readiness_input['test_attempts'] = [{'percentage': t.percentage} for t in student.test_attempts]
        readiness_input['mock_interviews'] = [{'overall_score': m.overall_score} for m in student.mock_interviews]
        student_data['readiness'] = scorer.compute_readiness(readiness_input)

        os.makedirs('reports/generated', exist_ok=True)
        pdf_path = os.path.join('reports/generated', f"Student_Report_{student.usn}.pdf")
        PlacementReportGenerator.generate_student_report(pdf_path, student_data)

        return send_file(pdf_path, as_attachment=True, download_name=f"Career_Intelligence_{student.usn}.pdf")
    finally:
        db.close()

@student_bp.route('/resume/builder', methods=['GET', 'POST'])
@login_required
@role_required('student')
def resume_builder():
    student_id = session.get('student_id')
    db = SessionLocal()
    try:
        student = db.query(Student).filter_by(id=student_id).first()
        if request.method == 'POST':
            student.bio = request.form.get('summary', student.bio)
            student.phone = request.form.get('phone', student.phone)
            
            # Optional project addition
            proj_title = request.form.get('project_title')
            proj_tech = request.form.get('project_tech')
            proj_desc = request.form.get('project_desc')
            if proj_title and proj_desc:
                db.add(Project(
                    student_id=student.id,
                    title=proj_title,
                    technologies=proj_tech or 'Python, MySQL',
                    description=proj_desc
                ))

            # Optional internship addition
            intern_comp = request.form.get('intern_company')
            intern_role = request.form.get('intern_role')
            intern_desc = request.form.get('intern_desc')
            if intern_comp and intern_role:
                db.add(Internship(
                    student_id=student.id,
                    company_name=intern_comp,
                    role=intern_role,
                    description=intern_desc or 'Worked on software engineering tasks.'
                ))

            db.commit()
            flash('Resume builder details updated successfully!', 'success')
            return redirect(url_for('student.resume_builder'))

        # Calculate live ATS score
        ats_score = 0
        if student.bio and len(student.bio) > 30:
            ats_score += 15
        if student.student_skills:
            ats_score += min(25, len(student.student_skills) * 5)
        if student.projects:
            ats_score += 10
        if student.internships:
            ats_score += 10

        return render_template('student/resume_builder.html', student=student, ats_score=min(100, ats_score))
    finally:
        db.close()

@student_bp.route('/resume/export-pdf')
@login_required
@role_required('student')
def export_resume_pdf():
    student_id = session.get('student_id')
    db = SessionLocal()
    try:
        student = db.query(Student).filter_by(id=student_id).first()
        resume_data = {
            'full_name': student.user.full_name,
            'email': student.user.email,
            'phone': student.phone or '',
            'usn': student.usn,
            'department': student.department.name,
            'cgpa': student.cgpa,
            'batch_year': student.batch_year,
            'summary': student.bio or 'Dedicated BCA software engineering student with proven problem solving and hands-on full-stack development experience.',
            'skills': [s.skill.name for s in student.student_skills],
            'projects': [{'title': p.title, 'technologies': p.technologies, 'description': p.description} for p in student.projects],
            'internships': [{'company_name': i.company_name, 'role': i.role, 'description': i.description} for i in student.internships]
        }

        os.makedirs('reports/generated', exist_ok=True)
        pdf_path = os.path.join('reports/generated', f"ATS_Resume_{student.usn}.pdf")
        PlacementReportGenerator.generate_resume_pdf(pdf_path, resume_data)

        return send_file(pdf_path, as_attachment=True, download_name=f"Resume_{student.user.full_name.replace(' ', '_')}.pdf")
    finally:
        db.close()

@student_bp.route('/offers/<int:offer_id>/decision', methods=['POST'])
@login_required
@role_required('student')
def offer_decision(offer_id):
    student_id = session.get('student_id')
    db = SessionLocal()
    try:
        decision = request.form.get('decision')
        offer = db.query(Offer).filter_by(id=offer_id, student_id=student_id).first()
        if offer:
            # Prevent re-toggling already decided offers
            if offer.status in ('Accepted', 'Declined'):
                flash(f'This offer has already been {offer.status.lower()}. Decision cannot be changed.', 'warning')
                return redirect(url_for('student.applications_list'))
            if decision == 'accept':
                offer.status = 'Accepted'
                student = db.query(Student).filter_by(id=student_id).first()
                if student:
                    student.placement_status = 'Placed'
                if offer.application:
                    offer.application.status = 'Offer Accepted'
                db.commit()
                flash(f'🎉 Congratulations! You have formally accepted the offer from {offer.company_name} ({offer.package_lpa} LPA)! Your status is now PLACED.', 'success')
            elif decision == 'decline':
                offer.status = 'Declined'
                db.commit()
                flash(f'Offer from {offer.company_name} was declined.', 'info')
        return redirect(url_for('student.applications_list'))
    finally:
        db.close()

@student_bp.route('/notifications')
@login_required
@role_required('student')
def notifications():
    user_id = session.get('user_id')
    db = SessionLocal()
    try:
        notifs = db.query(Notification).filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
        unread_count = sum(1 for n in notifs if not n.is_read)
        return render_template('student/notifications.html', notifications=notifs, unread_count=unread_count)
    finally:
        db.close()

@student_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
@role_required('student')
def mark_notification_read(notification_id):
    db = SessionLocal()
    try:
        notification = db.query(Notification).filter_by(
            id=notification_id, user_id=session.get('user_id')
        ).first()
        if notification:
            notification.is_read = True
            db.commit()
        return redirect(url_for('student.notifications'))
    finally:
        db.close()

@student_bp.route('/notifications/read-all', methods=['POST'])
@login_required
@role_required('student')
def mark_all_notifications_read():
    db = SessionLocal()
    try:
        db.query(Notification).filter_by(user_id=session.get('user_id'), is_read=False).update(
            {'is_read': True}, synchronize_session=False
        )
        db.commit()
        flash('All notifications marked as read.', 'success')
        return redirect(url_for('student.notifications'))
    finally:
        db.close()

