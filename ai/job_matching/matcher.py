import re
import math
from typing import Dict, Any, List
from collections import Counter

class LocalJobMatchingEngine:
    @staticmethod
    def _tokenize(text: str) -> List[str]:
        words = re.findall(r"\b[a-zA-Z0-9\+\#\.]+\b", text.lower())
        stopwords = {
            "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
            "any", "are", "as", "at", "be", "because", "been", "before", "being", "below",
            "between", "both", "but", "by", "could", "did", "do", "does", "doing", "down",
            "during", "each", "few", "for", "from", "further", "had", "has", "have", "having",
            "he", "her", "here", "hers", "herself", "him", "himself", "his", "how", "i",
            "if", "in", "into", "is", "it", "its", "itself", "just", "me", "more", "most",
            "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once", "only",
            "or", "other", "our", "ours", "ourselves", "out", "over", "own", "same", "she",
            "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them",
            "themselves", "then", "there", "these", "they", "this", "those", "through", "to",
            "too", "under", "until", "up", "very", "was", "we", "were", "what", "when",
            "where", "which", "while", "who", "whom", "why", "with", "would", "you", "your",
            "yours", "yourself", "yourselves"
        }
        return [w for w in words if w not in stopwords and len(w) > 1]

    @classmethod
    def compute_cosine_similarity(cls, text1: str, text2: str) -> float:
        tokens1 = cls._tokenize(text1)
        tokens2 = cls._tokenize(text2)
        if not tokens1 or not tokens2:
            return 0.0

        vec1 = Counter(tokens1)
        vec2 = Counter(tokens2)

        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum([vec1[x] * vec2[x] for x in intersection])

        sum1 = sum([val**2 for val in vec1.values()])
        sum2 = sum([val**2 for val in vec2.values()])
        denominator = math.sqrt(sum1) * math.sqrt(sum2)

        if not denominator:
            return 0.0
        return float(numerator) / denominator * 100.0

    @staticmethod
    def _normalize_skill(s: str) -> str:
        s = s.lower().strip()
        s = re.sub(r"[\.\-\_\/\s]+", " ", s)
        alias_map = {
            "js": "javascript",
            "py": "python",
            "ml": "machine learning",
            "ai": "artificial intelligence",
            "db": "database",
            "postgres": "postgresql",
            "reactjs": "react",
            "vuejs": "vue",
            "nodejs": "node",
            "aws cloud": "aws"
        }
        return alias_map.get(s, s)

    def compute_match(self, student_dict: Dict[str, Any], job_dict: Dict[str, Any]) -> Dict[str, Any]:
        student_skills = [self._normalize_skill(s["name"]) for s in student_dict.get("skills", [])]
        req_skills_raw = [s.strip() for s in (job_dict.get("required_skills") or "").split(",") if s.strip()]
        req_skills = [self._normalize_skill(s) for s in req_skills_raw]
        pref_skills_raw = [s.strip() for s in (job_dict.get("preferred_skills") or "").split(",") if s.strip()]
        pref_skills = [self._normalize_skill(s) for s in pref_skills_raw]

        matched_required = []
        missing_required = []
        for orig, norm in zip(req_skills_raw, req_skills):
            if norm in student_skills:
                matched_required.append(orig)
            else:
                missing_required.append(orig)

        matched_preferred = []
        missing_preferred = []
        for orig, norm in zip(pref_skills_raw, pref_skills):
            if norm in student_skills:
                matched_preferred.append(orig)
            else:
                missing_preferred.append(orig)

        total_req = len(req_skills)
        skill_score = 0.0
        if total_req > 0:
            req_ratio = len(matched_required) / total_req
            pref_ratio = (len(matched_preferred) / len(pref_skills)) if pref_skills else 0.0
            skill_score = (req_ratio * 0.85 + pref_ratio * 0.15) * 100
        else:
            skill_score = 75.0

        student_text_parts = [
            " ".join([(s.get("name") or "") for s in student_dict.get("skills", [])]),
            " ".join([(p.get("title") or "") + " " + (p.get("technologies") or "") + " " + (p.get("description") or "") for p in student_dict.get("projects", [])]),
            " ".join([(i.get("role") or "") + " " + (i.get("description") or "") for i in student_dict.get("internships", [])]),
            student_dict.get("bio") or ""
        ]
        student_doc = " ".join(student_text_parts).strip()
        job_doc = ((job_dict.get("title") or "") + " " + (job_dict.get("description") or "") + " " + (job_dict.get("required_skills") or "")).strip()

        semantic_score = self.compute_cosine_similarity(student_doc, job_doc)

        student_cgpa = float(student_dict.get("cgpa") or 0.0)
        min_cgpa = float(job_dict.get("min_cgpa") or 0.0)
        academic_score = 100.0 if student_cgpa >= min_cgpa else max(30.0, 100.0 - (min_cgpa - student_cgpa) * 35.0)

        project_count = len(student_dict.get("projects", []))
        internship_count = len(student_dict.get("internships", []))
        exp_score = min(100.0, project_count * 30.0 + internship_count * 40.0)

        overall_match = round(
            (skill_score * 0.45) +
            (semantic_score * 0.25) +
            (academic_score * 0.15) +
            (exp_score * 0.15),
            1
        )
        overall_match = max(10.0, min(99.0, overall_match))

        explanation_lines = []
        if total_req > 0:
            pct = round((len(matched_required) / total_req) * 100)
            explanation_lines.append(f"{len(matched_required)} of {total_req} required skills are present ({pct}% coverage).")
        if matched_required:
            explanation_lines.append(f"Matched Core Skills: {', '.join(matched_required[:5])}.")
        if missing_required:
            explanation_lines.append(f"Missing Required Skills: {', '.join(missing_required[:4])}.")
        if student_cgpa >= min_cgpa:
            explanation_lines.append(f"Meets academic criteria (CGPA {student_cgpa} >= {min_cgpa}).")
        else:
            explanation_lines.append(f"CGPA deficit ({student_cgpa} < {min_cgpa} minimum).")

        return {
            "overall_match": overall_match,
            "skill_match_percentage": round(skill_score, 1),
            "semantic_similarity": round(semantic_score, 1),
            "academic_score": round(academic_score, 1),
            "experience_score": round(exp_score, 1),
            "matched_skills": matched_required + matched_preferred,
            "missing_skills": missing_required,
            "missing_preferred": missing_preferred,
            "meets_cgpa": student_cgpa >= min_cgpa,
            "explanation": " ".join(explanation_lines)
        }
