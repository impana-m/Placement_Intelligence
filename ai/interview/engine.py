import random
import re
from typing import Dict, Any, List

from ai.interview.question_bank import QUESTION_BANK


class MockInterviewEngine:
    """Local interview selector and response evaluator.

    No paid API is required. Question selection is randomized from the local
    tagged bank and answers are scored from observable response signals.
    """

    QUESTION_BANK = QUESTION_BANK

    FILLER_WORDS = [
        'um', 'uh', 'like', 'you know', 'basically', 'actually',
        'sort of', 'kind of', 'i mean'
    ]
    STAR_INDICATORS = {
        'situation': ['when', 'during', 'in my project', 'at my internship', 'while building', 'scenario'],
        'task': ['my responsibility was', 'needed to', 'tasked with', 'objective was', 'goal was'],
        'action': ['i implemented', 'i decided', 'i wrote', 'i analyzed', 'i refactored', 'we developed', 'i initiated'],
        'result': ['resulting in', 'increased', 'reduced', 'achieved', 'successfully', 'outcome was', 'delivered']
    }

    def get_questions_for_role(self, role: str, interview_type: str = 'Technical', count: int = 5, difficulty: str = 'All') -> List[Dict[str, Any]]:
        count = max(1, min(int(count), 15))
        role = role or 'Software Engineer'
        interview_type = interview_type or 'Technical'
        difficulty = difficulty or 'All'

        type_aliases = {
            'HR': {'HR', 'Communication'},
            'Behavioral': {'Behavioral'},
            'Situational': {'Situational'},
            'Communication': {'Communication'},
            'Technical': {'Technical'},
            'Mixed': {'Technical', 'HR', 'Behavioral', 'Situational', 'Communication'}
        }
        allowed_categories = type_aliases.get(interview_type, {'Technical'})

        def role_match(q):
            q_role = q['role'].lower()
            requested = role.lower()
            return q_role == 'general' or q_role in requested or requested in q_role

        candidates = [q for q in self.QUESTION_BANK if q['category'] in allowed_categories and role_match(q)]
        if difficulty != 'All':
            filtered = [q for q in candidates if q.get('difficulty') == difficulty]
            if len(filtered) >= count:
                candidates = filtered

        # Fill from category-compatible general questions first, then any
        # suitable local question so every requested session can start.
        if len(candidates) < count:
            for q in self.QUESTION_BANK:
                if q in candidates or q['category'] not in allowed_categories:
                    continue
                candidates.append(q)
                if len(candidates) >= count:
                    break
        if len(candidates) < count:
            for q in self.QUESTION_BANK:
                if q not in candidates:
                    candidates.append(q)
                if len(candidates) >= count:
                    break

        random.shuffle(candidates)
        return candidates[:count]

    def evaluate_answer(self, question: str, expected_keywords: List[str], answer: str, category: str = 'Technical') -> Dict[str, Any]:
        cleaned_answer = (answer or '').strip()
        words = cleaned_answer.lower().split()
        word_count = len(words)

        if word_count < 10:
            return {
                'overall_score': 20.0,
                'technical_score': 15.0,
                'relevance_score': 20.0,
                'communication_score': 30.0,
                'structure_score': 15.0,
                'feedback': 'Answer is too brief to evaluate thoroughly. Provide at least 3-4 structured sentences with specific details.',
                'strengths': ['Attempted answer'],
                'weaknesses': ['Very low detail', 'Lacks supporting explanation']
            }

        lower_ans = cleaned_answer.lower()
        matched_kw = [kw for kw in expected_keywords if kw.lower() in lower_ans]
        kw_ratio = len(matched_kw) / max(1, len(expected_keywords))
        tech_score = min(100.0, kw_ratio * 120.0)
        if category in ['HR', 'Behavioral', 'Situational', 'Communication']:
            tech_score = min(100.0, 55.0 + min(word_count, 120) / 3.0)

        if 50 <= word_count <= 250:
            rel_score = 90.0
        elif 30 <= word_count < 50:
            rel_score = 70.0
        elif word_count > 250:
            rel_score = 80.0
        else:
            rel_score = 50.0

        filler_found = []
        for fw in self.FILLER_WORDS:
            occurrences = len(re.findall(r'\b' + re.escape(fw) + r'\b', lower_ans))
            if occurrences > 0:
                filler_found.append(f'{fw} ({occurrences}x)')
        filler_deduction = min(35.0, len(filler_found) * 8.0)
        comm_score = max(40.0, 95.0 - filler_deduction)

        star_found = []
        for stage, markers in self.STAR_INDICATORS.items():
            if any(m in lower_ans for m in markers):
                star_found.append(stage)

        if category in ['Behavioral', 'HR', 'Situational']:
            struct_score = max(40.0, min(100.0, (len(star_found) / 4.0) * 100.0))
        else:
            connectors = ['because', 'therefore', 'firstly', 'secondly', 'in comparison', 'for example', 'however']
            conn_count = sum(1 for c in connectors if c in lower_ans)
            struct_score = min(100.0, 50.0 + conn_count * 12.5)

        overall = round(
            (tech_score * 0.35) +
            (rel_score * 0.25) +
            (comm_score * 0.20) +
            (struct_score * 0.20),
            1
        )
        overall = max(20.0, min(98.0, overall))

        strengths = []
        weaknesses = []
        if matched_kw:
            strengths.append('Relevant concepts detected: ' + ', '.join(matched_kw[:4]))
        if word_count >= 50:
            strengths.append('Good answer depth and detail')
        if star_found:
            strengths.append('Structured response elements detected: ' + ', '.join(star_found))
        if comm_score >= 85:
            strengths.append('Clear communication with limited filler words')

        if len(matched_kw) < max(1, len(expected_keywords) // 2) and category == 'Technical':
            missing = [k for k in expected_keywords if k not in matched_kw]
            weaknesses.append('Consider covering: ' + ', '.join(missing[:4]))
        if filler_found:
            weaknesses.append('Reduce conversational fillers: ' + ', '.join(filler_found[:3]))
        if word_count < 40:
            weaknesses.append('Add a concrete example, reasoning or measurable outcome')
        if category in ['Behavioral', 'HR', 'Situational'] and len(star_found) < 3:
            weaknesses.append('Use a clearer Situation → Task → Action → Result structure')

        if overall >= 75:
            feedback = 'Clear and relevant response with useful supporting detail.'
        elif overall >= 55:
            feedback = 'Good foundation. Add stronger evidence, examples and role-specific detail.'
        else:
            feedback = 'Needs more structure, detail and role-specific evidence.'

        return {
            'overall_score': overall,
            'technical_score': round(tech_score, 1),
            'relevance_score': round(rel_score, 1),
            'communication_score': round(comm_score, 1),
            'structure_score': round(struct_score, 1),
            'matched_keywords': matched_kw,
            'filler_words_detected': filler_found,
            'star_elements_detected': star_found,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'feedback': feedback
        }
