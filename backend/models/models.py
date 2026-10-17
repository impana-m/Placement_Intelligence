from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum, JSON, UniqueConstraint, Index, Numeric
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class TimestampMixin:
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

class Department(Base, TimestampMixin):
    __tablename__ = 'departments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    users = relationship('User', back_populates='department')
    students = relationship('Student', back_populates='department', cascade='all, delete-orphan')

class User(Base, TimestampMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(Enum('student', 'officer', 'faculty', 'recruiter', name='user_roles'), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='SET NULL'), nullable=True)

    department = relationship('Department', back_populates='users')
    student_profile = relationship('Student', back_populates='user', uselist=False, cascade='all, delete-orphan')
    recruiter_profile = relationship('Recruiter', back_populates='user', uselist=False, cascade='all, delete-orphan')
    notifications = relationship('Notification', back_populates='user', cascade='all, delete-orphan')

class Company(Base, TimestampMixin):
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), unique=True, nullable=False)
    industry = Column(String(100), nullable=True)
    website = Column(String(200), nullable=True)
    location = Column(String(150), nullable=True)
    tier = Column(Enum('Tier 1', 'Tier 2', 'Tier 3', 'Startup', name='company_tiers'), default='Tier 2')
    description = Column(Text, nullable=True)
    contact_email = Column(String(120), nullable=True)

    recruiters = relationship('Recruiter', back_populates='company', cascade='all, delete-orphan')
    jobs = relationship('Job', back_populates='company', cascade='all, delete-orphan')

class Recruiter(Base, TimestampMixin):
    __tablename__ = 'recruiters'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    designation = Column(String(100), nullable=True)
    phone = Column(String(30), nullable=True)

    user = relationship('User', back_populates='recruiter_profile')
    company = relationship('Company', back_populates='recruiters')

class Student(Base, TimestampMixin):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    usn = Column(String(50), unique=True, nullable=False, index=True)
    phone = Column(String(30), nullable=True)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='RESTRICT'), nullable=False)
    batch_year = Column(Integer, nullable=False)
    current_semester = Column(Integer, default=6)
    cgpa = Column(Numeric(4, 2), default=0.0)
    attendance_percentage = Column(Float, default=85.0)
    placement_status = Column(Enum('Not Placed', 'In Process', 'Placed', 'Opted Out', name='placement_statuses'), default='Not Placed')
    preferred_roles = Column(String(255), nullable=True)
    preferred_locations = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)

    user = relationship('User', back_populates='student_profile')
    department = relationship('Department', back_populates='students')
    student_skills = relationship('StudentSkill', back_populates='student', cascade='all, delete-orphan')
    projects = relationship('Project', back_populates='student', cascade='all, delete-orphan')
    certifications = relationship('Certification', back_populates='student', cascade='all, delete-orphan')
    internships = relationship('Internship', back_populates='student', cascade='all, delete-orphan')
    resumes = relationship('Resume', back_populates='student', cascade='all, delete-orphan')
    applications = relationship('Application', back_populates='student', cascade='all, delete-orphan')
    test_attempts = relationship('TestAttempt', back_populates='student', cascade='all, delete-orphan')
    mock_interviews = relationship('MockInterviewSession', back_populates='student', cascade='all, delete-orphan')
    actual_interviews = relationship('ActualInterview', back_populates='student', cascade='all, delete-orphan')
    training_enrollments = relationship('TrainingEnrollment', back_populates='student', cascade='all, delete-orphan')
    roadmap_tasks = relationship('RoadmapTask', back_populates='student', cascade='all, delete-orphan')
    interventions = relationship('Intervention', back_populates='student', cascade='all, delete-orphan')
    readiness_history = relationship('ReadinessHistory', back_populates='student', cascade='all, delete-orphan')
    offers = relationship('Offer', back_populates='student', cascade='all, delete-orphan')

class Skill(Base, TimestampMixin):
    __tablename__ = 'skills'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(Enum('Technical', 'Programming', 'Framework', 'Database', 'Cloud/DevOps', 'Soft Skill', name='skill_categories'), default='Technical')
    description = Column(String(255), nullable=True)

class StudentSkill(Base, TimestampMixin):
    __tablename__ = 'student_skills'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    skill_id = Column(Integer, ForeignKey('skills.id', ondelete='CASCADE'), nullable=False)
    proficiency = Column(Enum('Beginner', 'Intermediate', 'Advanced', name='proficiency_levels'), default='Intermediate')
    verified = Column(Boolean, default=False)

    student = relationship('Student', back_populates='student_skills')
    skill = relationship('Skill')
    __table_args__ = (UniqueConstraint('student_id', 'skill_id', name='uq_student_skill'),)

class Project(Base, TimestampMixin):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(150), nullable=False)
    technologies = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    github_url = Column(String(255), nullable=True)
    live_url = Column(String(255), nullable=True)

    student = relationship('Student', back_populates='projects')

class Certification(Base, TimestampMixin):
    __tablename__ = 'certifications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(150), nullable=False)
    issuing_organization = Column(String(150), nullable=True)
    issue_date = Column(DateTime, nullable=True)
    credential_id = Column(String(100), nullable=True)

    student = relationship('Student', back_populates='certifications')

class Internship(Base, TimestampMixin):
    __tablename__ = 'internships'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    company_name = Column(String(150), nullable=False)
    role = Column(String(100), nullable=False)
    duration_months = Column(Integer, default=3)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)

    student = relationship('Student', back_populates='internships')

class Resume(Base, TimestampMixin):
    __tablename__ = 'resumes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    file_path = Column(String(255), nullable=False)
    filename = Column(String(200), nullable=False)
    extracted_text = Column(Text, nullable=True)
    detected_skills = Column(JSON, nullable=True)
    detected_sections = Column(JSON, nullable=True)
    completeness_score = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)

    student = relationship('Student', back_populates='resumes')

class Job(Base, TimestampMixin):
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(150), nullable=False)
    role_type = Column(Enum('Full-Time', 'Internship', 'Internship + PPO', name='role_types'), default='Full-Time')
    location = Column(String(150), nullable=False)
    salary_package = Column(String(100), nullable=True)
    salary_numeric = Column(Numeric(8, 2), default=0.0)
    min_cgpa = Column(Float, default=6.0)
    qualification = Column(String(100), default='BCA / B.Sc / B.Tech')
    experience_required = Column(String(100), default='Freshers / 0-1 yr')
    description = Column(Text, nullable=False)
    selection_process = Column(Text, nullable=True)
    required_skills = Column(Text, nullable=True)
    preferred_skills = Column(Text, nullable=True)
    deadline = Column(DateTime, nullable=True)
    status = Column(
        Enum('Active', 'Paused', 'Closed', 'Draft', name='job_statuses'),
        default='Active',
        nullable=False
    )

    company = relationship('Company', back_populates='jobs')
    applications = relationship('Application', back_populates='job', cascade='all, delete-orphan')

class Application(Base, TimestampMixin):
    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    status = Column(Enum(
        'Applied', 'Shortlisted', 'Test', 'Technical Interview', 'HR Interview',
        'Selected', 'Rejected', 'Offer Received', 'Offer Accepted',
        name='application_statuses'
    ), default='Applied', index=True)
    ai_match_score = Column(Float, default=0.0)
    match_breakdown = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)

    job = relationship('Job', back_populates='applications')
    student = relationship('Student', back_populates='applications')
    interviews = relationship('ActualInterview', back_populates='application', cascade='all, delete-orphan')
    offer = relationship('Offer', back_populates='application', uselist=False, cascade='all, delete-orphan')

    __table_args__ = (UniqueConstraint('job_id', 'student_id', name='uq_job_student_application'),)

class Test(Base, TimestampMixin):
    __tablename__ = 'tests'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(150), nullable=False)
    category = Column(Enum('Aptitude', 'Technical', 'Verbal/Soft', name='test_categories'), default='Technical')
    topic = Column(String(100), nullable=False)
    duration_minutes = Column(Integer, default=20)
    total_marks = Column(Integer, default=10)
    pass_percentage = Column(Float, default=60.0)

    questions = relationship('Question', back_populates='test', cascade='all, delete-orphan')
    attempts = relationship('TestAttempt', back_populates='test', cascade='all, delete-orphan')

class Question(Base, TimestampMixin):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(Integer, ForeignKey('tests.id', ondelete='CASCADE'), nullable=False)
    question_text = Column(Text, nullable=False)
    option_a = Column(String(255), nullable=False)
    option_b = Column(String(255), nullable=False)
    option_c = Column(String(255), nullable=False)
    option_d = Column(String(255), nullable=False)
    correct_option = Column(Enum('A', 'B', 'C', 'D', name='answer_options'), nullable=False)
    explanation = Column(Text, nullable=True)
    topic = Column(String(100), nullable=True)
    difficulty = Column(String(20), default='Medium', nullable=False)
    marks = Column(Integer, default=1, nullable=False)

    test = relationship('Test', back_populates='questions')

class TestAttempt(Base, TimestampMixin):
    __tablename__ = 'test_attempts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(Integer, ForeignKey('tests.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    score = Column(Float, default=0.0)
    total_marks = Column(Integer, default=10)
    percentage = Column(Float, default=0.0)
    passed = Column(Boolean, default=False)
    answers_data = Column(JSON, nullable=True)

    test = relationship('Test', back_populates='attempts')
    student = relationship('Student', back_populates='test_attempts')

class MockInterviewSession(Base, TimestampMixin):
    __tablename__ = 'mock_interview_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    target_role = Column(String(100), nullable=False)
    interview_type = Column(Enum('Technical', 'HR', 'Behavioral', 'Situational', 'Communication', 'Mixed', name='interview_types'), default='Technical')
    total_questions = Column(Integer, default=5)
    overall_score = Column(Float, default=0.0)
    technical_score = Column(Float, default=0.0)
    communication_score = Column(Float, default=0.0)
    relevance_score = Column(Float, default=0.0)
    structure_score = Column(Float, default=0.0)
    feedback_summary = Column(Text, nullable=True)
    strengths = Column(JSON, nullable=True)
    weaknesses = Column(JSON, nullable=True)

    student = relationship('Student', back_populates='mock_interviews')
    qa_items = relationship('MockInterviewQA', back_populates='session', cascade='all, delete-orphan')

class MockInterviewQA(Base, TimestampMixin):
    __tablename__ = 'mock_interview_qa'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('mock_interview_sessions.id', ondelete='CASCADE'), nullable=False)
    question_text = Column(Text, nullable=False)
    category = Column(String(50), default='Technical')
    difficulty = Column(String(20), default='Medium', nullable=False)
    expected_keywords = Column(String(255), nullable=True)
    student_answer = Column(Text, nullable=True)
    time_taken_seconds = Column(Integer, default=0)
    question_score = Column(Float, default=0.0)
    eval_breakdown = Column(JSON, nullable=True)

    session = relationship('MockInterviewSession', back_populates='qa_items')

class ActualInterview(Base, TimestampMixin):
    __tablename__ = 'actual_interviews'

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey('applications.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    round_name = Column(String(100), nullable=False)
    interviewer_name = Column(String(100), nullable=True)
    scheduled_at = Column(DateTime, nullable=False)
    location_or_link = Column(String(255), nullable=True)
    status = Column(Enum('Scheduled', 'Completed', 'Cancelled', 'Rescheduled', name='interview_statuses'), default='Scheduled')
    result = Column(Enum('Pending', 'Selected', 'Rejected', name='interview_results'), default='Pending')
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)

    application = relationship('Application', back_populates='interviews')
    student = relationship('Student', back_populates='actual_interviews')

class TrainingProgram(Base, TimestampMixin):
    __tablename__ = 'training_programs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(150), nullable=False)
    topic_skill = Column(String(100), nullable=False)
    trainer_name = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    capacity = Column(Integer, default=40)
    status = Column(Enum('Upcoming', 'Ongoing', 'Completed', name='training_statuses'), default='Upcoming')

    enrollments = relationship('TrainingEnrollment', back_populates='training', cascade='all, delete-orphan')

class TrainingEnrollment(Base, TimestampMixin):
    __tablename__ = 'training_enrollments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    training_id = Column(Integer, ForeignKey('training_programs.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    enrollment_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(Enum('Enrolled', 'Completed', 'Dropped', name='enrollment_statuses'), default='Enrolled')
    pre_score = Column(Float, nullable=True)
    post_score = Column(Float, nullable=True)
    attendance_rate = Column(Float, default=100.0)
    feedback = Column(Text, nullable=True)

    training = relationship('TrainingProgram', back_populates='enrollments')
    student = relationship('Student', back_populates='training_enrollments')

    __table_args__ = (UniqueConstraint('training_id', 'student_id', name='uq_training_student'),)

class RoadmapTask(Base, TimestampMixin):
    __tablename__ = 'roadmap_tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    stage = Column(Enum(
        'Foundation', 'Skill Development', 'Resume Preparation', 'Aptitude Preparation',
        'Technical Preparation', 'Interview Preparation', 'Application Strategy', 'Placement Preparation',
        name='roadmap_stages'
    ), default='Foundation')
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Enum('Critical', 'High', 'Medium', 'Low', name='task_priorities'), default='Medium')
    status = Column(Enum('Pending', 'In Progress', 'Completed', name='task_statuses'), default='Pending')
    progress_percentage = Column(Integer, default=0)
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    student = relationship('Student', back_populates='roadmap_tasks')

class Intervention(Base, TimestampMixin):
    __tablename__ = 'interventions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    trigger_reason = Column(String(200), nullable=False)
    severity = Column(Enum('Needs Attention', 'Preparation Gap', 'Low Activity', name='intervention_severities'), default='Needs Attention')
    recommendation = Column(Text, nullable=False)
    assigned_faculty = Column(String(100), nullable=True)
    follow_up_date = Column(DateTime, nullable=True)
    status = Column(Enum('Open', 'In Progress', 'Resolved', name='intervention_statuses'), default='Open')
    notes = Column(Text, nullable=True)

    student = relationship('Student', back_populates='interventions')

class ReadinessHistory(Base, TimestampMixin):
    __tablename__ = 'readiness_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    overall_score = Column(Float, nullable=False)
    academic_score = Column(Float, default=0.0)
    technical_score = Column(Float, default=0.0)
    resume_score = Column(Float, default=0.0)
    aptitude_score = Column(Float, default=0.0)
    interview_score = Column(Float, default=0.0)
    activity_score = Column(Float, default=0.0)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    student = relationship('Student', back_populates='readiness_history')

class Offer(Base, TimestampMixin):
    __tablename__ = 'offers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey('applications.id', ondelete='CASCADE'), unique=True, nullable=False)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    company_name = Column(String(150), nullable=False)
    job_title = Column(String(150), nullable=False)
    package_lpa = Column(Numeric(6, 2), nullable=False)
    offer_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(Enum('Offered', 'Accepted', 'Declined', name='offer_statuses'), default='Offered')

    application = relationship('Application', back_populates='offer')
    student = relationship('Student', back_populates='offers')

class Notification(Base, TimestampMixin):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(Enum('job', 'interview', 'test', 'training', 'offer', 'intervention', 'system', name='notif_types'), default='system')
    is_read = Column(Boolean, default=False)
    link = Column(String(255), nullable=True)

    user = relationship('User', back_populates='notifications')

    __table_args__ = (
        Index('idx_notification_user_read', 'user_id', 'is_read'),
    )
