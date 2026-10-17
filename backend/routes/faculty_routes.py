from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from sqlalchemy.orm import joinedload
from backend.models.database import SessionLocal
from backend.models.models import Student, Department, Application, Intervention, User, Skill, StudentSkill, Job
from backend.auth.security import login_required, role_required
from backend.analytics.funnel import PlacementAnalytics

faculty_bp = Blueprint('faculty', __name__, url_prefix='/faculty')

@faculty_bp.route('/dashboard')
@login_required
@role_required('faculty')
def dashboard():
    dept_id = session.get('department_id')
    db = SessionLocal()
    try:
        dept = db.query(Department).filter_by(id=dept_id).first()
        dept_students = db.query(Student).options(
            joinedload(Student.user),
            joinedload(Student.student_skills)
        ).filter_by(department_id=dept_id).all() if dept_id else []

        total_students = len(dept_students)
        placed_students = sum(1 for s in dept_students if s.placement_status == 'Placed')
        placement_rate = round((placed_students / total_students * 100), 1) if total_students > 0 else 0.0
        avg_cgpa = round(sum(s.cgpa for s in dept_students) / max(1, total_students), 2)

        # Department Funnel
        funnel = PlacementAnalytics.get_placement_funnel(department_id=dept_id)
        interventions = db.query(Intervention).options(
            joinedload(Intervention.student).joinedload(Student.user)
        ).join(Student).filter(Student.department_id == dept_id, Intervention.status == 'Open').all()

        return render_template(
            'faculty/dashboard.html',
            department=dept,
            students=dept_students,
            total_students=total_students,
            placed_students=placed_students,
            placement_rate=placement_rate,
            avg_cgpa=avg_cgpa,
            funnel=funnel,
            interventions=interventions
        )
    finally:
        db.close()

@faculty_bp.route('/students')
@login_required
@role_required('faculty')
def students():
    dept_id = session.get('department_id')
    db = SessionLocal()
    try:
        dept = db.query(Department).filter_by(id=dept_id).first()
        dept_students = db.query(Student).options(joinedload(Student.user)).filter_by(department_id=dept_id).all() if dept_id else []
        return render_template('faculty/students.html', department=dept, students=dept_students)
    finally:
        db.close()

@faculty_bp.route('/curriculum')
@login_required
@role_required('faculty')
def curriculum():
    dept_id = session.get('department_id')
    db = SessionLocal()
    try:
        dept = db.query(Department).filter_by(id=dept_id).first()
        # Compute skill demand from active drives and department proficiency
        active_jobs = db.query(Application).join(Student).filter(Student.department_id == dept_id).count()
        jobs = db.query(Job).filter(Job.status == 'Active').all()
        demand = {}
        for job in jobs:
            for raw in (job.required_skills or '').split(','):
                skill_name = raw.strip()
                if skill_name:
                    demand[skill_name] = demand.get(skill_name, 0) + 3
            for raw in (job.preferred_skills or '').split(','):
                skill_name = raw.strip()
                if skill_name:
                    demand[skill_name] = demand.get(skill_name, 0) + 1

        proficiency_map = {'Beginner': 40, 'Intermediate': 75, 'Advanced': 100}
        demand_skills = []
        dept_students = db.query(Student).filter_by(department_id=dept_id).all() if dept_id else []
        for name, score in sorted(demand.items(), key=lambda x: x[1], reverse=True)[:8]:
            values = []
            for student in dept_students:
                for student_skill in student.student_skills:
                    if student_skill.skill and student_skill.skill.name.lower() == name.lower():
                        values.append(proficiency_map.get(student_skill.proficiency, 50))
            proficiency = round(sum(values) / len(values), 1) if values else 0.0
            demand_label = 'Critical' if score >= 9 else ('High' if score >= 5 else 'Emerging')
            status = 'Strong Alignment' if proficiency >= 75 else ('Needs Lab Focus' if proficiency >= 50 else 'Curriculum Gap')
            demand_skills.append({'name': name, 'industry_demand': demand_label, 'dept_proficiency': f'{proficiency:.0f}%', 'status': status})

        if not demand_skills:
            demand_skills = [{'name': 'No active-drive skill demand yet', 'industry_demand': 'No Data', 'dept_proficiency': '0%', 'status': 'Awaiting job data'}]
        return render_template('faculty/curriculum.html', department=dept, skills=demand_skills)
    finally:
        db.close()

@faculty_bp.route('/interventions', methods=['GET', 'POST'])
@login_required
@role_required('faculty')
def interventions():
    dept_id = session.get('department_id')
    db = SessionLocal()
    try:
        if request.method == 'POST':
            student_id = request.form.get('student_id')
            reason = request.form.get('reason')
            action_plan = request.form.get('action_plan')
            if student_id and reason:
                # Verify student belongs to faculty's department
                try:
                    sid = int(student_id)
                except (TypeError, ValueError):
                    flash('Invalid student ID.', 'danger')
                    return redirect(url_for('faculty.interventions'))
                target_student = db.query(Student).filter_by(id=sid, department_id=dept_id).first()
                if not target_student:
                    flash('Unauthorized: Student does not belong to your department.', 'danger')
                    return redirect(url_for('faculty.interventions'))
                new_inv = Intervention(
                    student_id=sid,
                    trigger_reason=reason,
                    recommendation=action_plan or 'Faculty Mentorship & Skill Drill',
                    status='Open'
                )
                db.add(new_inv)
                db.commit()
                flash('Academic intervention logged successfully!', 'success')
            return redirect(url_for('faculty.interventions'))

        dept_students = db.query(Student).options(joinedload(Student.user)).filter_by(department_id=dept_id).all() if dept_id else []
        items = db.query(Intervention).options(
            joinedload(Intervention.student).joinedload(Student.user)
        ).join(Student).filter(Student.department_id == dept_id).order_by(Intervention.created_at.desc()).all()
        
        return render_template('faculty/interventions.html', students=dept_students, interventions=items)
    finally:
        db.close()

