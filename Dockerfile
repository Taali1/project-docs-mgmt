FROM python:3.12.4-slim

WORKDIR /main

COPY . .

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV SECRET_KEY=${SECRET_KEY}
ENV ALGORITHM=${ALGORITHM}
ENV DATABASE_URL=${DATABASE_URL}
ENV TOKEN_EXPIRE_IN_MINUTES=${TOKEN_EXPIRE_IN_MINUTES}

CMD ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"]