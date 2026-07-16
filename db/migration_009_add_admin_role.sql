INSERT INTO role (role) VALUES ('admin') ON CONFLICT DO NOTHING;

INSERT INTO users (fullname, email, password, role)
VALUES ('Admin', 'admin@system.com', 'admin123', 'admin')
ON CONFLICT DO NOTHING;
