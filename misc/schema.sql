CREATE TABLE users (
	user_id SERIAL PRIMARY KEY,
	username VARCHAR NOT NULL,
	email VARCHAR,
	join_date DATE NOT NULL
	);

CREATE TABLE user_extras (
	user_id INT PRIMARY KEY,
    full_name: VARCHAR,
	bio TEXT,
	avatar VARCHAR
	);

CREATE TABLE user_skills (
    user_id INT NOT NULL,
    skill VARCHAR NOT NULL,
    level VARCHAR DEFAULT 'Beginner'
    );

CREATE TABLE project_info (
	project_id SERIAL PRIMARY KEY,
	owner VARCHAR NOT NULL,
	title VARCHAR NOT NULL,
	short_desc TEXT,
	long_desc TEXT,
	last_edit DATE,
	posted_date DATE NOT NULL
	);

CREATE TABLE project_skills (
    project_id INT NOT NULL,
    skill VARCHAR NOT NULL
    );

CREATE TABLE project_members (
    project_id INT NOT NULL,
    member VARCHAR NOT NULL
    );

CREATE TABLE project_extras (
	project_id INT NOT NULL,
	update TEXT,
	git_link VARCHAR
	);

CREATE TABLE applications (
    id SERIAL PRIMARY KEY,
	project_id INT NOT NULL,
	applicant_id INT NOT NULL,
    status VARCHAR DEFAULT 'pending',
	date_applied DATE NOT NULL
	);

CREATE TABLE skills (
    name VARCHAR NOT NULL,
    approved BOOLEAN DEFAULT False,
    count INT DEFAULT 0
    );

CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    recipient_id INT NOT NULL,
    sender_id INT NOT NULL,
    type_id INT NOT NULL,
    read BOOLEAN DEFAULT False,
    deleted BOOLEAN DEFAULT False,
    created_date DATE NOT NULL
    );

CREATE TABLE notification_type (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    template TEXT
    );

CREATE TABLE invitations (
    id SERIAL PRIMARY KEY,
    recipient_id INT NOT NULL,
    sender_id INT NOT NULL,
    project_id INT NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'pending',
    sent_date DATE NOT NULL
);
