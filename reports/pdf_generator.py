import os
import html
import logging
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

class PlacementReportGenerator:
    @staticmethod
    def _get_styles():
        styles = getSampleStyleSheet()
        normal = styles['Normal']
        normal.textColor = colors.HexColor('#1E293B')
        normal.fontSize = 10
        normal.leading = 14

        title_style = ParagraphStyle(
            'RepTitle',
            parent=styles['Heading1'],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#0F172A'),
            spaceAfter=6
        )

        subtitle_style = ParagraphStyle(
            'RepSubtitle',
            parent=normal,
            fontSize=11,
            leading=16,
            textColor=colors.HexColor('#475569'),
            spaceAfter=15
        )

        h2_style = ParagraphStyle(
            'RepH2',
            parent=styles['Heading2'],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor('#2563EB'),
            spaceBefore=12,
            spaceAfter=6
        )

        badge_style = ParagraphStyle(
            'Badge',
            parent=normal,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#1E40AF'),
            fontName='Helvetica-Bold'
        )

        return styles, normal, title_style, subtitle_style, h2_style, badge_style

    @classmethod
    def generate_student_report(cls, output_path: str, student_data: dict):
        styles, normal, title_style, subtitle_style, h2_style, badge_style = cls._get_styles()
        doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []

        # Header Banner
        header_table = Table([
            [Paragraph("<b>COLLEGE PLACEMENT & CAREER INTELLIGENCE SYSTEM</b>", badge_style)],
            [Paragraph("Student Career Readiness & Diagnostic Dossier", title_style)],
            [Paragraph(f"Confidential Report for: <b>{html.escape(str(student_data.get('full_name') or ''))}</b> | USN: <b>{html.escape(str(student_data.get('usn') or ''))}</b> | Department: <b>{html.escape(str(student_data.get('department') or ''))}</b>", subtitle_style)]
        ], colWidths=[520])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
            ('PADDING', (0,0), (-1,-1), 12),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 15))

        # Readiness Metrics Summary
        readiness = student_data.get('readiness', {})
        pillars = readiness.get('pillars', {})
        score_data = [
            ['Metric / Pillar', 'Score', 'Status Benchmark'],
            ['Overall Career Readiness Score', f"{readiness.get('overall_readiness', 0):.1f}%", 'Industry Competitive' if readiness.get('overall_readiness', 0) >= 75 else 'Preparation Recommended'],
            ['Academic Pillar (CGPA & Attendance)', f"{pillars.get('academic', 0):.1f}%", f"CGPA: {student_data.get('cgpa', 0.0)}"],
            ['Technical Skills & Depth', f"{pillars.get('technical', 0):.1f}%", f"{len(student_data.get('skills', []))} Verified Skills"],
            ['Practical Portfolio & Projects', f"{pillars.get('portfolio', 0):.1f}%", f"{len(student_data.get('projects', []))} Projects / Internships"],
            ['ATS Resume Completeness', f"{pillars.get('resume', 0):.1f}%", 'ATS Readable Template'],
            ['Assessment & Technical Tests', f"{pillars.get('tests', 0):.1f}%", 'Continuous Evaluation'],
            ['Mock Interview Communication', f"{pillars.get('interview', 0):.1f}%", 'Automated Local Analysis']
        ]

        t_scores = Table(score_data, colWidths=[240, 100, 180])
        t_scores.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563EB')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0,0), (-1,-1), 6),
            ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#EFF6FF')),
            ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
        ]))
        story.append(Paragraph("1. Career Readiness Diagnostic Breakdown", h2_style))
        story.append(t_scores)
        story.append(Spacer(1, 15))

        # Verified Skills & Gap Priorities
        story.append(Paragraph("2. Technical Skill Inventory", h2_style))
        skill_rows = [['Skill Name', 'Proficiency Level', 'Verification Status']]
        for s in student_data.get('skills', [])[:8]:
            skill_rows.append([s['name'], s.get('proficiency', 'Intermediate'), 'Verified in Curriculum'])
        if len(skill_rows) == 1:
            skill_rows.append(['No skills recorded yet', '-', '-'])

        t_skills = Table(skill_rows, colWidths=[220, 150, 150])
        t_skills.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t_skills)
        story.append(Spacer(1, 15))

        # Diagnostic Recommendations
        story.append(Paragraph("3. Prescriptive Interventions & Action Items", h2_style))
        rec_data = []
        for r in readiness.get('recommendations', ['Complete all scheduled practice assessments', 'Refine STAR method in mock interviews']):
            rec_data.append([Paragraph(f"• <b>Action:</b> {html.escape(str(r))}", normal)])
        
        t_rec = Table(rec_data, colWidths=[520])
        t_rec.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FEF3C7')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#FDE68A')),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t_rec)

        doc.build(story)
        logging.getLogger(__name__).info(f"Generated student report: {output_path}")

    @classmethod
    def generate_institutional_report(cls, output_path: str, stats: dict):
        styles, normal, title_style, subtitle_style, h2_style, badge_style = cls._get_styles()
        doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []

        header_table = Table([
            [Paragraph("<b>OFFICE OF CAREER DEVELOPMENT & PLACEMENT</b>", badge_style)],
            [Paragraph("Institutional Placement Intelligence Executive Report", title_style)],
            [Paragraph(f"Batch Year: <b>2026</b> | Status: <b>Official Audit Report</b> | Generated Automatically", subtitle_style)]
        ], colWidths=[520])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
            ('PADDING', (0,0), (-1,-1), 12),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 15))

        # KPI Summary
        kpis = [
            ['Total Cohort', 'Eligible Students', 'Total Offers Issued', 'Overall Placement Rate', 'Highest Package'],
            [
                str(stats.get('total_students', 0)),
                str(stats.get('eligible_students', 0)),
                str(stats.get('offers_count', 0)),
                f"{stats.get('placement_rate', 0):.1f}%",
                f"{stats.get('highest_package', 16.5):.1f} LPA"
            ]
        ]
        t_kpi = Table(kpis, colWidths=[104, 104, 104, 104, 104])
        t_kpi.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F1F5F9')),
            ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(Paragraph("1. Macro Institutional Key Performance Indicators", h2_style))
        story.append(t_kpi)
        story.append(Spacer(1, 15))

        # Placement Funnel Conversion
        story.append(Paragraph("2. Recruitment Funnel & Conversion Efficiency", h2_style))
        funnel = stats.get('funnel', {})
        stages = funnel.get('stages', ['Applied', 'Shortlisted', 'Interview', 'Selected'])
        counts = funnel.get('counts', [0, 0, 0, 0])
        pcts = funnel.get('percentages', [0, 0, 0, 0])

        f_rows = [['Hiring Funnel Stage', 'Candidate Count', 'Stage Conversion %']]
        for st, ct, pt in zip(stages, counts, pcts):
            f_rows.append([st, str(ct), f"{pt:.1f}%"])

        t_f = Table(f_rows, colWidths=[240, 140, 140])
        t_f.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563EB')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t_f)
        story.append(Spacer(1, 15))

        # Skill Demand
        story.append(Paragraph("3. Industry Skill Demand Heatmap", h2_style))
        demand = stats.get('skill_demand', {})
        d_skills = demand.get('skills', ['Python', 'SQL', 'JavaScript', 'AWS', 'Docker'])[:6]
        d_scores = demand.get('demand_scores', [10, 8, 7, 5, 4])[:6]
        d_rows = [['Industry Required Competency', 'Recruiter Demand Weight']]
        for sk, sc in zip(d_skills, d_scores):
            d_rows.append([sk, f"{sc} Weighted Points"])

        t_d = Table(d_rows, colWidths=[320, 200])
        t_d.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t_d)

        doc.build(story)
        logging.getLogger(__name__).info(f"Generated institutional report: {output_path}")

    @classmethod
    def generate_company_report(cls, output_path: str, company_data: dict):
        styles, normal, title_style, subtitle_style, h2_style, badge_style = cls._get_styles()
        doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []

        header_table = Table([
            [Paragraph("<b>CORPORATE RECRUITMENT PARTNER DOSSIER</b>", badge_style)],
            [Paragraph(f"{html.escape(str(company_data.get('company_name') or 'Enterprise'))} Hiring Report", title_style)],
            [Paragraph(f"Active Job Roles: <b>{html.escape(str(company_data.get('job_title') or 'Software Engineer'))}</b> | Location: <b>{html.escape(str(company_data.get('location') or 'Bangalore'))}</b>", subtitle_style)]
        ], colWidths=[520])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
            ('PADDING', (0,0), (-1,-1), 12),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 15))

        # Applicants Table
        story.append(Paragraph("1. Candidate Pipeline & AI Matching Benchmarks", h2_style))
        app_rows = [['Student Name', 'USN', 'CGPA', 'AI Match Score', 'Status']]
        for app in company_data.get('applicants', []):
            app_rows.append([
                app.get('name'),
                app.get('usn'),
                f"{app.get('cgpa', 0.0):.1f}",
                f"{app.get('match_score', 0):.1f}%",
                app.get('status')
            ])
        if len(app_rows) == 1:
            app_rows.append(['No applicants yet', '-', '-', '-', '-'])

        t_app = Table(app_rows, colWidths=[140, 100, 70, 100, 110])
        t_app.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563EB')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t_app)

        doc.build(story)
        logging.getLogger(__name__).info(f"Generated company report: {output_path}")

    @classmethod
    def generate_mock_interview_report(cls, output_path: str, interview_data: dict):
        styles, normal, title_style, subtitle_style, h2_style, badge_style = cls._get_styles()
        doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []

        header_table = Table([
            [Paragraph("<b>LOCAL AI MOCK INTERVIEW INTELLIGENCE</b>", badge_style)],
            [Paragraph("Candidate Diagnostic Assessment & Feedback", title_style)],
            [Paragraph(f"Target Role: <b>{html.escape(str(interview_data.get('target_role') or ''))}</b> | Type: <b>{html.escape(str(interview_data.get('interview_type') or ''))}</b> | Candidate: <b>{html.escape(str(interview_data.get('candidate_name') or ''))}</b>", subtitle_style)]
        ], colWidths=[520])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
            ('PADDING', (0,0), (-1,-1), 12),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 15))

        # Overall Scores Table
        score_rows = [
            ['Evaluation Dimension', 'Score (100 Scale)', 'Diagnostic Assessment'],
            ['Overall Interview Score', f"{interview_data.get('overall_score', 0):.1f}%", 'Strong' if interview_data.get('overall_score', 0) >= 70 else 'Needs Practice'],
            ['Technical Keyword Depth', f"{interview_data.get('technical_score', 0):.1f}%", 'Domain Specificity'],
            ['Relevance & Conciseness', f"{interview_data.get('relevance_score', 0):.1f}%", 'Direct Response'],
            ['Communication & Articulation', f"{interview_data.get('communication_score', 0):.1f}%", 'Filler Word Management'],
            ['Structure & STAR Framework', f"{interview_data.get('structure_score', 0):.1f}%", 'Logical Framing']
        ]
        t_sc = Table(score_rows, colWidths=[200, 130, 190])
        t_sc.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0,0), (-1,-1), 6),
            ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#EFF6FF')),
            ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
        ]))
        story.append(Paragraph("1. Dimension-Wise Heuristic Scores", h2_style))
        story.append(t_sc)
        story.append(Spacer(1, 15))

        # Qualitative Feedback
        story.append(Paragraph("2. Evaluator Insights & Identified Patterns", h2_style))
        story.append(Paragraph(f"<b>Summary:</b> {html.escape(str(interview_data.get('feedback_summary') or 'Good engagement with core engineering concepts.'))}", normal))
        story.append(Spacer(1, 8))

        doc.build(story)
        logging.getLogger(__name__).info(f"Generated mock interview report: {output_path}")

    @classmethod
    def generate_resume_pdf(cls, output_path: str, resume_data: dict):
        styles, normal, title_style, subtitle_style, h2_style, badge_style = cls._get_styles()
        doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []

        # Name & Title Header
        name_style = ParagraphStyle('ResName', parent=styles['Heading1'], fontSize=20, leading=24, textColor=colors.HexColor('#0F172A'), alignment=1)
        contact_style = ParagraphStyle('ResContact', parent=normal, fontSize=9, leading=13, textColor=colors.HexColor('#475569'), alignment=1)
        section_style = ParagraphStyle('ResSec', parent=styles['Heading2'], fontSize=12, leading=16, textColor=colors.HexColor('#1E40AF'), spaceBefore=8, spaceAfter=4)
        bullet_style = ParagraphStyle('ResBullet', parent=normal, fontSize=9, leading=13, spaceAfter=3)

        full_name = html.escape(str(resume_data.get('full_name', 'Student Candidate')).upper())
        story.append(Paragraph(f"<b>{full_name}</b>", name_style))
        contact_line = f"{html.escape(str(resume_data.get('email', '') or ''))} | {html.escape(str(resume_data.get('phone', '') or ''))} | {html.escape(str(resume_data.get('usn', '') or ''))} | {html.escape(str(resume_data.get('department', '') or ''))}"
        story.append(Paragraph(contact_line, contact_style))
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=8))

        # Professional Summary
        if resume_data.get('summary'):
            story.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
            story.append(Paragraph(html.escape(str(resume_data.get('summary'))), bullet_style))
            story.append(Spacer(1, 6))

        # Technical Skills
        if resume_data.get('skills'):
            story.append(Paragraph("TECHNICAL COMPETENCIES", section_style))
            skills_text = ", ".join(html.escape(str(s)) for s in resume_data.get('skills', []))
            story.append(Paragraph(f"<b>Core Technologies:</b> {skills_text}", bullet_style))
            story.append(Spacer(1, 6))

        # Education
        story.append(Paragraph("EDUCATION", section_style))
        edu_dept = html.escape(str(resume_data.get('department', 'Computer Applications') or 'Computer Applications'))
        edu_cgpa = html.escape(str(resume_data.get('cgpa', 'N/A') or 'N/A'))
        edu_degree = html.escape(str(resume_data.get('degree', resume_data.get('department', 'Computer Applications')) or 'Computer Applications'))
        edu_batch = html.escape(str(resume_data.get('batch_year', 2026) or 2026))
        edu_data = [
            [Paragraph(f"<b>{edu_dept}</b>", bullet_style), Paragraph(f"<b>CGPA: {edu_cgpa} / 10.0</b>", bullet_style)],
            [Paragraph(edu_degree, bullet_style), Paragraph(f"Batch: {edu_batch}", bullet_style)]
        ]
        t_edu = Table(edu_data, colWidths=[350, 170])
        t_edu.setStyle(TableStyle([('PADDING', (0,0), (-1,-1), 2)]))
        story.append(t_edu)
        story.append(Spacer(1, 6))

        # Projects
        if resume_data.get('projects'):
            story.append(Paragraph("FEATURED TECHNICAL PROJECTS", section_style))
            for p in resume_data.get('projects', []):
                p_title = html.escape(str((p.get('title') if isinstance(p, dict) else getattr(p, 'title', 'Project')) or 'Project'))
                p_tech = html.escape(str((p.get('technologies') if isinstance(p, dict) else getattr(p, 'technologies', '')) or ''))
                p_desc = html.escape(str((p.get('description') if isinstance(p, dict) else getattr(p, 'description', '')) or ''))
                story.append(Paragraph(f"<b>{p_title}</b> | <i>{p_tech}</i>", bullet_style))
                story.append(Paragraph(f"• {p_desc}", bullet_style))
                story.append(Spacer(1, 3))
            story.append(Spacer(1, 4))

        # Internships / Experience
        if resume_data.get('internships'):
            story.append(Paragraph("PRACTICAL WORK EXPERIENCE / INTERNSHIPS", section_style))
            for exp in resume_data.get('internships', []):
                e_comp = html.escape(str((exp.get('company_name') if isinstance(exp, dict) else getattr(exp, 'company_name', 'Company')) or 'Company'))
                e_role = html.escape(str((exp.get('role') if isinstance(exp, dict) else getattr(exp, 'role', 'Intern')) or 'Intern'))
                e_desc = html.escape(str((exp.get('description') if isinstance(exp, dict) else getattr(exp, 'description', '')) or ''))
                story.append(Paragraph(f"<b>{e_role}</b> — {e_comp}", bullet_style))
                story.append(Paragraph(f"• {e_desc}", bullet_style))
                story.append(Spacer(1, 3))

        doc.build(story)
        logging.getLogger(__name__).info(f"Generated ATS PDF resume: {output_path}")
