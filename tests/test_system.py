import os
import sys
import unittest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from backend.models.database import SessionLocal
from backend.models.models import User, Student, Job, Skill, Application, Department
from ai.job_matching.matcher import LocalJobMatchingEngine
from ai.skill_gap.engine import SkillGapEngine
from ai.readiness.scorer import CareerReadinessScorer
from ai.interview.engine import MockInterviewEngine
from ai.interview.question_bank import QUESTION_BANK
from ai.simulation.simulator import CareerSimulator
from reports.pdf_generator import PlacementReportGenerator

class TestPlacementSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_01_database_seed_integrity(self):
        db = SessionLocal()
        try:
            users_count = db.query(User).count()
            students_count = db.query(Student).count()
            jobs_count = db.query(Job).count()
            skills_count = db.query(Skill).count()

            self.assertGreaterEqual(users_count, 6)
            self.assertGreaterEqual(students_count, 4)
            self.assertGreaterEqual(jobs_count, 3)
            self.assertGreaterEqual(skills_count, 15)
            print(f"[TEST PASS] Database Seed Verified: {users_count} Users, {students_count} Students, {jobs_count} Jobs, {skills_count} Skills.")
        finally:
            db.close()

    def test_02_ai_job_matching_engine(self):
        matcher = LocalJobMatchingEngine()
        student = {
            'skills': [{'name': 'Python', 'proficiency': 'Advanced'}, {'name': 'SQL', 'proficiency': 'Advanced'}],
            'cgpa': 8.5,
            'projects': [{'title': 'Data Engine', 'technologies': 'Python, SQL', 'description': 'Backend analytics'}],
            'internships': [],
            'bio': 'Passionate backend developer'
        }
        job = {
            'title': 'Python Backend Engineer',
            'description': 'Building scalable APIs in Python and SQL',
            'required_skills': 'Python, SQL, Flask',
            'preferred_skills': 'Docker',
            'min_cgpa': 7.5
        }
        result = matcher.compute_match(student, job)
        self.assertIn('overall_match', result)
        self.assertGreaterEqual(result['overall_match'], 60.0)
        self.assertTrue(result['meets_cgpa'])
        self.assertIn('Python', result['matched_skills'])
        print(f"[TEST PASS] AI Job Matching Engine: Overall Match = {result['overall_match']}%")

    def test_03_skill_gap_engine(self):
        engine = SkillGapEngine()
        student_skills = [{'name': 'Python', 'proficiency': 'Beginner'}]
        gap_res = engine.analyze_gaps(student_skills, 'Python, Docker, AWS', 'Kubernetes')

        self.assertIn('gap_items', gap_res)
        self.assertGreater(gap_res['critical_gaps_count'], 0)
        print(f"[TEST PASS] Skill Gap Engine: Detected {gap_res['critical_gaps_count']} critical gaps.")

    def test_04_career_readiness_scorer(self):
        scorer = CareerReadinessScorer()
        student_data = {
            'cgpa': 8.8,
            'attendance': 90.0,
            'skills': [{'name': 'Python', 'proficiency': 'Advanced'}, {'name': 'SQL', 'proficiency': 'Advanced'}],
            'projects': [{'title': 'Project A'}, {'title': 'Project B'}],
            'certifications': [{'name': 'Cert A'}],
            'internships': [{'role': 'Intern A'}],
            'resume_completeness': 85.0,
            'test_attempts': [{'percentage': 80.0}],
            'mock_interviews': [{'overall_score': 75.0}]
        }
        res = scorer.compute_readiness(student_data)
        self.assertGreaterEqual(res['overall_readiness'], 70.0)
        self.assertIn('academic', res['pillars'])
        print(f"[TEST PASS] Career Readiness Scorer: Overall = {res['overall_readiness']}%")

    def test_05_mock_interview_evaluator(self):
        engine = MockInterviewEngine()
        answer = "In my previous project, when our payment system had high latency, I decided to refactor the database queries using indexed SQL joins, which resulted in reducing latency by 45%."
        eval_res = engine.evaluate_answer("Describe an optimization task", ['indexed', 'sql', 'joins', 'latency'], answer, 'Technical')
        self.assertGreaterEqual(eval_res['overall_score'], 60.0)
        self.assertIn('situation', eval_res['star_elements_detected'])
        print(f"[TEST PASS] Mock Interview Evaluator: Score = {eval_res['overall_score']}%, STAR detected = {eval_res['star_elements_detected']}")

    def test_06_what_if_simulator(self):
        sim = CareerSimulator()
        base_data = {
            'cgpa': 7.5,
            'attendance': 85.0,
            'skills': [{'name': 'Python', 'proficiency': 'Beginner'}],
            'projects': [],
            'certifications': [],
            'internships': [],
            'resume_completeness': 60.0
        }
        scenario = {
            'upgraded_skills': {'python': 'Advanced'},
            'added_projects': 2,
            'added_internship': True,
            'simulated_aptitude_pct': 90.0,
            'simulated_interview_score': 85.0,
            'simulated_resume_score': 90.0
        }
        res = sim.simulate_what_if(base_data, scenario)
        self.assertGreater(res['simulated_score'], res['base_score'])
        self.assertGreater(res['score_delta'], 10.0)
        print(f"[TEST PASS] What-If Simulation: Delta = +{res['score_delta']}%")

    def test_07_pdf_reports_generation(self):
        os.makedirs('reports/test_output', exist_ok=True)
        pdf_path = 'reports/test_output/test_student_report.pdf'
        student_data = {
            'full_name': 'Test Student',
            'usn': '1BC22TEST',
            'department': 'Computer Applications',
            'cgpa': 8.5,
            'skills': [{'name': 'Python', 'proficiency': 'Advanced'}],
            'projects': [{'title': 'Test Project'}],
            'readiness': {'overall_readiness': 85.0, 'pillars': {'academic': 85.0, 'technical': 80.0, 'portfolio': 90.0, 'resume': 85.0, 'tests': 80.0, 'interview': 80.0}, 'recommendations': ['Keep coding']}
        }
        PlacementReportGenerator.generate_student_report(pdf_path, student_data)
        self.assertTrue(os.path.exists(pdf_path))
        self.assertGreater(os.path.getsize(pdf_path), 1000)
        print(f"[TEST PASS] ReportLab PDF Generation Verified ({os.path.getsize(pdf_path)} bytes)")


    def test_09_interview_question_bank(self):
        self.assertGreaterEqual(len(QUESTION_BANK), 100)
        self.assertEqual(len({q['question'] for q in QUESTION_BANK}), len(QUESTION_BANK))
        self.assertTrue(all(q.get('difficulty') in {'Beginner','Intermediate','Advanced'} for q in QUESTION_BANK))
        print(f"[TEST PASS] Mock Interview Bank: {len(QUESTION_BANK)} unique tagged questions.")

    def test_10_qt_question_pool(self):
        db = SessionLocal()
        try:
            from backend.models.models import Test, Question
            aptitude_count = db.query(Question).join(Test).filter(Test.category == 'Aptitude').count()
            self.assertGreaterEqual(aptitude_count, 200)
            print(f"[TEST PASS] QT Pool: {aptitude_count} aptitude questions available.")
        finally:
            db.close()

    def test_08_rbac_security_isolation(self):
        # Unauthenticated access to student dashboard -> should redirect to login
        res = self.client.get('/student/dashboard', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/auth/login', res.headers['Location'])
        print("[TEST PASS] RBAC Security Route Protection Verified.")

if __name__ == '__main__':
    unittest.main()
