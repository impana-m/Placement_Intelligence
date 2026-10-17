from typing import Dict, Any, List
from sqlalchemy import text
from backend.models.database import SessionLocal

class PlacementAnalytics:
    @staticmethod
    def get_placement_funnel(department_id: int = None, batch_year: int = None) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            sql = """
                SELECT 
                    a.status,
                    COUNT(a.id) as count
                FROM applications a
                JOIN students s ON a.student_id = s.id
                WHERE 1=1
            """
            params = {}
            if department_id:
                sql += " AND s.department_id = :dept_id"
                params['dept_id'] = department_id
            if batch_year:
                sql += " AND s.batch_year = :batch_year"
                params['batch_year'] = batch_year

            sql += " GROUP BY a.status"

            res = db.execute(text(sql), params).fetchall()
            status_counts = {row[0]: row[1] for row in res}

            stages = [
                'Applied',
                'Shortlisted',
                'Test',
                'Technical Interview',
                'HR Interview',
                'Selected',
                'Offer Received'
            ]

            counts = [status_counts.get(stage, 0) for stage in stages]
            total_apps = max(1, sum(counts))
            percentages = [round((c / total_apps) * 100, 1) for c in counts]

            return {
                'stages': stages,
                'counts': counts,
                'percentages': percentages,
                'total_applications': sum(counts)
            }
        finally:
            db.close()

    @staticmethod
    def get_skill_demand_analytics() -> Dict[str, Any]:
        db = SessionLocal()
        try:
            sql = "SELECT required_skills, preferred_skills FROM jobs WHERE status = 'Active'"
            jobs = db.execute(text(sql)).fetchall()

            skill_freq = {}
            for j in jobs:
                req = [s.strip() for s in (j[0] or '').split(',') if s.strip()]
                pref = [s.strip() for s in (j[1] or '').split(',') if s.strip()]
                for s in req:
                    s_clean = s.title()
                    skill_freq[s_clean] = skill_freq.get(s_clean, 0) + 3
                for s in pref:
                    s_clean = s.title()
                    skill_freq[s_clean] = skill_freq.get(s_clean, 0) + 1

            sorted_skills = sorted(skill_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            labels = [s[0] for s in sorted_skills]
            demand_scores = [s[1] for s in sorted_skills]

            return {
                'skills': labels,
                'demand_scores': demand_scores
            }
        finally:
            db.close()

    @staticmethod
    def get_department_comparison() -> Dict[str, Any]:
        db = SessionLocal()
        try:
            sql = """
                SELECT 
                    d.name as dept_name,
                    COUNT(s.id) as total_students,
                    SUM(CASE WHEN s.placement_status = 'Placed' THEN 1 ELSE 0 END) as placed_students,
                    AVG(s.cgpa) as avg_cgpa
                FROM departments d
                LEFT JOIN students s ON d.id = s.department_id
                GROUP BY d.id, d.name
            """
            rows = db.execute(text(sql)).fetchall()
            dept_names = []
            placement_rates = []
            avg_cgpas = []
            for r in rows:
                dept_names.append(r[0])
                total = r[1] or 0
                placed = r[2] or 0
                rate = round((placed / total * 100), 1) if total > 0 else 0.0
                placement_rates.append(rate)
                avg_cgpas.append(round(float(r[3] or 0.0), 2))

            return {
                'departments': dept_names,
                'placement_rates': placement_rates,
                'avg_cgpas': avg_cgpas
            }
        finally:
            db.close()

    @staticmethod
    def get_salary_distribution() -> Dict[str, Any]:
        db = SessionLocal()
        try:
            sql = "SELECT package_lpa FROM offers WHERE status IN ('Offered', 'Accepted')"
            rows = db.execute(text(sql)).fetchall()
            packages = [float(r[0]) for r in rows if r[0] is not None]

            buckets = {'< 5 LPA': 0, '5-8 LPA': 0, '8-12 LPA': 0, '> 12 LPA': 0}
            for p in packages:
                if p < 5.0:
                    buckets['< 5 LPA'] += 1
                elif p <= 8.0:
                    buckets['5-8 LPA'] += 1
                elif p <= 12.0:
                    buckets['8-12 LPA'] += 1
                else:
                    buckets['> 12 LPA'] += 1

            return {
                'labels': list(buckets.keys()),
                'counts': list(buckets.values()),
                'avg_package': round(sum(packages) / len(packages), 2) if packages else 0.0,
                'max_package': max(packages) if packages else 0.0
            }
        finally:
            db.close()
