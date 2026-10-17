import os
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from backend.models.database import SessionLocal, init_db
from backend.models.models import (
    Department, User, Company, Recruiter, Student, Skill, StudentSkill,
    Project, Certification, Internship, Resume, Job, Application,
    Test, Question, TestAttempt, MockInterviewSession, MockInterviewQA,
    ActualInterview, TrainingProgram, TrainingEnrollment, RoadmapTask,
    Intervention, ReadinessHistory, Offer, Notification
)
from ai.readiness.scorer import CareerReadinessScorer

def seed_database():
    init_db()
    db = SessionLocal()
    try:
        print("Starting realistic database seed...")

        # 1. Departments
        dept_data = [
            ('Computer Applications', 'BCA', 'Department of Computer Applications & Information Technology'),
            ('Computer Science & Engineering', 'CSE', 'Department of Computer Science & Engineering'),
            ('Information Science', 'ISE', 'Department of Information Science & Engineering'),
            ('Data Science & AI', 'DSAI', 'Department of Data Science and Artificial Intelligence')
        ]
        departments = {}
        for name, code, desc in dept_data:
            dept = db.query(Department).filter_by(code=code).first()
            if not dept:
                dept = Department(name=name, code=code, description=desc)
                db.add(dept)
                db.flush()
            departments[code] = dept
        print(f"  [OK] {len(departments)} Departments verified.")

        # 2. Master Skills Catalogue
        skill_catalog = [
            ('Python', 'Programming'),
            ('Java', 'Programming'),
            ('C++', 'Programming'),
            ('JavaScript', 'Programming'),
            ('SQL', 'Database'),
            ('MySQL', 'Database'),
            ('PostgreSQL', 'Database'),
            ('MongoDB', 'Database'),
            ('Flask', 'Framework'),
            ('Django', 'Framework'),
            ('React', 'Framework'),
            ('Machine Learning', 'Technical'),
            ('Data Analysis', 'Technical'),
            ('Docker', 'Cloud/DevOps'),
            ('AWS', 'Cloud/DevOps'),
            ('Git & GitHub', 'Technical'),
            ('Problem Solving', 'Soft Skill'),
            ('Technical Communication', 'Soft Skill'),
            ('Agile / Scrum', 'Soft Skill')
        ]
        skills = {}
        for sname, scat in skill_catalog:
            sk = db.query(Skill).filter_by(name=sname).first()
            if not sk:
                sk = Skill(name=sname, category=scat, description=f"{sname} competency for modern software engineering")
                db.add(sk)
                db.flush()
            skills[sname] = sk
        print(f"  [OK] {len(skills)} Skills verified.")

        # 3. Companies & Recruiters
        company_info = [
            ('TechCorp Solutions', 'IT Services & Consulting', 'https://techcorp.example.com', 'Bangalore, India', 'Tier 1', 'Leading global cloud transformation and AI consultancy.'),
            ('FinTech Labs', 'Financial Technology', 'https://fintechlabs.example.com', 'Mumbai, India', 'Tier 1', 'Next-generation algorithmic trading and high-frequency payment gateways.'),
            ('NextGen Innovations', 'Product Development & SaaS', 'https://nextgen.example.com', 'Hyderabad, India', 'Tier 2', 'High-growth B2B enterprise workflow intelligence.'),
            ('DataPulse Analytics', 'Data & AI Intelligence', 'https://datapulse.example.com', 'Bangalore, India', 'Tier 2', 'Predictive behavioral analytics and business intelligence engines.')
        ]
        companies = {}
        recruiters = {}
        pw_hash = generate_password_hash('Password@123', method='pbkdf2:sha256')

        for cname, ind, web, loc, tier, desc in company_info:
            c = db.query(Company).filter_by(name=cname).first()
            if not c:
                c = Company(name=cname, industry=ind, website=web, location=loc, tier=tier, description=desc, contact_email=f"careers@{cname.lower().replace(' ', '')}.com")
                db.add(c)
                db.flush()
            companies[cname] = c

            rec_email = f"recruiter@{cname.lower().replace(' ', '')}.com"
            r_user = db.query(User).filter_by(email=rec_email).first()
            if not r_user:
                r_user = User(email=rec_email, password_hash=pw_hash, full_name=f"Lead Recruiter ({cname.split()[0]})", role='recruiter')
                db.add(r_user)
                db.flush()
                rec = Recruiter(user_id=r_user.id, company_id=c.id, designation='Senior Talent Acquisition Manager', phone='+91 98765 43210')
                db.add(rec)
                db.flush()
                recruiters[cname] = rec
        print(f"  [OK] {len(companies)} Companies & Recruiters initialized.")

        # 4. Placement Officers & Faculty
        officer_user = db.query(User).filter_by(email='officer@college.edu').first()
        if not officer_user:
            officer_user = User(
                email='officer@college.edu',
                password_hash=pw_hash,
                full_name='Dr. Ramesh Sharma (Placement Director)',
                role='officer'
            )
            db.add(officer_user)
            db.flush()

        faculty_user = db.query(User).filter_by(email='faculty.bca@college.edu').first()
        if not faculty_user:
            faculty_user = User(
                email='faculty.bca@college.edu',
                password_hash=pw_hash,
                full_name='Prof. Anitha Rao (BCA Placement Coordinator)',
                role='faculty',
                department_id=departments['BCA'].id
            )
            db.add(faculty_user)
            db.flush()
        print("  [OK] Placement Officer and Faculty accounts verified.")

        # 5. Core Student Profiles
        student_configs = [
            {
                'email': 'student.rahul@college.edu',
                'name': 'Rahul Sharma',
                'usn': '1BC22001',
                'dept': 'BCA',
                'cgpa': 8.7,
                'status': 'Placed',
                'skills': [('Python', 'Advanced'), ('SQL', 'Advanced'), ('Flask', 'Intermediate'), ('Git & GitHub', 'Advanced'), ('Machine Learning', 'Intermediate')],
                'projects': [
                    ('AI Decision Memory Vault', 'Python, Flask, MySQL, Scikit-Learn', 'Institutional memory system with local TF-IDF conflict heuristics.'),
                    ('Predictive Hospital Triage Engine', 'Python, Pandas, Scikit-Learn', 'Classification model predicting emergency patient admission with 91% recall.')
                ],
                'cert': ('Python Certified Associate Programmer (PCAP)', 'Python Institute'),
                'intern': ('FinTech Labs', 'Backend Engineering Intern', 3)
            },
            {
                'email': 'student.priya@college.edu',
                'name': 'Priya Patel',
                'usn': '1BC22002',
                'dept': 'BCA',
                'cgpa': 8.2,
                'status': 'In Process',
                'skills': [('Java', 'Advanced'), ('SQL', 'Intermediate'), ('React', 'Intermediate'), ('JavaScript', 'Intermediate')],
                'projects': [
                    ('E-Commerce Cloud Gateway', 'Java, Spring Boot, MySQL', 'Microservices order fulfillment service with JWT authentication.')
                ],
                'cert': ('Oracle Certified Java Associate', 'Oracle'),
                'intern': None
            },
            {
                'email': 'student.arjun@college.edu',
                'name': 'Arjun Mehta',
                'usn': '1BC22003',
                'dept': 'BCA',
                'cgpa': 7.1,
                'status': 'In Process',
                'skills': [('Python', 'Beginner'), ('SQL', 'Intermediate'), ('HTML', 'Intermediate')],
                'projects': [
                    ('Student Management Portal', 'Python, SQLite', 'Basic CRUD portal for internal grade verification.')
                ],
                'cert': None,
                'intern': None
            },
            {
                'email': 'student.sneha@college.edu',
                'name': 'Sneha Nair',
                'usn': '1CS22010',
                'dept': 'CSE',
                'cgpa': 9.1,
                'status': 'Placed',
                'skills': [('Python', 'Advanced'), ('Docker', 'Intermediate'), ('AWS', 'Intermediate'), ('SQL', 'Advanced')],
                'projects': [
                    ('Serverless Event Pipeline', 'Python, AWS Lambda, Docker', 'Real-time telemetry event processor with S3 ingestion.')
                ],
                'cert': ('AWS Certified Cloud Practitioner', 'Amazon Web Services'),
                'intern': ('TechCorp Solutions', 'Cloud Developer Intern', 6)
            }
        ]

        scorer = CareerReadinessScorer()
        created_students = []

        for sc in student_configs:
            u = db.query(User).filter_by(email=sc['email']).first()
            if not u:
                u = User(
                    email=sc['email'],
                    password_hash=pw_hash,
                    full_name=sc['name'],
                    role='student',
                    department_id=departments[sc['dept']].id
                )
                db.add(u)
                db.flush()

                s = Student(
                    user_id=u.id,
                    usn=sc['usn'],
                    phone='+91 91234 56789',
                    department_id=departments[sc['dept']].id,
                    batch_year=2026,
                    current_semester=6,
                    cgpa=sc['cgpa'],
                    attendance_percentage=88.5,
                    placement_status=sc['status'],
                    preferred_roles='Software Engineer, Backend Developer, Data Analyst',
                    preferred_locations='Bangalore, Hyderabad, Pune',
                    bio=f"Passionate {sc['dept']} undergraduate focused on high-reliability backend systems and real-world software engineering."
                )
                db.add(s)
                db.flush()

                # Skills
                for sk_name, prof in sc['skills']:
                    if sk_name in skills:
                        db.add(StudentSkill(student_id=s.id, skill_id=skills[sk_name].id, proficiency=prof, verified=True))

                # Projects
                for ptitle, ptech, pdesc in sc['projects']:
                    db.add(Project(student_id=s.id, title=ptitle, technologies=ptech, description=pdesc))

                # Certifications
                if sc['cert']:
                    db.add(Certification(student_id=s.id, name=sc['cert'][0], issuing_organization=sc['cert'][1]))

                # Internships
                if sc['intern']:
                    db.add(Internship(student_id=s.id, company_name=sc['intern'][0], role=sc['intern'][1], duration_months=sc['intern'][2]))

                # Active ATS Resume
                db.add(Resume(
                    student_id=s.id,
                    file_path='uploads/resumes/sample_resume.pdf',
                    filename=f"{sc['name'].lower().replace(' ', '_')}_resume.pdf",
                    extracted_text=f"Resume of {sc['name']} - Education: BCA/CSE, Skills: {', '.join([k[0] for k in sc['skills']])}",
                    detected_skills=[k[0] for k in sc['skills']],
                    detected_sections={'education': True, 'skills': True, 'projects': True, 'experience': bool(sc['intern']), 'certifications': bool(sc['cert'])},
                    completeness_score=85.0 if sc['intern'] else 70.0,
                    is_active=True
                ))

                # Roadmap Tasks
                stages = [
                    ('Foundation', 'Master Core Computer Science & OOP Concepts', 'Completed', 100),
                    ('Skill Development', 'Achieve Advanced Proficiency in Python & SQL', 'Completed' if sc['cgpa'] > 8 else 'In Progress', 80),
                    ('Resume Preparation', 'Format ATS Resume with Quantified Impact', 'Completed', 100),
                    ('Aptitude Preparation', 'Complete Quantitative & Reasoning Drills', 'Completed', 100),
                    ('Interview Preparation', 'Mock Technical & Behavioral Interview Sessions', 'In Progress', 60),
                    ('Placement Preparation', 'Targeted Company Applications & Technical Rounds', 'In Progress', 50)
                ]
                for rstg, rtit, rstat, rprog in stages:
                    db.add(RoadmapTask(
                        student_id=s.id,
                        stage=rstg,
                        title=rtit,
                        description=f"Curated milestone for {sc['dept']} placement cohort.",
                        priority='High',
                        status=rstat,
                        progress_percentage=rprog
                    ))

                # Readiness History
                readiness_res = scorer.compute_readiness({
                    'cgpa': sc['cgpa'],
                    'attendance': 88.5,
                    'skills': [{'name': k[0], 'proficiency': k[1]} for k in sc['skills']],
                    'projects': sc['projects'],
                    'certifications': [sc['cert']] if sc['cert'] else [],
                    'internships': [sc['intern']] if sc['intern'] else [],
                    'resume_completeness': 85.0 if sc['intern'] else 70.0
                })
                db.add(ReadinessHistory(
                    student_id=s.id,
                    overall_score=readiness_res['overall_readiness'],
                    academic_score=readiness_res['pillars']['academic'],
                    technical_score=readiness_res['pillars']['technical'],
                    resume_score=readiness_res['pillars']['resume'],
                    aptitude_score=readiness_res['pillars']['tests'],
                    interview_score=readiness_res['pillars']['interview']
                ))

                # Interventions if CGPA < 7.5
                if sc['cgpa'] < 7.5:
                    db.add(Intervention(
                        student_id=s.id,
                        trigger_reason='Preparation Gap: Lower Technical Test Average & Academic Margin',
                        severity='Needs Attention',
                        recommendation='Schedule 1-on-1 department mentoring and assign supplementary SQL & Python coding challenges.',
                        assigned_faculty='Prof. Anitha Rao',
                        status='Open'
                    ))

                created_students.append(s)
                db.flush()

        # 6. Active Campus Jobs
        job_postings = [
            {
                'company': 'TechCorp Solutions',
                'title': 'Graduate Software Engineer - Cloud & Python',
                'role_type': 'Full-Time',
                'location': 'Bangalore, India',
                'salary_package': '8.5 - 10 LPA',
                'salary_numeric': 9.2,
                'min_cgpa': 7.5,
                'required_skills': 'Python, SQL, Flask, Git & GitHub',
                'preferred_skills': 'Docker, AWS',
                'desc': 'Design and maintain high-throughput backend services and cloud infrastructure pipelines.'
            },
            {
                'company': 'FinTech Labs',
                'title': 'Backend Developer - Financial Engineering',
                'role_type': 'Full-Time',
                'location': 'Mumbai, India',
                'salary_package': '12 - 14 LPA',
                'salary_numeric': 13.0,
                'min_cgpa': 8.0,
                'required_skills': 'Python, SQL, PostgreSQL, Problem Solving',
                'preferred_skills': 'Machine Learning, Docker',
                'desc': 'Build high-frequency ledger processing engines and secure banking settlement endpoints.'
            },
            {
                'company': 'NextGen Innovations',
                'title': 'Associate Full-Stack Developer',
                'role_type': 'Full-Time',
                'location': 'Hyderabad, India',
                'salary_package': '7.0 - 8.5 LPA',
                'salary_numeric': 7.8,
                'min_cgpa': 7.0,
                'required_skills': 'Java, JavaScript, React, SQL',
                'preferred_skills': 'Agile / Scrum',
                'desc': 'Develop enterprise web portals and interactive dashboards with responsive user interfaces.'
            }
        ]

        jobs = {}
        for jp in job_postings:
            j = db.query(Job).filter_by(title=jp['title']).first()
            if not j:
                j = Job(
                    company_id=companies[jp['company']].id,
                    title=jp['title'],
                    role_type=jp['role_type'],
                    location=jp['location'],
                    salary_package=jp['salary_package'],
                    salary_numeric=jp['salary_numeric'],
                    min_cgpa=jp['min_cgpa'],
                    required_skills=jp['required_skills'],
                    preferred_skills=jp['preferred_skills'],
                    description=jp['desc'],
                    selection_process='Online Assessment -> Technical Interview -> HR Round',
                    deadline=datetime.utcnow() + timedelta(days=21),
                    status='Active'
                )
                db.add(j)
                db.flush()
            jobs[jp['title']] = j

        # 7. Applications & Offers
        rahul = db.query(Student).filter_by(usn='1BC22001').first()
        priya = db.query(Student).filter_by(usn='1BC22002').first()
        techcorp_job = jobs['Graduate Software Engineer - Cloud & Python']
        fintech_job = jobs['Backend Developer - Financial Engineering']
        nextgen_job = jobs['Associate Full-Stack Developer']

        if rahul:
            app1 = db.query(Application).filter_by(student_id=rahul.id, job_id=techcorp_job.id).first()
            if not app1:
                app1 = Application(
                    student_id=rahul.id,
                    job_id=techcorp_job.id,
                    status='Offer Accepted',
                    ai_match_score=89.5,
                    notes='Top candidate across technical interview rounds.'
                )
                db.add(app1)
                db.flush()

                # Offer
                db.add(Offer(
                    application_id=app1.id,
                    student_id=rahul.id,
                    company_name='TechCorp Solutions',
                    job_title='Graduate Software Engineer - Cloud & Python',
                    package_lpa=9.5,
                    status='Accepted'
                ))

        if priya:
            app2 = db.query(Application).filter_by(student_id=priya.id, job_id=nextgen_job.id).first()
            if not app2:
                app2 = Application(
                    student_id=priya.id,
                    job_id=nextgen_job.id,
                    status='Technical Interview',
                    ai_match_score=82.0,
                    notes='Shortlisted for technical interview round.'
                )
                db.add(app2)
                db.flush()

                db.add(ActualInterview(
                    application_id=app2.id,
                    student_id=priya.id,
                    round_name='Technical Architecture Round',
                    interviewer_name='Amit Verma (Tech Lead)',
                    scheduled_at=datetime.utcnow() + timedelta(days=3),
                    location_or_link='https://meet.example.com/nextgen-interview',
                    status='Scheduled'
                ))

        # 8. Curated Aptitude & Technical Tests
        test_py = db.query(Test).filter_by(title='Python Core & Algorithms Assessment').first()
        if not test_py:
            test_py = Test(
                title='Python Core & Algorithms Assessment',
                category='Technical',
                topic='Python Fundamentals',
                duration_minutes=15,
                total_marks=5,
                pass_percentage=60.0
            )
            db.add(test_py)
            db.flush()

            questions_py = [
                ('What is the output of bool([]) in Python?', 'True', 'False', 'None', 'Error', 'B', 'An empty list evaluates to False in boolean context.'),
                ('Which data structure is immutable in Python?', 'List', 'Set', 'Tuple', 'Dictionary', 'C', 'Tuples are immutable sequences.'),
                ('What is the time complexity of searching a key in a Python dict on average?', 'O(n)', 'O(log n)', 'O(1)', 'O(n^2)', 'C', 'Python dictionaries use hash tables with O(1) average lookup.'),
                ('Which keyword is used for exception handling in Python?', 'catch', 'except', 'handle', 'rescue', 'B', 'Python uses try...except blocks.'),
                ('What does GIL stand for in Python?', 'General Input Loop', 'Global Interpreter Lock', 'Graphical Interface Library', 'Generic Instruction List', 'B', 'GIL is the Global Interpreter Lock.')
            ]
            for q, a, b, c, d, corr, exp in questions_py:
                db.add(Question(test_id=test_py.id, question_text=q, option_a=a, option_b=b, option_c=c, option_d=d, correct_option=corr, explanation=exp))

        test_apt = db.query(Test).filter_by(title='Quantitative & Logical Aptitude Test').first()
        if not test_apt:
            test_apt = Test(
                title='Quantitative & Logical Aptitude Test',
                category='Aptitude',
                topic='Quantitative Reasoning',
                duration_minutes=15,
                total_marks=5,
                pass_percentage=60.0
            )
            db.add(test_apt)
            db.flush()

            questions_apt = [
                ('If a train travels 360 km in 4 hours, what is its speed in m/s?', '20 m/s', '25 m/s', '30 m/s', '35 m/s', 'B', 'Speed = 90 km/h = 90 * (5/18) = 25 m/s.'),
                ('What is 15% of 400 plus 25% of 240?', '100', '120', '130', '140', 'B', '60 + 60 = 120.'),
                ('If A is B brother and B is C sister, how is A related to C?', 'Brother', 'Sister', 'Father', 'Uncle', 'A', 'A is brother to C.'),
                ('Find the next number in series: 2, 6, 12, 20, 30, ?', '40', '42', '44', '46', 'B', 'Differences are 4, 6, 8, 10, 12 -> 30 + 12 = 42.'),
                ('A pipe can fill a tank in 6 hours. Another pipe empties it in 12 hours. If both are open, how long to fill?', '8 hours', '10 hours', '12 hours', '14 hours', 'C', '1/6 - 1/12 = 1/12 -> 12 hours.')
            ]
            for q, a, b, c, d, corr, exp in questions_apt:
                db.add(Question(test_id=test_apt.id, question_text=q, option_a=a, option_b=b, option_c=c, option_d=d, correct_option=corr, explanation=exp))

        # 9. Training Programs
        tprog = db.query(TrainingProgram).filter_by(title='Full-Stack Microservices & Cloud Bootcamp').first()
        if not tprog:
            tprog = TrainingProgram(
                title='Full-Stack Microservices & Cloud Bootcamp',
                topic_skill='Python, Docker, REST APIs',
                trainer_name='Suresh Kulkarni (Industry Veteran)',
                description='Intensive hands-on training on microservices architecture, Docker containerization, and AWS deployment.',
                start_date=datetime.utcnow() - timedelta(days=14),
                end_date=datetime.utcnow() + timedelta(days=10),
                capacity=40,
                status='Ongoing'
            )
            db.add(tprog)
            db.flush()

            if rahul:
                db.add(TrainingEnrollment(
                    training_id=tprog.id,
                    student_id=rahul.id,
                    status='Completed',
                    pre_score=62.0,
                    post_score=89.0,
                    attendance_rate=100.0,
                    feedback='Excellent practical coverage of production Docker and API architecture.'
                ))

        db.commit()
        print("[OK] Core realistic seed data populated.")

        # Expand the same database with interconnected demo records and large
        # local preparation pools. The helper is idempotent, so existing seed
        # records are preserved.
        from database.expand_demo_data import expand_demo_data
        expand_demo_data()

    finally:
        db.close()

if __name__ == '__main__':
    seed_database()
