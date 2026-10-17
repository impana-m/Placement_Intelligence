"""Idempotent demo-data expansion for Placement Intelligence.

Run with: python database/expand_demo_data.py
The script only adds records that are missing and keeps the existing seed data.
"""
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

from backend.models.database import SessionLocal, init_db
from backend.models.models import (
    Department, User, Company, Recruiter, Student, Skill, StudentSkill,
    Project, Certification, Internship, Resume, Job, Application, Offer,
    ActualInterview, MockInterviewSession, MockInterviewQA, Test, Question,
    TestAttempt, Notification, RoadmapTask, Intervention, ReadinessHistory
)
from ai.interview.question_bank import QUESTION_BANK

RNG = random.Random(20260928)
PASSWORD_HASH = generate_password_hash('Password@123', method='pbkdf2:sha256')

COMPANIES = [
    ('CloudNova Systems', 'Cloud & SaaS', 'Bangalore, India', 'Tier 1'),
    ('Apex Digital Works', 'IT Services', 'Pune, India', 'Tier 2'),
    ('BlueOrbit Technologies', 'Enterprise Software', 'Chennai, India', 'Tier 2'),
    ('Nexora Analytics', 'Data & AI', 'Bangalore, India', 'Tier 1'),
    ('SecureStack Labs', 'Cybersecurity', 'Hyderabad, India', 'Tier 2'),
    ('RetailGrid', 'E-Commerce Technology', 'Gurugram, India', 'Tier 2'),
    ('HealthByte Systems', 'HealthTech', 'Bangalore, India', 'Startup'),
    ('GreenRoute Mobility', 'Mobility & Logistics', 'Pune, India', 'Startup'),
]

JOB_TEMPLATES = [
    ('Python Backend Developer', 'Full-Time', 8.5, 7.0, 'Python, SQL, Flask', 'Docker, AWS'),
    ('Junior Data Analyst', 'Full-Time', 6.8, 6.5, 'Python, SQL, Data Analysis', 'Machine Learning, PostgreSQL'),
    ('Full-Stack Web Developer', 'Full-Time', 7.5, 7.0, 'JavaScript, React, SQL', 'Flask, Git & GitHub'),
    ('Cloud Support Engineer', 'Full-Time', 6.2, 6.0, 'Linux, Python, Git & GitHub', 'Docker, AWS'),
    ('QA Automation Engineer', 'Full-Time', 6.5, 6.5, 'Python, SQL, Problem Solving', 'JavaScript, Git & GitHub'),
    ('Software Engineering Intern', 'Internship + PPO', 4.5, 6.0, 'Python, Git & GitHub, SQL', 'Docker, JavaScript'),
    ('Business Intelligence Analyst', 'Full-Time', 7.2, 7.0, 'SQL, Data Analysis, Excel', 'Python, Machine Learning'),
    ('Associate Product Engineer', 'Full-Time', 8.0, 7.2, 'Python, SQL, Problem Solving', 'Agile / Scrum, Docker'),
]

FIRST_NAMES = ['Aarav','Aditi','Akash','Ananya','Aniket','Anjali','Arnav','Bhavana','Chetan','Diya','Esha','Gaurav','Harish','Isha','Jatin','Kavya','Kiran','Lakshmi','Manish','Meera','Mohit','Nandini','Nikhil','Pooja','Pranav','Riya','Rohan','Sahil','Samarth','Shreya','Siddharth','Tanvi','Varun','Vedika','Vivek','Yash','Zoya']
LAST_NAMES = ['Sharma','Patel','Rao','Nair','Iyer','Kulkarni','Mehta','Reddy','Joshi','Menon','Gupta','Bhat','Desai','Khan','Mishra','Verma','Shetty','Naik','Das','Kapoor']
SKILL_NAMES = ['Python','Java','C++','JavaScript','SQL','MySQL','PostgreSQL','MongoDB','Flask','Django','React','Machine Learning','Data Analysis','Docker','AWS','Git & GitHub','Problem Solving','Technical Communication','Agile / Scrum']


def option_pack(correct, distractors):
    values = [str(correct)] + [str(x) for x in distractors]
    # Deterministic shuffle while retaining the correct letter.
    order = list(range(4))
    RNG.shuffle(order)
    opts = [values[i] for i in order]
    correct_letter = 'ABCD'[opts.index(str(correct))]
    return opts[0], opts[1], opts[2], opts[3], correct_letter


def qt_questions_for(topic):
    qs = []
    for i in range(1, 19):
        if topic == 'Percentages':
            base = 80 + i * 10
            pct = 5 + (i % 6) * 5
            correct = base * pct / 100
            text = f'What is {pct}% of {base}?'
            explanation = f'{pct}% of {base} = {base} × {pct}/100 = {correct:g}.'
            distract = [correct + 5, correct - 5, correct + 10]
        elif topic == 'Profit & Loss':
            cost = 1000 + i * 125
            profit = 5 + (i % 5) * 5
            correct = cost * (100 + profit) / 100
            text = f'An item costs ₹{cost} and is sold at a profit of {profit}%. What is its selling price?'
            explanation = f'Selling price = cost × (100 + profit)/100 = ₹{correct:g}.'
            distract = [cost * (100 + profit + 5) / 100, cost * (100 + profit - 5) / 100, cost + profit]
        elif topic == 'Ratio & Proportion':
            a, b = 2 + i % 5, 3 + (i % 4)
            total = (a + b) * (4 + i)
            correct = total * a / (a + b)
            text = f'Two quantities are in the ratio {a}:{b}. If their total is {total:g}, what is the first quantity?'
            explanation = f'First quantity = {total:g} × {a}/({a}+{b}) = {correct:g}.'
            distract = [correct + a, correct - b, total * b / (a + b)]
        elif topic == 'Averages':
            count = 5 + i % 5
            old_avg = 20 + i
            new_value = 35 + i * 2
            old_sum = count * old_avg
            correct = (old_sum + new_value) / (count + 1)
            text = f'The average of {count} values is {old_avg}. If {new_value} is added, what is the new average?'
            explanation = f'New average = ({old_sum} + {new_value}) / {count + 1} = {correct:.2f}.'
            distract = [correct + 2, correct - 2, old_avg + new_value]
        elif topic == 'Time & Work':
            a, b = 6 + i % 5, 8 + i % 4
            correct = (a * b) / (a + b)
            text = f'One worker completes a job in {a} days and another in {b} days. Working together, how many days will they need?'
            explanation = f'Combined rate = 1/{a} + 1/{b}; time = {a*b}/{a+b} = {correct:.2f} days.'
            distract = [correct + 1, max(1, correct - 1), (a + b) / 2]
        elif topic == 'Time, Speed & Distance':
            speed = 30 + i * 3
            hours = 2 + (i % 4)
            correct = speed * hours
            text = f'A vehicle travels at {speed} km/h for {hours} hours. What distance does it cover?'
            explanation = f'Distance = speed × time = {speed} × {hours} = {correct} km.'
            distract = [correct + speed, correct - speed, speed + hours]
        elif topic == 'Simple Interest':
            principal = 1000 + i * 100
            rate = 4 + i % 5
            years = 2 + i % 3
            correct = principal * rate * years / 100
            text = f'Find the simple interest on ₹{principal} at {rate}% per annum for {years} years.'
            explanation = f'SI = P×R×T/100 = {principal}×{rate}×{years}/100 = ₹{correct:g}.'
            distract = [correct + 100, correct - 100, principal + correct]
        elif topic == 'Compound Interest':
            principal = 1000 + i * 100
            rate = 5
            years = 2
            amount = principal * (1.05 ** years)
            correct = amount - principal
            text = f'Find the compound interest on ₹{principal} at {rate}% per annum for {years} years, compounded annually.'
            explanation = f'CI = P[(1+R/100)^T - 1] = ₹{correct:.2f}.'
            distract = [principal * rate * years / 100, correct + 50, correct - 50]
        elif topic == 'Probability':
            favorable = 2 + i % 5
            total = 8 + i % 7
            if favorable >= total: favorable = total - 1
            correct = favorable / total
            text = f'A box has {favorable} favorable outcomes among {total} equally likely outcomes. What is the probability of a favorable outcome?'
            explanation = f'Probability = favorable outcomes / total outcomes = {favorable}/{total} = {correct:.3f}.'
            distract = [(favorable + 1) / total, favorable / (total + 1), 1 - correct]
        elif topic == 'Permutations & Combinations':
            n = 5 + i % 5
            r = 2 + i % 3
            if r > n: r = 2
            correct = 1
            for x in range(r): correct *= n - x
            text = f'How many ordered arrangements of {r} objects can be selected from {n} distinct objects?'
            explanation = f'P({n},{r}) = {n}!/({n}-{r})! = {correct}.'
            distract = [correct // max(1, r), correct + n, correct + r]
        elif topic == 'Number Systems':
            a = 100 + i * 7
            b = 12 + i % 8
            correct = a % b
            text = f'What is the remainder when {a} is divided by {b}?'
            explanation = f'{a} = {a//b} × {b} + {correct}, so the remainder is {correct}.'
            distract = [(correct + 1) % b, (correct + 2) % b, max(0, correct - 1)]
        elif topic == 'Algebra':
            x = 3 + i
            a = 2 + i % 4
            b = 5 + i % 6
            correct = x
            text = f'If {a}x + {b} = {a*x+b}, what is x?'
            explanation = f'Subtract {b} and divide by {a}: x = {x}.'
            distract = [x + 1, x - 1, x + 2]
        else:  # Data Interpretation
            base = 100 + i * 10
            qtype = i % 3
            if qtype == 0:
                sales = [base, base + 20, base + 40]
                correct = sum(sales)
                text = f'A shop records monthly sales of {sales[0]}, {sales[1]} and {sales[2]} units. What is the total sales?'
                explanation = f'Total = {sales[0]} + {sales[1]} + {sales[2]} = {correct}.'
            elif qtype == 1:
                jan, feb = base, base + 25
                correct = feb - jan
                text = f'Website visits increased from {jan} in January to {feb} in February. By how many visits did they increase?'
                explanation = f'Increase = {feb} - {jan} = {correct} visits.'
            else:
                completed, total = 60 + i, 100 + i
                correct = completed / total * 100
                text = f'A training program has {total} enrolled students and {completed} completed it. What percentage completed the program?'
                explanation = f'Completion rate = {completed}/{total} × 100 = {correct:.2f}%.'
            distract = [correct + 5, max(0, correct - 5), correct + 10]

        a, b, c, d, letter = option_pack(correct, distract)
        qs.append({
            'question': f'{text} [Variant {i}]',
            'options': (a, b, c, d),
            'correct': letter,
            'explanation': explanation,
            'difficulty': ['Easy', 'Medium', 'Hard'][(i - 1) % 3],
            'topic': topic,
        })
    return qs



def ensure_foundation(db):
    dept_data = [
        ('Computer Applications', 'BCA'),
        ('Computer Science & Engineering', 'CSE'),
        ('Information Science', 'ISE'),
        ('Data Science & AI', 'DSAI'),
    ]
    departments = {}
    for name, code in dept_data:
        d = db.query(Department).filter_by(code=code).first()
        if not d:
            d = Department(name=name, code=code, description=f'{name} placement cohort')
            db.add(d); db.flush()
        departments[code] = d

    categories = {
        'Python':'Programming','Java':'Programming','C++':'Programming','JavaScript':'Programming',
        'SQL':'Database','MySQL':'Database','PostgreSQL':'Database','MongoDB':'Database',
        'Flask':'Framework','Django':'Framework','React':'Framework','Machine Learning':'Technical',
        'Data Analysis':'Technical','Docker':'Cloud/DevOps','AWS':'Cloud/DevOps','Git & GitHub':'Technical',
        'Problem Solving':'Soft Skill','Technical Communication':'Soft Skill','Agile / Scrum':'Soft Skill'
    }
    skills = {}
    for name in SKILL_NAMES:
        sk = db.query(Skill).filter_by(name=name).first()
        if not sk:
            sk = Skill(name=name, category=categories.get(name, 'Technical'), description=f'{name} placement competency')
            db.add(sk); db.flush()
        skills[name] = sk
    return departments, skills

def ensure_companies(db):
    companies = {}
    for name, industry, location, tier in COMPANIES:
        c = db.query(Company).filter_by(name=name).first()
        if not c:
            c = Company(name=name, industry=industry, location=location, tier=tier,
                        description=f'{name} placement partner for {industry}.',
                        contact_email=f'careers@{name.lower().replace(" ", "")}.example')
            db.add(c)
            db.flush()
        companies[name] = c
        email = f'recruiter.{name.lower().replace(" ", "")}@college.edu'
        u = db.query(User).filter_by(email=email).first()
        if not u:
            u = User(email=email, password_hash=PASSWORD_HASH, full_name=f'{name} Recruiter', role='recruiter')
            db.add(u); db.flush()
            db.add(Recruiter(user_id=u.id, company_id=c.id, designation='Talent Acquisition Partner', phone='+91 90000 00000'))
    return companies


def ensure_students(db, departments, skills):
    students = db.query(Student).all()
    target = 75
    while len(students) < target:
        n = len(students) + 1
        name = f'{FIRST_NAMES[(n-1) % len(FIRST_NAMES)]} {LAST_NAMES[(n*3-1) % len(LAST_NAMES)]}'
        email = f'demo.student{n:03d}@college.edu'
        if db.query(User).filter_by(email=email).first():
            students = db.query(Student).all(); continue
        dept_code = ['BCA','CSE','ISE','DSAI'][(n-1) % 4]
        cgpa = round(6.1 + ((n * 17) % 34) / 10, 2)
        status = 'Placed' if n % 7 == 0 else ('In Process' if n % 3 == 0 else 'Not Placed')
        u = User(email=email, password_hash=PASSWORD_HASH, full_name=name, role='student', department_id=departments[dept_code].id)
        db.add(u); db.flush()
        s = Student(user_id=u.id, usn=f'1{dept_code[:2]}26{n:04d}', phone=f'+91 91{n:08d}',
                    department_id=departments[dept_code].id, batch_year=2026, current_semester=6,
                    cgpa=cgpa, attendance_percentage=round(72 + ((n*11)%25),1),
                    placement_status=status,
                    preferred_roles='Software Engineer, Data Analyst' if n % 2 else 'Full-Stack Developer, Backend Developer',
                    preferred_locations='Bangalore, Hyderabad, Pune',
                    bio=f'Final-year {dept_code} student focused on practical placement preparation.')
        db.add(s); db.flush()
        chosen = RNG.sample(SKILL_NAMES, 3 + n % 4)
        for idx, skn in enumerate(chosen):
            prof = ['Beginner','Intermediate','Advanced'][(n + idx) % 3]
            db.add(StudentSkill(student_id=s.id, skill_id=skills[skn].id, proficiency=prof, verified=(idx == 0)))
        db.add(Project(student_id=s.id, title=f'{name.split()[0]} Placement Analytics Project', technologies='Python, Flask, MySQL, JavaScript', description='A practical analytics project for student placement preparation.'))
        if n % 4 == 0:
            db.add(Certification(student_id=s.id, name='Python Data Analysis Certificate', issuing_organization='Industry Skills Academy', issue_date=datetime.utcnow()-timedelta(days=120)))
        if n % 5 == 0:
            db.add(Internship(student_id=s.id, company_name='Campus Technology Partner', role='Software Intern', duration_months=3, start_date=datetime.utcnow()-timedelta(days=180), end_date=datetime.utcnow()-timedelta(days=90), description='Worked on internal web applications and testing.'))
        db.add(Resume(student_id=s.id, file_path=f'uploads/resumes/{s.usn}.pdf', filename=f'{s.usn}.pdf', extracted_text=f'{name} Python SQL Flask Git projects data analysis.', detected_skills=chosen, detected_sections=['summary','skills','projects','education'], completeness_score=round(62 + (n % 35),1)))
        for stage, title in [('Foundation','Complete core programming revision'),('Aptitude Preparation','Complete weekly quantitative drill'),('Technical Preparation','Practice SQL and DBMS questions'),('Interview Preparation','Complete a mock interview')]:
            status_task = 'Completed' if (n + len(title)) % 5 == 0 else 'Pending'
            db.add(RoadmapTask(student_id=s.id, stage=stage, title=title, description='Placement preparation task', priority='Medium', status=status_task, progress_percentage=100 if status_task=='Completed' else 0, due_date=datetime.utcnow()+timedelta(days=30)))
        students.append(s)
    db.flush()
    return students


def ensure_jobs(db, companies):
    jobs = db.query(Job).all()
    existing_titles = {j.title for j in jobs}
    company_list = list(companies.values())
    for i in range(27):
        company = company_list[i % len(company_list)]
        template = JOB_TEMPLATES[i % len(JOB_TEMPLATES)]
        title = f'{template[0]} — {company.name} — 2026 Drive {i+1}'
        if title in existing_titles:
            continue
        salary = round(template[2] + (i % 4) * 0.6, 1)
        status = ['Active','Active','Active','Paused','Closed','Draft'][i % 6]
        deadline = datetime.utcnow() + timedelta(days=7 + (i % 40))
        job = Job(company_id=company.id, title=title, role_type=template[1], location=company.location,
                  salary_package=f'{max(3.5,salary-1.0):.1f} - {salary:.1f} LPA', salary_numeric=salary,
                  min_cgpa=template[3], required_skills=template[4], preferred_skills=template[5],
                  description=f'{template[0]} opportunity at {company.name}. Build production-ready solutions, collaborate with engineers and learn from real placement projects.',
                  selection_process='Aptitude -> Technical Interview -> HR', deadline=deadline, status=status)
        db.add(job)
        existing_titles.add(title)
    db.flush()
    return db.query(Job).all()


def ensure_applications(db, students, jobs):
    eligible_jobs = [j for j in jobs if j.status in {'Active','Closed'}]
    for idx, student in enumerate(students):
        matching = [j for j in eligible_jobs if student.cgpa >= j.min_cgpa]
        if not matching:
            continue
        selected_jobs = [matching[(idx * 3) % len(matching)]]
        if len(matching) > 1:
            selected_jobs.append(matching[(idx * 3 + 5) % len(matching)])
        for offset, job in enumerate(selected_jobs):
            if db.query(Application).filter_by(student_id=student.id, job_id=job.id).first():
                continue
            statuses = ['Applied','Shortlisted','Test','Technical Interview','HR Interview','Selected','Rejected','Offer Received']
            status = 'Selected' if idx % 9 == 0 and offset == 0 else statuses[(idx + offset) % len(statuses)]
            app = Application(
                student_id=student.id, job_id=job.id, status=status,
                ai_match_score=round(62 + ((idx*7+offset*11)%34),1),
                notes='Seeded interconnected placement pipeline record.'
            )
            db.add(app); db.flush()
            if status in {'Technical Interview','HR Interview','Selected'}:
                db.add(ActualInterview(
                    application_id=app.id, student_id=student.id,
                    round_name='Technical Round' if status != 'HR Interview' else 'HR Round',
                    interviewer_name=f'{job.company.name} Hiring Team',
                    scheduled_at=datetime.utcnow()+timedelta(days=idx%10+1),
                    location_or_link='Campus Placement Center',
                    status='Scheduled' if status != 'Selected' else 'Completed',
                    result='Selected' if status == 'Selected' else 'Pending',
                    score=round(65+(idx%30),1)
                ))
    db.flush()

    # Add a realistic offer history for a subset of distinct candidates.
    offered_students = set()
    candidate_apps = db.query(Application).join(Job).order_by(Application.id).all()
    for app in candidate_apps:
        if len(offered_students) >= 12 or app.student_id in offered_students:
            continue
        if app.status in {'Rejected', 'Applied'}:
            continue
        if not db.query(Offer).filter_by(application_id=app.id).first():
            app.status = 'Offer Received' if app.status != 'Selected' else 'Selected'
            db.add(Offer(
                application_id=app.id, student_id=app.student_id,
                company_name=app.job.company.name, job_title=app.job.title,
                package_lpa=app.job.salary_numeric,
                status='Accepted' if len(offered_students) % 3 == 0 else 'Offered'
            ))
        offered_students.add(app.student_id)
    db.flush()

    for student_id in offered_students:
        student = db.query(Student).filter_by(id=student_id).first()
        if student:
            student.placement_status = 'Placed' if student.placement_status != 'Opted Out' else student.placement_status


def ensure_qt_bank(db):
    topics = ['Percentages','Profit & Loss','Ratio & Proportion','Averages','Time & Work','Time, Speed & Distance','Simple Interest','Compound Interest','Probability','Permutations & Combinations','Number Systems','Algebra','Data Interpretation']
    for topic in topics:
        title = f'QT Practice — {topic}'
        test = db.query(Test).filter_by(title=title).first()
        if not test:
            test = Test(title=title, category='Aptitude', topic=topic, duration_minutes=20, total_marks=15, pass_percentage=60.0)
            db.add(test); db.flush()
        existing = {q.question_text for q in test.questions}
        for item in qt_questions_for(topic):
            if item['question'] in existing:
                continue
            a,b,c,d,correct = item['options'][0],item['options'][1],item['options'][2],item['options'][3],item['correct']
            db.add(Question(test_id=test.id, question_text=item['question'], option_a=a, option_b=b, option_c=c, option_d=d, correct_option=correct, explanation=item['explanation'], topic=topic, difficulty=item['difficulty'], marks=1))
        db.flush()


def ensure_mock_history(db, students):
    engine_questions = QUESTION_BANK[:]
    for idx, student in enumerate(students[:24]):
        if db.query(MockInterviewSession).filter_by(student_id=student.id).count() >= 1:
            continue
        chosen = RNG.sample(engine_questions, 5)
        session_obj = MockInterviewSession(student_id=student.id, target_role='Software Engineer' if idx%2==0 else 'Data Analyst', interview_type='Mixed', total_questions=5)
        db.add(session_obj); db.flush()
        scores=[]
        for q in chosen:
            score = round(58 + ((idx*9 + len(q['question'])) % 36),1); scores.append(score)
            db.add(MockInterviewQA(session_id=session_obj.id, question_text=q['question'], category=q['category'], difficulty=q['difficulty'], expected_keywords=','.join(q['keywords']), student_answer='I approached the problem by understanding the requirements, testing a practical solution and reviewing the result with the team.', time_taken_seconds=90, question_score=score, eval_breakdown={'overall_score':score,'technical_score':score,'relevance_score':score,'communication_score':min(95,score+5),'structure_score':min(95,score+2),'feedback':'Seeded historical response for dashboard analytics.','strengths':['Clear response'], 'weaknesses':['Add more concrete evidence']}))
        session_obj.overall_score=round(sum(scores)/len(scores),1); session_obj.technical_score=session_obj.overall_score; session_obj.communication_score=min(100,session_obj.overall_score+4); session_obj.relevance_score=session_obj.overall_score; session_obj.structure_score=min(100,session_obj.overall_score+2); session_obj.feedback_summary='Historical local mock interview diagnostic.'; session_obj.strengths=['Clear response','Relevant concepts']; session_obj.weaknesses=['Add more concrete evidence']
    db.flush()


def ensure_notifications(db, students):
    for s in students[:30]:
        if db.query(Notification).filter_by(user_id=s.user_id).count() == 0:
            db.add(Notification(user_id=s.user_id, title='Placement Preparation Reminder', message='Complete one timed QT drill and one mock interview this week to keep your preparation profile current.', notification_type='test', link='/tests/'))


def expand_demo_data():
    init_db()
    db = SessionLocal()
    try:
        departments, skills = ensure_foundation(db)
        companies = ensure_companies(db)
        students = ensure_students(db, departments, skills)
        jobs = ensure_jobs(db, companies)
        ensure_applications(db, students, jobs)
        ensure_qt_bank(db)
        ensure_mock_history(db, students)
        ensure_notifications(db, students)
        db.commit()
        print(f'[OK] Students: {db.query(Student).count()}')
        print(f'[OK] Companies: {db.query(Company).count()}')
        print(f'[OK] Jobs: {db.query(Job).count()}')
        qt_count = db.query(Question).join(Test).filter(Test.category == "Aptitude").count()
        print(f'[OK] QT questions: {qt_count}')
        print(f'[OK] Mock interview question bank: {len(QUESTION_BANK)} local questions')
        print(f'[OK] Mock history sessions: {db.query(MockInterviewSession).count()}')
        print(f'[OK] Applications: {db.query(Application).count()}')
        print(f'[OK] Offers: {db.query(Offer).count()}')
    finally:
        db.close()


if __name__ == '__main__':
    expand_demo_data()
