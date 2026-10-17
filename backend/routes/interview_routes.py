import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file
from backend.models.database import SessionLocal
from backend.models.models import MockInterviewSession, MockInterviewQA, Student
from backend.auth.security import login_required, role_required
from ai.interview.engine import MockInterviewEngine
from reports.pdf_generator import PlacementReportGenerator

interview_bp = Blueprint('interview', __name__, url_prefix='/interview')


def _safe_count(value, default=8):
    try:
        return max(5, min(int(value), 15))
    except (TypeError, ValueError):
        return default


@interview_bp.route('/mock/start', methods=['GET', 'POST'])
@login_required
@role_required('student')
def mock_start():
    student_id = session.get('student_id')
    db = SessionLocal()
    try:
        student = db.query(Student).filter_by(id=student_id).first()
        engine = MockInterviewEngine()

        if request.method == 'POST':
            target_role = request.form.get('target_role', 'Software Engineer')
            interview_type = request.form.get('interview_type', 'Technical')
            difficulty = request.form.get('difficulty', 'All')
            q_count = _safe_count(request.form.get('question_count', 8))

            allowed_types = {'Technical', 'HR', 'Behavioral', 'Situational', 'Communication', 'Mixed'}
            if interview_type not in allowed_types:
                interview_type = 'Technical'
            if difficulty not in {'All', 'Beginner', 'Intermediate', 'Advanced'}:
                difficulty = 'All'

            selected_qs = engine.get_questions_for_role(target_role, interview_type, q_count, difficulty)
            new_sess = MockInterviewSession(
                student_id=student.id,
                target_role=target_role,
                interview_type=interview_type,
                total_questions=len(selected_qs)
            )
            db.add(new_sess)
            db.flush()

            for q in selected_qs:
                db.add(MockInterviewQA(
                    session_id=new_sess.id,
                    question_text=q['question'],
                    category=q['category'],
                    difficulty=q.get('difficulty', 'Intermediate'),
                    expected_keywords=','.join(q['keywords'])
                ))

            db.commit()
            session[f'mock_progress_{new_sess.id}'] = {'index': 0, 'started_at': datetime.utcnow().isoformat()}
            return redirect(url_for('interview.mock_session', session_id=new_sess.id))

        previous_sessions = db.query(MockInterviewSession).filter_by(
            student_id=student.id
        ).order_by(MockInterviewSession.created_at.desc()).limit(20).all()
        return render_template('interview/mock_start.html', student=student, previous_sessions=previous_sessions)
    finally:
        db.close()


@interview_bp.route('/mock/<int:session_id>', methods=['GET', 'POST'])
@login_required
@role_required('student')
def mock_session(session_id):
    student_id = session.get('student_id')
    db = SessionLocal()
    try:
        sess = db.query(MockInterviewSession).filter_by(id=session_id, student_id=student_id).first()
        if not sess:
            flash('Mock interview session not found.', 'danger')
            return redirect(url_for('interview.mock_start'))

        items = sorted(sess.qa_items, key=lambda x: x.id)
        if not items:
            flash('This mock interview has no questions.', 'danger')
            return redirect(url_for('interview.mock_start'))

        state_key = f'mock_progress_{sess.id}'
        state = session.get(state_key) or {'index': 0, 'started_at': datetime.utcnow().isoformat()}
        current_index = int(state.get('index', 0))

        # Completed sessions are read-only and should go to their diagnostic.
        if all(item.student_answer is not None for item in items):
            return redirect(url_for('interview.mock_result', session_id=sess.id))

        current_index = max(0, min(current_index, len(items) - 1))
        current = items[current_index]

        if request.method == 'POST':
            answer = request.form.get(f'ans_{current.id}', '').strip()
            if not answer:
                flash('Please provide an answer before continuing.', 'warning')
                return redirect(url_for('interview.mock_session', session_id=sess.id))

            engine = MockInterviewEngine()
            keywords = [k.strip() for k in (current.expected_keywords or '').split(',') if k.strip()]
            evaluation = engine.evaluate_answer(current.question_text, keywords, answer, current.category)
            current.student_answer = answer
            current.time_taken_seconds = max(0, int(request.form.get('time_taken', 0) or 0))
            current.question_score = evaluation['overall_score']
            current.eval_breakdown = evaluation

            next_index = current_index + 1
            if next_index < len(items):
                session[state_key] = {'index': next_index, 'started_at': datetime.utcnow().isoformat()}
                db.commit()
                return redirect(url_for('interview.mock_session', session_id=sess.id))

            evaluations = [i.eval_breakdown for i in items if i.eval_breakdown]
            if evaluations:
                sess.overall_score = round(sum(e['overall_score'] for e in evaluations) / len(evaluations), 1)
                sess.technical_score = round(sum(e['technical_score'] for e in evaluations) / len(evaluations), 1)
                sess.communication_score = round(sum(e['communication_score'] for e in evaluations) / len(evaluations), 1)
                sess.relevance_score = round(sum(e['relevance_score'] for e in evaluations) / len(evaluations), 1)
                sess.structure_score = round(sum(e['structure_score'] for e in evaluations) / len(evaluations), 1)
                strengths = []
                weaknesses = []
                for e in evaluations:
                    strengths.extend(e.get('strengths', []))
                    weaknesses.extend(e.get('weaknesses', []))
                sess.strengths = list(dict.fromkeys(strengths))[:6]
                sess.weaknesses = list(dict.fromkeys(weaknesses))[:6]
                sess.feedback_summary = (
                    f'Local diagnostic completed across {len(evaluations)} responses. '
                    f'Composite performance: {sess.overall_score:.1f}%. '
                    'Review the strongest and weakest response patterns below.'
                )
            db.commit()
            session.pop(state_key, None)
            flash('Mock interview completed and evaluated locally.', 'success')
            return redirect(url_for('interview.mock_result', session_id=sess.id))

        return render_template(
            'interview/mock_session.html',
            mock_session=sess,
            current_item=current,
            current_index=current_index,
            total_questions=len(items),
            progress_pct=round(((current_index) / len(items)) * 100),
            question_seconds=180
        )
    finally:
        db.close()


@interview_bp.route('/mock/result/<int:session_id>')
@login_required
@role_required('student')
def mock_result(session_id):
    student_id = session.get('student_id')
    db = SessionLocal()
    try:
        sess = db.query(MockInterviewSession).filter_by(id=session_id, student_id=student_id).first()
        if not sess:
            flash('Mock interview session not found.', 'danger')
            return redirect(url_for('interview.mock_start'))
        return render_template('interview/mock_result.html', mock_session=sess)
    finally:
        db.close()


@interview_bp.route('/mock/report/<int:session_id>')
@login_required
@role_required('student')
def download_mock_report(session_id):
    student_id = session.get('student_id')
    db = SessionLocal()
    try:
        sess = db.query(MockInterviewSession).filter_by(id=session_id, student_id=student_id).first()
        student = db.query(Student).filter_by(id=student_id).first()
        if not sess or not student:
            flash('Mock interview report could not be found.', 'danger')
            return redirect(url_for('interview.mock_start'))

        interview_data = {
            'target_role': sess.target_role,
            'interview_type': sess.interview_type,
            'candidate_name': student.user.full_name,
            'overall_score': sess.overall_score,
            'technical_score': sess.technical_score,
            'communication_score': sess.communication_score,
            'relevance_score': sess.relevance_score,
            'structure_score': sess.structure_score,
            'feedback_summary': sess.feedback_summary
        }

        os.makedirs('reports/generated', exist_ok=True)
        pdf_path = os.path.join('reports/generated', f'Mock_Interview_Evaluation_Sess_{sess.id}.pdf')
        PlacementReportGenerator.generate_mock_interview_report(pdf_path, interview_data)
        return send_file(pdf_path, as_attachment=True, download_name=f'Mock_Interview_Diagnostic_{sess.id}.pdf')
    finally:
        db.close()
