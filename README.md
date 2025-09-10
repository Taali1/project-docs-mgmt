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
Get SQL schema file:
```bash
curl -L -o schema.sql https://raw.githubusercontent.com/Taali1/project-docs-mgmt/main/sql/schema.sql
```
Create databases:
```bash
psql -U postgres -c "CREATE DATABASE project_mgmt;"
```
```bash
psql -U postgres -c "CREATE DATABASE test_project_mgmt;"
```
Create schemas for databases
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

Create databases schema, it creates container from pulled image:
```bash
docker pull postgres:15
curl -L -o schema.sql https://raw.githubusercontent.com/Taali1/project-docs-mgmt/main/sql/schema.sql
docker run -d --name postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=project_mgmt -p 5432:5432 postgres:15
docker run -d --name test_postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=test_project_mgmt -p 5433:5433 postgres:15
docker exec -i postgres psql -U postgres -d project_mgmt < schema.sql
docker exec -i postgres psql -U postgres -d test_project_mgmt < schema.sql
```

Run Docker container:
```bash
docker run --env-file .env taali1/project-docs-mgmt
```
If postgres doesn't show in:
```bash
docker ps
```
Run Docker image once more:
```bash
docker run -d --name postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=project_mgmt -p 5432:5432 postgres:15
docker run -d --name test_postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=test_project_mgmt -p 5433:5433 postgres:15
```
