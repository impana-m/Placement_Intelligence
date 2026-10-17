import os
import re
from typing import Dict, Any, List

class ResumeParser:
    '''
    Extracts text from PDF (using PyMuPDF) or DOCX (using python-docx).
    Locates sections (Education, Skills, Experience, Projects, Certifications)
    and matches industry technology keywords.
    '''

    COMMON_SKILLS = [
        'Python', 'Java', 'C++', 'C#', 'JavaScript', 'TypeScript', 'HTML', 'CSS',
        'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis',
        'Flask', 'Django', 'FastAPI', 'React', 'Angular', 'Vue', 'Node.js', 'Express',
        'Docker', 'Kubernetes', 'AWS', 'Azure', 'Git', 'GitHub', 'Linux',
        'Machine Learning', 'Data Analysis', 'Pandas', 'NumPy', 'Scikit-Learn',
        'REST API', 'GraphQL', 'Tailwind', 'Bootstrap', 'Agile', 'Scrum'
    ]

    SECTION_PATTERNS = {
        'education': r'(?i)\b(education|academic|qualifications|degrees)\b',
        'skills': r'(?i)\b(skills|technical skills|technologies|proficiencies|competencies)\b',
        'projects': r'(?i)\b(projects|academic projects|key projects|portfolio)\b',
        'experience': r'(?i)\b(experience|work experience|employment|internships)\b',
        'certifications': r'(?i)\b(certifications|certificates|licenses|achievements)\b'
    }

    def extract_text_from_pdf(self, file_path: str) -> str:
        text = ''
        try:
            import fitz
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text() + '\n'
            doc.close()
        except Exception as e:
            text = f'PDF Extraction Error: {str(e)}'
        return text

    def extract_text_from_docx(self, file_path: str) -> str:
        text = ''
        try:
            import docx
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + '\n'
        except Exception as e:
            text = f'DOCX Extraction Error: {str(e)}'
        return text

    def parse_resume(self, file_path: str) -> Dict[str, Any]:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            raw_text = self.extract_text_from_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            raw_text = self.extract_text_from_docx(file_path)
        else:
            raw_text = ''

        # Detect sections
        detected_sections = {}
        for sec_name, pattern in self.SECTION_PATTERNS.items():
            if re.search(pattern, raw_text):
                detected_sections[sec_name] = True
            else:
                detected_sections[sec_name] = False

        # Detect skills
        found_skills = []
        lower_text = raw_text.lower()
        for skill in self.COMMON_SKILLS:
            # Word boundary regex
            pattern = r'(?i)(?:\b|(?<=\W))' + re.escape(skill) + r'(?:\b|(?=\W))'
            if re.search(pattern, lower_text):
                found_skills.append(skill)

        # Completeness calculation
        sections_found = sum(1 for v in detected_sections.values() if v)
        section_score = (sections_found / len(detected_sections)) * 60.0 # 60%
        skill_score = min(40.0, (len(found_skills) / 8.0) * 40.0) # 40%
        completeness = round(section_score + skill_score, 1)

        return {
            'raw_text': raw_text[:5000], # store preview
            'detected_sections': detected_sections,
            'detected_skills': sorted(list(set(found_skills))),
            'completeness_score': completeness,
            'word_count': len(raw_text.split())
        }

    def align_with_job(self, resume_skills: List[str], raw_text: str, job_dict: Dict[str, Any]) -> Dict[str, Any]:
        job_req = [s.strip() for s in (job_dict.get('required_skills') or '').split(',') if s.strip()]
        job_pref = [s.strip() for s in (job_dict.get('preferred_skills') or '').split(',') if s.strip()]

        norm_resume_skills = [s.lower() for s in resume_skills]

        matched_skills = [s for s in job_req if s.lower() in norm_resume_skills]
        missing_skills = [s for s in job_req if s.lower() not in norm_resume_skills]

        pref_matched = [s for s in job_pref if s.lower() in norm_resume_skills]
        pref_missing = [s for s in job_pref if s.lower() not in norm_resume_skills]

        total_req = len(job_req)
        score = 0.0
        if total_req > 0:
            score = (len(matched_skills) / total_req) * 85.0 + ((len(pref_matched) / len(job_pref)) * 15.0 if job_pref else 15.0)
        else:
            score = 75.0
        score = round(max(15.0, min(100.0, score)), 1)

        # ATS recommendations
        suggestions = []
        if missing_skills:
            suggestions.append('Add these missing critical ATS keywords: ' + ', '.join(missing_skills) + '.')
        if not re.search(r'(?i)\b(achieved|improved|optimized|spearheaded|developed)\b', raw_text):
            suggestions.append('Use strong action verbs (e.g. Optimized, Built, Engineered, Deployed) in experience/projects.')
        if not re.search(r'\b\d+%\b|\b\d+x\b|\b\$\d+\b|\b\d+\s*(users|requests|ms)\b', raw_text):
            suggestions.append('Quantify your project outcomes with metrics (e.g., "Reduced response latency by 35%").')

        return {
            'alignment_score': score,
            'matched_skills': matched_skills + pref_matched,
            'missing_skills': missing_skills,
            'missing_preferred': pref_missing,
            'suggestions': suggestions
        }