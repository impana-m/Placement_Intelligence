from typing import List, Dict, Any

class SkillGapEngine:
    '''
    Layer 2 Explainable Intelligence:
    Diagnoses skill gaps between student profile and target job requirements.
    Classifies priority as Critical, High, Medium, Low based on whether it is required or preferred,
    and maps actionable training recommendations, projects, and certifications.
    '''

    PROFICIENCY_WEIGHTS = {
        'Beginner': 1,
        'Intermediate': 2,
        'Advanced': 3
    }

    ACTION_MAP = {
        'python': {
            'training': 'Advanced Python & Object-Oriented Design',
            'project': 'Build a full-stack REST API with Flask/FastAPI and unit testing',
            'certification': 'Python Institute Certified Associate in Python Programming (PCAP)'
        },
        'sql': {
            'training': 'Relational Database Design, Complex Joins & Query Optimization',
            'project': 'Design an e-commerce transactional database with indexed queries',
            'certification': 'Oracle Certified Database Associate or MySQL Developer'
        },
        'machine learning': {
            'training': 'Hands-on Machine Learning with Scikit-Learn & Feature Engineering',
            'project': 'End-to-end customer churn prediction pipeline with ML model evaluation',
            'certification': 'Coursera DeepLearning.AI Machine Learning Specialization'
        },
        'docker': {
            'training': 'Containerization & Docker Orchestration for Developers',
            'project': 'Containerize a multi-service web app with Docker Compose',
            'certification': 'Docker Certified Associate (DCA)'
        },
        'aws': {
            'training': 'AWS Cloud Practitioner & Core Services Architecture',
            'project': 'Deploy a serverless backend with AWS Lambda and S3 storage',
            'certification': 'AWS Certified Cloud Practitioner or Solutions Architect'
        },
        'javascript': {
            'training': 'Modern JavaScript (ES6+), Async/Await & DOM Manipulation',
            'project': 'Build an interactive dynamic analytics dashboard with Vanilla JS & Chart.js',
            'certification': 'OpenJS Foundation Certified Node/JS Developer'
        },
        'react': {
            'training': 'React.js Component Architecture, Hooks & State Management',
            'project': 'Build a single-page collaborative management portal',
            'certification': 'Meta Frontend Developer Professional Certificate'
        },
        'data structures': {
            'training': 'Data Structures & Algorithms Problem Solving Bootcamp',
            'project': 'Solve 75 LeetCode core algorithmic problems with time complexity analysis',
            'certification': 'HackerRank Problem Solving Advanced'
        }
    }

    def analyze_gaps(self, student_skills: List[Dict[str, Any]], required_skills_str: str, preferred_skills_str: str = '') -> Dict[str, Any]:
        student_skill_map = {}
        for s in student_skills:
            name = s['name'].strip().lower()
            prof = s.get('proficiency', 'Intermediate')
            student_skill_map[name] = prof

        req_list = [s.strip() for s in (required_skills_str or '').split(',') if s.strip()]
        pref_list = [s.strip() for s in (preferred_skills_str or '').split(',') if s.strip()]

        gap_items = []
        critical_count = 0
        high_count = 0

        for skill in req_list:
            norm = skill.lower()
            if norm not in student_skill_map:
                actions = self.ACTION_MAP.get(norm, {
                    'training': f'Master {skill} Core Fundamentals & Industry Use Cases',
                    'project': f'Build a practical hands-on portfolio project incorporating {skill}',
                    'certification': f'Earn an industry-recognized assessment or certificate in {skill}'
                })
                gap_items.append({
                    'skill_name': skill,
                    'is_required': True,
                    'current_level': 'Not Possessed',
                    'target_level': 'Intermediate / Advanced',
                    'priority': 'Critical',
                    'gap_status': 'Missing Core Skill',
                    'training_recommendation': actions['training'],
                    'project_recommendation': actions['project'],
                    'certification_recommendation': actions['certification']
                })
                critical_count += 1
            else:
                curr_level = student_skill_map[norm]
                if curr_level == 'Beginner':
                    actions = self.ACTION_MAP.get(norm, {
                        'training': f'Advance from Beginner to Intermediate {skill}',
                        'project': f'Refactor existing {skill} code for production performance',
                        'certification': f'Complete intermediate assessment in {skill}'
                    })
                    gap_items.append({
                        'skill_name': skill,
                        'is_required': True,
                        'current_level': 'Beginner',
                        'target_level': 'Intermediate',
                        'priority': 'High',
                        'gap_status': 'Proficiency Upgrade Needed',
                        'training_recommendation': actions['training'],
                        'project_recommendation': actions['project'],
                        'certification_recommendation': actions['certification']
                    })
                    high_count += 1

        for skill in pref_list:
            norm = skill.lower()
            if norm not in student_skill_map:
                actions = self.ACTION_MAP.get(norm, {
                    'training': f'Explore introductory concepts in {skill}',
                    'project': f'Create a mini tutorial or demo integrating {skill}',
                    'certification': f'Explore foundational badges for {skill}'
                })
                gap_items.append({
                    'skill_name': skill,
                    'is_required': False,
                    'current_level': 'Not Possessed',
                    'target_level': 'Beginner / Intermediate',
                    'priority': 'Medium',
                    'gap_status': 'Value-Add Skill Missing',
                    'training_recommendation': actions['training'],
                    'project_recommendation': actions['project'],
                    'certification_recommendation': actions['certification']
                })

        total_analyzed = len(req_list) + len(pref_list)
        gap_score = 100.0 - (critical_count * 20.0 + high_count * 10.0)
        gap_score = max(10.0, min(100.0, gap_score))

        return {
            'readiness_percentage': round(gap_score, 1),
            'critical_gaps_count': critical_count,
            'high_gaps_count': high_count,
            'total_gaps_count': len(gap_items),
            'gap_items': gap_items
        }