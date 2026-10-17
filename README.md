# AI-Powered College Placement & Career Development Intelligence System

Placement Intelligence is an existing Flask + SQLAlchemy + MySQL platform for students, placement officers, faculty and recruiters. The project keeps its original architecture and local-intelligence approach.

## Main capabilities

- Role-based student, officer, faculty and recruiter workflows
- AI/local-NLP job matching and skill-gap analysis
- Explainable placement-readiness scoring from stored student activity
- Resume parsing and ATS-style completeness analysis
- Placement drives, applications, interviews, offers and notifications
- Institutional analytics and PDF reports
- **Local Mock Interview:** 120 tagged questions across technical, HR, behavioral, situational and communication categories, with difficulty selection and response diagnostics
- **QT/Aptitude Hub:** 234 seeded quantitative-practice questions across 13 topics, randomized timed tests, explanations, topic performance and history

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Student | `student.rahul@college.edu` | `Password@123` |
| Placement Officer | `officer@college.edu` | `Password@123` |
| Faculty | `faculty.bca@college.edu` | `Password@123` |
| Recruiter | `recruiter@techcorpsolutions.com` | `Password@123` |

Additional demo students/recruiters created by the expansion script use `Password@123`.

## Setup

1. Create the MySQL database `placement_intelligence`.
2. Configure `.env` using `.env.example`. Never commit `.env`.
3. Install the pinned requirements:

```powershell
pip install -r requirements.txt
```

4. If this is an **existing database**, run the one-time schema migration:

```text
database/migration_2026_09_28.sql
```

The migration adds `Paused` to job-drive status and adds question difficulty/topic/marks plus the expanded mock-interview categories.

5. Seed and expand the realistic demo dataset:

```powershell
python database/seed_data.py
```

The seed is idempotent and preserves existing records. The expansion stage creates approximately 75 students, 30 total job drives when combined with the original seed, 150 interconnected applications, 12 offers, 234 QT questions, and mock-interview history. The local interview bank contains 120 questions in code.

6. Run automated tests:

```powershell
python -m unittest tests/test_system.py
```

7. Start the application:

```powershell
python app.py
```

Open `http://127.0.0.1:5000`.

## Database notes

The production/demo database remains **MySQL 8**. SQLite is only suitable as an isolated development/test substitute; do not migrate the project's intended database architecture.

## Security notes

- Public registration creates student accounts only. Institutional roles are provisioned by the institution.
- Login redirects accept only local relative paths, preventing external open redirects.
- Recruiter application-status updates verify company ownership server-side.
- Closed and draft job drives cannot be reactivated through the pause/activate action.
- Production/demo mode does not enable Flask's raw debug traceback unless `FLASK_DEBUG=1` is explicitly set.
