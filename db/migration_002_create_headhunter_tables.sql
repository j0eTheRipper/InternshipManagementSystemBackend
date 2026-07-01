INSERT INTO role (role) VALUES ('headhunter') ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS company (
    company_id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    email VARCHAR NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS headhunter (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    company_id INTEGER NOT NULL REFERENCES company(company_id)
);

CREATE TABLE IF NOT EXISTS job_opportunity (
    opportunity_id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    job_role VARCHAR NOT NULL,
    description TEXT NOT NULL,
    location VARCHAR NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'remote',
    headhunter_id INTEGER NOT NULL REFERENCES headhunter(user_id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS application (
    application_id SERIAL PRIMARY KEY,
    student_id VARCHAR NOT NULL REFERENCES student(student_id),
    opportunity_id INTEGER NOT NULL REFERENCES job_opportunity(opportunity_id),
    resume_id INTEGER NOT NULL REFERENCES resume(resume_id),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    UNIQUE(student_id, opportunity_id)
);
