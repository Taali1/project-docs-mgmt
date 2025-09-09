# <center> Project Dcoumentation Management Application </center>

### About
`project-docs-mgmt` is a Python-based application for managing project documentation. It offers a structured way to create, store, and organize documentation directly within the project repository.


## How to setup
#### Prerequisites: For application working you need have installed Python, Git and PostgreSQL

In your choosen directory, run commands:

#### Manual application setup
```bash
git clone https://github.com/Taali1/project-docs-mgmt.git
cd project-docs-mgmt
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

#### Database setup (it will ask for password)
```bash
psql -U postgres -c "CREATE DATABASE project_mgmt;"
```
```bash
psql -U postgres -c "CREATE DATABASE test_project_mgmt;"
```
```bash
psql -U postgres -d test_project_mgmt -f sql/schema.sql
```
```bash
psql -U postgres -d project_mgmt -f sql/schema.sql
```


## How to run
In your project directory, run commands
```bash
fastapi run main.py
```

## Or in the Docker container
#### Prerequisites: You need a docker to be installed on your machine
Pulling Docker container:
```bash
docker pull taali1/project-docs-mgmt:latest
```
Run Docker container:
```bash
docker run --env-file .env taali1/project-docs-mgmt
```
