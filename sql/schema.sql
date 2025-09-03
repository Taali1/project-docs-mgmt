-- Create users TABLE
CREATE TABLE users (
	user_id VARCHAR(40) PRIMARY KEY ,
	password VARCHAR(40) NOT NULL
	);

-- Create projects TABLE
CREATE TABLE projects (
	project_id SERIAL PRIMARY KEY, 
	name VARCHAR(50) NOT NULL, 
	description TEXT, 
	created_at TIMESTAMP NOT NULL, 
	modified_at TIMESTAMP NOT NULL
	);

-- Create TYPE ENUM for permission used in user_project table
CREATE TYPE permission AS ENUM ('owner', 'participant');

-- Create user_project table TABLE
CREATE TABLE user_project (
	user_id VARCHAR(30) NOT NULL, 
	project_id INT NOT NULL, 
	permission PERMISSION NOT NULL, 
	FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE, 
	FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
	);
