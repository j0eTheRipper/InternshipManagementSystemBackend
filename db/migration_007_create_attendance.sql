CREATE TABLE IF NOT EXISTS attendance (
    attendance_id SERIAL PRIMARY KEY,
    student_id VARCHAR NOT NULL REFERENCES student(student_id),
    checked_at TIMESTAMP NOT NULL DEFAULT NOW()
);
