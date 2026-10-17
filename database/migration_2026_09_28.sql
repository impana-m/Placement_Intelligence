-- Placement Intelligence schema update — 2026-09-28
-- Run once against an existing MySQL 8 database after backing up the DB.
USE placement_intelligence;

-- 1) Campus job-drive status: Active <-> Paused, plus Closed/Draft.
ALTER TABLE jobs
MODIFY COLUMN status ENUM('Active', 'Paused', 'Closed', 'Draft')
NOT NULL DEFAULT 'Active';

-- 2) Larger QT question metadata.
ALTER TABLE questions
ADD COLUMN topic VARCHAR(100) NULL,
ADD COLUMN difficulty VARCHAR(20) NOT NULL DEFAULT 'Medium',
ADD COLUMN marks INT NOT NULL DEFAULT 1;

-- 3) More precise local mock-interview categories.
ALTER TABLE mock_interview_sessions
MODIFY COLUMN interview_type ENUM(
    'Technical', 'HR', 'Behavioral', 'Situational', 'Communication', 'Mixed'
) NOT NULL DEFAULT 'Technical';

ALTER TABLE mock_interview_qa
ADD COLUMN difficulty VARCHAR(20) NOT NULL DEFAULT 'Medium';

-- Verify the critical schema changes.
SHOW COLUMNS FROM jobs LIKE 'status';
SHOW COLUMNS FROM questions LIKE 'difficulty';
SHOW COLUMNS FROM questions LIKE 'marks';
SHOW COLUMNS FROM mock_interview_sessions LIKE 'interview_type';
SHOW COLUMNS FROM mock_interview_qa LIKE 'difficulty';
