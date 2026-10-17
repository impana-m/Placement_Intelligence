-- Placement Intelligence: one-time job status migration
USE placement_intelligence;

ALTER TABLE jobs
MODIFY COLUMN status ENUM('Active', 'Paused', 'Closed', 'Draft')
NOT NULL DEFAULT 'Active';

SHOW COLUMNS FROM jobs LIKE 'status';
