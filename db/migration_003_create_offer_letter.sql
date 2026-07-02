CREATE TABLE IF NOT EXISTS offer_letter (
    offer_letter_id SERIAL PRIMARY KEY,
    application_id INTEGER NOT NULL REFERENCES application(application_id),
    student_id VARCHAR NOT NULL REFERENCES student(student_id),
    file VARCHAR NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
