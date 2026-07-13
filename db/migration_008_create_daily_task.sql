CREATE TABLE IF NOT EXISTS daily_task (
    daily_task_id SERIAL PRIMARY KEY,
    student_id VARCHAR NOT NULL REFERENCES student(student_id),
    update_text TEXT NOT NULL,
    update_date DATE NOT NULL DEFAULT CURRENT_DATE,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    submitted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(student_id, update_date)
);
