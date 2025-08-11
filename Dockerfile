FROM python:3.12.4-slim

WORKDIR /main

COPY . .

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"]