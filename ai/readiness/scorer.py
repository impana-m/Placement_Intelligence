from typing import Dict, Any, List

class CareerReadinessScorer:
    '''
    Layer 2 Explainable Intelligence:
    Calculates a multi-pillar Career Readiness score out of 100 with clear weighting:
      1. Academics & Attendance (20%)
      2. Technical Skills & Proficiencies (25%)
      3. Projects & Certifications (15%)
      4. Resume Completeness (10%)
      5. Aptitude & Technical Tests (15%)
      6. Mock Interview Performance (15%)
    Includes explainable strengths, weaknesses, and targeted recommendations.
    '''

    def compute_readiness(self, student_data: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Academic Pillar (20%)
        cgpa = float(student_data.get('cgpa') or 0.0)
        attendance = float(student_data.get('attendance') or 0.0)
        # Note: Assumes a 10.0 scale (CGPA normalized to 10 scale -> 10 = 100%)
        cgpa_score = min(100.0, (cgpa / 10.0) * 100.0)  # Assumes 10.0 GPA scale
        attendance_score = min(100.0, attendance)
        academic_pillar = (cgpa_score * 0.7) + (attendance_score * 0.3)

        # 2. Technical Skills Pillar (25%)
        skills = student_data.get('skills', [])
        if not skills:
            technical_pillar = 20.0
        else:
            skill_weights = {'Beginner': 40.0, 'Intermediate': 75.0, 'Advanced': 100.0}
            scores = [skill_weights.get(s.get('proficiency', 'Intermediate'), 70.0) for s in skills]
            avg_skill_quality = sum(scores) / len(scores)
            count_factor = min(1.0, len(skills) / 6.0) # 6 skills target
            technical_pillar = (avg_skill_quality * 0.7) + (count_factor * 100.0 * 0.3)

        # 3. Projects & Certifications & Internships (15%)
        projects = student_data.get('projects', [])
        certifications = student_data.get('certifications', [])
        internships = student_data.get('internships', [])
        project_score = min(50.0, len(projects) * 25.0)
        cert_score = min(25.0, len(certifications) * 15.0)
        intern_score = min(25.0, len(internships) * 25.0)
        portfolio_pillar = project_score + cert_score + intern_score

        # 4. Resume Completeness (10%)
        resume_score = float(student_data.get('resume_completeness') or 0.0)

        # 5. Aptitude & Technical Tests (15%)
        test_attempts = student_data.get('test_attempts', [])
        if test_attempts:
            test_percentages = [t.get('percentage', 0.0) for t in test_attempts]
            test_pillar = sum(test_percentages) / len(test_percentages)
        else:
            test_pillar = 0.0

        # 6. Mock Interview Performance (15%)
        mock_sessions = student_data.get('mock_interviews', [])
        if mock_sessions:
            mock_scores = [m.get('overall_score', 0.0) for m in mock_sessions]
            interview_pillar = sum(mock_scores) / len(mock_scores)
        else:
            interview_pillar = 0.0

        # Overall Weighted Score
        overall = round(
            (academic_pillar * 0.20) +
            (technical_pillar * 0.25) +
            (portfolio_pillar * 0.15) +
            (resume_score * 0.10) +
            (test_pillar * 0.15) +
            (interview_pillar * 0.15),
            1
        )
        overall = max(5.0, min(99.0, overall))

        # Strengths & Weaknesses
        strengths = []
        weaknesses = []
        recommendations = []

        if academic_pillar >= 75:
            strengths.append(f'Consistent academic standing (CGPA: {cgpa:.1f})')
        else:
            weaknesses.append('Academic CGPA could be enhanced before major drive deadlines')
            recommendations.append('Attend remedial review sessions to boost semester GPA')

        if technical_pillar >= 70:
            strengths.append(f'Solid skill foundation with {len(skills)} verified competencies')
        else:
            weaknesses.append('Skill profile needs more diversity or advanced proficiencies')
            recommendations.append('Upskill to Intermediate/Advanced in at least 2 core job-aligned technologies')

        if len(projects) >= 2:
            strengths.append(f'{len(projects)} practical development projects in portfolio')
        else:
            weaknesses.append('Practical portfolio requires additional demonstrable projects')
            recommendations.append('Build and deploy at least 1 comprehensive full-stack capstone project')

        if resume_score >= 80:
            strengths.append('High resume completeness and structured ATS readability')
        else:
            weaknesses.append(f'Resume completeness is low ({resume_score:.0f}%)')
            recommendations.append('Upload an updated ATS-formatted resume with quantified impact metrics')

        if test_pillar >= 70:
            strengths.append('Strong aptitude and technical assessment benchmarks')
        else:
            weaknesses.append('Assessment performance is below target placement cut-off (70%)')
            recommendations.append('Practice weekly aptitude and technical MCQ drills on the platform')

        if interview_pillar >= 70:
            strengths.append('Confident mock interview performance and structured responses')
        else:
            weaknesses.append('Mock interview communication and STAR structure need refinement')
            recommendations.append('Complete mock interview sessions for target roles with detailed answer reviews')

        return {
            'overall_readiness': overall,
            'pillars': {
                'academic': round(academic_pillar, 1),
                'technical': round(technical_pillar, 1),
                'portfolio': round(portfolio_pillar, 1),
                'resume': round(resume_score, 1),
                'tests': round(test_pillar, 1),
                'interview': round(interview_pillar, 1)
            },
            'strengths': strengths,
            'weaknesses': weaknesses,
            'recommendations': recommendations
        }