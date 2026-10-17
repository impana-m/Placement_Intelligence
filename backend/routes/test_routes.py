import random
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from backend.models.database import SessionLocal
from backend.models.models import Test, Question, TestAttempt, Student
from backend.auth.security import login_required, role_required

test_bp = Blueprint('test', __name__, url_prefix='/tests')


def _safe_count(value, default=15):
    try:
        return max(5, min(int(value), 30))
    except (TypeError, ValueError):
        return default


@test_bp.route('/')
@login_required
@role_required('student')
def list_tests():
    student_id = session.get('student_id')
    db = SessionLocal()
    try:
        student = db.query(Student).filter_by(id=student_id).first()
        tests = db.query(Test).order_by(Test.category, Test.topic, Test.title).all()
        attempts = {}
        for attempt in db.query(TestAttempt).filter_by(student_id=student_id).order_by(TestAttempt.created_at.desc()).all():
            attempts.setdefault(attempt.test_id, attempt)
        return render_template('tests/list.html', tests=tests, attempts=attempts, student=student)
    finally:
        db.close()


@test_bp.route('/<int:test_id>/take', methods=['GET', 'POST'])
@login_required
@role_required('student')
def take_test(test_id):
    student_id = session.get('student_id')
    db = SessionLocal()
    try:
        test = db.query(Test).filter_by(id=test_id).first()
        if not test:
            flash('Assessment test not found.', 'danger')
            return redirect(url_for('test.list_tests'))

        session_key = f'qt_test_{test.id}'

        if request.method == 'GET':
            requested_count = _safe_count(request.args.get('count', 15))
            difficulty = request.args.get('difficulty', 'All')

            query = db.query(Question).filter(Question.test_id == test.id)
            if difficulty in {'Easy', 'Medium', 'Hard'}:
                query = query.filter(Question.difficulty == difficulty)
            pool = query.all()
            if not pool:
                flash('This assessment does not have questions for the selected difficulty.', 'warning')
                return redirect(url_for('test.list_tests'))

            selected_count = min(requested_count, len(pool))
            selected = random.sample(pool, selected_count)
            session[session_key] = {
                'question_ids': [q.id for q in selected],
                'started_at': datetime.now(timezone.utc).isoformat(),
                'difficulty': difficulty,
            }
            return render_template(
                'tests/take.html',
                test=test,
                questions=selected,
                duration_seconds=int(test.duration_minutes * 60),
                selected_count=selected_count,
                difficulty=difficulty
            )

        state = session.get(session_key)
        if not state or not state.get('question_ids'):
            flash('Your test session expired. Please start the assessment again.', 'warning')
            return redirect(url_for('test.take_test', test_id=test.id))

        question_ids = state['question_ids']
        questions = db.query(Question).filter(
            Question.test_id == test.id,
            Question.id.in_(question_ids)
        ).all()
        question_map = {q.id: q for q in questions}
        elapsed = max(0, int((datetime.now(timezone.utc) - datetime.fromisoformat(state['started_at'])).total_seconds()))
        timed_out = elapsed > int(test.duration_minutes * 60)

        correct_count = 0
        marks_scored = 0
        max_marks = sum(max(1, q.marks or 1) for q in questions)
        user_answers = {}
        topic_stats = {}

        for qid in question_ids:
            q = question_map.get(qid)
            if not q:
                continue
            selected = request.form.get(f'q_{qid}')
            user_answers[str(qid)] = selected
            topic = q.topic or test.topic
            stats = topic_stats.setdefault(topic, {'correct': 0, 'attempted': 0, 'total': 0})
            stats['total'] += 1
            if selected:
                stats['attempted'] += 1
            if selected == q.correct_option:
                correct_count += 1
                marks_scored += max(1, q.marks or 1)
                stats['correct'] += 1

        percentage = round((marks_scored / max(1, max_marks)) * 100, 1)
        passed = (not timed_out) and (percentage >= test.pass_percentage)
        attempt = TestAttempt(
            test_id=test.id,
            student_id=student_id,
            score=marks_scored,
            total_marks=max_marks,
            percentage=percentage,
            passed=passed,
            answers_data={
                'answers': user_answers,
                'selected_question_ids': question_ids,
                'elapsed_seconds': elapsed,
                'timed_out': timed_out,
                'correct_count': correct_count,
                'question_count': len(question_ids),
                'topic_stats': topic_stats,
            }
        )
        db.add(attempt)
        db.commit()
        session.pop(session_key, None)
        flash(f'Assessment completed: {marks_scored}/{max_marks} marks ({percentage}%).', 'success')
        return redirect(url_for('test.view_result', attempt_id=attempt.id))
    finally:
        db.close()


@test_bp.route('/result/<int:attempt_id>')
@login_required
@role_required('student')
def view_result(attempt_id):
    student_id = session.get('student_id')
    db = SessionLocal()
    try:
        attempt = db.query(TestAttempt).filter_by(id=attempt_id, student_id=student_id).first()
        if not attempt:
            flash('Attempt record not found.', 'danger')
            return redirect(url_for('test.list_tests'))
        data = attempt.answers_data or {}
        question_ids = data.get('selected_question_ids', [])
        questions = db.query(Question).filter(Question.id.in_(question_ids)).all() if question_ids else []
        question_map = {q.id: q for q in questions}
        answers = data.get('answers', {})
        breakdown = []
        for qid in question_ids:
            q = question_map.get(qid)
            if q:
                selected = answers.get(str(qid))
                breakdown.append({
                    'question': q,
                    'selected': selected,
                    'correct': selected == q.correct_option,
                })
        return render_template(
            'tests/result.html',
            attempt=attempt,
            test=attempt.test,
            breakdown=breakdown,
            topic_stats=data.get('topic_stats', {}),
            elapsed_seconds=data.get('elapsed_seconds', 0),
            timed_out=data.get('timed_out', False),
            correct_count=data.get('correct_count', 0)
        )
    finally:
        db.close()
