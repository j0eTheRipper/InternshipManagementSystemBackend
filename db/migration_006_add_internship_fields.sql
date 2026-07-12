ALTER TABLE student ADD COLUMN IF NOT EXISTS internship_start_date VARCHAR;
ALTER TABLE student ADD COLUMN IF NOT EXISTS internship_duration_weeks INTEGER DEFAULT 12;
