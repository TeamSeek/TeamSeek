CREATE TABLE users (
	user_id SERIAL PRIMARY KEY,
	username VARCHAR NOT NULL,
	email VARCHAR,
	join_date DATE
	);

CREATE TABLE user_extras (
	user_id INT PRIMARY KEY,
  full_name: VARCHAR,
	bio TEXT,
	avatar VARCHAR
	);

CREATE TABLE user_skills (
    user_id INT,
    skill VARCHAR,
    level VARCHAR DEFAULT 'Beginner'
    );

CREATE TABLE project_info (
	project_id SERIAL PRIMARY KEY,
	owner VARCHAR,
	title VARCHAR,
	short_desc TEXT,
	long_desc TEXT,
	last_edit DATE,
	posted_date DATE
	);

CREATE TABLE project_skills (
    project_id INT,
    skill VARCHAR
    );

CREATE TABLE project_members (
    project_id INT,
    member VARCHAR
    );

CREATE TABLE project_extras (
	project_id INT,
	update TEXT,
	git_link VARCHAR
	);

CREATE TABLE applications (
	project_id INT,
	user_id INT,
	status VARCHAR,
	date_applied DATE
	);

CREATE TABLE skills (
    name VARCHAR,
    approved BOOLEAN,
    count INT
    );
