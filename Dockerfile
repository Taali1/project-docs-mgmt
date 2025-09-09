FROM python:3.10.7-slim

# Coping a necessary files
COPY . .

# Install curl
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y libpq-dev gcc python3-dev

# Installing required packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Importing environmental variables
ENV SECRET_KEY=${SECRET_KEY}
ENV ALGORITHM=${ALGORITHM}
ENV TOKEN_EXPIRE_IN_MINUTES=${TOKEN_EXPIRE_IN_MINUTES}
ENV TIME_ZONE_UTC_OFFSET=${TIME_ZONE_UTC_OFFSET}

ENV DB_HOST=${DB_HOST}
ENV DB_NAME=${DB_NAME}
ENV DB_USER=${DB_USER}
ENV DB_PASSWORD=${DB_PASSWORD}

# Starting a service
CMD ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"]