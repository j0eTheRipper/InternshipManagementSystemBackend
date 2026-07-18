ALTER TYPE progress ADD VALUE IF NOT EXISTS 'pending_documents';

CREATE TABLE IF NOT EXISTS indemnity_letter (
    indemnity_letter_id SERIAL PRIMARY KEY,
    student_id VARCHAR NOT NULL REFERENCES student(student_id),
    file VARCHAR NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS placement_agreement (
    placement_agreement_id SERIAL PRIMARY KEY,
    student_id VARCHAR NOT NULL REFERENCES student(student_id),
    file VARCHAR NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE student ADD COLUMN IF NOT EXISTS company_supervisor_name VARCHAR;
ALTER TABLE student ADD COLUMN IF NOT EXISTS company_supervisor_email VARCHAR;
ALTER TABLE student ADD COLUMN IF NOT EXISTS company_supervisor_phone VARCHAR;
