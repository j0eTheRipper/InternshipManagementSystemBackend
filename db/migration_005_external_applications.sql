ALTER TABLE application ALTER COLUMN opportunity_id DROP NOT NULL;

CREATE TABLE IF NOT EXISTS external_application (
    application_id INTEGER PRIMARY KEY REFERENCES application(application_id) ON DELETE CASCADE,
    company_name VARCHAR NOT NULL,
    job_title VARCHAR NOT NULL,
    job_mode VARCHAR(20) NOT NULL,
    company_location VARCHAR NOT NULL,
    application_screenshot VARCHAR NOT NULL
);
