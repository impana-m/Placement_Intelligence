import copy
from typing import Dict, Any, List
from ai.readiness.scorer import CareerReadinessScorer

class CareerSimulator:
    '''
    Layer 2 Explainable Intelligence:
    Enables students to simulate  What-If scenarios:
      - Upskill Python / SQL to Advanced
      - Complete an AWS or Docker Certification
      - Add a full-stack project or 3-month internship
      - Boost aptitude score to 85%
      - Elevate mock interview score to 80%
    Simulates recalculated readiness score and delta improvement WITHOUT mutating student database state.
    '''

    def __init__(self):
        self.scorer = CareerReadinessScorer()

    def simulate_what_if(self, base_student_data: Dict[str, Any], scenario: Dict[str, Any]) -> Dict[str, Any]:
        '''
        scenario: {
            'added_skills': [{'name': 'Docker', 'proficiency': 'Intermediate'}],
            'upgraded_skills': {'python': 'Advanced'},
            'added_certifications': 1,
            'added_projects': 1,
            'added_internship': True,
            'simulated_aptitude_pct': 85.0,
            'simulated_interview_score': 80.0,
            'simulated_resume_score': 90.0
        }
        '''
        base_res = self.scorer.compute_readiness(base_student_data)
        base_overall = base_res['overall_readiness']

        # Construct simulated clone
        sim_data = copy.deepcopy(base_student_data)
        sim_data['cgpa'] = sim_data.get('cgpa', 7.5)
        sim_data['attendance'] = sim_data.get('attendance', 85.0)
        sim_data['skills'] = list(sim_data.get('skills') or [])
        sim_data['projects'] = list(sim_data.get('projects') or [])
        sim_data['certifications'] = list(sim_data.get('certifications') or [])
        sim_data['internships'] = list(sim_data.get('internships') or [])
        sim_data['test_attempts'] = list(sim_data.get('test_attempts') or [])
        sim_data['mock_interviews'] = list(sim_data.get('mock_interviews') or [])
        sim_data['resume_completeness'] = sim_data.get('resume_completeness', 70.0)

        # Apply skill upgrades
        upgrades = scenario.get('upgraded_skills', {})
        for i, s in enumerate(sim_data['skills']):
            if s['name'].lower() in upgrades:
                sim_data['skills'][i] = {
                    'name': s['name'],
                    'proficiency': upgrades[s['name'].lower()]
                }

        # Add new skills
        for new_s in scenario.get('added_skills', []):
            sim_data['skills'].append(new_s)

        # Projects, Certs, Internships
        for p in range(scenario.get('added_projects', 0)):
            sim_data['projects'].append({'title': f'Simulated Capstone Project {p+1}', 'technologies': 'Python, MySQL'})

        for c in range(scenario.get('added_certifications', 0)):
            sim_data['certifications'].append({'name': f'Simulated Industry Certification {c+1}'})

        if scenario.get('added_internship'):
            sim_data['internships'].append({'role': 'Software Development Intern', 'duration_months': 3})

        # Test scores
        if 'simulated_aptitude_pct' in scenario and scenario['simulated_aptitude_pct'] is not None:
            sim_data['test_attempts'] = [{'percentage': float(scenario['simulated_aptitude_pct'])}]

        # Interview scores
        if 'simulated_interview_score' in scenario and scenario['simulated_interview_score'] is not None:
            sim_data['mock_interviews'] = [{'overall_score': float(scenario['simulated_interview_score'])}]

        # Resume score
        if 'simulated_resume_score' in scenario and scenario['simulated_resume_score'] is not None:
            sim_data['resume_completeness'] = float(scenario['simulated_resume_score'])

        # Compute simulated readiness
        sim_res = self.scorer.compute_readiness(sim_data)
        sim_overall = sim_res['overall_readiness']

        delta = round(sim_overall - base_overall, 1)

        insights = []
        if delta > 15:
            insights.append('Remarkable boost (+{:.1f}%): This combination transitions your profile into the top placement readiness quartile.'.format(delta))
        elif delta > 8:
            insights.append('Strong readiness lift (+{:.1f}%): Substantially increases shortlisting probability for Tier-1/Tier-2 drives.'.format(delta))
        elif delta > 0:
            insights.append('Positive incremental gain (+{:.1f}%): Reinforces candidate consistency.'.format(delta))
        else:
            insights.append('No improvement detected: Simulated changes did not increase overall readiness.')

        return {
            'is_simulation': True,
            'base_score': base_overall,
            'simulated_score': sim_overall,
            'score_delta': delta,
            'base_pillars': base_res['pillars'],
            'simulated_pillars': sim_res['pillars'],
            'insights': insights,
            'recommendations': sim_res['recommendations']
        }