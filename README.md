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

#### Database setup
```bash
psql -U postgres -c "CREATE DATABASE project_mgmt;"
psql -U postgres -c "CREATE DATABASE test_project_mgmt;"
psql -U postgres -d test_project_mgmt -f sql/schema.sql
psql -U postgres -d project_mgmt -f sql/schema.sql
```


## How to run
In your project directory, run commands
```bash
fastapi run main.py
```

## OR IN DOCKER CONTAINER
#### Prerequisites: You need a docker to be installed on your machine
Build Docker container:
```bash

```
Run Docker container:
```bash

```
